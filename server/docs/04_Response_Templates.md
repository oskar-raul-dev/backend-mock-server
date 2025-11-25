# Response Templates

This guide covers response configuration in MockServer, including status codes, headers, body formats, template variables, Jinja2 templating, and file-based responses.

---

## Response Configuration Structure

Every endpoint definition includes a `response` section that defines what to return when the request matches.

**Basic structure:**
```python
"response": {
    "status": 200,                           # HTTP status code
    "headers": {                             # Response headers
        "Content-Type": "application/json"
    },
    "body": '{"message": "Hello"}'           # Response body
}
```

**Alternative - response from file:**
```python
"response": {
    "status": 200,
    "headers": {"Content-Type": "application/json"},
    "body_file": "response.json"             # Load from file
}
```

---

## HTTP Status Codes

Specify any valid HTTP status code (100-599).

### Common Status Codes

| Code | Meaning | Use Case |
|------|---------|----------|
| **2xx Success** |
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (resource created) |
| 202 | Accepted | Request accepted for processing |
| 204 | No Content | Successful DELETE (no response body) |
| **3xx Redirection** |
| 301 | Moved Permanently | Resource moved |
| 302 | Found | Temporary redirect |
| 304 | Not Modified | Cached resource still valid |
| **4xx Client Errors** |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource conflict (duplicate) |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| **5xx Server Errors** |
| 500 | Internal Server Error | Generic server error |
| 502 | Bad Gateway | Upstream server error |
| 503 | Service Unavailable | Server overloaded/down |
| 504 | Gateway Timeout | Upstream timeout |

### Examples

**Success response:**
```python
"response": {
    "status": 200,
    "body": '{"message": "Operation successful"}'
}
```

**Created response:**
```python
"response": {
    "status": 201,
    "body": '{"id": "{{ BODY_PROCESSED.user_id }}", "message": "User created"}'
}
```

**No content response:**
```python
"response": {
    "status": 204,
    # No body for 204
}
```

**Validation error:**
```python
"response": {
    "status": 422,
    "body": '{"error": "Validation failed", "details": ["Email is required"]}'
}
```

**Server error:**
```python
"response": {
    "status": 500,
    "body": '{"error": "Internal server error", "message": "Something went wrong"}'
}
```

---

## Response Headers

Headers are specified as a dictionary of key-value pairs.

### Content-Type Headers

```python
# JSON
"headers": {
    "Content-Type": "application/json"
}

# XML
"headers": {
    "Content-Type": "application/xml"
}

# Plain text
"headers": {
    "Content-Type": "text/plain"
}

# HTML
"headers": {
    "Content-Type": "text/html"
}

# Binary data
"headers": {
    "Content-Type": "application/octet-stream"
}

# PDF
"headers": {
    "Content-Type": "application/pdf"
}
```

### CORS Headers

```python
"headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
}
```

### Cache Control

```python
# No cache
"headers": {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}

# Cache for 1 hour
"headers": {
    "Cache-Control": "public, max-age=3600"
}
```

### Custom Headers

```python
"headers": {
    "Content-Type": "application/json",
    "X-Request-ID": "{{ HEADERS.x-request-id }}",  # Echo request header
    "X-Response-Time": "25ms",
    "X-API-Version": "v1",
    "X-Rate-Limit-Remaining": "99"
}
```

### Security Headers

```python
"headers": {
    "Content-Type": "application/json",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000"
}
```

---

## Response Body Formats

### JSON Responses

**Simple JSON:**
```python
"body": '{"message": "Hello World"}'
```

**Structured JSON:**
```python
"body": '''{
    "success": true,
    "data": {
        "id": 123,
        "name": "Alice"
    },
    "meta": {
        "timestamp": "2024-01-15T10:30:00Z"
    }
}'''
```

**JSON array:**
```python
"body": '''[
    {"id": 1, "name": "Item 1"},
    {"id": 2, "name": "Item 2"},
    {"id": 3, "name": "Item 3"}
]'''
```

### XML Responses

```python
"body": '''<?xml version="1.0" encoding="UTF-8"?>
<response>
    <status>success</status>
    <data>
        <user>
            <id>123</id>
            <name>Alice</name>
        </user>
    </data>
</response>'''
```

### Plain Text Responses

```python
"body": "This is a plain text response"
```

### HTML Responses

```python
"headers": {"Content-Type": "text/html"},
"body": '''<!DOCTYPE html>
<html>
<head>
    <title>MockServer Response</title>
</head>
<body>
    <h1>Hello World</h1>
    <p>This is a mock HTML response.</p>
</body>
</html>'''
```

### Binary/File Responses

For binary data, use `body_file` instead (see below).

---

## Template Variables

Template variables allow dynamic response generation using data from the request.

### Available Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `QUERY_PARAMS.name` | Query parameter value | `{{ QUERY_PARAMS.user_id }}` |
| `PATH_PARAMS.index` | Path parameter by index (0-based) | `{{ PATH_PARAMS.0 }}` |
| `HEADERS.name` | Request header value (lowercase) | `{{ HEADERS.authorization }}` |
| `BODY` | Complete request body (raw string) | `{{ BODY }}` |
| `BODY_PROCESSED.field` | Processed data from processor | `{{ BODY_PROCESSED.user_id }}` |

### Query Parameter Variables

**Request:**
```
GET /api/users?user_id=123&status=active
```

**Response:**
```python
"body": '''{
    "user_id": "{{ QUERY_PARAMS.user_id }}",
    "status": "{{ QUERY_PARAMS.status }}"
}'''
```

**Output:**
```json
{
    "user_id": "123",
    "status": "active"
}
```

### Path Parameter Variables

**Request:**
```
GET /api/users/123/orders/456
```

**Endpoint:**
```python
"url": r"^/api/users/([^/]+)/orders/([^/]+)$"
```

**Response:**
```python
"body": '''{
    "user_id": "{{ PATH_PARAMS.0 }}",
    "order_id": "{{ PATH_PARAMS.1 }}"
}'''
```

**Output:**
```json
{
    "user_id": "123",
    "order_id": "456"
}
```

### Header Variables

**Request:**
```
GET /api/users
Authorization: Bearer abc123xyz
X-Request-ID: req-001
```

**Response:**
```python
"body": '''{
    "auth_token": "{{ HEADERS.authorization }}",
    "request_id": "{{ HEADERS.x-request-id }}"
}'''
```

**Output:**
```json
{
    "auth_token": "Bearer abc123xyz",
    "request_id": "req-001"
}
```

**Note:** Header names are normalized to lowercase.

### Body Variable

**Request:**
```json
POST /api/echo
{"message": "Hello"}
```

**Response:**
```python
"body": '{"received": {{ BODY }} }'
```

**Output:**
```json
{
    "received": {"message": "Hello"}
}
```

### Processed Body Variables

**Request:**
```json
POST /api/users
{"name": "Alice", "email": "alice@example.com", "age": 25}
```

**Processor:**
```python
def process_user(body: str) -> dict:
    data = json.loads(body)
    return {
        "user_id": str(uuid.uuid4()),
        "name": data['name'].upper(),
        "email": data['email'].lower(),
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Response:**
```python
"body": '''{
    "id": "{{ BODY_PROCESSED.user_id }}",
    "name": "{{ BODY_PROCESSED.name }}",
    "email": "{{ BODY_PROCESSED.email }}",
    "created_at": "{{ BODY_PROCESSED.timestamp }}"
}'''
```

**Output:**
```json
{
    "id": "a7f3d9c2-8e4b-4a1c-9f2e-3b5c6d7e8f9a",
    "name": "ALICE",
    "email": "alice@example.com",
    "created_at": "2024-01-15T10:30:45.123456"
}
```

---

## Jinja2 Templating

MockServer uses Jinja2 for template rendering, enabling advanced logic in responses.

### Basic Syntax

```python
{{ variable }}           # Variable substitution
{% if condition %}...{% endif %}    # Conditionals
{% for item in list %}...{% endfor %}  # Loops
```

### Conditional Responses

```python
"body": '''{
    "status": "{{ QUERY_PARAMS.status }}",
    "message": "{% if QUERY_PARAMS.status == 'active' %}User is active{% else %}User is inactive{% endif %}"
}'''
```

### Loops

```python
# Assuming BODY_PROCESSED.items is a list
"body": '''{
    "items": [
        {% for item in BODY_PROCESSED.items %}
        {
            "name": "{{ item.name }}",
            "price": {{ item.price }}
        }{% if not loop.last %},{% endif %}
        {% endfor %}
    ]
}'''
```

### Filters

```python
# Uppercase
"body": '{"name": "{{ QUERY_PARAMS.name | upper }}"}'

# Lowercase
"body": '{"email": "{{ QUERY_PARAMS.email | lower }}"}'

# Default value
"body": '{"status": "{{ QUERY_PARAMS.status | default("pending") }}"}'

# Length
"body": '{"name_length": {{ QUERY_PARAMS.name | length }}}'
```

### Complex Example

```python
"body": '''{
    "request_info": {
        "path": "/api/users/{{ PATH_PARAMS.0 }}",
        "method": "GET",
        "user_id": "{{ PATH_PARAMS.0 }}",
        "is_admin": {% if HEADERS.get('x-admin') == 'true' %}true{% else %}false{% endif %}
    },
    "response_data": {
        "user": {
            "id": "{{ BODY_PROCESSED.user_id }}",
            "name": "{{ BODY_PROCESSED.name | title }}",
            "email": "{{ BODY_PROCESSED.email | lower }}",
            "role": "{% if BODY_PROCESSED.age >= 18 %}adult{% else %}minor{% endif %}"
        },
        "metadata": {
            "timestamp": "{{ BODY_PROCESSED.timestamp }}",
            "environment": "{{ 'production' if HEADERS.get('x-env') == 'prod' else 'development' }}"
        }
    }
}'''
```

---

## Response from File

Load response body from a file in the `responses/` directory.

### Basic File Response

**Directory structure:**
```
config/
├── endpoints.py
└── responses/
    └── user_response.json
```

**Endpoint:**
```python
"response": {
    "status": 200,
    "headers": {"Content-Type": "application/json"},
    "body_file": "user_response.json"
}
```

**File: `responses/user_response.json`:**
```json
{
    "id": 123,
    "name": "Alice",
    "email": "alice@example.com"
}
```

### File with Template Variables

Files can contain template variables just like inline bodies:

**File: `responses/user_created.json`:**
```json
{
    "success": true,
    "user": {
        "id": "{{ BODY_PROCESSED.user_id }}",
        "name": "{{ BODY_PROCESSED.name }}",
        "email": "{{ BODY_PROCESSED.email }}",
        "created_at": "{{ BODY_PROCESSED.timestamp }}"
    }
}
```

**Endpoint:**
```python
{
    "request": {
        "url": r"^/api/users$",
        "methods": ["POST"],
        "body": {
            "format": "json",
            "processor": process_user
        }
    },
    "response": {
        "status": 201,
        "headers": {"Content-Type": "application/json"},
        "body_file": "user_created.json"
    }
}
```

### Nested Directory Structure

Organize response files in subdirectories:

```
config/
└── responses/
    ├── users/
    │   ├── created.json
    │   └── updated.json
    ├── orders/
    │   ├── created.json
    │   └── completed.json
    └── errors/
        ├── 404.json
        └── 500.json
```

**Endpoint:**
```python
"body_file": "users/created.json"
"body_file": "orders/completed.json"
"body_file": "errors/404.json"
```

### Large Responses

Use files for large responses to keep `endpoints.py` clean:

**File: `responses/lorem_ipsum.txt`:**
```
Lorem ipsum dolor sit amet, consectetur adipiscing elit...
(2000+ words of text)
```

**Endpoint:**
```python
"response": {
    "status": 200,
    "headers": {"Content-Type": "text/plain"},
    "body_file": "lorem_ipsum.txt"
}
```

### Binary File Responses

```python
# PDF file
"response": {
    "status": 200,
    "headers": {
        "Content-Type": "application/pdf",
        "Content-Disposition": "attachment; filename=document.pdf"
    },
    "body_file": "documents/sample.pdf"
}

# Image file
"response": {
    "status": 200,
    "headers": {
        "Content-Type": "image/png"
    },
    "body_file": "images/logo.png"
}
```

### XML File Response

**File: `responses/user_created.xml`:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<response>
    <success>true</success>
    <user>
        <id>{{ BODY_PROCESSED.user_id }}</id>
        <fullName>{{ BODY_PROCESSED.full_name }}</fullName>
        <email>{{ BODY_PROCESSED.email }}</email>
        <ageGroup>{{ BODY_PROCESSED.age_group }}</ageGroup>
        <createdAt>{{ BODY_PROCESSED.timestamp }}</createdAt>
    </user>
</response>
```

**Endpoint:**
```python
"response": {
    "status": 201,
    "headers": {"Content-Type": "application/xml"},
    "body_file": "user_created.xml"
}
```

---

## Dynamic Response Examples

### Greeting Based on Time of Day

```python
"body": '''{
    "greeting": "{% set hour = now().hour %}{% if hour < 12 %}Good morning{% elif hour < 18 %}Good afternoon{% else %}Good evening{% endif %} {{ QUERY_PARAMS.name }}!"
}'''
```

### Pagination Response

```python
"body": '''{
    "page": {{ QUERY_PARAMS.page | default(1) }},
    "limit": {{ QUERY_PARAMS.limit | default(10) }},
    "total": 100,
    "has_next": {% if QUERY_PARAMS.page | int < 10 %}true{% else %}false{% endif %},
    "has_previous": {% if QUERY_PARAMS.page | int > 1 %}true{% else %}false{% endif %}
}'''
```

### Error Response with Details

```python
"body": '''{
    "error": "Validation failed",
    "message": "The request could not be processed",
    "details": {
        "field": "{{ BODY_PROCESSED.error_field }}",
        "reason": "{{ BODY_PROCESSED.error_reason }}"
    },
    "request_id": "{{ HEADERS.x-request-id | default('N/A') }}",
    "timestamp": "{{ BODY_PROCESSED.timestamp }}"
}'''
```

### User Profile with Computed Fields

```python
"body": '''{
    "user": {
        "id": "{{ BODY_PROCESSED.user_id }}",
        "name": "{{ BODY_PROCESSED.name }}",
        "email": "{{ BODY_PROCESSED.email }}",
        "age": {{ BODY_PROCESSED.age }},
        "age_group": "{{ BODY_PROCESSED.age_group }}",
        "is_adult": {% if BODY_PROCESSED.age >= 18 %}true{% else %}false{% endif %},
        "is_senior": {% if BODY_PROCESSED.age >= 65 %}true{% else %}false{% endif %},
        "discount_eligible": {% if BODY_PROCESSED.age >= 65 or BODY_PROCESSED.age < 18 %}true{% else %}false{% endif %}
    },
    "metadata": {
        "created_at": "{{ BODY_PROCESSED.timestamp }}",
        "source": "{{ BODY_PROCESSED.source | default('web') }}"
    }
}'''
```

---

## Multiple Responses (Round-Robin)

Return different responses on sequential requests (see [Request Configuration - Multiple Responses](03_Request_Configuration.md#multiple-responses-round-robin)).

```python
"response": [
    {
        "status": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"status": "pending", "progress": 0}'
    },
    {
        "status": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"status": "processing", "progress": 50}'
    },
    {
        "status": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"status": "completed", "progress": 100}'
    }
]
```

---

## Best Practices

### 1. Use Appropriate Content-Type

Always set the correct `Content-Type` header:

```python
# JSON
"headers": {"Content-Type": "application/json"}

# XML
"headers": {"Content-Type": "application/xml"}

# Text
"headers": {"Content-Type": "text/plain"}
```

### 2. Use body_file for Large Responses

Keep `endpoints.py` clean by externalizing large responses:

```python
# Good
"body_file": "large_response.json"

# Bad - inline 500-line JSON in endpoints.py
"body": '''{ ... 500 lines ... }'''
```

### 3. Validate JSON Syntax

Use triple quotes for multi-line JSON and validate syntax:

```python
# Good
"body": '''{
    "key": "value"
}'''

# Bad - syntax error
"body": '{"key": "value"'
```

### 4. Use Template Variables for Dynamic Data

```python
# Good - dynamic
"body": '{"user_id": "{{ BODY_PROCESSED.user_id }}"}'

# Bad - static
"body": '{"user_id": "12345"}'
```

### 5. Document Complex Templates

Add comments in endpoint definitions:

```python
{
    "request": {...},
    "response": {
        "status": 200,
        "body": '''{
            # User ID generated by processor
            "user_id": "{{ BODY_PROCESSED.user_id }}",
            # Full name constructed from first and last name
            "full_name": "{{ BODY_PROCESSED.full_name }}",
            # Age group calculated based on age (young_adult, adult, senior)
            "age_group": "{{ BODY_PROCESSED.age_group }}"
        }'''
    }
}
```

### 6. Handle Missing Variables Gracefully

Use Jinja2 default filter:

```python
"body": '''{
    "user_id": "{{ QUERY_PARAMS.user_id | default('unknown') }}",
    "status": "{{ QUERY_PARAMS.status | default('active') }}"
}'''
```

### 7. Test Template Rendering

Always test endpoints with various inputs to ensure templates render correctly:

```bash
# Test with all parameters
curl "http://localhost:9090/api/users?user_id=123&status=active"

# Test with missing parameters (if using defaults)
curl "http://localhost:9090/api/users"
```

---

## Common Patterns

### RESTful Resource Response

```python
"response": {
    "status": 200,
    "headers": {"Content-Type": "application/json"},
    "body": '''{
        "id": "{{ PATH_PARAMS.0 }}",
        "type": "user",
        "attributes": {
            "name": "{{ BODY_PROCESSED.name }}",
            "email": "{{ BODY_PROCESSED.email }}"
        },
        "links": {
            "self": "/api/users/{{ PATH_PARAMS.0 }}"
        }
    }'''
}
```

### Envelope Pattern

```python
"response": {
    "status": 200,
    "body": '''{
        "success": true,
        "data": {
            "user_id": "{{ BODY_PROCESSED.user_id }}",
            "name": "{{ BODY_PROCESSED.name }}"
        },
        "meta": {
            "timestamp": "{{ BODY_PROCESSED.timestamp }}",
            "version": "v1"
        }
    }'''
}
```

### Error Response Pattern

```python
"response": {
    "status": 400,
    "body": '''{
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": [
                {"field": "email", "error": "Invalid format"}
            ]
        },
        "request_id": "{{ HEADERS.x-request-id | default('N/A') }}"
    }'''
}
```

---

## Next Steps

- **[Body Matching](05_Body_Matching.md)** - Understand semantic matching for XML/JSON
- **[Validators and Processors](06_Validators_And_Processors.md)** - Learn to create processors for `BODY_PROCESSED`
- **[Advanced Examples](07_Advanced_Examples.md)** - See complete examples with all features
- **[Troubleshooting](09_Troubleshooting.md)** - Debug template rendering issues
