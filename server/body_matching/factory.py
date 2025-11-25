"""
Factory for creating body matchers based on configuration.

This module provides the factory function that instantiates the appropriate
BodyMatcher implementation based on a resolved BodyMatchingConfig.

The factory pattern allows the config module to remain decoupled from the specific
matcher implementations, while ensuring type safety and proper validation.

Factory Logic:
    1. Determine matcher type from matching_mode and format
    2. Instantiate appropriate BodyMatcher subclass
    3. Validate the expected body content using the matcher
    4. Validate custom validator/processor functions if provided
    5. Return complete tuple ready for use in RequestDef

The factory performs early validation to catch configuration errors during
server startup rather than at request-matching time.
"""
import re
import logging
from typing import Tuple, Optional, Callable

from .base import BodyMatcher
from .matchers import RegexBodyMatcher, VerbatimBodyMatcher, XMLBodyMatcher, JSONBodyMatcher
from .config import BodyMatchingConfig


def create_body_matcher(
    config: BodyMatchingConfig
) -> Tuple[BodyMatcher, str, Optional[Callable], Optional[Callable]]:
    """
    Create appropriate BodyMatcher instance based on configuration.

    This factory function is the bridge between configuration and matcher implementation.
    It takes a resolved BodyMatchingConfig and returns everything needed for body
    matching during request processing.

    Matcher Selection Logic:
        matching_mode == "regex":
            → RegexBodyMatcher(content)

        matching_mode == "verbatim":
            → RegexBodyMatcher(re.escape(content))  # Escaped for exact match

        matching_mode in ["semantic", "strict", "partial"]:
            format == "xml" → XMLBodyMatcher(matching_mode)
            format == "json" → JSONBodyMatcher(matching_mode)
            (else) → ValueError

    Validation Performed:
        - Matcher validates expected body content (e.g., JSON.parse on mock value)
        - Validator function checked for callability
        - Processor function checked for callability and dict return type
        - Warnings logged if validator/processor raise exceptions on mock value

    Args:
        config: Resolved body matching configuration from resolve_body_matching_config()

    Returns:
        Tuple of four elements:
            1. matcher: BodyMatcher instance configured for this matching mode
            2. expected_value: The content string to match against (from config.content)
            3. validator: Optional custom validation function (callable or None)
            4. processor: Optional custom processing function (callable or None)

        This tuple is stored in RequestDef and used during request matching.

    Raises:
        ValueError: If configuration is invalid:
                   - Unsupported matching_mode
                   - Format not supported for semantic matching
                   - Expected body content fails validation
                   - Validator is not callable
                   - Processor is not callable or doesn't return dict

    Example (regex matcher):
        >>> config = BodyMatchingConfig(
        ...     content=r'"user_id":\s*\d+',
        ...     format=None,
        ...     matching_mode="regex",
        ...     validator=None,
        ...     processor=None
        ... )
        >>> matcher, expected, validator, processor = create_body_matcher(config)
        >>> type(matcher).__name__
        'RegexBodyMatcher'
        >>> expected
        '"user_id":\\s*\\d+'

    Example (JSON semantic matcher):
        >>> config = BodyMatchingConfig(
        ...     content='{"name": "Alice", "age": 30}',
        ...     format="json",
        ...     matching_mode="semantic",
        ...     validator=None,
        ...     processor=None
        ... )
        >>> matcher, expected, validator, processor = create_body_matcher(config)
        >>> type(matcher).__name__
        'JSONBodyMatcher'
        >>> expected
        '{"name": "Alice", "age": 30}'

    Example (XML with custom processor):
        >>> def my_processor(body):
        ...     return {"processed": "data"}
        >>> config = BodyMatchingConfig(
        ...     content='<user><name>Bob</name></user>',
        ...     format="xml",
        ...     matching_mode="semantic",
        ...     validator=None,
        ...     processor=my_processor
        ... )
        >>> matcher, expected, validator, processor = create_body_matcher(config)
        >>> processor is my_processor
        True

    Example (invalid format):
        >>> config = BodyMatchingConfig(
        ...     content='data',
        ...     format="unsupported",
        ...     matching_mode="semantic",
        ...     validator=None,
        ...     processor=None
        ... )
        >>> create_body_matcher(config)
        Traceback (most recent call last):
            ...
        ValueError: Format 'unsupported' not supported for semantic matching
    """
    logger = logging.getLogger(__name__)

    content = config.content
    format_type = config.format
    matching_mode = config.matching_mode
    validator = config.validator
    processor = config.processor

    # Determine matcher type based on matching_mode and format
    if matching_mode == "regex":
        # Regex matching
        matcher = RegexBodyMatcher(content)
        expected_value = content  # For regex, pattern itself is the "expected value"

    elif matching_mode == "verbatim":
        # Exact string matching (we use regex with escaped content)
        matcher = RegexBodyMatcher(re.escape(content))
        expected_value = content

    elif matching_mode in ["semantic", "strict", "partial"]:
        # Format-specific semantic matching
        if format_type == "xml":
            matcher = XMLBodyMatcher(matching_mode)
        elif format_type == "json":
            matcher = JSONBodyMatcher(matching_mode)
        else:
            raise ValueError(
                f"Format '{format_type}' not supported for {matching_mode} matching"
            )

        expected_value = content

        # Validate the mock body value itself
        try:
            matcher.validate(content)
        except Exception as e:
            raise ValueError(f"Invalid body value in mock definition: {e}")

    else:
        raise ValueError(f"Unsupported matching_mode: {matching_mode}")

    # Validate validator function if provided
    if validator is not None:
        if not callable(validator):
            raise ValueError(f"Validator must be callable, got {type(validator).__name__}")

        # Try calling validator with the mock value to catch errors early
        try:
            validator(content)
        except Exception as e:
            logger.warning(f"Validator raised exception on mock value: {e}")

    # Validate processor function if provided
    if processor is not None:
        if not callable(processor):
            raise ValueError(f"Processor must be callable, got {type(processor).__name__}")

        # Try calling processor with the mock value to catch errors early
        try:
            result = processor(content)
            if not isinstance(result, dict):
                raise ValueError(f"Processor must return dict, got {type(result).__name__}")
        except ValueError:
            # Re-raise ValueError (from the dict check above)
            raise
        except Exception as e:
            logger.warning(f"Processor raised exception on mock value: {e}")

    return (matcher, expected_value, validator, processor)
