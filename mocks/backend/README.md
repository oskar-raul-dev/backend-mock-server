# Backend Mocks

Mock definitions for the Beliberi e-commerce backend API.

## Source Repository

**GitLab**: `git@oskar.cahuenas.projects.gitlab:beliberi-app/backend.git`

## API Namespaces

The backend exposes four main API namespaces that should be mocked:

| Namespace | Purpose |
|-----------|---------|
| `/api/` | Mobile app authentication (auth/, auth-picker/, payment-gateway/) |
| `/api_web/` | Web frontend API (profile/, address/, product/, category/, order/, etc.) |
| `/api_mobile/` | Mobile-specific features (blocked_app_version/) |
| `/api_oscar/` | Oscar e-commerce API (basket/, products/, checkout/, partners/) |

## Directory Structure

```
mocks/backend/
├── config.py           # Server configuration (port, CORS, etc.)
├── endpoints.py        # Mock endpoint definitions
├── requests/           # Request body templates for matching
│   └── *.json|xml
└── responses/          # Response body templates
    └── *.json|xml
```

## Running the Mock Server

From the repository root:

```bash
# Linux/macOS
./start.sh backend

# Windows CMD
start.bat backend

# Windows PowerShell
.\start.ps1 backend

# Custom port
./start.sh backend 8080
```

Server will be available at `http://localhost:9090` (default port).

## Key Endpoints to Mock

### Authentication (`/api/`)
- `POST /api/auth/sign-in/` - User sign-in
- `POST /api/auth-picker/sign-in/` - Picker sign-in
- `GET /api/auth-picker/registration-status/` - Picker registration status

### Web API (`/api_web/`)
- `GET /api_web/profile/` - Get user profile
- `GET /api_web/address/` - List user addresses
- `POST /api_web/address/` - Create address
- `GET /api_web/product/` - List products
- `GET /api_web/category/` - List categories
- `GET /api_web/location/` - List retail locations
- `GET /api_web/exchange_rate/` - Get exchange rates
- `GET /api_web/order/` - List user orders
- `POST /api_web/order/` - Create order

### Oscar API (`/api_oscar/`)
- `GET /api_oscar/basket/` - Get current basket
- `POST /api_oscar/basket/add-multiple/` - Add multiple products
- `GET /api_oscar/products/` - List products (Oscar format)
- `GET /api_oscar/partners/` - List partners
- `POST /api_oscar/partners/select/` - Select partner
- `GET /api_oscar/page-content/main-carousel/` - Main carousel content

## Test Users (from backend fixtures)

| Role | Email | Password | Location |
|------|-------|----------|----------|
| Customer | customer1@beliberi.com | Beliberi.1234 | Valencia |
| Picker | picker1@beliberi.com | Beliberi.1234 | Valencia |
| Customer | customer2@beliberi.com | Beliberi.1234 | Bogotá |
| Customer | customer3@beliberi.com | Beliberi.1234 | Caldas |
| Customer | customer4@beliberi.com | Beliberi.1234 | Caracas |
