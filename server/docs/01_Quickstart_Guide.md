# Quickstart Guide

Get up and running with MockServer in 5 minutes! This guide walks you through installation, your first mock, and testing with validators and processors.

---

## Prerequisites

- **Python 3.11 or higher**
- **pip** (Python package manager)
- **curl** (for testing endpoints)

### Check Your Python Version

**Linux/macOS:**
```bash
python3 --version
```

**Windows:**
```cmd
python --version
```

If you need to install Python, visit [python.org/downloads](https://www.python.org/downloads/).

---

## Installation

### Step 1: Navigate to MockServer Directory

From your project root:

```bash
cd mockserver
```

### Step 2: Create Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv venv
```

**Windows:**
```cmd
python -m venv venv
```

### Step 3: Activate Virtual Environment

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask (web server)
- Jinja2 (template engine)
- lxml (XML processing)
- Other dependencies

---

## Your First Mock: Hello World

Let's create a simple "Hello World" endpoint that responds to GET requests.

### Step 1: Create Configuration Directory

For this quickstart, we'll use the included example configuration:

```bash
# Already exists in mockserver/config/
ls config
```

You should see:
- `config.py` - Server configuration
- `endpoints.py` - Endpoint definitions
- `requests/` - Request body examples
- `responses/` - Response template files

### Step 2: Review Basic Configuration

The `config/config.py` file contains server settings:

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
    }
}
```

### Step 3: Review Simple Endpoint Definition

Open `config/endpoints.py` and look at the first example:

```python
definitions = [
    {
        "request": {
            "url": r"^/hello$",
            "methods": ["GET"],
            "query_params": {
                "name": r".+"  # Matches any non-empty value
            }
        },
        "response": {
            "status": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '{"message": "hello world {{ QUERY_PARAMS.name }}"}'
        }
    }
]
```

**What this does:**
- Matches GET requests to `/hello`
- Requires a `name` query parameter
- Returns JSON with the name in the message
- Uses `{{ QUERY_PARAMS.name }}` template variable

### Step 4: Start the Server

```bash
python main.py --config-dir config --endpoints-file endpoints.py
```

You should see:

```
[INFO] Starting MockServer...
[INFO] Loaded 8 endpoint definitions
[INFO] Server running on http://0.0.0.0:9090
```

### Step 5: Test Your First Mock

Open a new terminal (keep the server running) and test with curl:

```bash
curl "http://localhost:9090/hello?name=World"
```

**Expected response:**
```json
{"message": "hello world World"}
```

**Try different names:**
```bash
curl "http://localhost:9090/hello?name=Alice"
# {"message": "hello world Alice"}

curl "http://localhost:9090/hello?name=Bob"
# {"message": "hello world Bob"}
```

**What happens without the name parameter?**
```bash
curl "http://localhost:9090/hello"
# {"error": "No matching mock found for request"}
```

The request doesn't match because the `name` parameter is required.

---

## Adding a Validator

Validators enforce business rules on incoming requests. Let's create an endpoint that validates user age.

### Step 1: Create a New Endpoints File

Create `config/quickstart_endpoints.py`:

```python
import json

def validate_user_age(body):
    """Validator: Ensure user age is between 18 and 120"""
    data = json.loads(body)

    age = data.get("age")

    if age is None:
        raise ValueError("Age is required")

    if not isinstance(age, int):
        raise ValueError("Age must be an integer")

    if age < 18:
        raise ValueError("User must be at least 18 years old")

    if age > 120:
        raise ValueError("Age must be 120 or less")

definitions = [
    {
        "request": {
            "url": r"^/api/users$",
            "methods": ["POST"],
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {
                "value": '{"name": "...", "email": "...", "age": 0}',
                "format": "json",
                "matching_mode": "semantic",
                "validator": validate_user_age
            }
        },
        "response": {
            "status": 201,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '{"success": true, "message": "User created successfully"}'
        }
    }
]
```

### Step 2: Restart Server with New Configuration

Stop the server (Ctrl+C) and restart with the new file:

```bash
python main.py --config-dir config --endpoints-file quickstart_endpoints.py
```

### Step 3: Test Valid Request

```bash
curl -X POST http://localhost:9090/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "age": 25}'
```

**Expected response:**
```json
{"success": true, "message": "User created successfully"}
```

### Step 4: Test Invalid Requests

**Missing age:**
```bash
curl -X POST http://localhost:9090/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "email": "bob@example.com"}'
```

**Response:**
```json
{"error": "Validation failed: Age is required"}
```

**Age too young:**
```bash
curl -X POST http://localhost:9090/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Charlie", "email": "charlie@example.com", "age": 15}'
```

**Response:**
```json
{"error": "Validation failed: User must be at least 18 years old"}
```

**Age too old:**
```bash
curl -X POST http://localhost:9090/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Dave", "email": "dave@example.com", "age": 150}'
```

**Response:**
```json
{"error": "Validation failed: Age must be 120 or less"}
```

---

## Adding a Processor

Processors extract and transform data from requests for use in responses. Let's create an endpoint that generates a user ID and formats the response.

### Step 1: Update Endpoints File with Processor

Update `config/quickstart_endpoints.py`:

```python
import json
import uuid
from datetime import datetime

def validate_user_age(body):
    """Validator: Ensure user age is between 18 and 120"""
    data = json.loads(body)

    age = data.get("age")

    if age is None:
        raise ValueError("Age is required")

    if not isinstance(age, int):
        raise ValueError("Age must be an integer")

    if age < 18:
        raise ValueError("User must be at least 18 years old")

    if age > 120:
        raise ValueError("Age must be 120 or less")

def process_user_data(body):
    """Processor: Generate user ID and format response data"""
    data = json.loads(body)

    # Generate unique user ID
    user_id = str(uuid.uuid4())

    # Determine age group
    age = data.get("age", 0)
    if age < 30:
        age_group = "young_adult"
    elif age < 60:
        age_group = "adult"
    else:
        age_group = "senior"

    # Format email to lowercase
    email = data.get("email", "").lower()

    # Add timestamp
    timestamp = datetime.utcnow().isoformat() + "Z"

    return {
        "user_id": user_id,
        "name": data.get("name", ""),
        "email": email,
        "age": age,
        "age_group": age_group,
        "created_at": timestamp
    }

definitions = [
    {
        "request": {
            "url": r"^/api/users$",
            "methods": ["POST"],
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {
                "value": '{"name": "...", "email": "...", "age": 0}',
                "format": "json",
                "matching_mode": "semantic",
                "validator": validate_user_age,
                "processor": process_user_data
            }
        },
        "response": {
            "status": 201,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": '''{
                "success": true,
                "message": "User created successfully",
                "data": {
                    "user_id": "{{ BODY_PROCESSED.user_id }}",
                    "name": "{{ BODY_PROCESSED.name }}",
                    "email": "{{ BODY_PROCESSED.email }}",
                    "age": {{ BODY_PROCESSED.age }},
                    "age_group": "{{ BODY_PROCESSED.age_group }}",
                    "created_at": "{{ BODY_PROCESSED.created_at }}"
                }
            }'''
        }
    }
]
```

### Step 2: Restart Server

```bash
python main.py --config-dir config --endpoints-file quickstart_endpoints.py
```

### Step 3: Test with Processor

```bash
curl -X POST http://localhost:9090/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Smith", "email": "ALICE@EXAMPLE.COM", "age": 25}'
```

**Expected response:**
```json
{
    "success": true,
    "message": "User created successfully",
    "data": {
        "user_id": "a7f3d9c2-8e4b-4a1c-9f2e-3b5c6d7e8f9a",
        "name": "Alice Smith",
        "email": "alice@example.com",
        "age": 25,
        "age_group": "young_adult",
        "created_at": "2024-01-15T10:30:45.123456Z"
    }
}
```

**Note:**
- `user_id` is auto-generated (UUID)
- `email` is converted to lowercase
- `age_group` is calculated based on age
- `created_at` timestamp is added
- All these values come from the processor via `{{ BODY_PROCESSED.* }}` template variables

**Test with different ages:**

```bash
# Young adult (age < 30)
curl -X POST http://localhost:9090/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "email": "bob@example.com", "age": 28}'
# age_group: "young_adult"

# Adult (30 <= age < 60)
curl -X POST http://localhost:9090/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Carol", "email": "carol@example.com", "age": 45}'
# age_group: "adult"

# Senior (age >= 60)
curl -X POST http://localhost:9090/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Dave", "email": "dave@example.com", "age": 65}'
# age_group: "senior"
```

---

## Understanding Template Variables

Template variables allow you to dynamically insert data from the request into the response.

### Available Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `QUERY_PARAMS.name` | Query parameter value | `{{ QUERY_PARAMS.user_id }}` |
| `PATH_PARAMS.0` | Path parameter by index | `{{ PATH_PARAMS.0 }}` |
| `HEADERS.name` | Request header value | `{{ HEADERS.Authorization }}` |
| `BODY` | Complete request body | `{{ BODY }}` |
| `BODY_PROCESSED.field` | Processed data from processor | `{{ BODY_PROCESSED.user_id }}` |

### Example: Using Multiple Template Variables

```python
{
    "request": {
        "url": r"^/api/greet/(?P<name>[^/]+)$",
        "methods": ["GET"],
        "query_params": {
            "lang": r"(en|es|fr)"
        },
        "headers": {
            "X-User-Id": r".+"
        }
    },
    "response": {
        "status": 200,
        "body": '''{
            "greeting": "Hello {{ PATH_PARAMS.0 }}!",
            "language": "{{ QUERY_PARAMS.lang }}",
            "user_id": "{{ HEADERS.X-User-Id }}"
        }'''
    }
}
```

**Test:**
```bash
curl "http://localhost:9090/api/greet/Alice?lang=en" \
  -H "X-User-Id: 12345"
```

**Response:**
```json
{
    "greeting": "Hello Alice!",
    "language": "en",
    "user_id": "12345"
}
```

---

## Complete Example: All Features Together

Here's a complete example combining validators, processors, and template variables:

```python
import json
import uuid
from datetime import datetime, timedelta

def validate_order(body):
    """Validate order data"""
    data = json.loads(body)

    if "items" not in data:
        raise ValueError("Order must contain items")

    if not isinstance(data["items"], list):
        raise ValueError("Items must be a list")

    if len(data["items"]) == 0:
        raise ValueError("Order must contain at least one item")

    for item in data["items"]:
        if "quantity" not in item or item["quantity"] <= 0:
            raise ValueError("Each item must have a positive quantity")

def process_order(body):
    """Process order and calculate totals"""
    data = json.loads(body)

    # Generate order ID
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

    # Calculate totals
    subtotal = sum(
        item.get("price", 0) * item.get("quantity", 0)
        for item in data.get("items", [])
    )

    tax = subtotal * 0.16  # 16% tax
    total = subtotal + tax

    # Estimate delivery
    delivery_date = (datetime.utcnow() + timedelta(days=3)).isoformat()[:10]

    return {
        "order_id": order_id,
        "subtotal": f"{subtotal:.2f}",
        "tax": f"{tax:.2f}",
        "total": f"{total:.2f}",
        "estimated_delivery": delivery_date
    }

definitions = [
    {
        "request": {
            "url": r"^/api/orders$",
            "methods": ["POST"],
            "body": {
                "value": '{"items": [{"name": "...", "quantity": 0, "price": 0}]}',
                "format": "json",
                "matching_mode": "semantic",
                "validator": validate_order,
                "processor": process_order
            }
        },
        "response": {
            "status": 201,
            "body": '''{
                "success": true,
                "order_id": "{{ BODY_PROCESSED.order_id }}",
                "subtotal": "{{ BODY_PROCESSED.subtotal }}",
                "tax": "{{ BODY_PROCESSED.tax }}",
                "total": "{{ BODY_PROCESSED.total }}",
                "estimated_delivery": "{{ BODY_PROCESSED.estimated_delivery }}"
            }'''
        }
    }
]
```

**Test:**
```bash
curl -X POST http://localhost:9090/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
        {"name": "Product A", "quantity": 2, "price": 10.00},
        {"name": "Product B", "quantity": 1, "price": 25.00}
    ]
}'
```

**Response:**
```json
{
    "success": true,
    "order_id": "ORD-A3F9D2C8",
    "subtotal": "45.00",
    "tax": "7.20",
    "total": "52.20",
    "estimated_delivery": "2024-01-18"
}
```

---

## Server Health Check

MockServer provides a built-in health check endpoint:

```bash
curl http://localhost:9090/_health
```

**Response:**
```json
{
    "status": "healthy",
    "uptime": 42.5,
    "definitions_loaded": 1,
    "config_dir": "/path/to/config"
}
```

---

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

---

## Next Steps

Now that you've mastered the basics, explore more advanced features:

1. **[Server Startup Options](02_Server_Startup_Options.md)** - Learn all CLI options and configuration settings
2. **[Request Configuration](03_Request_Configuration.md)** - Deep dive into request matching, validators, and processors
3. **[Response Templates](04_Response_Templates.md)** - Advanced response generation with Jinja2 templates
4. **[Body Matching](05_Body_Matching.md)** - Understand semantic XML/JSON matching
5. **[Advanced Examples](07_Advanced_Examples.md)** - Real-world examples with complex validators and processors

---

## Common Issues

### Port Already in Use

```
Error: Address already in use
```

**Solution:** Use a different port:
```bash
python main.py --config-dir config --endpoints-file endpoints.py --port 8080
```

### Module Not Found

```
ModuleNotFoundError: No module named 'flask'
```

**Solution:** Ensure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### No Matching Mock Found

```json
{"error": "No matching mock found for request"}
```

**Solution:**
- Check the URL matches exactly (including query parameters)
- Verify HTTP method (GET, POST, etc.)
- Check request headers match if specified
- Review server logs for details (use `--log-level DEBUG`)

---

## Summary

You've learned:

✅ How to install and set up MockServer
✅ How to create basic mocks with template variables
✅ How to add validators to enforce business rules
✅ How to use processors to transform request data
✅ How to test endpoints with curl
✅ How to combine all features for complex scenarios

**Ready to dive deeper?** Check out the [Advanced Examples](07_Advanced_Examples.md) for real-world use cases with XML, JSON, and complex processing logic.
