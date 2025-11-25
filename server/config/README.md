# Configuration Directory

This directory contains example configurations demonstrating MockServer capabilities.

## ⚠️ Important - Reference Only

This `config/` directory is **for reference and examples only**.

**Best Practice**: Copy this directory to your project location and customize it:

```bash
# Copy example configuration
cp -r mockserver/config /path/to/your/project/my-mocks

# Navigate to your configuration
cd /path/to/your/project/my-mocks

# Edit configuration files
# - endpoints.py (or endpoints_advanced_examples.py)
# - config.py
# - Add files to requests/ and responses/

# Start server with your configuration
python main.py --config-dir /path/to/your/project/my-mocks
```

This approach keeps the original examples intact for reference while allowing you to maintain project-specific configurations separately.

---

## Directory Structure

```
config/
├── config.py                          # Server configuration
├── endpoints.py                       # Basic endpoint definitions
├── endpoints_advanced_examples.py     # Advanced examples with validators/processors
├── requests/                          # Example request body files
│   ├── create_user.xml
│   ├── update_order.xml
│   ├── payment_notification.xml
│   ├── create_product.json
│   ├── search_products.json
│   └── checkout.json
└── responses/                         # Example response template files
    ├── lorem_ipsum.txt
    ├── user_created.xml
    ├── order_updated.xml
    ├── payment_processed.xml
    ├── product_created.json
    ├── search_results.json
    └── checkout_complete.json
```

---

## Configuration Files

### `config.py` - Server Configuration

Basic server settings:

| Setting | Description | Default |
|---------|-------------|---------|
| `server.port` | Server port | 9090 |
| `server.host` | Server host (0.0.0.0 = all interfaces) | 0.0.0.0 |
| `server.cors_enabled` | Enable CORS for cross-origin requests | true |
| `server.cors_origins` | Allowed CORS origins (* = all) | * |
| `server.reload` | Auto-reload on file changes | true |
| `logging.level` | Log level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `paths.requests_dir` | Custom requests directory | None (uses default) |
| `paths.responses_dir` | Custom responses directory | None (uses default) |

**Example:**
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

---

### `endpoints.py` / `endpoints_advanced_examples.py` - Mock Definitions

Define your mock endpoints with request matching and response configuration.

**Basic Structure:**
```python
definitions = [
    {
        "request": {
            "url": r"^/api/hello$",
            "methods": ["GET", "POST"],
            "query_params": {},      # Optional
            "headers": {},           # Optional
            "body": {}               # Optional
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"message": "Hello World"}'
        }
    }
]
```

**With Validators and Processors:**
```python
def validate_request(body):
    """Validate request body - raise ValueError on failure"""
    # Your validation logic
    pass

def process_request(body):
    """Process request body - return dict for template variables"""
    # Your processing logic
    return {"processed_data": "value"}

definitions = [
    {
        "request": {
            "url": r"^/api/users$",
            "methods": ["POST"],
            "body": {
                "value": '{"name": "...", "email": "..."}',
                "format": "json",
                "matching_mode": "semantic",
                "validator": validate_request,
                "processor": process_request
            }
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"result": "{{ BODY_PROCESSED.processed_data }}"}'
        }
    }
]
```

---

## Quick Start

### 1. Start with Example Configuration

```bash
# From mockserver directory
python main.py --config-dir config --endpoints-file endpoints.py
```

Server will start at `http://localhost:9090`

### 2. Test Basic Example

```bash
curl "http://localhost:9090/hello?name=World"
```

### 3. Test Advanced Example

```bash
# Start with advanced examples
python main.py --config-dir config --endpoints-file endpoints_advanced_examples.py

# Test user creation endpoint
curl -X POST http://localhost:9090/api/users/create \
  -H "Content-Type: application/xml" \
  -d @config/requests/create_user.xml
```

---

## Example Files

### `endpoints.py` - Basic Examples

Demonstrates core features:
- Query parameter matching
- Path parameter extraction with regex
- Header validation
- JSON body handling
- File-based responses
- Round-robin responses (cycling)
- Error simulation (404, 500)

**8 example endpoints** covering basic MockServer functionality.

### `endpoints_advanced_examples.py` - Advanced Examples

Demonstrates advanced features:
- **XML Examples** (3): Semantic matching with validators and processors
  - User creation with email/age validation
  - Order updates with calculations
  - Payment processing with currency conversion
- **JSON Examples** (3): Semantic matching with partial mode
  - Product creation with SKU validation
  - Product search with pagination
  - Checkout with tax calculations

**6 example endpoints** showing real-world validation and data processing.

---

## File Organization

The `requests/` and `responses/` directories are flexible. Organize them as you prefer:

### Option 1: Flat Structure
```
requests/
├── request1.xml
├── request2.json
└── request3.txt

responses/
├── response1.xml
└── response2.json
```

### Option 2: Grouped by Feature
```
requests/
├── users/
│   ├── create.xml
│   └── update.xml
└── orders/
    └── checkout.json

responses/
├── users/
│   └── created.xml
└── orders/
    └── completed.json
```

Reference files in `endpoints.py` using relative paths:
```python
"body_file": "users/created.xml"  # Relative to responses/
```

---

## Template Variables

Use template variables in responses to include data from requests:

| Variable | Description | Example |
|----------|-------------|---------|
| `QUERY_PARAMS.name` | Query parameter value | `{{ QUERY_PARAMS.user_id }}` |
| `PATH_PARAMS.0` | Path parameter by index | `{{ PATH_PARAMS.0 }}` |
| `HEADERS.Authorization` | Header value | `{{ HEADERS.Authorization }}` |
| `BODY` | Complete request body | `{{ BODY }}` |
| `BODY_PROCESSED.field` | Processor output | `{{ BODY_PROCESSED.user_id }}` |

**Example:**
```python
"body": '{
    "greeting": "Hello {{ QUERY_PARAMS.name }}!",
    "user_id": "{{ BODY_PROCESSED.generated_id }}"
}'
```

---

## Testing Your Configuration

Use the included test files:

### cURL Commands
```bash
# See docs/sample_curls/endpoints.curl.txt
# See docs/sample_curls/endpoints_advanced_examples.curl.txt
```

### Postman Collections
```bash
# Import from docs/sample_postman/
# - endpoints.postman.collection.json
# - endpoints_advanced_examples.postman.collection.json
```

---

## Full Documentation

For comprehensive guides, see the `docs/` directory:

- [Quickstart Guide](../docs/01_Quickstart_Guide.md)
- [Request Configuration](../docs/03_Request_Configuration.md)
- [Response Templates](../docs/04_Response_Templates.md)
- [Validators and Processors](../docs/06_Validators_And_Processors.md)
- [Advanced Examples](../docs/07_Advanced_Examples.md)

---

## Next Steps

1. **Explore Examples**: Start the server and test the included endpoints
2. **Copy Configuration**: Create your own configuration directory
3. **Define Endpoints**: Add your mock endpoint definitions
4. **Add Validation**: Implement custom validators for business rules
5. **Process Data**: Create processors to transform request data
6. **Test**: Use curl or Postman to verify your mocks

---

## Common Patterns

### Simple GET with Query Parameter
```python
{
    "request": {
        "url": r"^/api/items$",
        "methods": ["GET"],
        "query_params": {"id": r"\d+"}
    },
    "response": {
        "status": 200,
        "body": '{"item_id": "{{ QUERY_PARAMS.id }}"}'
    }
}
```

### POST with JSON Validation
```python
def validate_json(body):
    data = json.loads(body)
    if "email" not in data:
        raise ValueError("Email is required")
    if "@" not in data["email"]:
        raise ValueError("Invalid email format")

{
    "request": {
        "url": r"^/api/register$",
        "methods": ["POST"],
        "body": {
            "value": '{"email": "...", "name": "..."}',
            "format": "json",
            "matching_mode": "semantic",
            "validator": validate_json
        }
    },
    "response": {
        "status": 201,
        "body": '{"success": true}'
    }
}
```

### Response from File
```python
{
    "request": {
        "url": r"^/api/docs$",
        "methods": ["GET"]
    },
    "response": {
        "status": 200,
        "headers": {"Content-Type": "application/json"},
        "body_file": "documentation.json"  # Loads from responses/documentation.json
    }
}
```

---

For more examples and detailed explanations, see the full documentation in `docs/`.
