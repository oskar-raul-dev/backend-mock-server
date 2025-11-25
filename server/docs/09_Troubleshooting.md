# Troubleshooting

This guide covers common issues, debugging techniques, and solutions for MockServer.

## Table of Contents

1. [Common Issues](#common-issues)
   - [Server Won't Start](#server-wont-start)
   - [Module Import Errors](#module-import-errors)
   - [Configuration Not Loading](#configuration-not-loading)
   - [Matching Failures](#matching-failures)
   - [Validation Errors](#validation-errors)
   - [Template Rendering Errors](#template-rendering-errors)
2. [Debugging Techniques](#debugging-techniques)
   - [Enable DEBUG Logging](#enable-debug-logging)
   - [Inspect Request Details](#inspect-request-details)
   - [Test Body Matching](#test-body-matching)
   - [Validate JSON/XML Syntax](#validate-jsonxml-syntax)
3. [Error Messages Explained](#error-messages-explained)
   - [404 Not Found](#404-not-found)
   - [400 Bad Request](#400-bad-request)
   - [500 Internal Server Error](#500-internal-server-error)
   - [Module/Import Errors](#moduleimport-errors)
4. [Performance Tips](#performance-tips)
   - [Definition Ordering](#definition-ordering)
   - [Optimize Validators](#optimize-validators)
   - [Template Performance](#template-performance)
   - [Auto-Reload in Production](#auto-reload-in-production)
5. [FAQ](#faq)

---

## Common Issues

### Server Won't Start

**Symptom**: Server fails to start or crashes immediately.

**Possible Causes and Solutions**:

1. **Port Already in Use**
   ```
   Error: [Errno 48] Address already in use
   ```

   **Solution**: Change the port or kill the process using it:
   ```bash
   # Find process using port 9090
   lsof -i :9090

   # Kill process
   kill -9 <PID>

   # Or use a different port
   python main.py --port 8080
   ```

2. **Missing Dependencies**
   ```
   ModuleNotFoundError: No module named 'flask'
   ```

   **Solution**: Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. **Python Version Incompatible**
   ```
   SyntaxError: invalid syntax
   ```

   **Solution**: Ensure Python 3.11 or higher:
   ```bash
   python --version  # Should be 3.11+
   ```

### Module Import Errors

**Symptom**: Validators or processors fail to load.

**Error Example**:
```
Error loading endpoints: cannot import name 'validate_user' from 'validators.user_validators'
```

**Solutions**:

1. **Check File Location**

   Ensure validators/processors are in the correct directory:
   ```
   config/
   ├── validators/
   │   ├── __init__.py
   │   └── user_validators.py
   └── processors/
       ├── __init__.py
       └── user_processors.py
   ```

2. **Verify __init__.py Files**

   Each directory must have an `__init__.py` file (can be empty).

3. **Check Function Names**

   Function name in import must match the actual function:
   ```python
   # In endpoints.py
   "validator": "validators.user_validators.validate_user"

   # In validators/user_validators.py
   def validate_user(body: str) -> None:  # Must match!
       pass
   ```

4. **Python Path Issues**

   Ensure you're running from the correct directory:
   ```bash
   # Should be in mockserver directory
   cd mockserver
   python main.py --config-dir config --endpoints-file endpoints.py
   ```

### Configuration Not Loading

**Symptom**: Configuration changes don't take effect.

**Solutions**:

1. **Verify File Path**
   ```bash
   # Ensure config directory exists
   ls config/

   # Should see: config.py, endpoints.py, etc.
   ```

2. **Check config.py Syntax**

   Python syntax errors in `config.py` will prevent loading:
   ```python
   # Bad - missing comma
   config = {
       "server": {
           "port": 9090
           "host": "0.0.0.0"  # Missing comma!
       }
   }

   # Good
   config = {
       "server": {
           "port": 9090,
           "host": "0.0.0.0"
       }
   }
   ```

3. **Restart Server**

   Without auto-reload, you must restart manually:
   ```bash
   # Stop server (Ctrl+C)
   # Restart
   python main.py --config-dir config --endpoints-file endpoints.py
   ```

4. **Enable Auto-Reload**
   ```bash
   python main.py --config-dir config --endpoints-file endpoints.py --auto-reload
   ```

### Matching Failures

**Symptom**: Requests receive 404 even though definition exists.

**Common Causes**:

1. **URL Pattern Mismatch**

   ```python
   # Definition
   "url": r"^/api/users/(\d+)$"

   # Request that FAILS
   curl http://localhost:9090/api/users/abc  # 'abc' is not \d+

   # Request that SUCCEEDS
   curl http://localhost:9090/api/users/123
   ```

2. **HTTP Method Mismatch**

   ```python
   # Definition
   "methods": ["POST"]

   # Request that FAILS
   curl -X GET http://localhost:9090/api/users  # Wrong method

   # Request that SUCCEEDS
   curl -X POST http://localhost:9090/api/users
   ```

3. **Query Parameter Mismatch**

   ```python
   # Definition
   "query_params": {
       "user_id": r"\d+"
   }

   # Request that FAILS
   curl http://localhost:9090/api/users  # Missing user_id

   # Request that SUCCEEDS
   curl http://localhost:9090/api/users?user_id=123
   ```

4. **Body Matching Issues**

   **Problem**: JSON field order or extra fields

   **Solution**: Use semantic matching mode (default):
   ```python
   # Pattern in definition
   "body": {
       "name": "...",
       "age": 0
   }

   # This matches (order doesn't matter)
   {"age": 25, "name": "Alice"}

   # This matches (extra fields ignored in semantic mode)
   {"name": "Alice", "age": 25, "email": "alice@example.com"}
   ```

5. **XML Namespace Issues**

   **Problem**: XML namespaces not matching

   **Solution**: Include namespaces in pattern or use partial matching:
   ```python
   # If request has namespace
   <user xmlns="http://example.com">...</user>

   # Pattern should include it or use partial mode
   "body": '''<user xmlns="http://example.com">
       <name>...</name>
   </user>'''
   ```

**Debugging Steps**:

1. Enable DEBUG logging to see matching details
2. Simplify definition (remove query_params, headers, body)
3. Add constraints back one at a time to identify issue
4. Check exact request details in logs

### Validation Errors

**Symptom**: Requests receive 400 with validation error message.

**Example Error**:
```json
{
    "error": "Validation failed: User age must be at least 18"
}
```

**Solutions**:

1. **Check Validator Logic**

   Ensure validator raises `ValueError` with clear message:
   ```python
   def validate_user_age(body: str) -> None:
       data = json.loads(body)
       age = data.get('age', 0)

       if age < 18:
           # Good - clear message
           raise ValueError(f"User age must be at least 18, got {age}")

       # Bad - no message
       # raise ValueError()
   ```

2. **JSON Parsing Errors**

   ```python
   def validate_user(body: str) -> None:
       try:
           data = json.loads(body)
       except json.JSONDecodeError as e:
           raise ValueError(f"Invalid JSON format: {e}")

       # Rest of validation...
   ```

3. **Missing Required Fields**

   ```python
   def validate_order(body: str) -> None:
       data = json.loads(body)

       required_fields = ['customer_id', 'items', 'total']
       for field in required_fields:
           if field not in data:
               raise ValueError(f"Missing required field: {field}")
   ```

### Template Rendering Errors

**Symptom**: 500 error when rendering response template.

**Common Issues**:

1. **Undefined Template Variable**

   ```python
   # Response template
   "body": '''{"user_id": "{{ BODY_PROCESSED.user_id }}"}'''

   # Error if processor doesn't return 'user_id'
   def process_user(body: str) -> dict:
       return {"name": "Alice"}  # Missing user_id!
   ```

   **Solution**: Ensure processor returns all required fields:
   ```python
   def process_user(body: str) -> dict:
       return {
           "user_id": str(uuid.uuid4()),  # Now provided
           "name": "Alice"
       }
   ```

2. **Invalid Jinja2 Syntax**

   ```python
   # Bad - unclosed tag
   "body": '''{"status": "{% if QUERY_PARAMS.status == 'active' %}Active"}'''

   # Good - closed tag
   "body": '''{"status": "{% if QUERY_PARAMS.status == 'active' %}Active{% endif %}"}'''
   ```

3. **Accessing Non-Existent Keys**

   ```python
   # Bad - crashes if 'user_id' not in query params
   "body": '''{"id": "{{ QUERY_PARAMS.user_id }}"}'''

   # Good - use default filter
   "body": '''{"id": "{{ QUERY_PARAMS.user_id | default('unknown') }}"}'''
   ```

---

## Debugging Techniques

### Enable DEBUG Logging

Enable verbose logging to see detailed matching information:

```bash
# Method 1: Command-line argument
python main.py --config-dir config --endpoints-file endpoints.py --log-level DEBUG

# Method 2: Configuration file
# In config/config.py
config = {
    "logging": {
        "level": "DEBUG"
    }
}
```

**DEBUG Output Example**:
```
DEBUG:MockServer:Incoming request: POST /api/users
DEBUG:MockServer:Checking definition: POST /api/users
DEBUG:MockServer:URL matches: True
DEBUG:MockServer:Method matches: True
DEBUG:MockServer:Query params match: True
DEBUG:MockServer:Headers match: True
DEBUG:MockServer:Body matches: True
DEBUG:MockServer:Definition matched successfully
DEBUG:MockServer:Executing validator: validators.user_validators.validate_user
DEBUG:MockServer:Validator passed
DEBUG:MockServer:Executing processor: processors.user_processors.process_user
DEBUG:MockServer:Processor returned: {'user_id': '123', 'name': 'ALICE'}
DEBUG:MockServer:Rendering response template
DEBUG:MockServer:Response: 201
```

### Inspect Request Details

Use curl verbose mode to see exact request details:

```bash
# Verbose output shows headers, body, etc.
curl -v -X POST http://localhost:9090/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "age": 25}'

# Output shows:
# > POST /api/users HTTP/1.1
# > Host: localhost:9090
# > Content-Type: application/json
# > Content-Length: 32
# > {"name": "Alice", "age": 25}
```

Or use browser DevTools Network tab for web requests.

### Test Body Matching

Create a simple test script to verify body matching:

```python
# test_matching.py
import json
from mockserver.body_matching import matches_body_semantic

pattern = {"name": "...", "age": 0}
request_body = '{"age": 25, "name": "Alice"}'

result = matches_body_semantic(pattern, request_body, content_type="application/json")
print(f"Match result: {result}")  # Should be True
```

Run it:
```bash
python test_matching.py
```

### Validate JSON/XML Syntax

Use online validators or command-line tools:

**JSON**:
```bash
# Validate JSON syntax
echo '{"name": "Alice", "age": 25}' | python -m json.tool

# If invalid, shows error:
echo '{"name": "Alice" "age": 25}' | python -m json.tool
# Expecting ',' delimiter: line 1 column 18 (char 17)
```

**XML**:
```bash
# Validate XML with xmllint (install: brew install libxml2)
echo '<user><name>Alice</name></user>' | xmllint --format -

# If invalid, shows error:
echo '<user><name>Alice</name>' | xmllint --format -
# error: Premature end of data in tag user line 1
```

---

## Error Messages Explained

### 404 Not Found

**Error Response**:
```json
{
    "error": "No matching endpoint found"
}
```

**Meaning**: No endpoint definition matched the request.

**Troubleshooting**:

1. Check URL pattern:
   ```bash
   # Enable DEBUG logging
   python main.py --log-level DEBUG

   # Make request and check logs
   curl http://localhost:9090/api/users/123

   # Look for "URL matches: False" in logs
   ```

2. Verify HTTP method:
   ```python
   # Ensure methods match
   "methods": ["GET", "POST"]  # Must include request method
   ```

3. Check query parameters and headers

4. Verify body matching if present

### 400 Bad Request

**Error Response**:
```json
{
    "error": "Validation failed: User age must be at least 18"
}
```

**Meaning**: Request matched an endpoint but failed validation.

**Troubleshooting**:

1. Read the error message carefully (it comes from your validator)

2. Check validator logic:
   ```python
   def validate_user_age(body: str) -> None:
       data = json.loads(body)
       age = data.get('age', 0)

       # This raises ValueError, causing 400
       if age < 18:
           raise ValueError(f"User age must be at least 18, got {age}")
   ```

3. Verify request body matches expected format

4. Test validator in isolation:
   ```python
   # test_validator.py
   from validators.user_validators import validate_user_age

   test_body = '{"name": "Alice", "age": 17}'

   try:
       validate_user_age(test_body)
       print("Validation passed")
   except ValueError as e:
       print(f"Validation failed: {e}")
   ```

### 500 Internal Server Error

**Error Response**:
```json
{
    "error": "Internal server error"
}
```

**Meaning**: Unexpected error in server code (validator, processor, or template rendering).

**Common Causes**:

1. **Processor Exception**
   ```python
   def process_user(body: str) -> dict:
       data = json.loads(body)
       # KeyError if 'name' doesn't exist
       name = data['name']  # Should use .get() instead
       return {"name": name.upper()}
   ```

   **Fix**: Handle missing keys gracefully:
   ```python
   def process_user(body: str) -> dict:
       data = json.loads(body)
       name = data.get('name', 'Unknown')  # Provide default
       return {"name": name.upper()}
   ```

2. **Template Rendering Error**
   ```python
   # Undefined variable in template
   "body": '''{"id": "{{ BODY_PROCESSED.user_id }}"}'''
   ```

   **Fix**: Ensure processor returns required fields or use default filter:
   ```python
   "body": '''{"id": "{{ BODY_PROCESSED.user_id | default('N/A') }}"}'''
   ```

3. **JSON Parsing Error**
   ```python
   def validate_user(body: str) -> None:
       data = json.loads(body)  # Crashes if body is not valid JSON
   ```

   **Fix**: Catch parsing errors:
   ```python
   def validate_user(body: str) -> None:
       try:
           data = json.loads(body)
       except json.JSONDecodeError as e:
           raise ValueError(f"Invalid JSON: {e}")
   ```

**Debugging**:

1. Check server logs for full stack trace
2. Enable DEBUG logging
3. Test validator/processor in isolation
4. Use try-except blocks to catch and log errors

### Module/Import Errors

**Error Example**:
```
ModuleNotFoundError: No module named 'validators'
```

**Solutions**:

1. **Ensure Directory Structure**:
   ```
   config/
   ├── __init__.py
   ├── validators/
   │   ├── __init__.py
   │   └── user_validators.py
   └── processors/
       ├── __init__.py
       └── user_processors.py
   ```

2. **Check Python Path**:
   ```bash
   # Must run from mockserver directory
   cd mockserver
   python main.py --config-dir config --endpoints-file endpoints.py
   ```

3. **Verify Import Path**:
   ```python
   # In endpoints.py
   "validator": "validators.user_validators.validate_user"
   # Translates to: from validators.user_validators import validate_user
   ```

---

## Performance Tips

### Definition Ordering

**Problem**: Server is slow when matching requests.

**Solution**: Order definitions from most specific to least specific.

**Why**: MockServer checks definitions in order and returns the first match.

**Example**:
```python
# Good - specific patterns first
definitions = [
    # Most specific - exact URL with body matching
    {
        "url": r"^/api/users/123$",
        "methods": ["GET"],
        "response": {"status": 200, "body": "User 123"}
    },
    # Less specific - URL with path parameter
    {
        "url": r"^/api/users/(\d+)$",
        "methods": ["GET"],
        "response": {"status": 200, "body": "User {{ PATH_PARAMS.0 }}"}
    },
    # Least specific - catch-all
    {
        "url": r"^/api/.*$",
        "methods": ["GET"],
        "response": {"status": 404, "body": "Not found"}
    }
]

# Bad - catch-all first (everything matches this, specific patterns never reached)
definitions = [
    {
        "url": r"^/api/.*$",  # Too broad!
        "methods": ["GET"],
        "response": {"status": 404, "body": "Not found"}
    },
    {
        "url": r"^/api/users/(\d+)$",  # Never reached!
        "methods": ["GET"],
        "response": {"status": 200, "body": "User {{ PATH_PARAMS.0 }}"}
    }
]
```

### Optimize Validators

**Problem**: Validation is slow.

**Solutions**:

1. **Avoid Complex Regex in Validators**

   ```python
   # Slow - complex regex
   def validate_email(body: str) -> None:
       data = json.loads(body)
       email = data.get('email', '')
       # Very complex regex - slow!
       pattern = r'^(?:[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-zA-Z0-9-]*[a-zA-Z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])$'
       if not re.match(pattern, email):
           raise ValueError("Invalid email")

   # Fast - simple check
   def validate_email(body: str) -> None:
       data = json.loads(body)
       email = data.get('email', '')
       # Simple check is usually sufficient
       if '@' not in email or '.' not in email.split('@')[-1]:
           raise ValueError("Invalid email")
   ```

2. **Parse JSON Once**

   ```python
   # Slow - parsing twice
   def validate_and_check(body: str) -> None:
       data = json.loads(body)  # Parse 1
       if 'name' not in data:
           raise ValueError("Missing name")

       data2 = json.loads(body)  # Parse 2 - unnecessary!
       if data2.get('age', 0) < 18:
           raise ValueError("Age too young")

   # Fast - parse once
   def validate_and_check(body: str) -> None:
       data = json.loads(body)  # Parse once
       if 'name' not in data:
           raise ValueError("Missing name")
       if data.get('age', 0) < 18:
           raise ValueError("Age too young")
   ```

### Template Performance

**Problem**: Response rendering is slow.

**Solutions**:

1. **Avoid Complex Jinja2 Logic**

   ```python
   # Slow - complex template logic
   "body": '''
   {
       "items": [
           {% for i in range(100) %}
           {
               "id": {{ i }},
               "calculated": {% if i % 2 == 0 %}{{ i * 2 }}{% else %}{{ i * 3 }}{% endif %}
           }{% if not loop.last %},{% endif %}
           {% endfor %}
       ]
   }'''

   # Fast - pre-calculate in processor
   def process_items(body: str) -> dict:
       items = [{"id": i, "calculated": i * 2 if i % 2 == 0 else i * 3} for i in range(100)]
       return {"items": json.dumps(items)}

   "body": '''{"items": {{ BODY_PROCESSED.items }}}'''
   ```

2. **Use body_file for Large Responses**

   ```python
   # Slow - large inline JSON
   "body": '''{
       "users": [...],  # 10,000 users
       "metadata": {...}
   }'''

   # Fast - load from file
   "body_file": "large_response.json"
   ```

### Auto-Reload in Production

**Problem**: Auto-reload causes performance issues in production.

**Solution**: Disable auto-reload in production:

```bash
# Development - auto-reload enabled
python main.py --config-dir config --endpoints-file endpoints.py --auto-reload

# Production - auto-reload disabled (default)
python main.py --config-dir config --endpoints-file endpoints.py
```

**Why**: File watching adds overhead. In production, configuration changes should be deployed via controlled releases.

---

## FAQ

### Q: Can I use environment variables in configuration?

**A**: Yes, use Python's `os.environ` in `config.py`:

```python
import os

config = {
    "server": {
        "port": int(os.environ.get("MOCK_SERVER_PORT", 9090)),
        "host": os.environ.get("MOCK_SERVER_HOST", "0.0.0.0")
    }
}
```

Then run:
```bash
export MOCK_SERVER_PORT=8080
python main.py --config-dir config --endpoints-file endpoints.py
```

### Q: How do I mock file uploads?

**A**: Match `multipart/form-data` requests:

```python
{
    "url": r"^/api/upload$",
    "methods": ["POST"],
    "headers": {
        "Content-Type": r"multipart/form-data.*"
    },
    "response": {
        "status": 201,
        "body": '{"file_id": "12345", "message": "File uploaded successfully"}'
    }
}
```

### Q: Can I return binary responses (images, PDFs)?

**A**: Yes, use `body_file` with appropriate Content-Type:

```python
{
    "url": r"^/api/files/([^/]+)$",
    "methods": ["GET"],
    "response": {
        "status": 200,
        "headers": {
            "Content-Type": "application/pdf"
        },
        "body_file": "sample.pdf"  # Place in config directory
    }
}
```

### Q: How do I test webhooks?

**A**: MockServer can receive webhook requests and validate them:

```python
{
    "url": r"^/webhooks/payment$",
    "methods": ["POST"],
    "validator": "validators.webhook_validators.validate_payment_signature",
    "response": {
        "status": 200,
        "body": '{"received": true}'
    }
}
```

### Q: Can I simulate slow responses?

**A**: Not directly, but you can use a processor with `time.sleep()`:

```python
import time

def slow_processor(body: str) -> dict:
    time.sleep(2)  # 2-second delay
    return {}
```

```python
{
    "url": r"^/api/slow$",
    "methods": ["GET"],
    "processor": "processors.utils.slow_processor",
    "response": {
        "status": 200,
        "body": '{"message": "Delayed response"}'
    }
}
```

### Q: How do I handle CORS preflight requests?

**A**: Add an OPTIONS endpoint:

```python
{
    "url": r"^/api/.*$",
    "methods": ["OPTIONS"],
    "response": {
        "status": 204,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    }
}
```

Or enable CORS globally in `config.py`:

```python
config = {
    "cors": {
        "enabled": True,
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "headers": ["Content-Type", "Authorization"]
    }
}
```

### Q: Can I use MockServer in automated tests?

**A**: Yes, start it programmatically:

```python
# test_api.py
import subprocess
import requests
import time

# Start MockServer
server = subprocess.Popen([
    "python", "main.py",
    "--config-dir", "test_config",
    "--endpoints-file", "test_endpoints.py",
    "--port", "9999"
])

time.sleep(2)  # Wait for server to start

try:
    # Run tests
    response = requests.get("http://localhost:9999/api/users/123")
    assert response.status_code == 200
    assert response.json()["name"] == "Test User"
finally:
    # Stop server
    server.terminate()
    server.wait()
```

### Q: How do I mock GraphQL endpoints?

**A**: Match POST requests to `/graphql` with query validation:

```python
def validate_graphql_query(body: str) -> None:
    data = json.loads(body)
    if 'query' not in data:
        raise ValueError("Missing GraphQL query")

    query = data['query']
    if 'user(' in query:
        # Validate user query
        pass

{
    "url": r"^/graphql$",
    "methods": ["POST"],
    "validator": "validators.graphql_validators.validate_graphql_query",
    "response": {
        "status": 200,
        "body": '''{
            "data": {
                "user": {
                    "id": "123",
                    "name": "Alice"
                }
            }
        }'''
    }
}
```

### Q: What's the difference between semantic and partial matching?

**A**: See [Body Matching Guide](05_Body_Matching.md) for details.

**Quick Answer**:
- **Semantic**: Pattern and request must have exact same fields (order doesn't matter)
- **Partial**: Request can have extra fields not in pattern (allows subset matching)

### Q: Can I chain multiple validators?

**A**: Yes, use a list:

```python
{
    "url": r"^/api/users$",
    "methods": ["POST"],
    "validators": [
        "validators.auth_validators.validate_auth_token",
        "validators.user_validators.validate_user_format",
        "validators.user_validators.validate_user_age"
    ],
    "response": {
        "status": 201,
        "body": '{"id": "123"}'
    }
}
```

Validators execute in order. First failure returns 400 with error message.

### Q: How do I debug template variables?

**A**: Use DEBUG logging and inspect the logs:

```bash
python main.py --config-dir config --endpoints-file endpoints.py --log-level DEBUG
```

Or add debug output to your processor:

```python
def process_user(body: str) -> dict:
    data = json.loads(body)
    result = {
        "user_id": str(uuid.uuid4()),
        "name": data.get('name', '').upper()
    }
    print(f"DEBUG: Processor result: {result}")  # Will appear in logs
    return result
```

### Q: Can I use regular expressions in response templates?

**A**: No, but you can process text in a processor:

```python
import re

def process_with_regex(body: str) -> dict:
    data = json.loads(body)
    email = data.get('email', '')

    # Extract domain using regex
    match = re.search(r'@(.+)$', email)
    domain = match.group(1) if match else 'unknown'

    return {"domain": domain}
```

```python
"body": '''{"email_domain": "{{ BODY_PROCESSED.domain }}"}'''
```

---

## Related Documentation

- [Quickstart Guide](01_Quickstart_Guide.md) - Get started with MockServer
- [Request Configuration](03_Request_Configuration.md) - Detailed endpoint configuration
- [Body Matching](05_Body_Matching.md) - Understanding semantic matching
- [Validators and Processors](06_Validators_And_Processors.md) - Custom validation and processing
- [Internals & Architecture](08_Internals_Architecture.md) - System architecture

---

## Still Having Issues?

If you're still experiencing problems:

1. **Check the logs** with DEBUG level enabled
2. **Simplify your configuration** to isolate the issue
3. **Test validators/processors in isolation** using Python shell
4. **Verify JSON/XML syntax** using validators
5. **Review related documentation** sections above

For common patterns and examples, see [Advanced Examples](07_Advanced_Examples.md).
