# Mocks Directory

This directory contains mock configurations for different microservices/backends.

## Structure

Each subdirectory represents a microservice that can be mocked:

```
mocks/
├── backend/          # Beliberi e-commerce backend API mocks
│   ├── config.py     # Server configuration
│   ├── endpoints.py  # Endpoint definitions
│   ├── requests/     # Request body templates
│   └── responses/    # Response body templates
└── <other-service>/  # Future microservice mocks
```

## Available Mocks

| Mock | Description | Repository |
|------|-------------|------------|
| `backend` | Beliberi e-commerce backend | `git@oskar.cahuenas.projects.gitlab:beliberi-app/backend.git` |

## Running a Mock

From the repository root:

```bash
# Linux/macOS
./start.sh <mock_name> [port]

# Windows CMD
start.bat <mock_name> [port]

# Windows PowerShell
.\start.ps1 <mock_name> [-Port <port>]
```

Example:
```bash
./start.sh backend 9090
```

## Creating a New Mock

1. Create a new directory under `mocks/`:
   ```bash
   mkdir -p mocks/my-service/requests mocks/my-service/responses
   ```

2. Copy the configuration template:
   ```bash
   cp server/config/config.py mocks/my-service/
   cp server/config/endpoints.py mocks/my-service/
   ```

3. Edit `endpoints.py` with your mock definitions

4. Add response files to `responses/` directory

5. Start the mock server:
   ```bash
   ./start.sh my-service
   ```
