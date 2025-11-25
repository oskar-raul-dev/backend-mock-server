"""
Mock Server - Advanced Examples with Validators and Processors

This file demonstrates all advanced mockserver capabilities:
- XML semantic matching with validators and processors
- JSON semantic matching with validators and processors
- Custom data extraction and transformation
- Template variable usage with BODY_PROCESSED
- Different matching modes (semantic, partial)
- Business rule validation

Examples are organized by content type:
- XML Examples (1-3): User creation, order updates, payment processing
- JSON Examples (4-6): Product creation, search, checkout

Each example includes:
- Custom validator: Validates business rules on request body
- Custom processor: Extracts and transforms data for response templates
- Semantic matching: Format-aware body comparison
- Template variables: Dynamic response generation
"""
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import hashlib
import random


# ============================================================================
# XML EXAMPLE 1: Create User with Validator and Processor
# ============================================================================
# Request: POST /api/users/create
# Body: XML with user data (firstName, lastName, email, age)
# Demonstrates:
#   - XML semantic matching
#   - Email validation in validator
#   - Age-based segmentation in processor
#   - Generated user ID and timestamps

def validate_create_user(body: str) -> None:
    """
    Validator for create user request.

    Validates:
    - Email format is valid
    - Age is between 18 and 120
    - Required fields are present

    Raises ValueError if validation fails.
    """
    root = ET.fromstring(body)

    # Validate email
    email_elem = root.find('.//email')
    if email_elem is None or not email_elem.text:
        raise ValueError("Email is required")

    email = email_elem.text
    if '@' not in email or '.' not in email:
        raise ValueError(f"Invalid email format: {email}")

    # Validate age
    age_elem = root.find('.//age')
    if age_elem is None:
        raise ValueError("Age is required")

    try:
        age = int(age_elem.text)
        if age < 18 or age > 120:
            raise ValueError(f"Age must be between 18 and 120, got {age}")
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"Age must be a number: {age_elem.text}")
        raise


def process_create_user(body: str) -> dict:
    """
    Processor for create user request.

    Extracts user data and generates:
    - user_id: Generated from email hash
    - full_name: Combination of firstName and lastName
    - age_group: Categorization based on age
    - timestamp: Current datetime

    Returns dict for use in response template variables.
    """
    root = ET.fromstring(body)

    # Extract data
    first_name = root.find('.//firstName').text
    last_name = root.find('.//lastName').text
    email = root.find('.//email').text
    age = int(root.find('.//age').text)
    source = root.find('.//source').text if root.find('.//source') is not None else 'unknown'

    # Generate user ID from email hash
    user_id = hashlib.md5(email.encode()).hexdigest()[:8].upper()

    # Build full name
    full_name = f"{first_name} {last_name}"

    # Determine age group
    if age < 25:
        age_group = "young_adult"
    elif age < 40:
        age_group = "adult"
    elif age < 60:
        age_group = "middle_aged"
    else:
        age_group = "senior"

    # Generate timestamp
    timestamp = datetime.now().isoformat()

    return {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "full_name": full_name,
        "age_group": age_group,
        "source": source,
        "timestamp": timestamp
    }


# ============================================================================
# XML EXAMPLE 2: Update Order with Validator and Processor
# ============================================================================
# Request: POST /api/orders/update
# Body: XML with order data (orderId, status, items)
# Demonstrates:
#   - XML semantic matching
#   - Status validation
#   - Order total calculation
#   - Delivery date estimation

def validate_update_order(body: str) -> None:
    """
    Validator for update order request.

    Validates:
    - Valid order status
    - At least one item in order
    - Item prices are positive numbers

    Raises ValueError if validation fails.
    """
    root = ET.fromstring(body)

    # Validate status
    status_elem = root.find('.//status')
    if status_elem is None:
        raise ValueError("Order status is required")

    valid_statuses = ['pending', 'processing', 'completed', 'cancelled']
    status = status_elem.text
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

    # Validate items
    items = root.findall('.//item')
    if not items:
        raise ValueError("Order must have at least one item")

    # Validate item prices
    for item in items:
        price_elem = item.find('price')
        if price_elem is not None:
            try:
                price = float(price_elem.text)
                if price <= 0:
                    raise ValueError(f"Item price must be positive, got {price}")
            except ValueError as e:
                if "could not convert" in str(e):
                    raise ValueError(f"Item price must be a number: {price_elem.text}")
                raise


def process_update_order(body: str) -> dict:
    """
    Processor for update order request.

    Calculates:
    - total_items: Count of items
    - total_amount: Sum of (price * quantity) for all items
    - estimated_delivery: Based on current status

    Returns dict for use in response template variables.
    """
    root = ET.fromstring(body)

    # Extract order data
    order_id = root.find('.//orderId').text
    status = root.find('.//status').text

    # Calculate totals
    items = root.findall('.//item')
    total_items = len(items)
    total_amount = 0.0

    for item in items:
        quantity = int(item.find('quantity').text)
        price = float(item.find('price').text)
        total_amount += quantity * price

    # Estimate delivery date based on status
    now = datetime.now()
    if status == 'pending':
        delivery_date = now + timedelta(days=7)
    elif status == 'processing':
        delivery_date = now + timedelta(days=3)
    elif status == 'completed':
        delivery_date = now
    else:  # cancelled
        delivery_date = None

    estimated_delivery = delivery_date.strftime('%Y-%m-%d') if delivery_date else 'N/A'

    return {
        "order_id": order_id,
        "status": status,
        "total_items": total_items,
        "total_amount": f"{total_amount:.2f}",
        "estimated_delivery": estimated_delivery
    }


# ============================================================================
# XML EXAMPLE 3: Payment Notification with Currency Conversion
# ============================================================================
# Request: POST /api/payments/notify
# Body: XML with payment transaction data
# Demonstrates:
#   - XML semantic matching
#   - Currency validation
#   - Currency conversion calculations
#   - Transaction fee computation

def validate_payment_notification(body: str) -> None:
    """
    Validator for payment notification request.

    Validates:
    - Valid currency code
    - Amount is positive
    - Valid payment status
    - Transaction ID format

    Raises ValueError if validation fails.
    """
    root = ET.fromstring(body)

    # Validate currency
    currency_elem = root.find('.//currency')
    if currency_elem is None:
        raise ValueError("Currency is required")

    valid_currencies = ['USD', 'EUR', 'VES']
    currency = currency_elem.text
    if currency not in valid_currencies:
        raise ValueError(f"Invalid currency: {currency}. Must be one of {valid_currencies}")

    # Validate amount
    amount_elem = root.find('.//amount')
    if amount_elem is None:
        raise ValueError("Amount is required")

    try:
        amount = float(amount_elem.text)
        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")
    except ValueError as e:
        if "could not convert" in str(e):
            raise ValueError(f"Amount must be a number: {amount_elem.text}")
        raise

    # Validate status
    status_elem = root.find('.//status')
    if status_elem is None:
        raise ValueError("Payment status is required")

    valid_statuses = ['approved', 'rejected', 'pending']
    status = status_elem.text
    if status not in valid_statuses:
        raise ValueError(f"Invalid payment status: {status}. Must be one of {valid_statuses}")


def process_payment_notification(body: str) -> dict:
    """
    Processor for payment notification request.

    Calculates:
    - amount_in_ves: Converts amount to VES using exchange rates
    - conversion_rate: Exchange rate used
    - processing_fee: 2.5% of transaction amount
    - message: Status-based message

    Returns dict for use in response template variables.
    """
    root = ET.fromstring(body)

    # Extract payment data
    transaction_id = root.find('.//transactionId').text
    amount = float(root.find('.//amount').text)
    currency = root.find('.//currency').text
    status = root.find('.//status').text
    customer_id = root.find('.//customerId').text

    # Exchange rates (mock data)
    exchange_rates = {
        'USD': 36.50,  # 1 USD = 36.50 VES
        'EUR': 40.20,  # 1 EUR = 40.20 VES
        'VES': 1.00    # 1 VES = 1 VES
    }

    # Convert to VES
    conversion_rate = exchange_rates.get(currency, 1.0)
    amount_in_ves = amount * conversion_rate

    # Calculate processing fee (2.5%)
    processing_fee = amount * 0.025

    # Generate status message
    if status == 'approved':
        message = f"Payment of {currency} {amount:.2f} approved successfully"
    elif status == 'rejected':
        message = f"Payment of {currency} {amount:.2f} was rejected"
    else:
        message = f"Payment of {currency} {amount:.2f} is pending approval"

    # Generate timestamp
    timestamp = datetime.now().isoformat()

    return {
        "transaction_id": transaction_id,
        "status": status,
        "amount": f"{amount:.2f}",
        "currency": currency,
        "amount_in_ves": f"{amount_in_ves:.2f}",
        "conversion_rate": f"{conversion_rate:.2f}",
        "processing_fee": f"{processing_fee:.2f}",
        "customer_id": customer_id,
        "timestamp": timestamp,
        "message": message
    }


# ============================================================================
# JSON EXAMPLE 4: Create Product with Validator and Processor
# ============================================================================
# Request: POST /api/products/create
# Body: JSON with product data (name, sku, price, category, stock)
# Demonstrates:
#   - JSON semantic matching
#   - SKU format validation
#   - Price formatting
#   - Stock availability calculation

def validate_create_product(body: str) -> None:
    """
    Validator for create product request.

    Validates:
    - Price is positive
    - Stock is non-negative
    - SKU format is correct
    - Category is not empty

    Raises ValueError if validation fails.
    """
    data = json.loads(body)
    product = data.get('product', {})

    # Validate price
    try:
        price = float(product.get('price', 0))
        if price <= 0:
            raise ValueError(f"Price must be positive, got {price}")
    except (ValueError, TypeError) as e:
        if "could not convert" in str(e) or isinstance(e, TypeError):
            raise ValueError(f"Price must be a number: {product.get('price')}")
        raise

    # Validate stock
    try:
        stock = int(product.get('stock', 0))
        if stock < 0:
            raise ValueError(f"Stock cannot be negative, got {stock}")
    except (ValueError, TypeError) as e:
        if "invalid literal" in str(e) or isinstance(e, TypeError):
            raise ValueError(f"Stock must be a number: {product.get('stock')}")
        raise

    # Validate SKU format (must be 6-10 alphanumeric characters)
    sku = product.get('sku', '')
    if not sku or len(sku) < 6 or len(sku) > 10:
        raise ValueError(f"SKU must be 6-10 characters, got '{sku}'")

    if not sku.replace('-', '').replace('_', '').isalnum():
        raise ValueError(f"SKU must be alphanumeric: '{sku}'")

    # Validate category
    category = product.get('category', '').strip()
    if not category:
        raise ValueError("Category cannot be empty")


def process_create_product(body: str) -> dict:
    """
    Processor for create product request.

    Generates:
    - product_id: Random ID for the product
    - price_formatted: Formatted price with currency
    - in_stock: Boolean based on stock level
    - timestamp: Current datetime

    Returns dict for use in response template variables.
    """
    data = json.loads(body)
    product = data.get('product', {})
    metadata = data.get('metadata', {})

    # Extract product data
    name = product.get('name')
    sku = product.get('sku')
    price = float(product.get('price'))
    category = product.get('category')
    stock = int(product.get('stock'))

    # Generate product ID
    product_id = f"PRD-{random.randint(10000, 99999)}"

    # Format price
    price_formatted = f"${price:.2f} USD"

    # Determine stock availability
    in_stock = "true" if stock > 0 else "false"

    # Get timestamp
    timestamp = datetime.now().isoformat()

    return {
        "product_id": product_id,
        "name": name,
        "sku": sku,
        "price": price,
        "category": category,
        "stock": stock,
        "price_formatted": price_formatted,
        "in_stock": in_stock,
        "timestamp": timestamp
    }


# ============================================================================
# JSON EXAMPLE 5: Search Products with Partial Matching
# ============================================================================
# Request: POST /api/products/search
# Body: JSON with search filters and pagination
# Demonstrates:
#   - JSON partial matching (only checks specified filters)
#   - Pagination calculation
#   - Mock result generation
#   - Price range formatting

def validate_search_products(body: str) -> None:
    """
    Validator for search products request.

    Validates:
    - Price range is valid (min < max)
    - Pagination values are positive
    - Page and limit are reasonable

    Raises ValueError if validation fails.
    """
    data = json.loads(body)
    filters = data.get('filters', {})
    pagination = data.get('pagination', {})

    # Validate price range
    try:
        min_price = float(filters.get('minPrice', 0))
        max_price = float(filters.get('maxPrice', 0))

        if min_price < 0:
            raise ValueError(f"Minimum price cannot be negative: {min_price}")
        if max_price < 0:
            raise ValueError(f"Maximum price cannot be negative: {max_price}")
        if min_price > max_price:
            raise ValueError(f"Minimum price ({min_price}) cannot be greater than maximum price ({max_price})")
    except (ValueError, TypeError) as e:
        if "could not convert" in str(e) or isinstance(e, TypeError):
            raise ValueError("Price values must be numbers")
        raise

    # Validate pagination
    try:
        page = int(pagination.get('page', 1))
        limit = int(pagination.get('limit', 10))

        if page < 1:
            raise ValueError(f"Page must be at least 1, got {page}")
        if limit < 1 or limit > 100:
            raise ValueError(f"Limit must be between 1 and 100, got {limit}")
    except (ValueError, TypeError) as e:
        if "invalid literal" in str(e) or isinstance(e, TypeError):
            raise ValueError("Pagination values must be numbers")
        raise


def process_search_products(body: str) -> dict:
    """
    Processor for search products request.

    Generates:
    - price_range: Formatted price range string
    - total_results: Mock total results (based on category)
    - total_pages: Calculated from total_results and limit
    - mock_results: Sample product list JSON

    Returns dict for use in response template variables.
    """
    data = json.loads(body)
    filters = data.get('filters', {})
    pagination = data.get('pagination', {})

    # Extract filter data
    category = filters.get('category', 'all')
    min_price = float(filters.get('minPrice', 0))
    max_price = float(filters.get('maxPrice', 0))

    # Extract pagination data
    page = int(pagination.get('page', 1))
    limit = int(pagination.get('limit', 10))

    # Format price range
    price_range = f"${min_price:.2f} - ${max_price:.2f}"

    # Generate mock total results (varies by category)
    category_results = {
        'electronics': 156,
        'clothing': 243,
        'books': 89,
        'food': 312
    }
    total_results = category_results.get(category.lower(), 50)

    # Calculate total pages
    total_pages = (total_results + limit - 1) // limit  # Ceiling division

    # Generate mock results (3 sample products)
    mock_results = json.dumps([
        {
            "id": "PRD-12345",
            "name": f"Sample {category.title()} Product 1",
            "price": (min_price + max_price) / 2,
            "category": category
        },
        {
            "id": "PRD-12346",
            "name": f"Sample {category.title()} Product 2",
            "price": min_price + (max_price - min_price) * 0.3,
            "category": category
        },
        {
            "id": "PRD-12347",
            "name": f"Sample {category.title()} Product 3",
            "price": min_price + (max_price - min_price) * 0.7,
            "category": category
        }
    ])

    return {
        "category": category,
        "price_range": price_range,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_results": total_results,
        "mock_results": mock_results
    }


# ============================================================================
# JSON EXAMPLE 6: Checkout with Order Calculations
# ============================================================================
# Request: POST /api/checkout
# Body: JSON with cart items, customer data, and payment info
# Demonstrates:
#   - JSON semantic matching
#   - Complex order calculations
#   - Tax computation
#   - Payment method validation

def validate_checkout(body: str) -> None:
    """
    Validator for checkout request.

    Validates:
    - Cart has at least one item
    - All item quantities and prices are positive
    - Valid payment method
    - Valid email format

    Raises ValueError if validation fails.
    """
    data = json.loads(body)
    cart = data.get('cart', {})
    customer = data.get('customer', {})
    payment = data.get('payment', {})

    # Validate cart
    items = cart.get('items', [])
    if not items:
        raise ValueError("Cart must have at least one item")

    for idx, item in enumerate(items):
        # Validate quantity
        try:
            quantity = int(item.get('quantity', 0))
            if quantity <= 0:
                raise ValueError(f"Item {idx+1} quantity must be positive, got {quantity}")
        except (ValueError, TypeError) as e:
            if "invalid literal" in str(e) or isinstance(e, TypeError):
                raise ValueError(f"Item {idx+1} quantity must be a number")
            raise

        # Validate price
        try:
            price = float(item.get('price', 0))
            if price <= 0:
                raise ValueError(f"Item {idx+1} price must be positive, got {price}")
        except (ValueError, TypeError) as e:
            if "could not convert" in str(e) or isinstance(e, TypeError):
                raise ValueError(f"Item {idx+1} price must be a number")
            raise

    # Validate payment method
    valid_methods = ['credit_card', 'debit_card', 'bank_transfer', 'paypal']
    payment_method = payment.get('method', '')
    if payment_method not in valid_methods:
        raise ValueError(f"Invalid payment method: {payment_method}. Must be one of {valid_methods}")

    # Validate email
    email = customer.get('email', '')
    if '@' not in email or '.' not in email:
        raise ValueError(f"Invalid email format: {email}")


def process_checkout(body: str) -> dict:
    """
    Processor for checkout request.

    Calculates:
    - order_id: Generated order ID
    - total_items: Count of items in cart
    - subtotal: Sum of (price * quantity) for all items
    - tax: 16% tax on subtotal
    - total: Subtotal + tax
    - transaction_id: Generated transaction ID
    - estimated_delivery: Delivery date based on payment method

    Returns dict for use in response template variables.
    """
    data = json.loads(body)
    cart = data.get('cart', {})
    customer = data.get('customer', {})
    payment = data.get('payment', {})

    # Extract data
    items = cart.get('items', [])
    customer_id = customer.get('customerId')
    payment_method = payment.get('method')
    currency = payment.get('currency', 'USD')

    # Calculate totals
    total_items = sum(int(item.get('quantity', 0)) for item in items)
    subtotal = sum(int(item.get('quantity', 0)) * float(item.get('price', 0)) for item in items)

    # Calculate tax (16%)
    tax = subtotal * 0.16
    total = subtotal + tax

    # Generate order ID
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

    # Generate transaction ID
    transaction_id = f"TXN-{hashlib.md5(order_id.encode()).hexdigest()[:12].upper()}"

    # Payment status
    payment_status = "approved" if payment_method != "bank_transfer" else "pending"

    # Estimate delivery (faster for credit/debit card)
    delivery_days = 2 if payment_method in ['credit_card', 'debit_card'] else 5
    estimated_delivery = (datetime.now() + timedelta(days=delivery_days)).strftime('%Y-%m-%d')

    # Timestamp
    timestamp = datetime.now().isoformat()

    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "total_items": total_items,
        "subtotal": f"{subtotal:.2f}",
        "tax": f"{tax:.2f}",
        "total": f"{total:.2f}",
        "currency": currency,
        "payment_method": payment_method,
        "payment_status": payment_status,
        "transaction_id": transaction_id,
        "estimated_delivery": estimated_delivery,
        "timestamp": timestamp
    }


# ============================================================================
# ENDPOINT DEFINITIONS
# ============================================================================

definitions = [
    # ========================================================================
    # XML EXAMPLE 1: Create User
    # ========================================================================
    {
        "request": {
            "url": r"^/api/users/create$",
            "methods": ["POST"],
            "headers": [
                {"name": "Content-Type", "value": "application/xml"}
            ],
            "body": {
                "file": "create_user.xml",
                "format": "xml",
                "matching_mode": "semantic",
                "validator": validate_create_user,
                "processor": process_create_user
            }
        },
        "response": {
            "status": 201,
            "headers": {
                "Content-Type": "application/xml"
            },
            "body_file": "user_created.xml"
        }
    },

    # ========================================================================
    # XML EXAMPLE 2: Update Order
    # ========================================================================
    {
        "request": {
            "url": r"^/api/orders/update$",
            "methods": ["POST"],
            "headers": [
                {"name": "Content-Type", "value": "application/xml"}
            ],
            "body": {
                "file": "update_order.xml",
                "format": "xml",
                "matching_mode": "semantic",
                "validator": validate_update_order,
                "processor": process_update_order
            }
        },
        "response": {
            "status": 200,
            "headers": {
                "Content-Type": "application/xml"
            },
            "body_file": "order_updated.xml"
        }
    },

    # ========================================================================
    # XML EXAMPLE 3: Payment Notification
    # ========================================================================
    {
        "request": {
            "url": r"^/api/payments/notify$",
            "methods": ["POST"],
            "headers": [
                {"name": "Content-Type", "value": "application/xml"}
            ],
            "body": {
                "file": "payment_notification.xml",
                "format": "xml",
                "matching_mode": "semantic",
                "validator": validate_payment_notification,
                "processor": process_payment_notification
            }
        },
        "response": {
            "status": 200,
            "headers": {
                "Content-Type": "application/xml"
            },
            "body_file": "payment_processed.xml"
        }
    },

    # ========================================================================
    # JSON EXAMPLE 4: Create Product
    # ========================================================================
    {
        "request": {
            "url": r"^/api/products/create$",
            "methods": ["POST"],
            "headers": [
                {"name": "Content-Type", "value": "application/json"}
            ],
            "body": {
                "file": "create_product.json",
                "format": "json",
                "matching_mode": "semantic",
                "validator": validate_create_product,
                "processor": process_create_product
            }
        },
        "response": {
            "status": 201,
            "headers": {
                "Content-Type": "application/json"
            },
            "body_file": "product_created.json"
        }
    },

    # ========================================================================
    # JSON EXAMPLE 5: Search Products (Partial Matching)
    # ========================================================================
    {
        "request": {
            "url": r"^/api/products/search$",
            "methods": ["POST"],
            "headers": [
                {"name": "Content-Type", "value": "application/json"}
            ],
            "body": {
                "file": "search_products.json",
                "format": "json",
                "matching_mode": "partial",  # Only checks fields in expected body
                "validator": validate_search_products,
                "processor": process_search_products
            }
        },
        "response": {
            "status": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body_file": "search_results.json"
        }
    },

    # ========================================================================
    # JSON EXAMPLE 6: Checkout
    # ========================================================================
    {
        "request": {
            "url": r"^/api/checkout$",
            "methods": ["POST"],
            "headers": [
                {"name": "Content-Type", "value": "application/json"}
            ],
            "body": {
                "file": "checkout.json",
                "format": "json",
                "matching_mode": "semantic",
                "validator": validate_checkout,
                "processor": process_checkout
            }
        },
        "response": {
            "status": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body_file": "checkout_complete.json"
        }
    }
]
