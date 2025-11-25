# Body Matching

This guide explains MockServer's semantic body matching capabilities, which understand XML and JSON structure rather than performing simple string comparison.

---

## What is Semantic Matching?

**Traditional string matching** compares request bodies character-by-character. This is fragile and fails when:
- JSON/XML keys are in different order
- Whitespace or formatting differs
- Comments are present (in formats that support them)

**Semantic matching** understands the structure and meaning of data formats:
- **JSON**: Compares object structure and values, ignoring key order and whitespace
- **XML**: Compares element structure and values, ignoring element order, whitespace, and attributes (when appropriate)
- **Result**: More reliable mocking that focuses on data content, not formatting

---

## Matching Modes

MockServer supports three matching modes for JSON and XML bodies:

| Mode | Description | Use Case |
|------|-------------|----------|
| **semantic** | Full structural equality, ignores formatting | Most common; ensures complete match |
| **partial** | Request can contain additional fields/elements | Flexible APIs where clients send extra data |
| **strict** | Exact match including order and formatting | Rare; when order matters |

**Configuration:**
```python
"body": {
    "value": '...',
    "format": "json|xml",
    "matching_mode": "semantic|partial|strict"
}
```

---

## JSON Semantic Matching

### How It Works

MockServer parses both the expected pattern and actual request into JSON objects, then compares:

1. **Structure**: Both must have the same keys (semantic mode) or pattern keys must be subset (partial mode)
2. **Values**: Values are compared for equality
3. **Types**: Data types must match (string, number, boolean, null, object, array)
4. **Order**: Key order doesn't matter

### Semantic Mode (Default)

**Pattern:**
```python
"body": {
    "value": '{"name": "...", "age": 0, "email": "..."}',
    "format": "json",
    "matching_mode": "semantic"
}
```

**Matches:**
```json
{"name": "Alice", "age": 25, "email": "alice@example.com"}
{"age": 25, "name": "Alice", "email": "alice@example.com"}
{"name":"Alice","age":25,"email":"alice@example.com"}
```

**Does NOT match:**
```json
{"name": "Alice", "age": 25}  # Missing 'email'
{"name": "Alice", "age": 25, "email": "alice@example.com", "phone": "123"}  # Extra 'phone'
```

### Partial Mode

Allows request to contain additional fields not in the pattern:

**Pattern:**
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
{"name": "Alice", "email": "alice@example.com", "age": 25}
{"name": "Alice", "email": "alice@example.com", "age": 25, "phone": "123", "address": "..."}
```

**Does NOT match:**
```json
{"name": "Alice"}  # Missing 'email'
{"email": "alice@example.com"}  # Missing 'name'
```

### Strict Mode

Exact match required, including key order:

**Pattern:**
```python
"body": {
    "value": '{"name": "...", "age": 0}',
    "format": "json",
    "matching_mode": "strict"
}
```

**Matches:**
```json
{"name": "Alice", "age": 25}
```

**Does NOT match:**
```json
{"age": 25, "name": "Alice"}  # Different key order
{"name": "Alice", "age": 25, "email": "..."}  # Extra key
{"name":"Alice","age":25}  # Different whitespace (in strict mode)
```

### Nested Objects

Semantic matching works recursively for nested objects:

**Pattern:**
```python
"body": {
    "value": '''{
        "user": {
            "name": "...",
            "address": {
                "city": "...",
                "country": "..."
            }
        }
    }''',
    "format": "json",
    "matching_mode": "semantic"
}
```

**Matches:**
```json
{
    "user": {
        "name": "Alice",
        "address": {
            "city": "New York",
            "country": "USA"
        }
    }
}

{
    "user": {
        "address": {
            "country": "USA",
            "city": "New York"
        },
        "name": "Alice"
    }
}
```

**Does NOT match:**
```json
{
    "user": {
        "name": "Alice",
        "address": {
            "city": "New York"
        }
    }
}  # Missing 'country'
```

### Arrays

Arrays are matched by position and content:

**Pattern:**
```python
"body": {
    "value": '''{
        "items": [
            {"name": "...", "quantity": 0},
            {"name": "...", "quantity": 0}
        ]
    }''',
    "format": "json",
    "matching_mode": "semantic"
}
```

**Matches:**
```json
{
    "items": [
        {"name": "Item 1", "quantity": 2},
        {"name": "Item 2", "quantity": 5}
    ]
}

{
    "items": [
        {"quantity": 2, "name": "Item 1"},
        {"quantity": 5, "name": "Item 2"}
    ]
}
```

**Does NOT match:**
```json
{
    "items": [
        {"name": "Item 1", "quantity": 2}
    ]
}  # Wrong array length

{
    "items": [
        {"name": "Item 2", "quantity": 5},
        {"name": "Item 1", "quantity": 2}
    ]
}  # Different order (array position matters)
```

### Placeholder Values

Use any value in the pattern; MockServer checks structure but values are not validated against the pattern:

**Pattern:**
```python
"body": {
    "value": '{"name": "...", "age": 0, "active": true}',
    "format": "json",
    "matching_mode": "semantic"
}
```

The pattern above means:
- `"name"` must be present (value can be any string)
- `"age"` must be present (value can be any number)
- `"active"` must be present (value can be any boolean)

**Validation happens in validators, not matching:**
```python
def validate_user(body: str) -> None:
    data = json.loads(body)
    if data['age'] < 18:
        raise ValueError("Age must be 18 or older")
```

---

## XML Semantic Matching

### How It Works

MockServer parses both the expected pattern and actual request into XML trees, then compares:

1. **Structure**: Both must have the same elements and hierarchy
2. **Content**: Text content is compared for equality
3. **Order**: Element order doesn't matter in semantic mode
4. **Attributes**: Attributes are compared when present in pattern
5. **Whitespace**: Ignored

### Semantic Mode

**Pattern:**
```python
"body": {
    "value": '''<?xml version="1.0"?>
    <user>
        <name>...</name>
        <age>0</age>
        <email>...</email>
    </user>''',
    "format": "xml",
    "matching_mode": "semantic"
}
```

**Matches:**
```xml
<user>
    <name>Alice</name>
    <age>25</age>
    <email>alice@example.com</email>
</user>

<user><age>25</age><name>Alice</name><email>alice@example.com</email></user>

<user>
    <email>alice@example.com</email>
    <name>Alice</name>
    <age>25</age>
</user>
```

**Does NOT match:**
```xml
<user>
    <name>Alice</name>
    <age>25</age>
</user>  <!-- Missing 'email' -->

<user>
    <name>Alice</name>
    <age>25</age>
    <email>alice@example.com</email>
    <phone>123</phone>
</user>  <!-- Extra 'phone' in semantic mode -->
```

### Partial Mode

Allows request to contain additional elements:

**Pattern:**
```python
"body": {
    "value": '''<user>
        <name>...</name>
        <email>...</email>
    </user>''',
    "format": "xml",
    "matching_mode": "partial"
}
```

**Matches:**
```xml
<user>
    <name>Alice</name>
    <email>alice@example.com</email>
</user>

<user>
    <name>Alice</name>
    <email>alice@example.com</email>
    <age>25</age>
    <phone>123</phone>
    <address>...</address>
</user>
```

### Nested Elements

**Pattern:**
```python
"body": {
    "value": '''<?xml version="1.0"?>
    <order>
        <customer>
            <name>...</name>
            <email>...</email>
        </customer>
        <items>
            <item>
                <name>...</name>
                <quantity>0</quantity>
            </item>
        </items>
    </order>''',
    "format": "xml",
    "matching_mode": "semantic"
}
```

**Matches:**
```xml
<order>
    <customer>
        <name>Alice</name>
        <email>alice@example.com</email>
    </customer>
    <items>
        <item>
            <name>Product A</name>
            <quantity>2</quantity>
        </item>
    </items>
</order>

<order>
    <items>
        <item>
            <quantity>2</quantity>
            <name>Product A</name>
        </item>
    </items>
    <customer>
        <email>alice@example.com</email>
        <name>Alice</name>
    </customer>
</order>
```

### Multiple Elements with Same Name

XML allows multiple elements with the same name:

**Pattern:**
```python
"body": {
    "value": '''<items>
        <item>
            <name>...</name>
            <quantity>0</quantity>
        </item>
        <item>
            <name>...</name>
            <quantity>0</quantity>
        </item>
    </items>''',
    "format": "xml",
    "matching_mode": "semantic"
}
```

**Matches:**
```xml
<items>
    <item>
        <name>Item 1</name>
        <quantity>2</quantity>
    </item>
    <item>
        <name>Item 2</name>
        <quantity>5</quantity>
    </item>
</items>
```

**Note:** Order of `<item>` elements matters (like arrays in JSON).

### Attributes

Attributes in the pattern must be present in the request:

**Pattern:**
```python
"body": {
    "value": '''<user id="...">
        <name>...</name>
    </user>''',
    "format": "xml",
    "matching_mode": "semantic"
}
```

**Matches:**
```xml
<user id="123">
    <name>Alice</name>
</user>
```

**Does NOT match:**
```xml
<user>
    <name>Alice</name>
</user>  <!-- Missing 'id' attribute -->
```

### Namespaces

XML namespaces are supported:

**Pattern:**
```python
"body": {
    "value": '''<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <user>
                <name>...</name>
            </user>
        </soap:Body>
    </soap:Envelope>''',
    "format": "xml",
    "matching_mode": "semantic"
}
```

**Matches:**
```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <user>
            <name>Alice</name>
        </user>
    </soap:Body>
</soap:Envelope>
```

---

## Format Detection

MockServer auto-detects format based on `Content-Type` header:

| Content-Type | Detected Format |
|--------------|-----------------|
| `application/json` | JSON |
| `application/xml`, `text/xml` | XML |
| `text/plain` | Plain text |
| `application/octet-stream` | Binary |
| Others | Plain text (default) |

**You can override detection:**
```python
"body": {
    "value": '{"name": "Alice"}',
    "format": "json",  # Explicit format
    "matching_mode": "semantic"
}
```

---

## Troubleshooting Matching Issues

### Issue: Request doesn't match despite looking correct

**Possible causes:**

1. **Missing fields**
   - Solution: Use `partial` mode or add all fields to pattern

2. **Wrong data types**
   - Pattern: `"age": 0` expects number
   - Request: `"age": "25"` sends string
   - Solution: Ensure types match

3. **Extra fields in semantic mode**
   - Solution: Use `partial` mode to allow extra fields

4. **Nested object mismatch**
   - Solution: Check nested structure matches exactly

### Issue: JSON matching fails unexpectedly

**Debug steps:**

1. **Enable DEBUG logging:**
```bash
python main.py --config-dir config --endpoints-file endpoints.py --log-level DEBUG
```

2. **Check logs for parsing errors:**
```
[DEBUG] Body parsing error: Expecting property name enclosed in double quotes
```

3. **Validate JSON syntax:**
```bash
echo '{"name": "Alice"}' | python -m json.tool
```

4. **Test with minimal pattern:**
```python
"body": {
    "value": '{}',  # Matches any JSON object
    "format": "json",
    "matching_mode": "partial"
}
```

### Issue: XML matching fails

**Debug steps:**

1. **Check for XML declaration:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
```

2. **Validate XML syntax:**
```bash
xmllint --noout your_file.xml
```

3. **Check for namespace issues:**
- Ensure namespaces in pattern match request
- Use same namespace prefixes

4. **Test with minimal pattern:**
```python
"body": {
    "value": '<root></root>',
    "format": "xml",
    "matching_mode": "partial"
}
```

### Issue: Pattern matches too broadly

**Solutions:**

1. **Use validators for specific checks:**
```python
def validate_user(body: str) -> None:
    data = json.loads(body)
    if data['age'] < 18:
        raise ValueError("Age must be 18+")
    if '@' not in data['email']:
        raise ValueError("Invalid email")
```

2. **Switch to semantic mode from partial:**
```python
"matching_mode": "semantic"  # Requires exact fields
```

3. **Add more fields to pattern:**
```python
"value": '{"name": "...", "email": "...", "age": 0, "phone": "..."}'
```

---

## Common Patterns

### Flexible JSON API

```python
"body": {
    "value": '{"action": "..."}',
    "format": "json",
    "matching_mode": "partial",  # Allows any additional fields
    "validator": validate_action  # Validates 'action' value
}
```

### Strict Contract Enforcement

```python
"body": {
    "value": '{"id": "...", "name": "...", "status": "..."}',
    "format": "json",
    "matching_mode": "semantic",  # No extra fields allowed
    "validator": validate_contract
}
```

### XML SOAP Request

```python
"body": {
    "value": '''<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <CreateUser>
                <Name>...</Name>
                <Email>...</Email>
            </CreateUser>
        </soap:Body>
    </soap:Envelope>''',
    "format": "xml",
    "matching_mode": "semantic"
}
```

### Nested JSON with Arrays

```python
"body": {
    "value": '''{
        "order": {
            "customer": {"id": "...", "name": "..."},
            "items": [
                {"product_id": "...", "quantity": 0}
            ]
        }
    }''',
    "format": "json",
    "matching_mode": "semantic"
}
```

---

## Best Practices

### 1. Use Semantic Mode by Default

Semantic mode provides the right balance of flexibility and strictness:

```python
"matching_mode": "semantic"  # Recommended
```

### 2. Use Partial Mode for Extensible APIs

When clients may send additional fields you don't care about:

```python
"matching_mode": "partial"
```

### 3. Validate Business Rules in Validators

Don't rely on matching for validation:

```python
# Good
"body": {
    "value": '{"age": 0}',
    "matching_mode": "semantic",
    "validator": validate_age_range  # Checks 18 <= age <= 120
}

# Bad - matching can't validate ranges
"body": {
    "value": '{"age": 0}',  # Can't enforce age range here
    "matching_mode": "semantic"
}
```

### 4. Document Expected Structure

Add comments explaining the structure:

```python
"body": {
    # Expects: name (string), email (string), age (number)
    # Allows additional fields
    "value": '{"name": "...", "email": "...", "age": 0}',
    "format": "json",
    "matching_mode": "partial"
}
```

### 5. Test Edge Cases

Test with:
- Minimum required fields
- Maximum fields (semantic mode)
- Different field orders
- Different whitespace/formatting
- Nested structures
- Empty arrays/objects

### 6. Use Placeholders Consistently

Use consistent placeholders for expected types:

```python
# Strings
"name": "..."
"email": "..."

# Numbers
"age": 0
"price": 0.0

# Booleans
"active": true

# Objects
"address": {}

# Arrays
"items": []
```

---

## Comparison Table

| Feature | Semantic | Partial | Strict |
|---------|----------|---------|--------|
| Key/element order | Ignored | Ignored | Must match |
| Whitespace | Ignored | Ignored | Must match |
| Extra fields | Not allowed | Allowed | Not allowed |
| Missing fields | Not allowed | Not allowed | Not allowed |
| Type checking | Yes | Yes | Yes |
| Use case | Standard APIs | Flexible/extensible APIs | Legacy/strict contracts |

---

## Next Steps

- **[Request Configuration](03_Request_Configuration.md)** - Configure body matching in endpoints
- **[Validators and Processors](06_Validators_And_Processors.md)** - Add business logic validation
- **[Advanced Examples](07_Advanced_Examples.md)** - See semantic matching in action
- **[Troubleshooting](09_Troubleshooting.md)** - Debug matching issues
