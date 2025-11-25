"""
Configuration and resolution logic for body matching.

This module handles the complex logic of resolving body matching configuration from
various sources with proper precedence rules. It supports:

1. Loading body content from files or inline values
2. Auto-detecting format from file extensions (.xml, .json, .yaml, .regex)
3. Resolving matching_mode with precedence:
   - Explicit matching_mode (highest)
   - Format implies semantic (if format specified)
   - File extension auto-detection
   - Default fallback (verbatim for dict, regex for string)
4. Validating consistency (e.g., can't use format with regex mode)
5. Returning a normalized BodyMatchingConfig

The configuration resolution ensures that users have maximum flexibility while
preventing invalid combinations and providing sensible defaults.

Key Functions:
    - load_file_content(): Load body from file
    - auto_detect_from_extension(): Infer format from file extension
    - resolve_body_matching_config(): Main resolution logic with precedence

Configuration Precedence (highest to lowest):
    1. Explicit matching_mode in body spec
    2. Format field (implies semantic matching)
    3. File extension auto-detection
    4. Type-based default (regex for string, verbatim for dict)
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union, Dict, Any, Callable


@dataclass
class BodyMatchingConfig:
    """
    Configuration container for body matching behavior.

    This dataclass encapsulates all the information needed to create a body matcher
    and perform body matching on incoming requests.

    Attributes:
        content: The body content to match against (from file or inline value)
        format: Optional format type ("xml", "json", "yaml", or None)
        matching_mode: Matching strategy ("regex", "verbatim", "semantic", "strict", "partial")
        validator: Optional custom validation function to call on request bodies
        processor: Optional custom processing function that returns dict for template variables

    The config is created by resolve_body_matching_config() and consumed by
    body_matching.factory.create_body_matcher().

    Example:
        >>> config = BodyMatchingConfig(
        ...     content='<user><name>Alice</name></user>',
        ...     format='xml',
        ...     matching_mode='semantic',
        ...     validator=None,
        ...     processor=None
        ... )
        >>> config.format
        'xml'
        >>> config.matching_mode
        'semantic'
    """

    content: str
    format: Optional[str]
    matching_mode: str
    validator: Optional[Callable]
    processor: Optional[Callable]


def load_file_content(file_path: str) -> str:
    """
    Load content from a file with UTF-8 encoding.

    This helper function reads file content for body matching. It's used when
    body specs reference external files via the 'file' field.

    Args:
        file_path: Absolute or relative path to the file to load

    Returns:
        Complete file content as string

    Raises:
        FileNotFoundError: If file doesn't exist at the specified path
        IOError: If file cannot be read (permissions, encoding errors, etc.)

    Example:
        >>> content = load_file_content('requests/user_create.xml')
        >>> '<user>' in content
        True

    Example with missing file:
        >>> load_file_content('/nonexistent/file.xml')
        Traceback (most recent call last):
            ...
        FileNotFoundError: File not found: /nonexistent/file.xml
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def auto_detect_from_extension(file_path: str) -> Tuple[Optional[str], str]:
    """
    Auto-detect format and matching mode from file extension.

    This function provides a convenient way to configure body matching without
    explicitly specifying format or matching_mode. Just use a file with the
    right extension and the system will infer the correct settings.

    Detection Rules:
        .xml, .json, .yaml, .yml → semantic matching with that format
        .regex, .re → regex matching with no format
        (any other) → verbatim matching with no format

    Args:
        file_path: Path to the file (can be absolute or relative)

    Returns:
        Tuple of (format, matching_mode):
            - format: "xml", "json", "yaml", or None
            - matching_mode: "semantic", "regex", or "verbatim"

    Example:
        >>> auto_detect_from_extension('request.xml')
        ('xml', 'semantic')
        >>> auto_detect_from_extension('pattern.regex')
        (None, 'regex')
        >>> auto_detect_from_extension('body.txt')
        (None, 'verbatim')
        >>> auto_detect_from_extension('data.json')
        ('json', 'semantic')

    Example with case insensitivity:
        >>> auto_detect_from_extension('REQUEST.XML')  # Uppercase handled
        ('xml', 'semantic')
    """
    ext = Path(file_path).suffix.lower()

    detection_map = {
        '.xml': ('xml', 'semantic'),
        '.json': ('json', 'semantic'),
        '.yaml': ('yaml', 'semantic'),
        '.yml': ('yaml', 'semantic'),
        '.regex': (None, 'regex'),
        '.re': (None, 'regex'),
    }

    return detection_map.get(ext, (None, 'verbatim'))


def resolve_body_matching_config(
    body_spec: Union[str, Dict[str, Any]],
    base_dir: Optional[str] = None
) -> BodyMatchingConfig:
    """
    Resolve body matching configuration with proper precedence and validation.

    This is the main configuration resolution function. It handles all the complexity
    of determining format, matching_mode, content source, and custom callbacks from
    various user input formats.

    Configuration Precedence (highest to lowest):
        1. Explicit matching_mode if specified in body spec
        2. Format field implies semantic matching
        3. File extension auto-detection
        4. Type-based default:
           - String body_spec → regex matching
           - Dict body_spec → verbatim matching

    Supported Body Spec Formats:
        1. String: Treated as regex pattern (legacy format)
           Example: r'"user_id":\s*\d+'

        2. Dict with 'value': Inline content
           Example: {"value": "<xml>...</xml>", "format": "xml"}

        3. Dict with 'file': External file content
           Example: {"file": "requests/create_user.xml"}

        4. With custom validator/processor:
           Example: {
               "value": '{"name": "Alice"}',
               "format": "json",
               "validator": my_validator_func,
               "processor": my_processor_func
           }

    Validation Rules:
        - Cannot specify both 'file' and 'value'
        - Must specify either 'file' or 'value' (for dict spec)
        - Cannot use format with matching_mode='regex'
        - Semantic/strict/partial modes require format to be specified
        - Format must be one of: xml, json, yaml
        - YAML not yet implemented

    Args:
        body_spec: Body specification as string (regex) or dict (structured config)
        base_dir: Optional base directory for resolving relative file paths.
                 If provided, file paths are resolved relative to this directory.

    Returns:
        BodyMatchingConfig with all fields resolved and validated

    Raises:
        ValueError: If configuration is invalid or inconsistent:
                   - Both file and value specified
                   - Neither file nor value specified
                   - Format incompatible with matching_mode
                   - Semantic mode without format
                   - Unsupported format
                   - YAML format (not implemented)

    Example (string regex):
        >>> config = resolve_body_matching_config(r'"id":\s*\d+')
        >>> config.matching_mode
        'regex'
        >>> config.format is None
        True

    Example (inline JSON with semantic matching):
        >>> body_spec = {
        ...     "value": '{"name": "Alice", "age": 30}',
        ...     "format": "json"
        ... }
        >>> config = resolve_body_matching_config(body_spec)
        >>> config.matching_mode
        'semantic'
        >>> config.format
        'json'

    Example (file with auto-detection):
        >>> body_spec = {"file": "requests/user.xml"}
        >>> config = resolve_body_matching_config(body_spec, base_dir="config")
        >>> config.format  # Auto-detected from .xml extension
        'xml'
        >>> config.matching_mode  # Implied by XML format
        'semantic'

    Example (explicit matching_mode overrides):
        >>> body_spec = {
        ...     "value": '{"name": "Alice"}',
        ...     "format": "json",
        ...     "matching_mode": "partial"  # Override default semantic
        ... }
        >>> config = resolve_body_matching_config(body_spec)
        >>> config.matching_mode
        'partial'

    Example (validation error):
        >>> body_spec = {"file": "a.txt", "value": "b"}  # Can't have both
        >>> resolve_body_matching_config(body_spec)
        Traceback (most recent call last):
            ...
        ValueError: Cannot specify both 'file' and 'value' in body spec
    """
    # Case 1: String (legacy) → Always regex
    if isinstance(body_spec, str):
        return BodyMatchingConfig(
            content=body_spec,
            format=None,
            matching_mode="regex",
            validator=None,
            processor=None
        )

    # Case 2: Dict
    if not isinstance(body_spec, dict):
        raise ValueError(f"Body spec must be string or dict, got {type(body_spec).__name__}")

    # Extract fields
    file_path = body_spec.get('file')
    value = body_spec.get('value')
    format_type = body_spec.get('format')
    matching_mode = body_spec.get('matching_mode')
    validator = body_spec.get('validator')
    processor = body_spec.get('processor')

    # Validation: file and value are mutually exclusive
    if file_path and value:
        raise ValueError("Cannot specify both 'file' and 'value' in body spec")

    if not file_path and not value:
        raise ValueError("Must specify either 'file' or 'value' in body spec")

    # Load content
    if file_path:
        # Resolve file path relative to base_dir if provided
        if base_dir:
            full_path = os.path.join(base_dir, file_path)
        else:
            full_path = file_path

        content = load_file_content(full_path)

        # Auto-detect format from extension if not specified
        if format_type is None and matching_mode is None:
            format_type, matching_mode = auto_detect_from_extension(file_path)
    else:
        content = value

    # Resolve matching_mode with precedence
    if matching_mode is None:
        if format_type is not None:
            # Format specified → Default to semantic matching
            matching_mode = "semantic"
        else:
            # No format, no matching_mode → Default to verbatim
            matching_mode = "verbatim"

    # Validate consistency
    if matching_mode == "regex" and format_type is not None:
        raise ValueError("Cannot use format with matching_mode='regex'")

    if matching_mode in ["semantic", "strict", "partial"] and format_type is None:
        raise ValueError(
            f"matching_mode='{matching_mode}' requires 'format' to be specified"
        )

    # Validate format is supported
    if format_type is not None and format_type not in ["xml", "json", "yaml"]:
        raise ValueError(
            f"Unsupported format: {format_type}. "
            f"Supported formats: xml, json, yaml"
        )

    # YAML not implemented yet
    if format_type == "yaml":
        raise ValueError("YAML format not yet implemented")

    return BodyMatchingConfig(
        content=content,
        format=format_type,
        matching_mode=matching_mode,
        validator=validator,
        processor=processor
    )
