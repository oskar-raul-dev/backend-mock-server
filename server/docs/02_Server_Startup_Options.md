# Server Startup Options

This guide covers all available options for starting and configuring the MockServer.

---

## Command-Line Interface (CLI)

### Basic Syntax

```bash
python main.py [OPTIONS]
```

### Required Options

| Option | Description | Example |
|--------|-------------|---------|
| `--config-dir` | Path to configuration directory | `--config-dir config` |
| `--endpoints-file` | Python file containing endpoint definitions | `--endpoints-file endpoints.py` |

### Optional Parameters

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `--port` | `-p` | Server port number | 9090 | `--port 8080` |
| `--host` | `-h` | Server host address | 0.0.0.0 | `--host 127.0.0.1` |
| `--log-level` | `-l` | Logging level | INFO | `--log-level DEBUG` |
| `--help` | | Show help message | | `--help` |

### Log Levels

Available log levels (from most to least verbose):

- **DEBUG**: Detailed debugging information, request/response details
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors that stop the server

---

## Starting the Server

### Basic Start (Example Configuration)

```bash
python main.py --config-dir config --endpoints-file endpoints.py
```

**Output:**
```
[INFO] Starting MockServer...
[INFO] Loaded 8 endpoint definitions
[INFO] Server running on http://0.0.0.0:9090
```

### Custom Port

```bash
python main.py --config-dir config --endpoints-file endpoints.py --port 8080
```

**When to use:**
- Port 9090 is already in use
- Running multiple MockServer instances
- Matching specific application configurations

### Custom Host

```bash
# Localhost only (not accessible from other machines)
python main.py --config-dir config --endpoints-file endpoints.py --host 127.0.0.1

# All interfaces (accessible from network)
python main.py --config-dir config --endpoints-file endpoints.py --host 0.0.0.0
```

**When to use:**
- `127.0.0.1`: Development on local machine only
- `0.0.0.0`: Testing from mobile devices or other computers on network

### Debug Logging

```bash
python main.py --config-dir config --endpoints-file endpoints.py --log-level DEBUG
```

**Output with DEBUG level:**
```
[DEBUG] Loading configuration from: config/config.py
[DEBUG] Loading endpoints from: config/endpoints.py
[DEBUG] Registered endpoint: GET /hello
[DEBUG] Registered endpoint: POST /api/users
[INFO] Loaded 2 endpoint definitions
[INFO] Server running on http://0.0.0.0:9090
[DEBUG] Incoming request: GET /hello?name=Test
[DEBUG] Matched endpoint: GET /hello
[DEBUG] Query params: {'name': 'Test'}
[DEBUG] Response status: 200
[DEBUG] Response body: {"message": "hello world Test"}
```

**When to use:**
- Troubleshooting matching issues
- Understanding request flow
- Debugging validators/processors
- Developing new endpoints

### Multiple Options Combined

```bash
python main.py \
  --config-dir /path/to/my-config \
  --endpoints-file my_endpoints.py \
  --port 8080 \
  --host 127.0.0.1 \
  --log-level DEBUG
```

---

## Configuration File (`config.py`)

The `config.py` file in your configuration directory contains server settings.

### Default Configuration

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

### Server Settings

#### `server.port`
- **Type**: Integer
- **Default**: 9090
- **Description**: Port number the server listens on
- **Example**:
```python
"port": 8080
```

#### `server.host`
- **Type**: String
- **Default**: "0.0.0.0"
- **Description**: Host address to bind to
- **Values**:
  - `"0.0.0.0"` - All network interfaces (accessible from network)
  - `"127.0.0.1"` - Localhost only
- **Example**:
```python
"host": "127.0.0.1"
```

#### `server.cors_enabled`
- **Type**: Boolean
- **Default**: true
- **Description**: Enable Cross-Origin Resource Sharing (CORS)
- **When to enable**: Frontend development with different origins
- **When to disable**: Backend-only testing, security requirements
- **Example**:
```python
"cors_enabled": False
```

#### `server.cors_origins`
- **Type**: String or List
- **Default**: "*" (all origins)
- **Description**: Allowed CORS origins
- **Examples**:
```python
# Allow all origins
"cors_origins": "*"

# Single origin
"cors_origins": "http://localhost:3000"

# Multiple origins
"cors_origins": ["http://localhost:3000", "http://localhost:3001"]
```

#### `server.reload`
- **Type**: Boolean
- **Default**: true
- **Description**: Auto-reload server when configuration files change
- **When to enable**: Active development
- **When to disable**: Production, performance testing
- **Example**:
```python
"reload": False
```

### Logging Settings

#### `logging.level`
- **Type**: String
- **Default**: "INFO"
- **Values**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Description**: Minimum log level to display
- **Example**:
```python
"level": "DEBUG"
```

### Path Settings

#### `paths.requests_dir`
- **Type**: String or None
- **Default**: None (uses `config/requests/`)
- **Description**: Custom directory for request body files
- **Example**:
```python
"requests_dir": "/path/to/custom/requests"
```

#### `paths.responses_dir`
- **Type**: String or None
- **Default**: None (uses `config/responses/`)
- **Description**: Custom directory for response template files
- **Example**:
```python
"responses_dir": "/path/to/custom/responses"
```

---

## Environment-Specific Configurations

### Development Configuration

**File: `config/config.dev.py`**
```python
CONFIG = {
    "server": {
        "port": 9090,
        "host": "0.0.0.0",
        "cors_enabled": True,
        "cors_origins": "*",
        "reload": True  # Auto-reload enabled
    },
    "logging": {
        "level": "DEBUG"  # Verbose logging
    }
}
```

**Start:**
```bash
python main.py --config-dir config --endpoints-file endpoints.py
# Manually copy config.dev.py to config.py or modify startup to use it
```

### Production Configuration

**File: `config/config.prod.py`**
```python
CONFIG = {
    "server": {
        "port": 9090,
        "host": "0.0.0.0",
        "cors_enabled": True,
        "cors_origins": ["https://myapp.com", "https://www.myapp.com"],
        "reload": False  # Auto-reload disabled
    },
    "logging": {
        "level": "WARNING"  # Minimal logging
    }
}
```

### Testing Configuration

**File: `config/config.test.py`**
```python
CONFIG = {
    "server": {
        "port": 9091,  # Different port
        "host": "127.0.0.1",  # Localhost only
        "cors_enabled": False,
        "reload": False
    },
    "logging": {
        "level": "ERROR"  # Errors only
    }
}
```

---

## Auto-Reload Configuration

When `reload: true` is enabled in `config.py`, the server automatically reloads when these files change:

- `config.py` - Server configuration
- `endpoints.py` (or your endpoints file) - Endpoint definitions
- Files in `requests/` directory - Request templates
- Files in `responses/` directory - Response templates

**Example:**
1. Start server:
```bash
python main.py --config-dir config --endpoints-file endpoints.py
```

2. Edit `config/endpoints.py` (add new endpoint)

3. Server detects change and reloads automatically:
```
[INFO] Configuration file changed, reloading...
[INFO] Loaded 9 endpoint definitions
[INFO] Server reloaded successfully
```

**Note:** Auto-reload watches the config directory. Changes outside this directory are not detected.

---

## Running Multiple Instances

You can run multiple MockServer instances simultaneously using different ports:

**Terminal 1: Instance for Frontend**
```bash
python main.py \
  --config-dir config/frontend \
  --endpoints-file api_endpoints.py \
  --port 9090
```

**Terminal 2: Instance for Mobile**
```bash
python main.py \
  --config-dir config/mobile \
  --endpoints-file mobile_endpoints.py \
  --port 9091
```

**Terminal 3: Instance for Testing**
```bash
python main.py \
  --config-dir config/test \
  --endpoints-file test_endpoints.py \
  --port 9092
```

---

## Docker Deployment

### Dockerfile Example

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 9090

# Start server
CMD ["python", "main.py", "--config-dir", "config", "--endpoints-file", "endpoints.py"]
```

### Build and Run

```bash
# Build image
docker build -t mockserver .

# Run container
docker run -p 9090:9090 mockserver

# Run with custom configuration
docker run -p 8080:8080 \
  -v $(pwd)/my-config:/app/config \
  mockserver \
  python main.py --config-dir config --endpoints-file my_endpoints.py --port 8080
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  mockserver:
    build: .
    ports:
      - "9090:9090"
    volumes:
      - ./config:/app/config
    command: python main.py --config-dir config --endpoints-file endpoints.py
    environment:
      - LOG_LEVEL=INFO
```

**Start:**
```bash
docker-compose up
```

---

## Health Check Endpoint

MockServer provides a built-in health check endpoint at `/_health`.

**Request:**
```bash
curl http://localhost:9090/_health
```

**Response:**
```json
{
    "status": "healthy",
    "uptime": 125.7,
    "definitions_loaded": 8,
    "config_dir": "/path/to/config"
}
```

**Fields:**
- `status`: Server status ("healthy")
- `uptime`: Seconds since server started
- `definitions_loaded`: Number of endpoint definitions loaded
- `config_dir`: Path to configuration directory

**Use cases:**
- Container orchestration health checks
- Monitoring and alerting
- Automated testing verification
- Load balancer health checks

---

## Troubleshooting Startup Issues

### Port Already in Use

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution 1: Use different port**
```bash
python main.py --config-dir config --endpoints-file endpoints.py --port 8080
```

**Solution 2: Find and kill process using port**

**Linux/macOS:**
```bash
# Find process
lsof -i :9090

# Kill process
lsof -ti:9090 | xargs kill -9
```

**Windows:**
```cmd
# Find process
netstat -ano | findstr :9090

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Configuration File Not Found

**Error:**
```
FileNotFoundError: config/config.py not found
```

**Solution:**
- Verify path to config directory is correct
- Ensure `config.py` exists in the directory
- Use absolute path if relative path fails:
```bash
python main.py --config-dir /full/path/to/config --endpoints-file endpoints.py
```

### Endpoints File Not Found

**Error:**
```
FileNotFoundError: config/endpoints.py not found
```

**Solution:**
- Verify endpoints file exists
- Check filename spelling
- Ensure file has `.py` extension

### Module Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'flask'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Permission Denied (Port < 1024)

**Error:**
```
PermissionError: [Errno 13] Permission denied
```

**Solution:**
Ports below 1024 require root/admin privileges. Use port >= 1024:
```bash
python main.py --config-dir config --endpoints-file endpoints.py --port 8080
```

---

## Performance Considerations

### Auto-Reload Impact

Auto-reload watches for file changes, which has minimal performance impact but can be disabled for production:

```python
# config.py
CONFIG = {
    "server": {
        "reload": False  # Disable in production
    }
}
```

### Logging Level

DEBUG logging has performance impact due to verbose output:

```python
# Development
"logging": {"level": "DEBUG"}

# Production
"logging": {"level": "WARNING"}
```

### CORS Configuration

Restrict CORS origins in production to improve security and reduce overhead:

```python
# Development: Allow all
"cors_origins": "*"

# Production: Specific origins only
"cors_origins": ["https://myapp.com"]
```

---

## Next Steps

- **[Request Configuration](03_Request_Configuration.md)** - Learn to define endpoint matchers and validators
- **[Response Templates](04_Response_Templates.md)** - Create dynamic responses
- **[Advanced Examples](07_Advanced_Examples.md)** - See real-world configurations
- **[Troubleshooting](09_Troubleshooting.md)** - Common issues and solutions
