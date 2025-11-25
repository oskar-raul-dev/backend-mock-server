# Mock Server Configuration for Beliberi Backend
# This file configures the mock server behavior

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
        "requests_dir": "requests",
        "responses_dir": "responses"
    }
}
