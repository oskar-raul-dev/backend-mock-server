"""
Command-line argument parsing for the mockserver.

This module handles CLI argument parsing using Python's argparse module.
It defines all the command-line options for controlling mockserver behavior
and provides default configuration values.

Key Functions:
    - get_default_config(): Returns default configuration structure
    - parse_args(): Parses CLI arguments and validates port availability

The CLI arguments follow these design principles:
    - All arguments are optional with sensible defaults
    - Paths are relative to config-dir for portability
    - Mutually exclusive groups for boolean flags (--reload/--no-reload)
    - Port availability validation before server starts
    - Clear help text with examples

Configuration Priority:
    CLI arguments > config.py file > defaults from get_default_config()
    (Actual merging happens in config.loader.merge_config())

Supported Arguments:
    --config-dir: Directory containing config.py and endpoints.py
    --port: Server port number
    --host: Server host address
    --log-level: Logging verbosity
    --requests-dir: Request body files directory
    --responses-dir: Response body files directory
    --endpoints-file: Endpoints definition file
    --config-file: Server configuration file
    --reload / --no-reload: Auto-reload on file changes
    --cors / --no-cors: CORS headers enabled/disabled
"""
import argparse
from typing import Dict, Any

from server.utils import is_port_available


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration values for the mockserver.

    This function returns the baseline configuration used when no config file
    exists and no CLI arguments are provided. These defaults are merged with
    config file values and CLI args in config.loader.merge_config().

    Default Values:
        server.port: 9090
        server.host: 0.0.0.0 (all interfaces)
        server.cors_enabled: True
        server.reload: True (auto-reload enabled)
        logging.level: INFO
        paths.requests_dir: None (will be set to "requests" in merge_config)
        paths.responses_dir: None (will be set to "responses" in merge_config)

    Returns:
        Dictionary with four sections:
            - server: Server settings (port, host, CORS, reload)
            - logging: Log configuration (level, format, date format)
            - paths: Directory paths (requests_dir, responses_dir)
            - custom: Empty dict for user-defined config

    Example:
        >>> config = get_default_config()
        >>> config['server']['port']
        9090
        >>> config['logging']['level']
        'INFO'
        >>> config['paths']['requests_dir'] is None
        True
    """
    return {
        "server": {
            "port": 9090,
            "host": "0.0.0.0",
            "cors_enabled": True,
            "reload": True,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s [%(levelname)s] %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S"
        },
        "paths": {
            "requests_dir": None,
            "responses_dir": None,
        },
        "custom": {}
    }


def parse_args() -> argparse.Namespace:
    """
    Parse and validate command-line arguments for the mockserver.

    This function sets up an argparse parser with all CLI options, parses
    sys.argv, and performs validation (port availability check).

    All arguments are optional with sensible defaults. The function handles:
        - Setting up argument parser with help text
        - Defining all CLI options with proper types and choices
        - Creating mutually exclusive groups for boolean flags
        - Parsing arguments from command line
        - Validating port is available before returning

    Path Resolution:
        All paths (config-dir, requests-dir, responses-dir, endpoints-file,
        config-file) are relative to the current working directory. The
        requests/responses directories are further resolved relative to
        config-dir during config loading.

    Mutually Exclusive Groups:
        --reload / --no-reload: Control auto-reload behavior
        --cors / --no-cors: Control CORS header inclusion

    Returns:
        argparse.Namespace containing all parsed arguments:
            - config_dir (str): Config directory path
            - port (int): Server port
            - host (str): Server host address
            - log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            - requests_dir (str): Requests directory name
            - responses_dir (str): Responses directory name
            - endpoints_file (str): Endpoints file name
            - config_file (str): Config file name
            - reload (bool): Auto-reload enabled
            - cors (bool): CORS enabled

    Raises:
        SystemExit: If port is already in use or arguments are invalid.
                   argparse handles invalid arguments automatically.

    Example usage:
        >>> # python main.py
        >>> args = parse_args()
        >>> args.port
        9090
        >>> args.host
        '0.0.0.0'

    Example with arguments:
        >>> # python main.py --port 8080 --log-level DEBUG --no-reload
        >>> args = parse_args()  # Would parse those arguments
        >>> args.port
        8080
        >>> args.log_level
        'DEBUG'
        >>> args.reload
        False

    Example with port conflict:
        >>> # python main.py --port 80  # (port 80 already in use)
        >>> args = parse_args()  # Raises SystemExit with error message
        Traceback (most recent call last):
            ...
        SystemExit: 2
    """
    VERSION = "1.0.0"

    parser = argparse.ArgumentParser(
        description=f'Mock HTTP Server v{VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --port 8080 --log-level DEBUG
  %(prog)s --config-dir /path/to/config --no-reload
  %(prog)s --requests-dir custom_requests --responses-dir custom_responses
        """
    )

    parser.add_argument(
        '--config-dir',
        type=str,
        default='config',
        help='Directory containing config.py and endpoints.py (default: config)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=9090,
        help='Port to listen on (default: 9090)'
    )

    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host address to bind to (default: 0.0.0.0)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--requests-dir',
        type=str,
        default='requests',
        help='Directory for request body files, relative to config-dir (default: requests)'
    )

    parser.add_argument(
        '--responses-dir',
        type=str,
        default='responses',
        help='Directory for response body files, relative to config-dir (default: responses)'
    )

    parser.add_argument(
        '--endpoints-file',
        type=str,
        default='endpoints.py',
        help='Endpoints definition file, relative to config-dir (default: endpoints.py)'
    )

    parser.add_argument(
        '--config-file',
        type=str,
        default='config.py',
        help='Configuration file, relative to config-dir (default: config.py)'
    )

    reload_group = parser.add_mutually_exclusive_group()
    reload_group.add_argument(
        '--reload',
        action='store_true',
        default=True,
        dest='reload',
        help='Enable auto-reload on file changes (default)'
    )
    reload_group.add_argument(
        '--no-reload',
        action='store_false',
        dest='reload',
        help='Disable auto-reload'
    )

    cors_group = parser.add_mutually_exclusive_group()
    cors_group.add_argument(
        '--cors',
        action='store_true',
        default=True,
        dest='cors',
        help='Enable CORS headers (default)'
    )
    cors_group.add_argument(
        '--no-cors',
        action='store_false',
        dest='cors',
        help='Disable CORS headers'
    )

    args = parser.parse_args()

    # Validate port availability
    if not is_port_available(args.host, args.port):
        parser.error(f"Port {args.port} is already in use on {args.host}")

    return args
