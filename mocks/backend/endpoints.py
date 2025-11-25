# Beliberi Backend - Mock Endpoint Definitions
# This file defines mock endpoints for the Beliberi e-commerce backend API
#
# API Namespaces:
#   /api/        - Mobile app authentication
#   /api_web/    - Web frontend API
#   /api_mobile/ - Mobile-specific features
#   /api_oscar/  - Oscar e-commerce API

definitions = [
    # ========================================================================
    # Health Check
    # ========================================================================
    {
        "request": {
            "url": r"^/health/?$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"status": "healthy", "service": "beliberi-backend-mock"}'
        }
    },

    # ========================================================================
    # API_WEB: Exchange Rate
    # ========================================================================
    # GET /api_web/exchange_rate/
    {
        "request": {
            "url": r"^/api_web/exchange_rate/?$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body_file": "exchange_rate_list.json"
        }
    },

    # ========================================================================
    # API_WEB: Locations
    # ========================================================================
    # GET /api_web/location/
    {
        "request": {
            "url": r"^/api_web/location/?$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body_file": "location_list.json"
        }
    },

    # ========================================================================
    # API_WEB: Categories
    # ========================================================================
    # GET /api_web/category/
    {
        "request": {
            "url": r"^/api_web/category/?$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body_file": "category_list.json"
        }
    },

    # ========================================================================
    # API_WEB: Products
    # ========================================================================
    # GET /api_web/product/
    {
        "request": {
            "url": r"^/api_web/product/?$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body_file": "product_list.json"
        }
    },

    # GET /api_web/product/{id}/
    {
        "request": {
            "url": r"^/api_web/product/(\d+)/?$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"id": {{ PATH_PARAMS[0] }}, "title": "Mock Product", "price": "10.00"}'
        }
    },

    # ========================================================================
    # API_WEB: Banners
    # ========================================================================
    # GET /api_web/banner/
    {
        "request": {
            "url": r"^/api_web/banner/?$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body_file": "banner_list.json"
        }
    },

    # ========================================================================
    # API_OSCAR: Page Content
    # ========================================================================
    # GET /api_oscar/page-content/main-carousel/
    {
        "request": {
            "url": r"^/api_oscar/page-content/main-carousel/?$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body_file": "main_carousel.json"
        }
    },

    # GET /api_oscar/page-content/main-banner/
    {
        "request": {
            "url": r"^/api_oscar/page-content/main-banner/?$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body_file": "main_banner.json"
        }
    },

    # ========================================================================
    # API_OSCAR: Partners
    # ========================================================================
    # GET /api_oscar/partners/
    {
        "request": {
            "url": r"^/api_oscar/partners/?$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body_file": "partners_list.json"
        }
    },

    # POST /api_oscar/partners/select/
    {
        "request": {
            "url": r"^/api_oscar/partners/select/?$",
            "methods": ["POST"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"success": true, "message": "Partner selected"}'
        }
    },

    # ========================================================================
    # API_OSCAR: Basket
    # ========================================================================
    # GET /api_oscar/basket/
    {
        "request": {
            "url": r"^/api_oscar/basket/?$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body_file": "basket.json"
        }
    },

    # POST /api_oscar/basket/add-multiple/
    {
        "request": {
            "url": r"^/api_oscar/basket/add-multiple/?$",
            "methods": ["POST"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"success": true, "message": "Products added to basket"}'
        }
    },

    # ========================================================================
    # API_OSCAR: Products
    # ========================================================================
    # GET /api_oscar/products/best-selling/
    {
        "request": {
            "url": r"^/api_oscar/products/best-selling/?$",
            "methods": ["GET"]
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body_file": "best_selling_products.json"
        }
    },

    # ========================================================================
    # Catch-all for unmatched API requests (for debugging)
    # ========================================================================
    {
        "request": {
            "url": r"^/api.*$",
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE"]
        },
        "response": {
            "status": 404,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Mock not implemented", "detail": "This endpoint has not been mocked yet"}'
        }
    }
]
