# Request Configuration

This guide provides an in-depth look at configuring request matching in MockServer, including URL patterns, HTTP methods, headers, query parameters, body matching, validators, and processors.

---

## Request Configuration Structure

Every endpoint definition consists of a `request` section that defines what to match and a `response` section that defines what to return.

**Basic structure:**
```python
{
    "request": {
        "url": r"^/api/endpoint$",           # URL pattern (regex)
        "methods": ["GET", "POST"],          # HTTP methods
        "query_params": {},                  # Query parameter matching (optional)
        "headers": {},                       # Header matching (optional)
        "body": {}                           # Body matching (optional)
    },
    "response": {
        # Response configuration (see Response Templates)
    }
}
```

---

## URL Matching

URLs are matched using Python regular expressions.

### Exact Match

```python
"url": r"^/api/users$"
```

Matches:
- `/api/users` ✓
- `/api/users/` ✗ (trailing slash)
- `/api/users/123` ✗ (extra path)

### Path Parameters

Extract values from the URL path using regex groups:

```python
# Single parameter
"url": r"^/api/users/([^/]+)$"
# Matches: /api/users/123

# Multiple parameters
"url": r"^/api/users/([^/]+)/orders/([^/]+)$"
# Matches: /api/users/123/orders/456

# Named groups (not used for extraction, but helpful for readability)
"url": r"^/api/users/(?P<user_id>[^/]+)$"
```

**Accessing path parameters in responses:**
```python
"body": '{"user_id": "{{ PATH_PARAMS.0 }}"}'  # First parameter
"body": '{"user_id": "{{ PATH_PARAMS.0 }}", "order_id": "{{ PATH_PARAMS.1 }}"}'  # Multiple
```

**Common patterns:**

| Pattern | Description | Example |
|---------|-------------|---------|
| `[^/]+` | Any characters except `/` | `/users/abc123` |
| `\d+` | One or more digits | `/users/123` |
| `[a-zA-Z]+` | Letters only | `/users/john` |
| `[0-9a-f-]+` | UUID format | `/users/a3f9d2c8-...` |
| `.*` | Any characters (greedy) | `/path/to/anything` |

### Complex URL Patterns

```python
# UUID pattern
"url": r"^/api/users/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$"

# Optional trailing slash
"url": r"^/api/users/?$"

# Version in URL
"url": r"^/api/v[12]/users$"

# File extensions
"url": r"^/api/downloads/([^/]+\.(pdf|doc|txt))$"
```

### Wildcards and Catch-All

```python
# Match any subpath
"url": r"^/api/.*$"

# Match specific prefix
"url": r"^/legacy/.*"

# Catch-all (useful for testing)
"url": r".*"
```

**⚠️ Warning:** More specific patterns should come before generic ones in your `definitions` list, as MockServer uses first-match logic.

---

## HTTP Methods

Specify which HTTP methods the endpoint accepts:

```python
# Single method
"methods": ["GET"]

# Multiple methods
"methods": ["GET", "POST"]

# All common methods
"methods": ["GET", "POST", "PUT", "PATCH", "DELETE"]

# Include OPTIONS for CORS preflight
"methods": ["GET", "POST", "OPTIONS"]
```

**Common combinations:**

| Use Case | Methods |
|----------|---------|
| Read-only endpoint | `["GET"]` |
| Create resource | `["POST"]` |
| Update resource | `["PUT", "PATCH"]` |
| Delete resource | `["DELETE"]` |
| Full CRUD | `["GET", "POST", "PUT", "DELETE"]` |
| With CORS | `["GET", "POST", "OPTIONS"]` |

---

## Query Parameters

Match and extract query parameters from the URL.

### Basic Query Parameter Matching

**Old format (array-based):**
```python
"query_params": [
    {"name": "user_id"}  # Parameter must exist
]
```

**New format (dict-based with regex):**
```python
"query_params": {
    "user_id": r".+"  # Parameter must exist and not be empty
}
```

### Query Parameter Validation

```python
# Require specific format
"query_params": {
    "user_id": r"\d+",          # Digits only
    "email": r".+@.+\..+",      # Basic email pattern
    "status": r"(active|inactive)",  # Enum values
    "page": r"\d{1,3}"          # 1-3 digit number
}
```

### Multiple Query Parameters

```python
"query_params": {
    "page": r"\d+",
    "limit": r"\d+",
    "sort": r"(asc|desc)",
    "filter": r".+"
}
```

**Example request:**
```
GET /api/users?page=1&limit=10&sort=asc&filter=active
```

### Optional Query Parameters

MockServer requires all query parameters specified in `query_params` to be present. For optional parameters, create separate endpoint definitions:

```python
# Endpoint with filter
{
    "request": {
        "url": r"^/api/users$",
        "methods": ["GET"],
        "query_params": {
            "page": r"\d+",
            "filter": r".+"
        }
    },
    "response": {
        "body": '{"page": {{ QUERY_PARAMS.page }}, "filter": "{{ QUERY_PARAMS.filter }}"}'
    }
},

# Endpoint without filter
{
    "request": {
        "url": r"^/api/users$",
        "methods": ["GET"],
        "query_params": {
            "page": r"\d+"
        }
    },
    "response": {
        "body": '{"page": {{ QUERY_PARAMS.page }}}'
    }
}
```

### Accessing Query Parameters

```python
"body": '{"user_id": "{{ QUERY_PARAMS.user_id }}"}'
"body": '{"page": {{ QUERY_PARAMS.page }}, "limit": {{ QUERY_PARAMS.limit }}}'
```

---

## Headers

Match and validate HTTP headers.

### Basic Header Matching

**Old format:**
```python
"headers": [
    {"name": "Content-Type", "value": "application/json"}
]
```

**New format (dict-based with regex):**
```python
"headers": {
    "Content-Type": "application/json"
}
```

### Header Validation with Regex

```python
"headers": {
    "Authorization": r"Bearer .+",           # Bearer token
    "Content-Type": "application/json",      # Exact match
    "X-API-Key": r"[A-Za-z0-9]{32}",        # 32-char alphanumeric
    "User-Agent": r".*"                      # Any user agent
}
```

### Common Header Patterns

```python
# Authentication
"headers": {
    "Authorization": r"Bearer [A-Za-z0-9\-\._~\+\/]+=*"  # JWT pattern
}

# Content negotiation
"headers": {
    "Accept": r"application/(json|xml)",
    "Content-Type": "application/json"
}

# Custom headers
"headers": {
    "X-Request-ID": r"[0-9a-f-]+",
    "X-Correlation-ID": r".+"
}

# Version headers
"headers": {
    "API-Version": r"v[12]"
}
```

### Case Sensitivity

Header names are case-insensitive in HTTP, but MockServer normalizes them to lowercase internally.

```python
# All these are equivalent:
"Content-Type"
"content-type"
"CONTENT-TYPE"
```

**When accessing in templates:**
```python
"body": '{"auth": "{{ HEADERS.authorization }}"}'  # lowercase
"body": '{"type": "{{ HEADERS.content-type }}"}'   # lowercase with hyphen
```

### Accessing Headers

```python
"body": '{
    "auth": "{{ HEADERS.authorization }}",
    "request_id": "{{ HEADERS.x-request-id }}",
    "user_agent": "{{ HEADERS.user-agent }}"
}'
```

---

## Body Matching

Body matching supports multiple formats with semantic (structure-aware) matching.

### Body Configuration Structure

```python
"body": {
    "value": '...',                    # Expected body content
    "format": "json|xml|text|binary",  # Content format
    "matching_mode": "semantic|partial|strict",  # Matching strategy
    "validator": function_name,        # Custom validator function (optional)
    "processor": function_name         # Custom processor function (optional)
}
```

### JSON Body Matching

#### Semantic Matching (Default)

Ignores key order and whitespace, focuses on structure and values:

```python
"body": {
    "value": '{"name": "...", "age": 0, "email": "..."}',
    "format": "json",
    "matching_mode": "semantic"
}
```

**Matches any of these:**
```json
{"name": "Alice", "age": 25, "email": "alice@example.com"}
{"age": 25, "name": "Alice", "email": "alice@example.com"}
{"name":"Alice","age":25,"email":"alice@example.com"}
```

#### Partial Matching

Request can contain additional fields not specified in the pattern:

```python
"body": {
    "value": '{"name": "...", "email": "..."}',
    "format": "json",
    "matching_mode": "partial"
}
```

**Matches:**
```json
{"name": "Alice", "email": "alice@example.com"}
{"name": "Alice", "email": "alice@example.com", "age": 25, "extra": "data"}
```

#### Strict Matching

Exact match required (including key order):

```python
"body": {
    "value": '{"name": "...", "age": 0}',
    "format": "json",
    "matching_mode": "strict"
}
```

**Matches only:**
```json
{"name": "Alice", "age": 25}
```

**Does not match:**
```json
{"age": 25, "name": "Alice"}  # Different key order
{"name": "Alice", "age": 25, "email": "..."}  # Extra fields
```

### XML Body Matching

#### Semantic Matching

Ignores element order, whitespace, and formatting:

```python
"body": {
    "value": '''<?xml version="1.0"?>
    <user>
        <name>...</name>
        <age>0</age>
    </user>''',
    "format": "xml",
    "matching_mode": "semantic"
}
```

**Matches any of these:**
```xml
<user><name>Alice</name><age>25</age></user>
<user><age>25</age><name>Alice</name></user>
<user>
    <name>Alice</name>
    <age>25</age>
</user>
```

#### Partial Matching

Request can contain additional elements:

```python
"body": {
    "value": '<user><name>...</name></user>',
    "format": "xml",
    "matching_mode": "partial"
}
```

**Matches:**
```xml
<user><name>Alice</name></user>
<user><name>Alice</name><age>25</age><email>alice@example.com</email></user>
```

### Plain Text Body Matching

```python
"body": {
    "value": "Hello World",
    "format": "text",
    "matching_mode": "strict"  # Exact match
}
```

For regex matching on text:
```python
"body": {
    "value": r"^Hello .+",  # Regex pattern
    "format": "text",
    "matching_mode": "strict"
}
```

### Binary Body Matching

```python
"body": {
    "value": b"binary_content_here",
    "format": "binary",
    "matching_mode": "strict"
}
```

### No Body Matching

If the request body doesn't matter, omit the `body` key:

```python
{
    "request": {
        "url": r"^/api/endpoint$",
        "methods": ["POST"]
        # No body specified - any body or no body matches
    },
    "response": {...}
}
```

---

## Validators

Validators enforce business rules on incoming requests. They must raise `ValueError` on failure.

### Validator Function Signature

```python
def validator_name(body: str) -> None:
    """
    Validates the request body.

    Args:
        body: Raw request body as string

    Raises:
        ValueError: If validation fails (message returned to client)
    """
    # Validation logic here
    pass
```

### JSON Validators

```python
import json

def validate_user_registration(body: str) -> None:
    """Validate user registration data"""
    data = json.loads(body)

    # Required fields
    required = ['name', 'email', 'age']
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Email format
    email = data['email']
    if '@' not in email or '.' not in email.split('@')[1]:
        raise ValueError(f"Invalid email format: {email}")

    # Age range
    age = data['age']
    if not isinstance(age, int):
        raise ValueError(f"Age must be an integer, got {type(age).__name__}")
    if age < 18 or age > 120:
        raise ValueError(f"Age must be between 18 and 120, got {age}")

    # Email domain whitelist (example)
    allowed_domains = ['example.com', 'test.com']
    domain = email.split('@')[1]
    if domain not in allowed_domains:
        raise ValueError(f"Email domain not allowed: {domain}")
```

### XML Validators

```python
import xml.etree.ElementTree as ET

def validate_order_xml(body: str) -> None:
    """Validate order XML structure"""
    root = ET.fromstring(body)

    # Required elements
    order_id = root.find('.//orderId')
    if order_id is None or not order_id.text:
        raise ValueError("Order ID is required")

    # Status validation
    status = root.find('.//status')
    if status is None:
        raise ValueError("Order status is required")

    valid_statuses = ['pending', 'processing', 'completed', 'cancelled']
    if status.text not in valid_statuses:
        raise ValueError(f"Invalid status: {status.text}. Must be one of {valid_statuses}")

    # Items validation
    items = root.findall('.//item')
    if not items:
        raise ValueError("Order must contain at least one item")

    # Validate each item
    for idx, item in enumerate(items):
        quantity = item.find('quantity')
        if quantity is None:
            raise ValueError(f"Item {idx + 1} missing quantity")

        try:
            qty_value = int(quantity.text)
            if qty_value <= 0:
                raise ValueError(f"Item {idx + 1} quantity must be positive, got {qty_value}")
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"Item {idx + 1} quantity must be a number: {quantity.text}")
            raise
```

### Complex Validation Example

```python
def validate_payment_request(body: str) -> None:
    """Comprehensive payment validation"""
    data = json.loads(body)

    # Required fields
    if 'amount' not in data:
        raise ValueError("Payment amount is required")
    if 'currency' not in data:
        raise ValueError("Currency is required")
    if 'payment_method' not in data:
        raise ValueError("Payment method is required")

    # Amount validation
    amount = data['amount']
    if not isinstance(amount, (int, float)):
        raise ValueError(f"Amount must be a number, got {type(amount).__name__}")
    if amount <= 0:
        raise ValueError(f"Amount must be positive, got {amount}")
    if amount > 100000:
        raise ValueError(f"Amount exceeds maximum limit of 100,000")

    # Currency validation
    valid_currencies = ['USD', 'EUR', 'GBP', 'MXN']
    currency = data['currency'].upper()
    if currency not in valid_currencies:
        raise ValueError(f"Invalid currency: {currency}. Must be one of {valid_currencies}")

    # Payment method validation
    valid_methods = ['credit_card', 'debit_card', 'paypal', 'bank_transfer']
    method = data['payment_method']
    if method not in valid_methods:
        raise ValueError(f"Invalid payment method: {method}")

    # Card number validation (if credit/debit card)
    if method in ['credit_card', 'debit_card']:
        if 'card_number' not in data:
            raise ValueError("Card number is required for card payments")

        card_number = data['card_number'].replace(' ', '').replace('-', '')
        if not card_number.isdigit():
            raise ValueError("Card number must contain only digits")
        if len(card_number) not in [15, 16]:  # Amex = 15, others = 16
            raise ValueError(f"Invalid card number length: {len(card_number)}")
```

### Using Validators in Endpoint Definitions

```python
{
    "request": {
        "url": r"^/api/users$",
        "methods": ["POST"],
        "body": {
            "value": '{"name": "...", "email": "...", "age": 0}',
            "format": "json",
            "matching_mode": "semantic",
            "validator": validate_user_registration  # Reference function
        }
    },
    "response": {
        "status": 201,
        "body": '{"success": true}'
    }
}
```

**When validator fails:**
```bash
curl -X POST http://localhost:9090/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "invalid", "age": 15}'
```

**Response:**
```json
{
    "error": "Validation failed: Invalid email format: invalid"
}
```

---

## Processors

Processors extract and transform data from requests for use in response templates.

### Processor Function Signature

```python
def processor_name(body: str) -> dict:
    """
    Processes the request body.

    Args:
        body: Raw request body as string

    Returns:
        Dictionary with processed data for template variables
    """
    # Processing logic here
    return {"key": "value"}
```

### JSON Processors

```python
import json
import uuid
from datetime import datetime

def process_user_data(body: str) -> dict:
    """Extract and enrich user data"""
    data = json.loads(body)

    # Generate unique ID
    user_id = str(uuid.uuid4())

    # Format name
    name = data.get('name', '').strip().title()

    # Normalize email
    email = data.get('email', '').lower().strip()

    # Calculate age category
    age = data.get('age', 0)
    if age < 18:
        category = "minor"
    elif age < 30:
        category = "young_adult"
    elif age < 60:
        category = "adult"
    else:
        category = "senior"

    # Add timestamp
    timestamp = datetime.utcnow().isoformat() + 'Z'

    return {
        "user_id": user_id,
        "name": name,
        "email": email,
        "age": age,
        "category": category,
        "created_at": timestamp
    }
```

### XML Processors

```python
import xml.etree.ElementTree as ET
import hashlib
from datetime import datetime, timedelta

def process_order_data(body: str) -> dict:
    """Calculate order totals and delivery estimates"""
    root = ET.fromstring(body)

    # Extract order ID
    order_id = root.find('.//orderId').text

    # Extract and sum items
    items = root.findall('.//item')
    total_items = len(items)
    total_amount = 0.0

    for item in items:
        price_elem = item.find('price')
        quantity_elem = item.find('quantity')

        if price_elem is not None and quantity_elem is not None:
            price = float(price_elem.text)
            quantity = int(quantity_elem.text)
            total_amount += price * quantity

    # Calculate tax (16%)
    tax = total_amount * 0.16
    grand_total = total_amount + tax

    # Estimate delivery (3 business days)
    estimated_delivery = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')

    # Generate tracking number
    tracking = hashlib.md5(order_id.encode()).hexdigest()[:12].upper()

    return {
        "order_id": order_id,
        "total_items": total_items,
        "subtotal": f"{total_amount:.2f}",
        "tax": f"{tax:.2f}",
        "total": f"{grand_total:.2f}",
        "estimated_delivery": estimated_delivery,
        "tracking_number": tracking
    }
```

### Complex Processing Example

```python
def process_checkout(body: str) -> dict:
    """Process checkout with complex calculations"""
    data = json.loads(body)

    # Extract cart items
    items = data.get('items', [])

    # Calculate subtotal
    subtotal = sum(
        item.get('price', 0) * item.get('quantity', 0)
        for item in items
    )

    # Apply discounts
    discount_code = data.get('discount_code', '')
    discount_percent = 0
    if discount_code == 'SAVE10':
        discount_percent = 10
    elif discount_code == 'SAVE20':
        discount_percent = 20

    discount_amount = subtotal * (discount_percent / 100)
    subtotal_after_discount = subtotal - discount_amount

    # Calculate shipping
    shipping_method = data.get('shipping_method', 'standard')
    shipping_cost = {
        'standard': 5.00,
        'express': 15.00,
        'overnight': 25.00
    }.get(shipping_method, 5.00)

    # Free shipping over $50
    if subtotal_after_discount >= 50:
        shipping_cost = 0.00

    # Calculate tax (based on state)
    state = data.get('state', 'CA')
    tax_rates = {
        'CA': 0.0725,  # California
        'NY': 0.08,    # New York
        'TX': 0.0625,  # Texas
        'FL': 0.06     # Florida
    }
    tax_rate = tax_rates.get(state, 0.07)
    tax = (subtotal_after_discount + shipping_cost) * tax_rate

    # Calculate total
    total = subtotal_after_discount + shipping_cost + tax

    # Generate IDs
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

    return {
        "order_id": order_id,
        "transaction_id": transaction_id,
        "subtotal": f"{subtotal:.2f}",
        "discount_code": discount_code,
        "discount_percent": discount_percent,
        "discount_amount": f"{discount_amount:.2f}",
        "shipping_method": shipping_method,
        "shipping_cost": f"{shipping_cost:.2f}",
        "tax_rate": f"{tax_rate * 100:.2f}",
        "tax": f"{tax:.2f}",
        "total": f"{total:.2f}"
    }
```

### Using Processors in Endpoint Definitions

```python
{
    "request": {
        "url": r"^/api/users$",
        "methods": ["POST"],
        "body": {
            "value": '{"name": "...", "email": "...", "age": 0}',
            "format": "json",
            "matching_mode": "semantic",
            "processor": process_user_data  # Reference function
        }
    },
    "response": {
        "status": 201,
        "body": '''{
            "success": true,
            "user": {
                "id": "{{ BODY_PROCESSED.user_id }}",
                "name": "{{ BODY_PROCESSED.name }}",
                "email": "{{ BODY_PROCESSED.email }}",
                "category": "{{ BODY_PROCESSED.category }}",
                "created_at": "{{ BODY_PROCESSED.created_at }}"
            }
        }'''
    }
}
```

### Combining Validators and Processors

```python
{
    "request": {
        "url": r"^/api/orders$",
        "methods": ["POST"],
        "body": {
            "value": '{"items": [...]}',
            "format": "json",
            "matching_mode": "semantic",
            "validator": validate_order,      # Runs first
            "processor": process_order_data   # Runs after validation succeeds
        }
    },
    "response": {
        "status": 201,
        "body": '{"order_id": "{{ BODY_PROCESSED.order_id }}", "total": "{{ BODY_PROCESSED.total }}"}'
    }
}
```

**Processing order:**
1. Request matches URL, methods, headers, query params
2. Body structure matches (semantic/partial/strict)
3. Validator runs - if it raises ValueError, request fails
4. Processor runs - returned dict available as `BODY_PROCESSED.*`
5. Response template rendered with processed data

---

## Multiple Responses (Round-Robin)

Simulate stateful behavior by cycling through multiple responses.

### Configuration

```python
{
    "request": {
        "url": r"^/api/counter$",
        "methods": ["GET"]
    },
    "response": [  # Array of responses
        {
            "status": 200,
            "body": '{"count": 1}'
        },
        {
            "status": 200,
            "body": '{"count": 2}'
        },
        {
            "status": 200,
            "body": '{"count": 3}'
        }
    ]
}
```

**Behavior:**
- 1st request: Returns `{"count": 1}`
- 2nd request: Returns `{"count": 2}`
- 3rd request: Returns `{"count": 3}`
- 4th request: Returns `{"count": 1}` (cycles back)

### Use Cases

**Simulating pagination:**
```python
"response": [
    {"status": 200, "body": '{"page": 1, "data": [...]}'},
    {"status": 200, "body": '{"page": 2, "data": [...]}'},
    {"status": 200, "body": '{"page": 3, "data": []}'}  # Empty last page
]
```

**Simulating state changes:**
```python
"response": [
    {"status": 200, "body": '{"status": "pending"}'},
    {"status": 200, "body": '{"status": "processing"}'},
    {"status": 200, "body": '{"status": "completed"}'}
]
```

**Simulating errors:**
```python
"response": [
    {"status": 200, "body": '{"success": true}'},
    {"status": 200, "body": '{"success": true}'},
    {"status": 500, "body": '{"error": "Unexpected error"}'}  # 3rd request fails
]
```

---

## Best Practices

### 1. Order Endpoint Definitions by Specificity

More specific patterns should come first:

```python
definitions = [
    # More specific first
    {
        "request": {
            "url": r"^/api/users/me$",
            "methods": ["GET"]
        },
        "response": {"body": '{"current_user": true}'}
    },

    # Less specific second
    {
        "request": {
            "url": r"^/api/users/([^/]+)$",
            "methods": ["GET"]
        },
        "response": {"body": '{"user_id": "{{ PATH_PARAMS.0 }}"}'}
    }
]
```

### 2. Use Semantic Matching for Flexibility

Prefer `semantic` mode for JSON/XML unless order matters:

```python
"body": {
    "value": '{"name": "...", "email": "..."}',
    "format": "json",
    "matching_mode": "semantic"  # Best for most cases
}
```

### 3. Validate Early, Process After

Keep validators focused on validation, processors focused on transformation:

```python
# Good
def validate_user(body):
    data = json.loads(body)
    if 'email' not in data:
        raise ValueError("Email required")
    if '@' not in data['email']:
        raise ValueError("Invalid email")

def process_user(body):
    data = json.loads(body)
    return {"user_id": generate_id(), "email": data['email'].lower()}

# Bad - mixing concerns
def validate_and_process_user(body):
    data = json.loads(body)
    if 'email' not in data:
        raise ValueError("Email required")
    return {"user_id": generate_id(), "email": data['email'].lower()}
```

### 4. Document Complex Validators

Add docstrings explaining validation rules:

```python
def validate_order(body: str) -> None:
    """
    Validates order request.

    Rules:
    - Status must be one of: pending, processing, completed, cancelled
    - Must have at least one item
    - Each item must have positive quantity
    - Total order value must not exceed $10,000

    Raises:
        ValueError: If any validation rule fails
    """
    # Implementation...
```

### 5. Use Partial Matching for Flexible APIs

Allow clients to send extra fields:

```python
"body": {
    "value": '{"name": "...", "email": "..."}',  # Only these required
    "format": "json",
    "matching_mode": "partial"  # Allows additional fields
}
```

### 6. Normalize Data in Processors

```python
def process_user(body: str) -> dict:
    data = json.loads(body)
    return {
        "email": data['email'].lower().strip(),  # Normalize
        "name": data['name'].strip().title(),     # Normalize
        "phone": data.get('phone', '').replace('-', '').replace(' ', '')  # Normalize
    }
```

---

## Next Steps

- **[Response Templates](04_Response_Templates.md)** - Learn to create dynamic responses using processed data
- **[Body Matching](05_Body_Matching.md)** - Deep dive into semantic matching algorithms
- **[Validators and Processors](06_Validators_And_Processors.md)** - More examples and patterns
- **[Advanced Examples](07_Advanced_Examples.md)** - Real-world complete examples
