# MockServer

A flexible HTTP mock server with semantic body matching, custom validators, and dynamic response generation.

## Features

- **Semantic Matching**: Format-aware XML and JSON comparison (not just string matching)
- **Custom Validators**: Add business rule validation to requests
- **Custom Processors**: Extract and transform data from requests
- **Template Variables**: Dynamic response generation with Jinja2
- **Round-Robin Responses**: Cycle through multiple responses
- **Auto-Reload**: Automatically reload configuration on file changes
- **CORS Support**: Built-in CORS handling for frontend development
- **Multiple Matching Modes**: Semantic, partial, and strict matching

## Repository Structure

```
backend-mock-server/
├── server/                 # Mock server source code
│   ├── main.py            # Entry point
│   ├── config/            # Example configurations
│   ├── docs/              # Full documentation
│   └── tests/             # Test suite
├── mocks/                  # Mock definitions by microservice
│   └── backend/           # Beliberi backend API mocks
├── venv/                   # Virtual environment (created on setup)
├── requirements.txt        # Python dependencies
├── start.sh               # Linux/macOS startup script
├── start.bat              # Windows CMD startup script
└── start.ps1              # Windows PowerShell startup script
```

## Quick Setup

### Prerequisites

- Python 3.11 or higher

### Linux/macOS

```bash
# 1. Clone the repository and navigate to it
cd backend-mock-server

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 5. Start the server with backend mocks
./start.sh backend

# Server will start at http://localhost:9090
```

### Windows (CMD)

```cmd
REM 1. Navigate to repository
cd backend-mock-server

REM 2. Create virtual environment
python -m venv venv

REM 3. Activate virtual environment
venv\Scripts\activate

REM 4. Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

REM 5. Start the server with backend mocks
start.bat backend

REM Server will start at http://localhost:9090
```

### Windows (PowerShell)

```powershell
# 1. Navigate to repository
cd backend-mock-server

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 5. Start the server with backend mocks
.\start.ps1 backend

# Server will start at http://localhost:9090
```

## Quick Example

Once the server is running, test it with:

```bash
# Simple GET request with query parameter
curl "http://localhost:9090/hello?name=World"

# Expected response:
# {"message": "hello world World"}
```

## Server Startup Options

Using the startup scripts:

```bash
# Linux/macOS
./start.sh backend              # Start with default port (9090)
./start.sh backend 8080         # Start with custom port

# Windows CMD
start.bat backend
start.bat backend 8080

# Windows PowerShell
.\start.ps1 backend
.\start.ps1 backend -Port 8080
```

Or run directly from the server directory:

```bash
cd server

# Start with custom port
python main.py --config-dir ../mocks/backend --port 8080

# Start with debug logging
python main.py --config-dir ../mocks/backend --log-level DEBUG

# View all options
python main.py --help
```

## Creating Your Own Mocks

### Using the mocks/ Directory

Create a new directory under `mocks/` for each microservice:

```bash
# Create new mock configuration
mkdir -p mocks/my-service/requests mocks/my-service/responses

# Copy example configuration as template
cp server/config/config.py mocks/my-service/
cp server/config/endpoints.py mocks/my-service/
```

### Mock Directory Structure

Each mock directory should contain:

```
mocks/my-service/
├── config.py           # Server configuration (port, CORS, etc.)
├── endpoints.py        # Mock endpoint definitions
├── requests/           # Request body templates for matching
│   └── *.json|xml
└── responses/          # Response body templates
    └── *.json|xml
```

### Basic Mock Definition

```python
# mocks/my-service/endpoints.py
definitions = [
    {
        "request": {
            "url": r"^/api/hello$",
            "methods": ["GET"],
            "query_params": {
                "name": r".+"  # Matches any non-empty value
            }
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"greeting": "Hello {{ QUERY_PARAMS.name }}!"}'
        }
    }
]
```

## Example Configurations

The `server/config/` directory contains example configurations:

- **`endpoints.py`**: Basic examples demonstrating core features
  - Query parameters, path parameters, headers
  - JSON and XML responses
  - File-based responses
  - Round-robin responses
  - Error simulation (404, 500)

- **`endpoints_advanced_examples.py`**: Advanced examples with validators and processors
  - XML semantic matching with validation
  - JSON semantic matching with partial mode
  - Custom validators for business rules
  - Custom processors for data transformation
  - Complex response generation

Test the examples using the included curl commands or Postman collections in `server/docs/sample_curls/` and `server/docs/sample_postman/`.

## Documentation

Complete documentation is available in the `server/docs/` directory:

- **[Documentation Index](server/docs/00_Index.md)** - Start here for full documentation
- **[Quickstart Guide](server/docs/01_Quickstart_Guide.md)** - Step-by-step tutorial with complete examples
- **[Server Startup Options](server/docs/02_Server_Startup_Options.md)** - CLI options and configuration
- **[Request Configuration](server/docs/03_Request_Configuration.md)** - Request matching, validators, processors
- **[Response Templates](server/docs/04_Response_Templates.md)** - Response generation and templating
- **[Body Matching](server/docs/05_Body_Matching.md)** - Semantic XML/JSON matching
- **[Validators and Processors](server/docs/06_Validators_And_Processors.md)** - Custom validation and data processing
- **[Advanced Examples](server/docs/07_Advanced_Examples.md)** - Real-world examples with validators/processors
- **[Internals & Architecture](server/docs/08_Internals_Architecture.md)** - System architecture and design
- **[Troubleshooting](server/docs/09_Troubleshooting.md)** - Common issues and solutions

### Quick Links

- **Testing Examples**: [cURL Commands](server/docs/sample_curls/) | [Postman Collections](server/docs/sample_postman/)
- **Configuration Reference**: [server/config/README.md](server/config/README.md)

## Health Check

The server provides a built-in health check endpoint:

```bash
curl http://localhost:9090/_health

# Response:
# {
#   "status": "healthy",
#   "uptime": 42.5,
#   "definitions_loaded": 8,
#   "config_dir": "/path/to/config"
# }
```

## Running Tests

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Run all tests
cd server
pytest

# Run specific test file
pytest tests/core/test_matcher.py

# Run with verbose output
pytest -v

# Run by marker
pytest -m unit
pytest -m integration
```

## Use Cases

- **API Development**: Mock external APIs during development
- **Frontend Development**: Work without backend dependencies
- **Testing**: Create deterministic test scenarios
- **Demo/Proof of Concept**: Quickly prototype API behavior
- **Training**: Simulate complex API interactions
- **Integration Testing**: Test error scenarios and edge cases

## What Makes It Different

Unlike simple HTTP mocking tools, MockServer provides:

1. **Semantic Matching**: Understands XML and JSON structure, not just strings
2. **Business Logic**: Add validators to enforce rules (age ranges, email formats, etc.)
3. **Data Transformation**: Use processors to extract and transform request data
4. **Dynamic Responses**: Generate responses with data from the request
5. **Stateful Mocking**: Round-robin responses for simulating state changes

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please see the documentation for architecture details and extension points.

## Support

- **Documentation**: See `server/docs/` directory
- **Examples**: See `server/config/` directory
- **Issues**: Report bugs or request features via GitLab issues
