# MockServer - cURL Examples Documentation

This folder contains cURL command documentation for testing the MockServer examples.

## Files in this Directory

### 1. `endpoints.curl.txt`
cURL examples for **basic MockServer features** defined in `config/endpoints.py`.

**Demonstrates:**
- Query parameter matching and template variables
- JSON body handling
- Path parameter extraction with regex
- File-based responses
- Round-robin response cycling
- Header validation
- Error responses (404, 500)

**Total Examples:** 8 basic endpoints + health check

---

### 2. `endpoints_advanced_examples.curl.txt`
cURL examples for **advanced MockServer features** defined in `config/endpoints_advanced_examples.py`.

**Demonstrates:**
- **XML Examples** (3): Semantic XML matching with validators and processors
  - User creation with email/age validation
  - Order updates with calculations
  - Payment processing with currency conversion
- **JSON Examples** (3): Semantic JSON matching with validators and processors
  - Product creation with SKU validation
  - Product search with partial matching
  - Checkout with tax calculations

**Total Examples:** 6 advanced endpoints + health check

---

## How to Use These Examples

### Step 1: Navigate to MockServer Directory

Navigate to the `mockserver/` directory from your project root:

```bash
# From your project root directory
cd mockserver
```

**Note:** If you're already in the mockserver directory, skip this step.

### Step 2: Activate Virtual Environment

**On Linux/macOS:**
```bash
# If you haven't created a virtual environment yet:
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

**On Windows:**
```cmd
# If you haven't created a virtual environment yet:
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

### Step 3: Install Dependencies (if not already installed)

```bash
pip install -r requirements.txt
```

### Step 4: Start the Server

#### For Basic Examples (endpoints.py):

```bash
python main.py --config-dir config --endpoints-file endpoints.py
```

Or with custom port:

```bash
python main.py --config-dir config --endpoints-file endpoints.py --port 9090
```

#### For Advanced Examples (endpoints_advanced_examples.py):

```bash
python main.py --config-dir config --endpoints-file endpoints_advanced_examples.py
```

Or with custom port:

```bash
python main.py --config-dir config --endpoints-file endpoints_advanced_examples.py --port 9090
```

#### With Debug Logging:

```bash
python main.py --config-dir config --endpoints-file endpoints.py --log-level DEBUG
```

### Step 5: Test with cURL Commands

Open the corresponding `.curl.txt` file and copy the commands you want to test.

**Example:**
```bash
# From endpoints.curl.txt
curl -X GET "http://localhost:9090/hello?name=Juan"
```

```bash
# From endpoints_advanced_examples.curl.txt
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

### Step 6: Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

---

## Quick Start Commands

### Basic Examples

**Linux/macOS:**
```bash
# 1. Navigate to mockserver directory from project root
cd mockserver

# 2. Activate venv
source venv/bin/activate

# 3. Start server
python main.py --config-dir config --endpoints-file endpoints.py

# 4. In another terminal, test with curl
curl -X GET "http://localhost:9090/hello?name=Test"
```

**Windows:**
```cmd
# 1. Navigate to mockserver directory from project root
cd mockserver

# 2. Activate venv
venv\Scripts\activate

# 3. Start server
python main.py --config-dir config --endpoints-file endpoints.py

# 4. In another terminal, test with curl
curl -X GET "http://localhost:9090/hello?name=Test"
```

### Advanced Examples

**Linux/macOS:**
```bash
# 1. Navigate to mockserver directory from project root
cd mockserver

# 2. Activate venv
source venv/bin/activate

# 3. Start server
python main.py --config-dir config --endpoints-file endpoints_advanced_examples.py

# 4. In another terminal, test with curl
curl -X POST http://localhost:9090/api/users/create \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<createUserRequest>
    <user>
        <firstName>Test</firstName>
        <lastName>User</lastName>
        <email>test@example.com</email>
        <age>30</age>
    </user>
    <metadata>
        <source>api</source>
    </metadata>
</createUserRequest>'
```

**Windows:**
```cmd
# 1. Navigate to mockserver directory from project root
cd mockserver

# 2. Activate venv
venv\Scripts\activate

# 3. Start server
python main.py --config-dir config --endpoints-file endpoints_advanced_examples.py

# 4. In another terminal, test with curl (PowerShell)
# Note: On Windows, use PowerShell or install curl separately
curl -X POST http://localhost:9090/api/users/create `
  -H "Content-Type: application/xml" `
  -d '<?xml version="1.0" encoding="UTF-8"?><createUserRequest><user><firstName>Test</firstName><lastName>User</lastName><email>test@example.com</email><age>30</age></user><metadata><source>api</source></metadata></createUserRequest>'
```

---

## Tips

### Pretty-print JSON responses with jq:
```bash
curl -s http://localhost:9090/hello?name=Juan | jq .
```

### View response headers:
```bash
curl -i http://localhost:9090/hello?name=Juan
```

### View verbose output (request/response details):
```bash
curl -v http://localhost:9090/hello?name=Juan
```

### Check server health:
```bash
curl http://localhost:9090/_health
```

---

## Configuration Files

These examples correspond to the following configuration files in the `config/` directory:

- **Basic Examples**: `config/endpoints.py`
- **Advanced Examples**: `config/endpoints_advanced_examples.py`
- **Request Templates**: `config/requests/`
- **Response Templates**: `config/responses/`

---

## Additional Resources

- **Postman Collections**: See `../sample_postman/` for Postman collection versions of these examples
- **Full Documentation**: See `config/EXAMPLES_README.md` for comprehensive documentation of all features
- **Main README**: See project root `README.md` for MockServer architecture and setup

---

## Troubleshooting

**Server won't start:**
- Check if port 9090 is already in use: `lsof -i :9090`
- Try a different port: `--port 9091`

**Connection refused:**
- Ensure the server is running
- Check the server logs for errors
- Verify you're using the correct port

**Invalid JSON/XML errors:**
- Ensure Content-Type header is set correctly
- Validate your JSON/XML syntax
- Check the request body matches the expected schema

**No matching mock found:**
- Verify the endpoint URL is correct
- Check that request headers match the mock definition
- Review server logs with `--log-level DEBUG`
