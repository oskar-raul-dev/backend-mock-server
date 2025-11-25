"""
Configuration and endpoints loading logic for the mockserver.

This module handles loading and merging configuration from multiple sources:
    1. CLI arguments (highest priority)
    2. Config file (config.py)
    3. Default values (lowest priority)

Key Functions:
    - load_config_file(): Loads server configuration from config.py
    - load_endpoints(): Loads endpoint definitions from endpoints.py
    - merge_config(): Merges configuration from all sources with priority handling

Configuration Sources:
    - config.py: Optional Python file with CONFIG dict containing server, logging,
                 paths, and custom sections
    - endpoints.py: Required Python file with definitions list containing mock
                   endpoint specifications
    - CLI args: Command-line arguments that override config file values

The module uses Python's importlib.util to dynamically load .py files as modules,
extracting CONFIG dict or definitions list from them. This provides a flexible
Python-based configuration approach with validation.
"""
import os
import logging
import argparse
import importlib.util
from typing import Optional, Dict, Any, List
import copy

from .validator import validate_definition_structure


def load_config_file(config_path: str) -> Optional[Dict[str, Any]]:
    """
    Load server configuration from a Python configuration file.

    Dynamically loads a Python file (config.py) as a module and extracts the CONFIG
    dictionary from it. The config file is optional - if it doesn't exist, returns
    None and the system will use default values.

    Expected Config File Structure:
        CONFIG = {
            'server': {
                'port': 8000,
                'host': '0.0.0.0',
                'cors_enabled': True,
                'cors_origins': '*',
                'reload': True
            },
            'logging': {
                'level': 'INFO'
            },
            'paths': {
                'requests_dir': 'requests',
                'responses_dir': 'responses'
            },
            'custom': {
                # User-defined custom configuration
            }
        }

    Validation Performed:
        - CONFIG must exist in the module
        - CONFIG must be a dictionary
        - Known sections (server, logging, paths) must be dictionaries if present
        - Unknown keys trigger a warning but don't fail loading

    Args:
        config_path: Absolute or relative path to config.py file

    Returns:
        Dictionary with configuration sections (server, logging, paths, custom)
        None if the file doesn't exist (not an error condition)

    Raises:
        ValueError: If config file exists but has invalid structure:
                   - No CONFIG variable
                   - CONFIG is not a dict
                   - Known sections are not dicts

    Example:
        >>> config = load_config_file("config/config.py")
        >>> if config:
        ...     print(config['server']['port'])  # 8000
        ... else:
        ...     print("Using defaults")
    """
    logger = logging.getLogger()

    if not os.path.exists(config_path):
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return None

    try:
        # Load the config file as a module
        spec = importlib.util.spec_from_file_location("config", config_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load config from {config_path}")

        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)

        # Get CONFIG dict from module
        if not hasattr(config_module, 'CONFIG'):
            raise ValueError(f"Config file {config_path} must define a CONFIG dictionary")

        config = config_module.CONFIG

        if not isinstance(config, dict):
            raise ValueError(f"CONFIG in {config_path} must be a dictionary, got {type(config).__name__}")

        # Validate known keys
        known_keys = {'server', 'logging', 'paths', 'custom'}
        unknown_keys = set(config.keys()) - known_keys

        if unknown_keys:
            logger.warning(f"Unknown keys in config file: {', '.join(unknown_keys)}")

        # Validate structure of known sections
        if 'server' in config and not isinstance(config['server'], dict):
            raise ValueError("'server' section must be a dictionary")

        if 'logging' in config and not isinstance(config['logging'], dict):
            raise ValueError("'logging' section must be a dictionary")

        if 'paths' in config and not isinstance(config['paths'], dict):
            raise ValueError("'paths' section must be a dictionary")

        logger.info(f"Loaded configuration from {config_path}")
        return config

    except Exception as e:
        logger.error(f"Error loading config file {config_path}: {e}")
        raise


def load_endpoints(endpoints_path: str) -> List[Dict[str, Any]]:
    """
    Load mock endpoint definitions from a Python definitions file.

    Dynamically loads a Python file (endpoints.py) as a module and extracts the
    'definitions' list from it. Unlike config.py, the endpoints file is required
    and must exist.

    Each definition in the list specifies one mock endpoint with request matching
    criteria and response(s) to return.

    Expected Endpoints File Structure:
        definitions = [
            {
                "request": {
                    "url": r"^/api/users$",
                    "methods": ["GET"],
                    "headers": [...],
                    "queryparams": [...],
                    "body": ...  # Optional
                },
                "response": {  # Can be dict or list of dicts
                    "status": 200,
                    "headers": {...},
                    "body": "..." or "body_file": "..."
                }
            },
            # ... more definitions
        ]

    Validation Performed:
        - File must exist (raises FileNotFoundError if missing)
        - Module must have 'definitions' variable
        - definitions must be a list
        - definitions must not be empty
        - Each definition validated by validate_definition_structure()
          - Must be a dict
          - Must have 'request' and 'response' keys
          - request must have 'url' key
          - response must be dict or list of dicts

    Args:
        endpoints_path: Absolute or relative path to endpoints.py file

    Returns:
        List of endpoint definition dictionaries ready for build_mock_definitions()

    Raises:
        FileNotFoundError: If endpoints file doesn't exist
        ValueError: If endpoints file has invalid structure:
                   - No 'definitions' variable
                   - definitions is not a list
                   - definitions list is empty
                   - Any definition has invalid structure

    Example:
        >>> definitions = load_endpoints("config/endpoints.py")
        >>> len(definitions)  # 8
        >>> definitions[0]['request']['url']  # r"^/hello$"
    """
    logger = logging.getLogger()

    if not os.path.exists(endpoints_path):
        error_msg = f"Endpoints file not found: {endpoints_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        # Load the endpoints file as a module
        spec = importlib.util.spec_from_file_location("endpoints", endpoints_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load endpoints from {endpoints_path}")

        endpoints_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(endpoints_module)

        # Get definitions list from module
        if not hasattr(endpoints_module, 'definitions'):
            raise ValueError(f"Endpoints file {endpoints_path} must define a 'definitions' list")

        definitions = endpoints_module.definitions

        if not isinstance(definitions, list):
            raise ValueError(
                f"'definitions' in {endpoints_path} must be a list, got {type(definitions).__name__}"
            )

        if len(definitions) == 0:
            raise ValueError(f"'definitions' list in {endpoints_path} is empty")

        # Validate structure of each definition
        errors = []
        for idx, definition in enumerate(definitions, start=1):
            def_errors = validate_definition_structure(definition, idx)
            errors.extend(def_errors)

        if errors:
            error_msg = f"Failed to load endpoints from {endpoints_path}\n"
            error_msg += "\n".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Loaded {len(definitions)} endpoint definition(s) from {endpoints_path}")
        return definitions

    except (ValueError, FileNotFoundError):
        raise
    except Exception as e:
        error_msg = f"Error loading endpoints file {endpoints_path}: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e


def merge_config(
    cli_args: argparse.Namespace,
    config_file_data: Optional[Dict[str, Any]],
    defaults: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge configuration from multiple sources with priority handling.

    Combines configuration from three sources in order of priority (highest first):
        1. CLI arguments - Always override other sources
        2. Config file values - Override defaults
        3. Default values - Baseline configuration

    The merge is performed section by section (server, logging, paths, custom) with
    deep merging for nested dictionaries.

    Merge Strategy:
        - Start with deep copy of defaults
        - Update with config file sections (if present)
        - Override with CLI args (always applied)

    CLI Args Priority:
        These CLI args always override config file and defaults:
            - port, host (server section)
            - cors, reload (server section)
            - log_level (logging section)
            - requests_dir, responses_dir (paths section, with special logic)

    Special Handling for paths:
        - requests_dir and responses_dir use CLI value if:
          a) CLI value differs from default ("requests"/"responses"), OR
          b) Config file doesn't specify a value (None)
        - This allows config file to override the default paths

    Args:
        cli_args: Parsed argparse.Namespace with command-line arguments
                 Expected attributes: port, host, cors, reload, log_level,
                 requests_dir, responses_dir
        config_file_data: Dict from config.py with sections: server, logging,
                         paths, custom. Can be None if config file doesn't exist.
        defaults: Dict with default values for all sections

    Returns:
        Merged configuration dictionary with structure:
        {
            'server': {port, host, cors_enabled, reload, ...},
            'logging': {level, ...},
            'paths': {requests_dir, responses_dir, ...},
            'custom': {...}  # From config file only
        }

    Example:
        >>> defaults = {
        ...     'server': {'port': 8000, 'host': '0.0.0.0', 'cors_enabled': True},
        ...     'logging': {'level': 'INFO'},
        ...     'paths': {'requests_dir': None, 'responses_dir': None}
        ... }
        >>> config_file = {
        ...     'server': {'port': 9000},
        ...     'paths': {'requests_dir': 'custom/requests'}
        ... }
        >>> cli_args = argparse.Namespace(
        ...     port=8080,  # CLI wins
        ...     host='127.0.0.1',
        ...     cors=True,
        ...     reload=True,
        ...     log_level='DEBUG',
        ...     requests_dir='requests',  # Uses config_file value
        ...     responses_dir='responses'
        ... )
        >>> merged = merge_config(cli_args, config_file, defaults)
        >>> merged['server']['port']  # 8080 (CLI override)
        >>> merged['paths']['requests_dir']  # 'custom/requests' (from config file)
    """
    # Start with defaults
    merged = copy.deepcopy(defaults)

    # Merge config file data if provided
    if config_file_data:
        # Merge server section
        if 'server' in config_file_data:
            merged['server'].update(config_file_data['server'])

        # Merge logging section
        if 'logging' in config_file_data:
            merged['logging'].update(config_file_data['logging'])

        # Merge paths section
        if 'paths' in config_file_data:
            merged['paths'].update(config_file_data['paths'])

        # Merge custom section
        if 'custom' in config_file_data:
            merged['custom'] = config_file_data['custom']

    # Override with CLI args (these have highest priority)
    merged['server']['port'] = cli_args.port
    merged['server']['host'] = cli_args.host
    merged['server']['cors_enabled'] = cli_args.cors
    merged['server']['reload'] = cli_args.reload
    merged['logging']['level'] = cli_args.log_level

    # For paths, CLI args override if they differ from defaults
    if cli_args.requests_dir != 'requests' or merged['paths']['requests_dir'] is None:
        merged['paths']['requests_dir'] = cli_args.requests_dir

    if cli_args.responses_dir != 'responses' or merged['paths']['responses_dir'] is None:
        merged['paths']['responses_dir'] = cli_args.responses_dir

    return merged
