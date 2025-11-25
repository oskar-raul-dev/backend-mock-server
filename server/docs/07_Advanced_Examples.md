# Advanced Examples

This guide provides comprehensive, real-world examples demonstrating all advanced MockServer capabilities including semantic body matching, custom validators, custom processors, and template variable usage.

## Overview

The `endpoints_examples.py` file contains 6 complete examples:

- **3 XML Examples**: User creation, order updates, payment processing
- **3 JSON Examples**: Product creation, product search, checkout flow

Each example demonstrates:
- ✅ Semantic body matching (XML or JSON format-aware comparison)
- ✅ Custom validator functions (business rule validation)
- ✅ Custom processor functions (data extraction and transformation)
- ✅ Template variables in responses using `BODY_PROCESSED`
- ✅ Different matching modes (`semantic`, `partial`)

## Running the Examples

### 1. Start the mockserver with the examples

```bash
# From the mockserver/ directory
python main.py --config-dir config --endpoints-file endpoints_examples.py
```

The server will start on `http://localhost:9090` with all 6 example endpoints configured.

### 2. Test the endpoints

Use the curl commands below to test each endpoint.

---

## XML Examples

### Example 1: Create User (POST /api/users/create)

**Features:**
- XML semantic matching
- Email format validation
- Age range validation (18-120)
- Auto-generated user ID from email hash
- Age-based grouping (young_adult, adult, middle_aged, senior)
- Full name composition

**Test Command:**
```bash
curl -X POST http://localhost:9090/api/users/create \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<createUserRequest>
    <user>
        <firstName>Juan</firstName>
        <lastName>Pérez</lastName>
        <email>juan.perez@example.com</email>
        <age>28</age>
    </user>
    <metadata>
        <source>web</source>
    </metadata>
</createUserRequest>'
```

**Expected Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<createUserResponse>
    <success>true</success>
    <user>
        <id>A1B2C3D4</id>
        <firstName>Juan</firstName>
        <lastName>Pérez</lastName>
        <email>juan.perez@example.com</email>
        <fullName>Juan Pérez</fullName>
        <ageGroup>adult</ageGroup>
        <createdAt>2024-11-23T22:30:00.123456</createdAt>
    </user>
    <metadata>
        <source>web</source>
        <processedBy>mockserver</processedBy>
    </metadata>
</createUserResponse>
```

**Processor Logic:**
- `user_id`: MD5 hash of email (first 8 chars uppercase)
- `full_name`: Combines firstName + lastName
- `age_group`: Categorizes based on age
  - < 25: young_adult
  - 25-39: adult
  - 40-59: middle_aged
  - 60+: senior

**Validator Rules:**
- Email must contain @ and .
- Age must be between 18 and 120
- All required fields must be present

**Test Invalid Request (age too young):**
```bash
curl -X POST http://localhost:9090/api/users/create \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<createUserRequest>
    <user>
        <firstName>Pedro</firstName>
        <lastName>García</lastName>
        <email>pedro@example.com</email>
        <age>15</age>
    </user>
    <metadata>
        <source>mobile</source>
    </metadata>
</createUserRequest>'
```

**Expected:** 400 Bad Request with validation error

---

### Example 2: Update Order (POST /api/orders/update)

**Features:**
- XML semantic matching
- Order status validation
- Item count and total calculation
- Delivery date estimation based on status

**Test Command:**
```bash
curl -X POST http://localhost:9090/api/orders/update \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<updateOrderRequest>
    <order>
        <orderId>12345</orderId>
        <status>processing</status>
        <items>
            <item>
                <productId>101</productId>
                <quantity>2</quantity>
                <price>25.50</price>
            </item>
            <item>
                <productId>102</productId>
                <quantity>1</quantity>
                <price>15.00</price>
            </item>
        </items>
    </order>
</updateOrderRequest>'
```

**Expected Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<updateOrderResponse>
    <success>true</success>
    <order>
        <orderId>12345</orderId>
        <status>processing</status>
        <totalItems>2</totalItems>
        <totalAmount>66.00</totalAmount>
        <estimatedDelivery>2024-11-26</estimatedDelivery>
    </order>
    <message>Order 12345 updated to processing</message>
</updateOrderResponse>
```

**Processor Logic:**
- `total_items`: Count of item elements
- `total_amount`: Sum of (quantity × price) for all items
- `estimated_delivery`: Based on status
  - pending: +7 days
  - processing: +3 days
  - completed: today
  - cancelled: N/A

**Validator Rules:**
- Status must be: pending, processing, completed, or cancelled
- Must have at least one item
- Item prices must be positive numbers

---

### Example 3: Payment Notification (POST /api/payments/notify)

**Features:**
- XML semantic matching
- Currency validation and conversion
- Processing fee calculation
- Multi-currency support (USD, EUR, VES)

**Test Command:**
```bash
curl -X POST http://localhost:9090/api/payments/notify \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<paymentNotification>
    <transaction>
        <transactionId>ABC123XYZ456</transactionId>
        <amount>100.00</amount>
        <currency>USD</currency>
        <status>approved</status>
        <customer>
            <customerId>7890</customerId>
            <email>customer@example.com</email>
        </customer>
    </transaction>
</paymentNotification>'
```

**Expected Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<paymentResponse>
    <success>true</success>
    <transaction>
        <transactionId>ABC123XYZ456</transactionId>
        <status>approved</status>
        <amount>100.00</amount>
        <currency>USD</currency>
        <amountInVES>3650.00</amountInVES>
        <conversionRate>36.50</conversionRate>
        <processingFee>2.50</processingFee>
        <customerId>7890</customerId>
        <processedAt>2024-11-23T22:30:00.123456</processedAt>
    </transaction>
    <message>Payment of USD 100.00 approved successfully</message>
</paymentResponse>
```

**Processor Logic:**
- `amount_in_ves`: Converts to VES using exchange rates
  - USD: 1 USD = 36.50 VES
  - EUR: 1 EUR = 40.20 VES
  - VES: 1 VES = 1.00 VES
- `processing_fee`: 2.5% of transaction amount
- `message`: Status-based message

**Validator Rules:**
- Currency must be: USD, EUR, or VES
- Amount must be positive
- Status must be: approved, rejected, or pending
- Transaction ID must match format

---

## JSON Examples

### Example 4: Create Product (POST /api/products/create)

**Features:**
- JSON semantic matching
- SKU format validation
- Price formatting
- Stock availability checking

**Test Command:**
```bash
curl -X POST http://localhost:9090/api/products/create \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
        "name": "Wireless Mouse",
        "sku": "WM2024XYZ",
        "price": "29.99",
        "category": "electronics",
        "stock": "150"
    },
    "metadata": {
        "source": "admin_panel",
        "timestamp": "2024-11-23T10:00:00Z"
    }
}'
```

**Expected Response:**
```json
{
    "success": true,
    "product": {
        "id": "PRD-45678",
        "name": "Wireless Mouse",
        "sku": "WM2024XYZ",
        "price": 29.99,
        "category": "electronics",
        "stock": 150,
        "priceFormatted": "$29.99 USD",
        "inStock": true,
        "createdAt": "2024-11-23T22:30:00.123456"
    },
    "message": "Product Wireless Mouse created successfully with SKU WM2024XYZ"
}
```

**Processor Logic:**
- `product_id`: Random ID (PRD-XXXXX format)
- `price_formatted`: Formats as "$XX.XX USD"
- `in_stock`: Boolean based on stock > 0
- `timestamp`: Current datetime ISO format

**Validator Rules:**
- Price must be positive
- Stock must be non-negative
- SKU must be 6-10 alphanumeric characters
- Category cannot be empty

**Test Invalid Request (negative stock):**
```bash
curl -X POST http://localhost:9090/api/products/create \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
        "name": "Test Product",
        "sku": "TEST123",
        "price": "10.00",
        "category": "test",
        "stock": "-5"
    },
    "metadata": {
        "source": "test"
    }
}'
```

**Expected:** 400 Bad Request with validation error

---

### Example 5: Search Products (POST /api/products/search)

**Features:**
- JSON **partial** matching (only validates specified filters)
- Price range validation
- Pagination calculation
- Mock result generation

**Test Command:**
```bash
curl -X POST http://localhost:9090/api/products/search \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
        "category": "electronics",
        "minPrice": "10.00",
        "maxPrice": "100.00"
    },
    "pagination": {
        "page": "1",
        "limit": "10"
    }
}'
```

**Expected Response:**
```json
{
    "success": true,
    "filters": {
        "category": "electronics",
        "priceRange": "$10.00 - $100.00"
    },
    "pagination": {
        "page": 1,
        "limit": 10,
        "totalPages": 16,
        "totalResults": 156
    },
    "results": [
        {
            "id": "PRD-12345",
            "name": "Sample Electronics Product 1",
            "price": 55.0,
            "category": "electronics"
        },
        {
            "id": "PRD-12346",
            "name": "Sample Electronics Product 2",
            "price": 37.0,
            "category": "electronics"
        },
        {
            "id": "PRD-12347",
            "name": "Sample Electronics Product 3",
            "price": 73.0,
            "category": "electronics"
        }
    ],
    "message": "Found 156 products in category electronics"
}
```

**Processor Logic:**
- `price_range`: Formatted as "$min - $max"
- `total_results`: Mock data based on category
  - electronics: 156 results
  - clothing: 243 results
  - books: 89 results
  - food: 312 results
  - other: 50 results
- `total_pages`: Calculated from total_results / limit (ceiling)
- `mock_results`: Generates 3 sample products with interpolated prices

**Validator Rules:**
- minPrice < maxPrice
- Both prices must be non-negative
- Page must be >= 1
- Limit must be between 1 and 100

**Partial Matching:**
This endpoint uses `"matching_mode": "partial"`, which means you can send additional fields not in the expected body, and they will be ignored. For example:

```bash
curl -X POST http://localhost:9090/api/products/search \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
        "category": "books",
        "minPrice": "5.00",
        "maxPrice": "50.00",
        "extraField": "ignored"
    },
    "pagination": {
        "page": "2",
        "limit": "20"
    },
    "anotherExtraField": "also ignored"
}'
```

This will still match because partial matching only validates the expected fields.

---

### Example 6: Checkout (POST /api/checkout)

**Features:**
- JSON semantic matching
- Complex order calculations (subtotal, tax, total)
- Payment method validation
- Order ID and transaction ID generation
- Delivery estimation based on payment method

**Test Command:**
```bash
curl -X POST http://localhost:9090/api/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cart": {
        "items": [
            {
                "productId": "101",
                "quantity": "2",
                "price": "25.50"
            },
            {
                "productId": "102",
                "quantity": "1",
                "price": "15.00"
            }
        ]
    },
    "customer": {
        "customerId": "7890",
        "email": "customer@example.com"
    },
    "payment": {
        "method": "credit_card",
        "currency": "USD"
    }
}'
```

**Expected Response:**
```json
{
    "success": true,
    "order": {
        "orderId": "ORD-20241123-4567",
        "customerId": "7890",
        "totalItems": 3,
        "subtotal": "66.00",
        "tax": "10.56",
        "total": "76.56",
        "currency": "USD",
        "paymentMethod": "credit_card",
        "estimatedDelivery": "2024-11-25",
        "createdAt": "2024-11-23T22:30:00.123456"
    },
    "payment": {
        "status": "approved",
        "transactionId": "TXN-A1B2C3D4E5F6"
    },
    "message": "Order ORD-20241123-4567 created successfully. Total: USD 76.56"
}
```

**Processor Logic:**
- `total_items`: Sum of quantities across all items
- `subtotal`: Sum of (quantity × price) for all items
- `tax`: 16% of subtotal
- `total`: subtotal + tax
- `order_id`: Format ORD-YYYYMMDD-XXXX
- `transaction_id`: MD5 hash of order_id (first 12 chars)
- `payment_status`:
  - approved for credit_card, debit_card, paypal
  - pending for bank_transfer
- `estimated_delivery`:
  - +2 days for credit_card, debit_card
  - +5 days for bank_transfer, paypal

**Validator Rules:**
- Cart must have at least one item
- All item quantities must be positive
- All item prices must be positive
- Payment method must be: credit_card, debit_card, bank_transfer, or paypal
- Email must be valid format

**Test with different payment method:**
```bash
curl -X POST http://localhost:9090/api/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cart": {
        "items": [
            {
                "productId": "201",
                "quantity": "5",
                "price": "12.00"
            }
        ]
    },
    "customer": {
        "customerId": "5555",
        "email": "test@example.com"
    },
    "payment": {
        "method": "bank_transfer",
        "currency": "EUR"
    }
}'
```

This will return `"paymentStatus": "pending"` and estimated delivery of +5 days.

---

## File Structure

```
config/
├── endpoints_advanced_examples.py  # All 6 example definitions with validators/processors
├── requests/                       # Request body files
│   ├── create_user.xml
│   ├── update_order.xml
│   ├── payment_notification.xml
│   ├── create_product.json
│   ├── search_products.json
│   └── checkout.json
└── responses/                      # Response template files
    ├── user_created.xml
    ├── order_updated.xml
    ├── payment_processed.xml
    ├── product_created.json
    ├── search_results.json
    └── checkout_complete.json
```

## Key Concepts Demonstrated

### 1. Semantic Matching
- **XML**: Compares XML structure semantically, ignoring whitespace and attribute order
- **JSON**: Compares JSON structure semantically, ignoring key order and whitespace

### 2. Matching Modes
- **semantic**: Full structural equality (used in 5 examples)
- **partial**: Expected body is subset of actual body (used in search example)

### 3. Validator Functions
Each validator receives the raw request body string and can:
- Parse it (XML or JSON)
- Validate business rules
- Raise `ValueError` with descriptive messages on validation failure

Validators run **before** processors, ensuring data is valid.

### 4. Processor Functions
Each processor receives the raw request body string and must:
- Parse it (XML or JSON)
- Extract relevant data
- Transform/calculate derived values
- Return a `dict` that becomes `BODY_PROCESSED` in templates

Processors run **after** validation, so data is guaranteed to be valid.

### 5. Template Variables
All response templates have access to:
- `PATH_PARAMS`: Regex capture groups from URL
- `QUERY_PARAMS`: Query string parameters
- `HEADERS`: Request headers (case-insensitive)
- `BODY`: Raw request body
- `BODY_PROCESSED`: Dict returned by processor function

## Testing Tips

### 1. View Server Logs
See detailed matching and processing logs:
```bash
python main.py --config-dir config --endpoints-file endpoints_examples.py --log-level DEBUG
```

### 2. Test Validation Errors
Try sending invalid data to trigger validators:
- Invalid email format
- Negative prices
- Out-of-range values
- Missing required fields

### 3. Test Partial Matching
For the search endpoint, add extra fields to see them ignored:
```bash
curl -X POST http://localhost:9090/api/products/search \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
        "category": "books",
        "minPrice": "10.00",
        "maxPrice": "50.00"
    },
    "pagination": {
        "page": "1",
        "limit": "10"
    },
    "thisFieldIsIgnored": "because partial matching",
    "soIsThis": {"nested": "data"}
}'
```

### 4. Pretty Print JSON Responses
Pipe curl output through jq:
```bash
curl -s http://localhost:9090/api/products/search \
  -H "Content-Type: application/json" \
  -d '{"filters": {"category": "electronics", "minPrice": "10.00", "maxPrice": "100.00"}, "pagination": {"page": "1", "limit": "10"}}' \
  | jq .
```

### 5. Test XML Formatting Flexibility
XML semantic matching ignores formatting, so these are equivalent:
```bash
# Compact
curl -X POST http://localhost:9090/api/users/create \
  -H "Content-Type: application/xml" \
  -d '<createUserRequest><user><firstName>Test</firstName><lastName>User</lastName><email>test@example.com</email><age>25</age></user><metadata><source>test</source></metadata></createUserRequest>'

# Pretty-printed (also works)
curl -X POST http://localhost:9090/api/users/create \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<createUserRequest>
  <user>
    <firstName>Test</firstName>
    <lastName>User</lastName>
    <email>test@example.com</email>
    <age>25</age>
  </user>
  <metadata>
    <source>test</source>
  </metadata>
</createUserRequest>'
```

## Advanced Usage

### Using Examples as Templates

You can copy any example and modify it for your own use:

1. Copy the validator/processor functions
2. Modify the validation logic for your business rules
3. Adjust the processor to extract your specific data
4. Update the request/response files
5. Add your modified definition to `definitions` list

### Combining with Other Features

These examples can be combined with:
- Multiple responses (round-robin cycling)
- Query parameter matching
- Header matching
- Path parameter extraction
- Different HTTP methods

Example combining features:
```python
{
    "request": {
        "url": r"^/api/users/([0-9]+)$",  # Path parameter for user ID
        "methods": ["PUT"],
        "headers": [
            {"name": "Authorization", "value": r"Bearer .+"}
        ],
        "queryparams": [
            {"name": "notify", "value": "(true|false)"}
        ],
        "body": {
            "file": "update_user.json",
            "format": "json",
            "matching_mode": "partial",
            "validator": validate_update_user,
            "processor": process_update_user
        }
    },
    "response": {
        "status": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"userId": "{{ PATH_PARAMS[0] }}", "updated": {{ BODY_PROCESSED.updated_fields }}, "notified": {{ QUERY_PARAMS.notify }}}'
    }
}
```

## Troubleshooting

### Validation Errors (400 Bad Request)
If you get a 400 error, check:
- Request body format matches expected format (XML vs JSON)
- All required fields are present
- Values meet validation criteria (e.g., positive numbers, valid emails)
- Content-Type header matches body format

### No Match Errors (404 Not Found)
If you get a 404 error with "No matching mock definition", check:
- URL path matches the regex exactly
- HTTP method is correct
- Required headers are present
- Request body matches the expected pattern (semantic matching)

### Template Errors (500 Internal Server Error)
If you get a 500 error, check:
- Template variables are referenced correctly (e.g., `{{ BODY_PROCESSED.field }}`)
- Processor function returns all fields used in template
- JSON syntax in response templates is valid

### Debug Mode
Run with DEBUG logging to see detailed matching information:
```bash
python main.py --config-dir config --endpoints-file endpoints_examples.py --log-level DEBUG
```

This will show:
- Which definitions are being checked
- Why matches succeed or fail
- Validation and processing details
- Template rendering information

## Summary

These examples demonstrate the full power of MockServer:
- XML and JSON semantic matching
- Custom validators for business rules
- Custom processors for data transformation
- Template variables for dynamic responses
- Partial matching for flexible APIs

## Next Steps

1. **Test all examples** using the curl commands above
2. **Modify examples** to fit your specific use cases
3. **Create new examples** using the patterns demonstrated
4. **Combine features** to create complex mock scenarios
5. **Share examples** with your team for consistent mocking

---

## Related Documentation

- **[Request Configuration](03_Request_Configuration.md)** - In-depth request matching and validation
- **[Response Templates](04_Response_Templates.md)** - Dynamic response generation
- **[Body Matching](05_Body_Matching.md)** - Semantic matching explained
- **[Validators and Processors](06_Validators_And_Processors.md)** - Detailed validator/processor patterns
- **[Troubleshooting](09_Troubleshooting.md)** - Debug common issues
- **[Documentation Index](00_Index.md)** - Full documentation overview
