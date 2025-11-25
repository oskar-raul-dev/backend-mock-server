# MockServer - Postman Collections

This folder contains Postman collections for testing the MockServer examples with a graphical interface.

## Files in this Directory

### 1. `endpoints.postman.collection.json`
Postman collection for **basic MockServer features** defined in `config/endpoints.py`.

**Collection Contents:**
- 8 example requests demonstrating basic features
- 1 health check endpoint
- Test scripts for automated validation
- Detailed descriptions and expected responses

**Demonstrates:**
- Query parameter matching and template variables
- JSON body handling
- Path parameter extraction with regex
- File-based responses
- Round-robin response cycling
- Header validation
- Error responses (404, 500)

---

### 2. `endpoints_advanced_examples.postman.collection.json`
Postman collection for **advanced MockServer features** defined in `config/endpoints_advanced_examples.py`.

**Collection Contents:**
- 6 advanced example requests (3 XML, 3 JSON)
- 1 health check endpoint
- Test scripts validating response structure
- Comprehensive descriptions of validator/processor logic

**Demonstrates:**
- **XML Examples**:
  - User creation with email/age validation and ID generation
  - Order updates with item calculations and delivery estimation
  - Payment processing with currency conversion and fees
- **JSON Examples**:
  - Product creation with SKU validation and price formatting
  - Product search with partial matching and pagination
  - Checkout with complex tax calculations and order generation

---

## Prerequisites

### Install Postman

Download and install Postman from:
- **Desktop App**: https://www.postman.com/downloads/
- **Web Version**: https://web.postman.com/

---

## How to Use These Collections

### Step 1: Start the MockServer

#### Navigate to the mockserver directory:

Navigate to the `mockserver/` directory from your project root:

```bash
# From your project root directory
cd mockserver
```

**Note:** If you're already in the mockserver directory, skip this step.

#### Activate virtual environment:

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

#### Install dependencies (if needed):

```bash
pip install -r requirements.txt
```

#### Start the server:

**For Basic Examples:**
```bash
python main.py --config-dir config --endpoints-file endpoints.py
```

**For Advanced Examples:**
```bash
python main.py --config-dir config --endpoints-file endpoints_advanced_examples.py
```

**With custom port:**
```bash
python main.py --config-dir config --endpoints-file endpoints.py --port 9090
```

**With debug logging:**
```bash
python main.py --config-dir config --endpoints-file endpoints.py --log-level DEBUG
```

The server will start at `http://localhost:9090` (or your custom port).

---

### Step 2: Import Collection into Postman

#### Option A: Desktop App

1. Open Postman desktop app
2. Click **Import** button (top left)
3. Click **Upload Files**
4. Select the collection JSON file:
   - `endpoints.postman.collection.json` for basic examples
   - `endpoints_advanced_examples.postman.collection.json` for advanced examples
5. Click **Import**

#### Option B: Web Version

1. Go to https://web.postman.com/
2. Click **Import** button
3. Drag and drop the collection JSON file or click **Upload Files**
4. Select the collection JSON file
5. Click **Import**

#### Option C: Direct File Opening

1. Open Postman
2. Click **File** → **Import**
3. Navigate to this directory
4. Select the collection file
5. Click **Open**

---

### Step 3: Configure Collection Variables (Optional)

The collections use a `baseUrl` variable set to `http://localhost:9090`.

**To change the server URL:**

1. Click on the collection name
2. Go to **Variables** tab
3. Edit `baseUrl` value (e.g., `http://localhost:8080`)
4. Click **Save**

---

### Step 4: Run Requests

#### Run Individual Requests:

1. Expand the collection in the left sidebar
2. Click on any request (e.g., "Example 1: GET /hello with Query Parameter")
3. Review the request details (method, URL, headers, body)
4. Click **Send**
5. View the response in the bottom panel

#### Run Collection with Tests:

1. Click the three dots (...) next to the collection name
2. Select **Run collection**
3. Select which requests to run
4. Click **Run [Collection Name]**
5. View test results for each request

---

### Step 5: View Test Results

Each request includes automated tests that validate:
- Response status codes
- Response structure
- Required fields
- Data types
- Value formats

**After sending a request:**
- Check the **Test Results** tab
- Green checkmarks indicate passed tests
- Red X marks indicate failed tests

---

## Quick Start Guide

### For Basic Examples:

**Linux/macOS:**
```bash
# Terminal 1: Start the server
cd mockserver  # From your project root
source venv/bin/activate
python main.py --config-dir config --endpoints-file endpoints.py

# In Postman:
# 1. Import: endpoints.postman.collection.json
# 2. Select: "Example 1: GET /hello with Query Parameter"
# 3. Click: Send
# 4. View: Response and test results
```

**Windows:**
```cmd
# Terminal 1: Start the server
cd mockserver  # From your project root
venv\Scripts\activate
python main.py --config-dir config --endpoints-file endpoints.py

# In Postman:
# 1. Import: endpoints.postman.collection.json
# 2. Select: "Example 1: GET /hello with Query Parameter"
# 3. Click: Send
# 4. View: Response and test results
```

### For Advanced Examples:

**Linux/macOS:**
```bash
# Terminal 1: Start the server
cd mockserver  # From your project root
source venv/bin/activate
python main.py --config-dir config --endpoints-file endpoints_advanced_examples.py

# In Postman:
# 1. Import: endpoints_advanced_examples.postman.collection.json
# 2. Select: "XML Example 1: Create User with Validation"
# 3. Click: Send
# 4. View: Response and test results
```

**Windows:**
```cmd
# Terminal 1: Start the server
cd mockserver  # From your project root
venv\Scripts\activate
python main.py --config-dir config --endpoints-file endpoints_advanced_examples.py

# In Postman:
# 1. Import: endpoints_advanced_examples.postman.collection.json
# 2. Select: "XML Example 1: Create User with Validation"
# 3. Click: Send
# 4. View: Response and test results
```

---

## Collection Features

### Test Scripts

Each request includes JavaScript test scripts that automatically validate responses:

```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has required field", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('success');
});
```

### Request Descriptions

Each request includes:
- **Feature overview** - What the endpoint demonstrates
- **Validator logic** - What validations are performed
- **Processor logic** - How the response is generated
- **Expected response** - Sample response with all fields
- **Variations to try** - Suggested tests with different data

### Collection Variables

- `baseUrl`: Server base URL (default: `http://localhost:9090`)

To use in requests: `{{baseUrl}}/api/endpoint`

---

## Example Requests

### Basic Collection Highlights:

1. **GET /hello with Query Parameter**
   - Simple query parameter example
   - Template variable usage

2. **POST /hello with JSON Body**
   - JSON body handling
   - Request echo example

3. **GET /counter - Round-Robin**
   - Multiple responses that cycle
   - Stateful mock behavior

4. **GET /api/protected - Header Auth**
   - Header validation
   - Bearer token example

### Advanced Collection Highlights:

1. **POST /api/users/create (XML)**
   - Email format validation
   - Age range validation (18-120)
   - Auto-generated user ID
   - Age-based grouping

2. **POST /api/checkout (JSON)**
   - Cart validation
   - Subtotal calculation
   - Tax calculation (16%)
   - Order and transaction ID generation

---

## Testing Tips

### 1. Run All Tests
Use the Collection Runner to execute all requests and view a summary of test results.

### 2. Modify Request Data
Edit the request body to test:
- Valid variations (different ages, categories, etc.)
- Invalid data (wrong formats, missing fields)
- Boundary cases (minimum/maximum values)

### 3. Check Validation Errors
Try invalid requests to see validator error messages:
- Invalid email format
- Age out of range
- Negative prices
- Invalid status values

### 4. View Detailed Logs
In Postman Console (View → Show Postman Console):
- See full request/response data
- Debug script execution
- View console.log() output

---

## Configuration Files

These collections correspond to the following configuration files in the `config/` directory:

- **Basic Examples**: `config/endpoints.py`
- **Advanced Examples**: `config/endpoints_advanced_examples.py`
- **Request Templates**: `config/requests/*.xml` and `config/requests/*.json`
- **Response Templates**: `config/responses/*.xml` and `config/responses/*.json`

---

## Additional Resources

- **cURL Examples**: See `../sample_curls/` for command-line versions
- **Full Documentation**: See `config/EXAMPLES_README.md` for comprehensive feature documentation
- **Main README**: See project root `README.md` for MockServer architecture

---

## Troubleshooting

### Collection import fails:
- Ensure you're using Postman v7.0 or later
- Verify the JSON file is not corrupted
- Try importing via URL or copy-paste

### Requests fail with "Connection refused":
- Ensure the MockServer is running
- Check the server is using the correct port
- Verify `baseUrl` variable matches server address

### Tests fail unexpectedly:
- Check server logs for errors
- Verify the correct endpoints file is loaded
- Ensure request body matches expected schema
- Review validator logic in request descriptions

### XML response parsing issues:
- Install the Postman XML to JSON converter
- Use `xml2Json()` helper in test scripts
- Check response Content-Type header

### Server won't start:
- Check if port is already in use: `lsof -i :9090`
- Kill existing process: `lsof -ti:9090 | xargs kill -9`
- Try a different port: `--port 9091`

---

## Environment Setup

### For Team Collaboration:

1. **Export Environment:**
   - Create a Postman Environment with `baseUrl` variable
   - Share environment file with team

2. **Version Control:**
   - These collection files are already in git
   - Update collections and commit changes
   - Team members can re-import updated versions

3. **CI/CD Integration:**
   - Use Postman CLI (Newman) to run collections in pipelines
   - Generate test reports automatically
   - Validate mock server behavior in automated tests

```bash
# Install Newman
npm install -g newman

# Run collection
newman run endpoints.postman.collection.json

# With environment
newman run endpoints.postman.collection.json -e environment.json
```

---

## Support

For issues or questions:
- Check the main README for general setup
- Review server logs with `--log-level DEBUG`
- Consult Postman documentation: https://learning.postman.com/
