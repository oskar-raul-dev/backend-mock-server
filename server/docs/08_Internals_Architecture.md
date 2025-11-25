# Internals & Architecture

This guide explains the internal architecture of MockServer, including system components, request flow, matching algorithms, design patterns, and extensibility points.

---

## System Architecture

MockServer follows a modular, layered architecture designed for maintainability and extensibility.

### High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                    HTTP Request                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Flask Web Server                            │
│  - CORS handling                                         │
│  - Request parsing                                       │
│  - Error handling                                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│           Request Matcher Engine                         │
│  - URL regex matching                                    │
│  - Method validation                                     │
│  - Header matching                                       │
│  - Query parameter matching                              │
│  - Body matching (semantic/partial/strict)               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│            Validation Layer                              │
│  - Custom validator execution                            │
│  - Business rule enforcement                             │
│  - ValueError handling                                   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│            Processing Layer                              │
│  - Custom processor execution                            │
│  - Data extraction                                       │
│  - Data transformation                                   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│          Response Generator                              │
│  - Template variable substitution                        │
│  - Jinja2 template rendering                             │
│  - Response formatting                                   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                HTTP Response                             │
└─────────────────────────────────────────────────────────┘
```

---

## Component Overview

### 1. Main Application (`main.py`)

**Responsibilities:**
- Command-line argument parsing
- Configuration loading
- Flask app initialization
- Server startup
- Auto-reload setup (development mode)

**Key functions:**
- `parse_arguments()` - Parses CLI options
- `load_configuration()` - Loads `config.py`
- `load_endpoints()` - Loads endpoint definitions
- `setup_flask_app()` - Initializes Flask with routes
- `run_server()` - Starts the HTTP server

**Example:**
```python
def main():
    args = parse_arguments()
    config = load_configuration(args.config_dir)
    definitions = load_endpoints(args.config_dir, args.endpoints_file)
    app = setup_flask_app(definitions, config)
    run_server(app, config)
```

### 2. Configuration Loader

**Location:** `mockserver/config/loader.py`

**Responsibilities:**
- Import Python configuration files
- Validate configuration structure
- Provide default values
- Handle configuration errors

**Configuration structure:**
```python
CONFIG = {
    "server": {
        "port": 9090,
        "host": "0.0.0.0",
        "cors_enabled": True,
        "cors_origins": "*",
        "reload": True
    },
    "logging": {
        "level": "INFO"
    },
    "paths": {
        "requests_dir": None,
        "responses_dir": None
    }
}
```

### 3. Request Matcher

**Location:** `mockserver/core/matcher.py`

**Responsibilities:**
- Iterate through endpoint definitions
- Match requests against patterns
- Handle multiple definition formats
- First-match semantics

**Matching order:**
1. URL pattern (regex)
2. HTTP method
3. Query parameters
4. Headers
5. Body structure

**Example:**
```python
def find_matching_definition(request, definitions):
    for definition in definitions:
        if matches_url(request, definition):
            if matches_method(request, definition):
                if matches_query_params(request, definition):
                    if matches_headers(request, definition):
                        if matches_body(request, definition):
                            return definition
    return None
```

### 4. Body Matching Engine

**Location:** `mockserver/body_matching/`

**Components:**
- `json_matcher.py` - JSON semantic matching
- `xml_matcher.py` - XML semantic matching
- `text_matcher.py` - Plain text matching
- `binary_matcher.py` - Binary data matching

#### JSON Matcher

**Algorithm:**
1. Parse expected and actual JSON
2. Compare structures recursively
3. Handle nested objects and arrays
4. Ignore key order (semantic mode)
5. Allow extra keys (partial mode)

**Example:**
```python
def match_json_semantic(expected, actual):
    """
    Semantic JSON matching - ignores key order.
    """
    expected_obj = json.loads(expected)
    actual_obj = json.loads(actual)

    return deep_compare(expected_obj, actual_obj)

def deep_compare(expected, actual):
    """
    Recursively compare JSON structures.
    """
    if type(expected) != type(actual):
        return False

    if isinstance(expected, dict):
        for key in expected:
            if key not in actual:
                return False
            if not deep_compare(expected[key], actual[key]):
                return False
        return True

    elif isinstance(expected, list):
        if len(expected) != len(actual):
            return False
        return all(
            deep_compare(expected[i], actual[i])
            for i in range(len(expected))
        )

    else:
        return expected == actual
```

#### XML Matcher

**Algorithm:**
1. Parse expected and actual XML
2. Build element trees
3. Compare structures recursively
4. Ignore element order (semantic mode)
5. Compare text content
6. Compare attributes

**Example:**
```python
def match_xml_semantic(expected, actual):
    """
    Semantic XML matching - ignores element order.
    """
    expected_tree = ET.fromstring(expected)
    actual_tree = ET.fromstring(actual)

    return compare_elements(expected_tree, actual_tree)

def compare_elements(expected, actual):
    """
    Recursively compare XML elements.
    """
    # Compare tag names
    if expected.tag != actual.tag:
        return False

    # Compare text content
    if (expected.text or '').strip() != (actual.text or '').strip():
        return False

    # Compare attributes
    if expected.attrib != actual.attrib:
        return False

    # Compare children (order-independent)
    expected_children = sorted(expected, key=lambda e: e.tag)
    actual_children = sorted(actual, key=lambda e: e.tag)

    if len(expected_children) != len(actual_children):
        return False

    return all(
        compare_elements(exp, act)
        for exp, act in zip(expected_children, actual_children)
    )
```

### 5. Validator Executor

**Location:** `mockserver/core/validator.py`

**Responsibilities:**
- Execute custom validator functions
- Catch and format ValueError exceptions
- Return validation errors to client

**Flow:**
```python
def execute_validator(validator_func, body):
    """
    Execute validator and handle errors.
    """
    try:
        validator_func(body)  # Raises ValueError on failure
        return None  # No error
    except ValueError as e:
        return {
            "error": "Validation failed",
            "message": str(e)
        }
    except Exception as e:
        return {
            "error": "Validator error",
            "message": f"Unexpected error: {str(e)}"
        }
```

### 6. Processor Executor

**Location:** `mockserver/core/processor.py`

**Responsibilities:**
- Execute custom processor functions
- Capture returned dictionary
- Handle processing errors gracefully

**Flow:**
```python
def execute_processor(processor_func, body):
    """
    Execute processor and return processed data.
    """
    try:
        processed_data = processor_func(body)

        if not isinstance(processed_data, dict):
            raise TypeError(
                f"Processor must return dict, got {type(processed_data)}"
            )

        return processed_data

    except Exception as e:
        logger.error(f"Processor error: {e}")
        return {}  # Return empty dict on error
```

### 7. Template Renderer

**Location:** `mockserver/core/template.py`

**Responsibilities:**
- Prepare template context
- Render Jinja2 templates
- Handle template errors

**Context variables:**
```python
def build_template_context(request, path_params, processed_body):
    """
    Build context for Jinja2 template rendering.
    """
    return {
        "QUERY_PARAMS": request.args,
        "PATH_PARAMS": path_params,
        "HEADERS": {k.lower(): v for k, v in request.headers.items()},
        "BODY": request.get_data(as_text=True),
        "BODY_PROCESSED": processed_body
    }
```

**Rendering:**
```python
def render_response_body(template_str, context):
    """
    Render response body using Jinja2.
    """
    try:
        template = jinja2.Template(template_str)
        return template.render(context)
    except jinja2.TemplateError as e:
        logger.error(f"Template rendering error: {e}")
        raise
```

### 8. Response Builder

**Location:** `mockserver/core/response.py`

**Responsibilities:**
- Build Flask response objects
- Set status codes
- Set headers
- Handle body from file or inline

**Flow:**
```python
def build_response(response_config, context, config_dir):
    """
    Build HTTP response from configuration.
    """
    status = response_config.get('status', 200)
    headers = response_config.get('headers', {})

    # Get body from file or inline
    if 'body_file' in response_config:
        body = load_body_from_file(
            response_config['body_file'],
            config_dir
        )
    else:
        body = response_config.get('body', '')

    # Render template
    rendered_body = render_response_body(body, context)

    # Create Flask response
    response = make_response(rendered_body, status)

    for key, value in headers.items():
        response.headers[key] = value

    return response
```

---

## Request Flow

### Complete Request Lifecycle

```
1. HTTP Request arrives
   └─> Flask receives request

2. CORS preflight (if OPTIONS)
   └─> Return CORS headers

3. Extract request data
   └─> URL, method, headers, query params, body

4. Find matching definition
   ├─> Match URL pattern
   ├─> Match HTTP method
   ├─> Match query parameters
   ├─> Match headers
   └─> Match body structure

5. Definition found?
   ├─> No: Return 404 with "No matching mock found"
   └─> Yes: Continue

6. Execute validator (if defined)
   ├─> Validation fails: Return 400 with error message
   └─> Validation succeeds: Continue

7. Execute processor (if defined)
   └─> Returns processed data dict

8. Build template context
   └─> QUERY_PARAMS, PATH_PARAMS, HEADERS, BODY, BODY_PROCESSED

9. Select response (handle round-robin)
   └─> Get next response in cycle

10. Render response body
    └─> Jinja2 template with context

11. Build HTTP response
    └─> Status, headers, rendered body

12. Return response
    └─> Send to client
```

### Error Handling

MockServer handles errors at multiple levels:

**1. Matching errors (404):**
```json
{
    "error": "No matching mock found for request",
    "details": {
        "method": "POST",
        "url": "/api/unknown",
        "headers": {...}
    }
}
```

**2. Validation errors (400):**
```json
{
    "error": "Validation failed",
    "message": "Age must be between 18 and 120, got 15"
}
```

**3. Template rendering errors (500):**
```json
{
    "error": "Template rendering failed",
    "message": "UndefinedError: 'BODY_PROCESSED' is undefined"
}
```

**4. Server errors (500):**
```json
{
    "error": "Internal server error",
    "message": "Unexpected error occurred"
}
```

---

## Matching Algorithm

### URL Matching

**Implementation:**
```python
import re

def matches_url(request, definition):
    """
    Match URL against regex pattern.
    """
    pattern = definition['request']['url']

    # Compile regex
    compiled = re.compile(pattern)

    # Match against request path
    match = compiled.match(request.path)

    if match:
        # Extract path parameters
        path_params = match.groups()
        return True, path_params
    else:
        return False, []
```

### Query Parameter Matching

**Implementation:**
```python
def matches_query_params(request, definition):
    """
    Match query parameters against patterns.
    """
    expected_params = definition['request'].get('query_params', {})

    for param_name, param_pattern in expected_params.items():
        # Check parameter exists
        if param_name not in request.args:
            return False

        # Match parameter value against regex
        param_value = request.args[param_name]
        if not re.match(param_pattern, param_value):
            return False

    return True
```

### Header Matching

**Implementation:**
```python
def matches_headers(request, definition):
    """
    Match headers against patterns (case-insensitive).
    """
    expected_headers = definition['request'].get('headers', {})

    # Normalize headers to lowercase
    actual_headers = {
        k.lower(): v for k, v in request.headers.items()
    }

    for header_name, header_pattern in expected_headers.items():
        header_name_lower = header_name.lower()

        # Check header exists
        if header_name_lower not in actual_headers:
            return False

        # Match header value against regex
        header_value = actual_headers[header_name_lower]
        if not re.match(header_pattern, header_value):
            return False

    return True
```

### Body Matching

**Implementation:**
```python
def matches_body(request, definition):
    """
    Match body using semantic/partial/strict matching.
    """
    body_config = definition['request'].get('body')

    if not body_config:
        return True  # No body matching required

    actual_body = request.get_data(as_text=True)
    expected_body = body_config.get('value', '')
    body_format = body_config.get('format', 'json')
    matching_mode = body_config.get('matching_mode', 'semantic')

    # Select matcher based on format
    if body_format == 'json':
        matcher = JsonMatcher(matching_mode)
    elif body_format == 'xml':
        matcher = XmlMatcher(matching_mode)
    elif body_format == 'text':
        matcher = TextMatcher(matching_mode)
    else:
        matcher = BinaryMatcher(matching_mode)

    return matcher.matches(expected_body, actual_body)
```

---

## Response Generation

### Round-Robin State Management

**Implementation:**
```python
class RoundRobinManager:
    """
    Manages round-robin response state.
    """
    def __init__(self):
        self.counters = {}  # definition_id -> current_index

    def get_next_response(self, definition_id, responses):
        """
        Get next response in round-robin cycle.
        """
        if definition_id not in self.counters:
            self.counters[definition_id] = 0

        # Get current index
        index = self.counters[definition_id]

        # Get response
        response = responses[index]

        # Increment counter (with wrap-around)
        self.counters[definition_id] = (index + 1) % len(responses)

        return response
```

### File-Based Responses

**Implementation:**
```python
def load_body_from_file(filename, config_dir):
    """
    Load response body from file.
    """
    responses_dir = config.get('paths', {}).get('responses_dir')

    if not responses_dir:
        responses_dir = os.path.join(config_dir, 'responses')

    file_path = os.path.join(responses_dir, filename)

    # Check file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Response file not found: {filename}")

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
```

---

## Design Patterns

### 1. Strategy Pattern (Matching)

Different matching strategies for different body formats:

```python
class BodyMatcher(ABC):
    """Abstract base class for body matchers"""

    @abstractmethod
    def matches(self, expected, actual):
        pass

class JsonMatcher(BodyMatcher):
    def matches(self, expected, actual):
        # JSON-specific matching logic
        pass

class XmlMatcher(BodyMatcher):
    def matches(self, expected, actual):
        # XML-specific matching logic
        pass
```

### 2. Chain of Responsibility (Request Matching)

Request goes through chain of matchers:

```python
def find_match(request, definitions):
    for definition in definitions:
        if url_matcher.matches(request, definition):
            if method_matcher.matches(request, definition):
                if header_matcher.matches(request, definition):
                    if query_matcher.matches(request, definition):
                        if body_matcher.matches(request, definition):
                            return definition
    return None
```

### 3. Template Method (Validation/Processing)

Base flow with customizable steps:

```python
def handle_request(request, definition):
    # Template method
    matched_def = match_request(request, definition)

    if not matched_def:
        return error_response(404)

    # Customizable step
    if validator := matched_def.get('validator'):
        error = execute_validator(validator, request.body)
        if error:
            return error_response(400, error)

    # Customizable step
    processed_data = {}
    if processor := matched_def.get('processor'):
        processed_data = execute_processor(processor, request.body)

    # Generate response
    return build_response(matched_def, request, processed_data)
```

### 4. Factory Pattern (Matcher Creation)

```python
def create_matcher(body_format, matching_mode):
    """
    Factory for creating body matchers.
    """
    matchers = {
        'json': JsonMatcher,
        'xml': XmlMatcher,
        'text': TextMatcher,
        'binary': BinaryMatcher
    }

    matcher_class = matchers.get(body_format, TextMatcher)
    return matcher_class(matching_mode)
```

---

## Extensibility Points

### 1. Custom Body Matchers

Add support for new body formats:

```python
class YamlMatcher(BodyMatcher):
    """
    Custom matcher for YAML bodies.
    """
    def matches(self, expected, actual):
        import yaml
        expected_obj = yaml.safe_load(expected)
        actual_obj = yaml.safe_load(actual)
        return expected_obj == actual_obj

# Register in factory
BODY_MATCHERS['yaml'] = YamlMatcher
```

### 2. Custom Template Functions

Add custom Jinja2 filters:

```python
def custom_filter(value):
    """Custom Jinja2 filter"""
    return value.upper()

# Register filter
jinja_env.filters['custom'] = custom_filter

# Use in template
"body": '{"name": "{{ BODY_PROCESSED.name | custom }}"}'
```

### 3. Middleware

Add custom request/response processing:

```python
@app.before_request
def log_request():
    logger.info(f"Request: {request.method} {request.path}")

@app.after_request
def log_response(response):
    logger.info(f"Response: {response.status_code}")
    return response
```

### 4. Custom Validators

Validators are already extensible by design:

```python
def validate_custom_format(body):
    """Your custom validation logic"""
    data = json.loads(body)
    # Custom validation
    if not meets_criteria(data):
        raise ValueError("Custom validation failed")
```

### 5. Custom Processors

Processors are already extensible by design:

```python
def process_custom_logic(body):
    """Your custom processing logic"""
    data = json.loads(body)
    # Custom processing
    return {
        "custom_field": calculate_something(data)
    }
```

---

## Performance Considerations

### Request Matching Performance

**O(n) complexity** where n = number of endpoint definitions

**Optimization tips:**
1. Place most frequently matched endpoints first
2. Use specific URL patterns (avoid wildcards)
3. Minimize use of complex regex patterns

### Memory Usage

**Configuration in memory:**
- All endpoint definitions loaded on startup
- Response templates cached
- Round-robin state minimal (one counter per definition with multiple responses)

**Optimization tips:**
1. Use `body_file` for large responses
2. Avoid loading unused endpoint files
3. Consider splitting configurations for different environments

### Template Rendering

**Jinja2 compilation:**
- Templates compiled on first use
- Cached for subsequent requests

**Optimization tips:**
1. Minimize template complexity
2. Use simple variable substitution when possible
3. Avoid complex Jinja2 logic in templates

---

## Testing Patterns

### Unit Testing Matchers

```python
def test_json_semantic_matching():
    matcher = JsonMatcher('semantic')

    expected = '{"name": "Alice", "age": 25}'
    actual = '{"age": 25, "name": "Alice"}'  # Different order

    assert matcher.matches(expected, actual)
```

### Integration Testing

```python
def test_endpoint_with_validator():
    response = client.post(
        '/api/users',
        json={"name": "Alice", "age": 15}
    )

    assert response.status_code == 400
    assert "Age must be at least 18" in response.json['message']
```

---

## Summary

MockServer's architecture provides:
- **Modularity**: Clear separation of concerns
- **Extensibility**: Easy to add new matchers, validators, processors
- **Maintainability**: Well-defined components with single responsibilities
- **Testability**: Components can be tested in isolation
- **Performance**: Efficient matching and caching

## Next Steps

- **[Troubleshooting](09_Troubleshooting.md)** - Debug issues using architecture knowledge
- **[Request Configuration](03_Request_Configuration.md)** - Apply architecture understanding
- **[Validators and Processors](06_Validators_And_Processors.md)** - Extend the system
- **[Documentation Index](00_Index.md)** - Explore other topics
