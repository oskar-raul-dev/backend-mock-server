# Validators and Processors

This guide provides comprehensive documentation on validators and processors - the two key mechanisms for adding business logic and data transformation to your mocks.

---

## Overview

**Validators** and **Processors** are Python functions that execute when a request body matches your endpoint definition:

| Feature | Purpose | When It Runs | Returns | On Failure |
|---------|---------|--------------|---------|------------|
| **Validator** | Enforce business rules | After body matching, before processor | Nothing | Raises `ValueError`, returns 400 error |
| **Processor** | Extract and transform data | After validator succeeds | Dictionary | Should not fail (or handle internally) |

**Execution flow:**
```
1. Request arrives
2. URL, methods, headers, query params checked
3. Body structure matched (semantic/partial/strict)
4. ✓ Validator runs (raises ValueError on failure)
5. ✓ Processor runs (returns dict)
6. Response template rendered with BODY_PROCESSED data
```

---

## Validators

Validators enforce business rules on incoming request data. They receive the raw request body and must raise `ValueError` if validation fails.

### Function Signature

```python
def validator_name(body: str) -> None:
    """
    Validates the request body according to business rules.

    Args:
        body: Raw request body as a string

    Raises:
        ValueError: If validation fails, with descriptive message

    Returns:
        None (implicitly returns None if validation succeeds)
    """
    # Validation logic
    pass
```

### Basic Validator Example

```python
import json

def validate_user_age(body: str) -> None:
    """Validate user age is within acceptable range"""
    data = json.loads(body)

    age = data.get('age')

    if age is None:
        raise ValueError("Age is required")

    if not isinstance(age, int):
        raise ValueError(f"Age must be an integer, got {type(age).__name__}")

    if age < 18:
        raise ValueError(f"User must be at least 18 years old, got {age}")

    if age > 120:
        raise ValueError(f"Age must be 120 or less, got {age}")
```

**Using in endpoint:**
```python
{
    "request": {
        "url": r"^/api/users$",
        "methods": ["POST"],
        "body": {
            "value": '{"name": "...", "age": 0}',
            "format": "json",
            "matching_mode": "semantic",
            "validator": validate_user_age
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
  -d '{"name": "Alice", "age": 15}'
```

**Response:**
```json
{
    "error": "Validation failed: User must be at least 18 years old, got 15"
}
```

### JSON Validation Patterns

#### Required Fields

```python
def validate_required_fields(body: str) -> None:
    """Ensure all required fields are present"""
    data = json.loads(body)

    required_fields = ['name', 'email', 'phone']

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

        if not data[field] or not str(data[field]).strip():
            raise ValueError(f"Field '{field}' cannot be empty")
```

#### Email Validation

```python
import re

def validate_email_format(body: str) -> None:
    """Validate email format"""
    data = json.loads(body)

    email = data.get('email', '')

    if not email:
        raise ValueError("Email is required")

    # Basic email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, email):
        raise ValueError(f"Invalid email format: {email}")

    # Check domain
    domain = email.split('@')[1]
    allowed_domains = ['example.com', 'test.com', 'company.com']

    if domain not in allowed_domains:
        raise ValueError(f"Email domain not allowed: {domain}")
```

#### Enum Validation

```python
def validate_status(body: str) -> None:
    """Validate status is one of allowed values"""
    data = json.loads(body)

    status = data.get('status')

    if status is None:
        raise ValueError("Status is required")

    valid_statuses = ['pending', 'active', 'completed', 'cancelled']

    if status not in valid_statuses:
        raise ValueError(
            f"Invalid status: {status}. "
            f"Must be one of: {', '.join(valid_statuses)}"
        )
```

#### Numeric Range Validation

```python
def validate_price(body: str) -> None:
    """Validate price is within acceptable range"""
    data = json.loads(body)

    price = data.get('price')

    if price is None:
        raise ValueError("Price is required")

    if not isinstance(price, (int, float)):
        raise ValueError(f"Price must be a number, got {type(price).__name__}")

    if price <= 0:
        raise ValueError(f"Price must be positive, got {price}")

    if price > 1000000:
        raise ValueError(f"Price exceeds maximum of 1,000,000, got {price}")

    # Check decimal places
    if isinstance(price, float):
        decimal_str = str(price).split('.')[1] if '.' in str(price) else ''
        if len(decimal_str) > 2:
            raise ValueError(f"Price can have at most 2 decimal places, got {price}")
```

#### Array Validation

```python
def validate_order_items(body: str) -> None:
    """Validate order contains valid items"""
    data = json.loads(body)

    items = data.get('items')

    if items is None:
        raise ValueError("Items are required")

    if not isinstance(items, list):
        raise ValueError(f"Items must be an array, got {type(items).__name__}")

    if len(items) == 0:
        raise ValueError("Order must contain at least one item")

    if len(items) > 100:
        raise ValueError(f"Order cannot contain more than 100 items, got {len(items)}")

    # Validate each item
    for idx, item in enumerate(items):
        if 'product_id' not in item:
            raise ValueError(f"Item {idx + 1} missing product_id")

        if 'quantity' not in item:
            raise ValueError(f"Item {idx + 1} missing quantity")

        quantity = item['quantity']
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError(f"Item {idx + 1} quantity must be a positive integer, got {quantity}")
```

#### Date Validation

```python
from datetime import datetime

def validate_date_range(body: str) -> None:
    """Validate date is within acceptable range"""
    data = json.loads(body)

    date_str = data.get('delivery_date')

    if not date_str:
        raise ValueError("Delivery date is required")

    # Parse date
    try:
        delivery_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Use ISO 8601 format")

    # Check date is in future
    now = datetime.utcnow()
    if delivery_date <= now:
        raise ValueError(f"Delivery date must be in the future, got {date_str}")

    # Check date is within 90 days
    max_date = now.replace(day=now.day + 90) if now.day <= 28 else now.replace(month=now.month + 3)
    if delivery_date > max_date:
        raise ValueError(f"Delivery date cannot be more than 90 days in the future")
```

### XML Validation Patterns

#### Basic XML Validation

```python
import xml.etree.ElementTree as ET

def validate_user_xml(body: str) -> None:
    """Validate user XML structure and content"""
    root = ET.fromstring(body)

    # Check required elements
    first_name = root.find('.//firstName')
    if first_name is None or not first_name.text:
        raise ValueError("firstName is required")

    last_name = root.find('.//lastName')
    if last_name is None or not last_name.text:
        raise ValueError("lastName is required")

    email = root.find('.//email')
    if email is None or not email.text:
        raise ValueError("email is required")

    # Validate email
    if '@' not in email.text or '.' not in email.text.split('@')[1]:
        raise ValueError(f"Invalid email format: {email.text}")

    # Validate age
    age_elem = root.find('.//age')
    if age_elem is None:
        raise ValueError("age is required")

    try:
        age = int(age_elem.text)
        if age < 18 or age > 120:
            raise ValueError(f"Age must be between 18 and 120, got {age}")
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"Age must be a number: {age_elem.text}")
        raise
```

#### XML with Namespaces

```python
def validate_soap_request(body: str) -> None:
    """Validate SOAP request structure"""
    root = ET.fromstring(body)

    # Define namespaces
    ns = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/'}

    # Check SOAP envelope
    body_elem = root.find('soap:Body', ns)
    if body_elem is None:
        raise ValueError("Missing SOAP Body element")

    # Check operation
    operation = body_elem.find('CreateUser', ns)
    if operation is None:
        raise ValueError("Missing CreateUser operation")

    # Validate operation content
    name = operation.find('Name')
    if name is None or not name.text:
        raise ValueError("Name is required in CreateUser operation")
```

### Complex Validation Example

```python
def validate_checkout(body: str) -> None:
    """Comprehensive checkout validation"""
    data = json.loads(body)

    # 1. Validate items
    items = data.get('items', [])
    if not items:
        raise ValueError("Cart is empty")

    total_quantity = 0
    for idx, item in enumerate(items):
        if 'product_id' not in item:
            raise ValueError(f"Item {idx + 1} missing product_id")

        if 'quantity' not in item or item['quantity'] <= 0:
            raise ValueError(f"Item {idx + 1} must have positive quantity")

        if 'price' not in item or item['price'] <= 0:
            raise ValueError(f"Item {idx + 1} must have positive price")

        total_quantity += item['quantity']

    if total_quantity > 100:
        raise ValueError(f"Cannot checkout more than 100 items total, got {total_quantity}")

    # 2. Validate shipping
    if 'shipping_method' not in data:
        raise ValueError("Shipping method is required")

    valid_shipping = ['standard', 'express', 'overnight']
    if data['shipping_method'] not in valid_shipping:
        raise ValueError(f"Invalid shipping method: {data['shipping_method']}")

    # 3. Validate shipping address
    if 'shipping_address' not in data:
        raise ValueError("Shipping address is required")

    address = data['shipping_address']
    required_address_fields = ['street', 'city', 'state', 'zip_code', 'country']

    for field in required_address_fields:
        if field not in address or not address[field]:
            raise ValueError(f"Shipping address missing {field}")

    # Validate zip code format (US)
    if address['country'] == 'US':
        zip_code = address['zip_code']
        if not re.match(r'^\d{5}(-\d{4})?$', zip_code):
            raise ValueError(f"Invalid US zip code format: {zip_code}")

    # 4. Validate payment method
    if 'payment_method' not in data:
        raise ValueError("Payment method is required")

    valid_payment = ['credit_card', 'debit_card', 'paypal']
    if data['payment_method'] not in valid_payment:
        raise ValueError(f"Invalid payment method: {data['payment_method']}")

    # 5. Validate credit card (if applicable)
    if data['payment_method'] in ['credit_card', 'debit_card']:
        if 'card_number' not in data:
            raise ValueError("Card number is required for card payments")

        card_number = data['card_number'].replace(' ', '').replace('-', '')

        if not card_number.isdigit():
            raise ValueError("Card number must contain only digits")

        if len(card_number) not in [15, 16]:
            raise ValueError(f"Invalid card number length: {len(card_number)}")
```

### Best Practices for Validators

1. **Be specific in error messages:**
```python
# Good
raise ValueError(f"Age must be between 18 and 120, got {age}")

# Bad
raise ValueError("Invalid age")
```

2. **Check types before operations:**
```python
# Good
if not isinstance(age, int):
    raise ValueError(f"Age must be an integer, got {type(age).__name__}")

# Bad (will crash with TypeError)
if age < 18:  # Crashes if age is a string
    raise ValueError("Too young")
```

3. **Validate early, fail fast:**
```python
# Good - check required field first
if 'email' not in data:
    raise ValueError("Email is required")

if '@' not in data['email']:
    raise ValueError("Invalid email format")

# Bad - will crash with KeyError if email missing
if '@' not in data['email']:
    raise ValueError("Invalid email format")
```

4. **Use constants for validation rules:**
```python
# Good
VALID_STATUSES = ['pending', 'active', 'completed', 'cancelled']
MIN_AGE = 18
MAX_AGE = 120

if status not in VALID_STATUSES:
    raise ValueError(f"Invalid status: {status}")

# Bad - magic numbers
if age < 18 or age > 120:
    raise ValueError("Invalid age")
```

---

## Processors

Processors extract and transform data from requests to generate dynamic response content. They receive the raw request body and return a dictionary accessible via `BODY_PROCESSED.*` template variables.

### Function Signature

```python
def processor_name(body: str) -> dict:
    """
    Processes the request body and extracts/transforms data.

    Args:
        body: Raw request body as a string

    Returns:
        Dictionary with processed data for use in response templates
        Keys become accessible as BODY_PROCESSED.key_name
    """
    # Processing logic
    return {"key": "value"}
```

### Basic Processor Example

```python
import json
import uuid
from datetime import datetime

def process_user_data(body: str) -> dict:
    """Extract user data and generate additional fields"""
    data = json.loads(body)

    # Extract fields
    name = data.get('name', '').strip()
    email = data.get('email', '').lower().strip()
    age = data.get('age', 0)

    # Generate ID
    user_id = str(uuid.uuid4())

    # Calculate age category
    if age < 18:
        age_category = "minor"
    elif age < 30:
        age_category = "young_adult"
    elif age < 60:
        age_category = "adult"
    else:
        age_category = "senior"

    # Add timestamp
    timestamp = datetime.utcnow().isoformat() + 'Z'

    return {
        "user_id": user_id,
        "name": name.title(),  # Capitalize
        "email": email,         # Lowercase
        "age": age,
        "age_category": age_category,
        "created_at": timestamp
    }
```

**Using in endpoint:**
```python
{
    "request": {
        "url": r"^/api/users$",
        "methods": ["POST"],
        "body": {
            "value": '{"name": "...", "email": "...", "age": 0}',
            "format": "json",
            "matching_mode": "semantic",
            "processor": process_user_data
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
                "age_category": "{{ BODY_PROCESSED.age_category }}",
                "created_at": "{{ BODY_PROCESSED.created_at }}"
            }
        }'''
    }
}
```

**Test:**
```bash
curl -X POST http://localhost:9090/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "alice smith", "email": "ALICE@EXAMPLE.COM", "age": 28}'
```

**Response:**
```json
{
    "success": true,
    "user": {
        "id": "a7f3d9c2-8e4b-4a1c-9f2e-3b5c6d7e8f9a",
        "name": "Alice Smith",
        "email": "alice@example.com",
        "age_category": "young_adult",
        "created_at": "2024-01-15T10:30:45.123456Z"
    }
}
```

### JSON Processing Patterns

#### ID Generation

```python
import uuid
import hashlib

def generate_user_id(body: str) -> dict:
    data = json.loads(body)

    # UUID-based ID
    user_id = str(uuid.uuid4())

    # Hash-based ID (deterministic)
    email_hash = hashlib.md5(data['email'].encode()).hexdigest()[:8].upper()

    # Sequential ID (for testing)
    import random
    sequential_id = f"USR{random.randint(100000, 999999)}"

    return {
        "user_id": user_id,
        "user_id_short": email_hash,
        "sequential_id": sequential_id
    }
```

#### Calculations

```python
def calculate_order_totals(body: str) -> dict:
    data = json.loads(body)

    items = data.get('items', [])

    # Calculate subtotal
    subtotal = sum(
        item.get('price', 0) * item.get('quantity', 0)
        for item in items
    )

    # Apply discount
    discount_code = data.get('discount_code', '')
    discount_percent = {
        'SAVE10': 10,
        'SAVE20': 20,
        'SAVE30': 30
    }.get(discount_code, 0)

    discount_amount = subtotal * (discount_percent / 100)
    subtotal_after_discount = subtotal - discount_amount

    # Calculate tax (16%)
    tax = subtotal_after_discount * 0.16

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

    # Calculate total
    total = subtotal_after_discount + tax + shipping_cost

    return {
        "subtotal": f"{subtotal:.2f}",
        "discount_code": discount_code,
        "discount_percent": discount_percent,
        "discount_amount": f"{discount_amount:.2f}",
        "subtotal_after_discount": f"{subtotal_after_discount:.2f}",
        "tax": f"{tax:.2f}",
        "shipping_cost": f"{shipping_cost:.2f}",
        "total": f"{total:.2f}",
        "item_count": len(items)
    }
```

#### Date Calculations

```python
from datetime import datetime, timedelta

def calculate_delivery_dates(body: str) -> dict:
    data = json.loads(body)

    shipping_method = data.get('shipping_method', 'standard')

    # Business days for each method
    business_days = {
        'standard': 5,
        'express': 2,
        'overnight': 1
    }.get(shipping_method, 5)

    # Calculate delivery date (skip weekends)
    current_date = datetime.now()
    days_added = 0
    delivery_date = current_date

    while days_added < business_days:
        delivery_date += timedelta(days=1)
        # Skip weekends (5 = Saturday, 6 = Sunday)
        if delivery_date.weekday() < 5:
            days_added += 1

    return {
        "order_date": current_date.strftime('%Y-%m-%d'),
        "estimated_delivery": delivery_date.strftime('%Y-%m-%d'),
        "delivery_days": business_days,
        "shipping_method": shipping_method
    }
```

#### Text Transformations

```python
def transform_user_data(body: str) -> dict:
    data = json.loads(body)

    name = data.get('name', '')
    email = data.get('email', '')

    # Extract parts
    name_parts = name.strip().split()
    first_name = name_parts[0] if name_parts else ''
    last_name = name_parts[-1] if len(name_parts) > 1 else ''

    # Generate username from email
    username = email.split('@')[0] if email else ''

    # Generate display name
    display_name = f"{first_name} {last_name[0]}." if last_name else first_name

    return {
        "first_name": first_name.title(),
        "last_name": last_name.title(),
        "full_name": name.title(),
        "display_name": display_name,
        "username": username.lower(),
        "email_domain": email.split('@')[1] if '@' in email else ''
    }
```

### XML Processing Patterns

```python
import xml.etree.ElementTree as ET
from datetime import datetime

def process_order_xml(body: str) -> dict:
    root = ET.fromstring(body)

    # Extract order data
    order_id = root.find('.//orderId').text
    status = root.find('.//status').text

    # Process items
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

    # Calculate tax
    tax = total_amount * 0.16
    grand_total = total_amount + tax

    # Estimate delivery
    delivery_days = 3 if status == 'express' else 5
    estimated_delivery = (datetime.now() + timedelta(days=delivery_days)).strftime('%Y-%m-%d')

    return {
        "order_id": order_id,
        "status": status,
        "total_items": total_items,
        "subtotal": f"{total_amount:.2f}",
        "tax": f"{tax:.2f}",
        "total": f"{grand_total:.2f}",
        "estimated_delivery": estimated_delivery
    }
```

### Combining Validators and Processors

Validators run before processors, ensuring data is valid before processing:

```python
def validate_order(body: str) -> None:
    """Validate order data"""
    data = json.loads(body)

    if 'items' not in data or len(data['items']) == 0:
        raise ValueError("Order must contain at least one item")

    for item in data['items']:
        if item.get('quantity', 0) <= 0:
            raise ValueError("Item quantity must be positive")
        if item.get('price', 0) <= 0:
            raise ValueError("Item price must be positive")

def process_order(body: str) -> dict:
    """Process order data (runs after validation succeeds)"""
    data = json.loads(body)

    # Safe to access items - validator guaranteed they exist
    items = data['items']

    subtotal = sum(item['price'] * item['quantity'] for item in items)
    tax = subtotal * 0.16
    total = subtotal + tax

    return {
        "order_id": str(uuid.uuid4()),
        "item_count": len(items),
        "subtotal": f"{subtotal:.2f}",
        "tax": f"{tax:.2f}",
        "total": f"{total:.2f}"
    }
```

**In endpoint:**
```python
"body": {
    "value": '{"items": [...]}',
    "format": "json",
    "matching_mode": "semantic",
    "validator": validate_order,     # Runs first
    "processor": process_order        # Runs second
}
```

### Best Practices for Processors

1. **Return consistent data types:**
```python
# Good - consistent formatting
return {
    "price": f"{price:.2f}",  # Always 2 decimals
    "tax": f"{tax:.2f}"
}

# Bad - inconsistent
return {
    "price": 10.5,  # Sometimes 1 decimal
    "tax": 1.265    # Sometimes 3 decimals
}
```

2. **Handle missing data gracefully:**
```python
# Good
name = data.get('name', 'Unknown')
age = data.get('age', 0)

# Bad - crashes if key missing
name = data['name']
age = data['age']
```

3. **Don't raise exceptions (use validators for that):**
```python
# Good
def process_user(body):
    data = json.loads(body)
    age = data.get('age', 18)  # Default if missing
    return {"age_group": "adult" if age >= 18 else "minor"}

# Bad - processing should not fail
def process_user(body):
    data = json.loads(body)
    if 'age' not in data:
        raise ValueError("Age required")  # Use validator for this
    return {"age": data['age']}
```

4. **Keep processors focused:**
```python
# Good - single responsibility
def process_user_id(body):
    return {"user_id": str(uuid.uuid4())}

def process_user_name(body):
    data = json.loads(body)
    return {"full_name": f"{data['first']} {data['last']}"}

# Bad - doing too much
def process_everything(body):
    # 200 lines of processing...
    return {...}
```

---

## Complete Examples

See [Advanced Examples](07_Advanced_Examples.md) for complete, real-world examples combining validators and processors for XML and JSON endpoints.

---

## Next Steps

- **[Advanced Examples](07_Advanced_Examples.md)** - See validators and processors in action
- **[Response Templates](04_Response_Templates.md)** - Use BODY_PROCESSED in templates
- **[Request Configuration](03_Request_Configuration.md)** - Configure validators/processors
- **[Troubleshooting](09_Troubleshooting.md)** - Debug validation and processing issues
