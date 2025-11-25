#!/usr/bin/env python3
"""
Mock HTTP Server - Main Entry Point

A flexible, production-ready HTTP mock server with advanced features:

Features:
    - Semantic body matching (XML, JSON with configurable modes)
    - Jinja2 template support in responses
    - Auto-reload on configuration file changes
    - CORS support for web development
    - Regex-based URL, query parameter, and header matching
    - Round-robin response cycling for multiple responses per endpoint
    - Colored terminal logging
    - Health check endpoint (/_health)

Architecture:
    This main module orchestrates the complete server lifecycle:
    1. Parse CLI arguments
    2. Load configuration from file (optional)
    3. Merge configuration with precedence (CLI > file > defaults)
    4. Load and validate endpoint definitions
    5. Build MockDefinition objects with body matchers
    6. Create HTTP server with MockEngine
    7. Setup file watcher for auto-reload (optional)
    8. Start serving requests
    9. Handle graceful shutdown on Ctrl+C

Configuration Precedence:
    CLI arguments > config.py > defaults
    (See config.loader.merge_config() for details)

Usage Examples:

    Basic usage (defaults):
        $ python main.py
        # Uses config/ directory, port 9090, auto-reload enabled

    Custom port and directory:
        $ python main.py --port 8080 --config-dir my_config

    Debug mode with no auto-reload:
        $ python main.py --log-level DEBUG --no-reload

    Production mode:
        $ python main.py --log-level WARNING --no-reload --port 80

    Custom request/response directories:
        $ python main.py --requests-dir custom_requests --responses-dir custom_responses

    Full customization:
        $ python main.py \\
            --config-dir /etc/mockserver \\
            --port 443 \\
            --host 0.0.0.0 \\
            --log-level INFO \\
            --no-cors \\
            --no-reload

Directory Structure:
    config/                  # Default config directory
    ├── config.py           # Optional server configuration
    ├── endpoints.py        # Required endpoint definitions
    ├── requests/           # Request body files for matching
    │   ├── user_create.xml
    │   └── auth_request.json
    └── responses/          # Response body templates
        ├── user_response.json
        └── error.xml

Endpoint Definition Example (endpoints.py):
    definitions = [
        {
            "request": {
                "url": r"^/api/users$",
                "methods": ["POST"],
                "body": {
                    "format": "json",
                    "value": '{"name": ".*", "email": ".*"}'
                }
            },
            "response": {
                "status": 201,
                "headers": {"Content-Type": "application/json"},
                "body": '{{"id": "123", "name": "{{BODY_PROCESSED.name}}"}}'
            }
        }
    ]

Configuration File Example (config.py):
    CONFIG = {
        "server": {
            "port": 8000,
            "host": "127.0.0.1",
            "cors_enabled": True,
            "reload": True
        },
        "logging": {
            "level": "DEBUG"
        }
    }

Health Check:
    GET http://localhost:9090/_health
    Returns JSON with server status and uptime

Version: 1.0.0
"""
import os
import sys
import logging
from colorama import Fore, Style

from cli.args import parse_args, get_default_config
from log_setup.setup import setup_logging
from config.loader import load_config_file, load_endpoints, merge_config
from config.builder import build_mock_definitions
from server.lifecycle import create_server, setup_reload_watcher


# Version constant
VERSION = "1.0.0"


def main():
    """
    Main entry point for the mockserver application.

    This function orchestrates the complete server lifecycle from startup to
    shutdown. It handles configuration loading, endpoint validation, server
    creation, and graceful shutdown on Ctrl+C.

    Startup Sequence:
        1. Parse CLI arguments and validate port availability
        2. Setup logging with configured level
        3. Load optional config.py file
        4. Merge configuration (CLI > file > defaults)
        5. Load endpoints.py and validate structure
        6. Build MockDefinition objects with body matchers
        7. Create HTTP server with MockEngine
        8. Setup file watcher for auto-reload (if enabled)
        9. Print startup summary
        10. Start serving requests (blocks until Ctrl+C)

    Shutdown Sequence (on Ctrl+C):
        1. Stop file watcher (if enabled)
        2. Shutdown HTTP server
        3. Close server socket
        4. Exit cleanly with code 0

    Error Handling:
        The function catches and handles specific errors with appropriate exit codes:
        - FileNotFoundError: Config or endpoints file missing (exit 1)
        - ValueError: Invalid configuration or endpoints (exit 1)
        - OSError: Port already in use or network error (exit 1)
        - Exception: Unexpected errors with stack trace in DEBUG mode (exit 1)
        - KeyboardInterrupt: Graceful shutdown (exit 0)

    Logging:
        Startup and configuration details are logged at INFO level.
        Detailed logs (file watching, shutdown) are logged at DEBUG level.
        Errors are logged at ERROR level with colored output.

    Exit Codes:
        0: Normal shutdown (Ctrl+C)
        1: Error during startup or operation

    Example startup output:
        2024-01-15 10:30:00 [INFO] ============================================================
        2024-01-15 10:30:00 [INFO] Mock Server v1.0.0 starting...
        2024-01-15 10:30:00 [INFO] ============================================================
        2024-01-15 10:30:00 [INFO] Configuration directory: config
        2024-01-15 10:30:00 [INFO] Endpoints file: endpoints.py
        2024-01-15 10:30:00 [INFO] Loading endpoints from config/endpoints.py...
        2024-01-15 10:30:00 [INFO] Loaded 5 endpoint definitions
        2024-01-15 10:30:00 [INFO] Building mock definitions...
        2024-01-15 10:30:00 [INFO] Built 5 mock definitions
        2024-01-15 10:30:00 [INFO] Creating HTTP server on 0.0.0.0:9090...
        2024-01-15 10:30:00 [INFO] ============================================================
        2024-01-15 10:30:00 [INFO] Server Configuration:
        2024-01-15 10:30:00 [INFO]   Listening: http://0.0.0.0:9090
        2024-01-15 10:30:00 [INFO]   Mock definitions: 5
        2024-01-15 10:30:00 [INFO]   CORS: Enabled
        2024-01-15 10:30:00 [INFO]   Auto-reload: Enabled
        2024-01-15 10:30:00 [INFO]   Log level: INFO
        2024-01-15 10:30:00 [INFO] ============================================================
        2024-01-15 10:30:00 [INFO] Press Ctrl+C to stop

    Example error handling:
        # Missing endpoints file:
        2024-01-15 10:30:00 [ERROR] File not found: config/endpoints.py
        # Exit code 1

        # Port already in use:
        2024-01-15 10:30:00 [ERROR] Server error: [Errno 48] Address already in use
        # Exit code 1

        # Invalid configuration:
        2024-01-15 10:30:00 [ERROR] Configuration error: Invalid regex in definition #1
        # Exit code 1
    """
    # Parse command line arguments
    args = parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        # Log startup
        logger.info(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}Mock Server v{VERSION} starting...{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")

        # Load configuration file
        config_file_data = None
        config_file_path = os.path.join(args.config_dir, args.config_file) if args.config_file else None
        if config_file_path:
            config_file_data = load_config_file(config_file_path)

        # Merge configuration
        defaults = get_default_config()
        config = merge_config(args, config_file_data, defaults)

        # Extract config values
        host = config['server']['host']
        port = config['server']['port']
        cors_enabled = config['server']['cors_enabled']
        reload_enabled = config['server']['reload']

        # Build full paths for requests/responses directories relative to config_dir
        requests_dir = os.path.join(args.config_dir, config['paths']['requests_dir'])
        responses_dir = os.path.join(args.config_dir, config['paths']['responses_dir'])

        # Log configuration
        logger.info(f"Configuration directory: {args.config_dir}")
        logger.info(f"Endpoints file: {args.endpoints_file}")
        if args.config_file:
            logger.info(f"Config file: {args.config_file}")
        logger.info(f"Requests directory: {requests_dir}")
        logger.info(f"Responses directory: {responses_dir}")

        # Load endpoints definitions
        endpoints_file_path = os.path.join(args.config_dir, args.endpoints_file)
        logger.info(f"Loading endpoints from {endpoints_file_path}...")
        definitions_data = load_endpoints(endpoints_file_path)
        logger.info(f"Loaded {len(definitions_data)} endpoint definitions")

        # Build mock definitions
        logger.info("Building mock definitions...")
        definitions = build_mock_definitions(definitions_data, requests_dir, responses_dir)
        logger.info(f"Built {len(definitions)} mock definitions")

        # Create server
        logger.info(f"Creating HTTP server on {host}:{port}...")
        server = create_server(
            definitions=definitions,
            base_dir=requests_dir,
            host=host,
            port=port,
            cors_enabled=cors_enabled,
            cors_origins=config['server'].get('cors_origins', '*'),
            log_level=args.log_level,
            responses_dir=responses_dir
        )

        # Track reload status for health check
        server.reload_enabled = reload_enabled

        # Setup auto-reload if enabled
        observer = None
        if reload_enabled:
            def reload_callback():
                """Callback to reload definitions."""
                try:
                    # Reload endpoints
                    new_data = load_endpoints(endpoints_file_path)
                    # Rebuild definitions
                    new_defs = build_mock_definitions(new_data, requests_dir, responses_dir)
                    return new_defs
                except Exception as e:
                    logger.error(f"Failed to reload: {e}")
                    return None

            observer = setup_reload_watcher(
                server=server,
                endpoints_file=endpoints_file_path,
                config_file=config_file_path,
                requests_dir=requests_dir,
                responses_dir=responses_dir,
                reload_callback=reload_callback
            )

        # Print startup summary
        logger.info(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}Server Configuration:{Style.RESET_ALL}")
        logger.info(f"  Listening: http://{host}:{port}")
        logger.info(f"  Mock definitions: {len(definitions)}")
        logger.info(f"  CORS: {'Enabled' if cors_enabled else 'Disabled'}")
        logger.info(f"  Auto-reload: {'Enabled' if reload_enabled else 'Disabled'}")
        logger.info(f"  Log level: {args.log_level}")
        logger.info(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
        logger.info(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}")

        # Start serving
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info(f"\n{Fore.CYAN}Shutting down...{Style.RESET_ALL}")

            # Stop reload watcher if enabled
            if observer:
                logger.debug("Stopping file watcher...")
                observer.stop()
                observer.join(timeout=2)

            # Shutdown server
            logger.debug("Closing server...")
            server.shutdown()
            server.server_close()

            logger.info(f"{Fore.GREEN}Server stopped{Style.RESET_ALL}")
            sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"{Fore.RED}File not found: {e}{Style.RESET_ALL}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"{Fore.RED}Configuration error: {e}{Style.RESET_ALL}")
        sys.exit(1)
    except OSError as e:
        logger.error(f"{Fore.RED}Server error: {e}{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        logger.error(
            f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}",
            exc_info=logger.isEnabledFor(logging.DEBUG)
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
