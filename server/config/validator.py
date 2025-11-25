"""
Validation logic for endpoint definition structure.

This module provides structural validation for endpoint definitions loaded from
endpoints.py. It verifies that each definition has the required structure before
attempting to build MockDefinition objects.

The validation is structural only - it checks for required keys and correct types,
but does not validate regex patterns, file existence, or semantic correctness.
Those validations are performed later by config.builder.

Validation Rules:
    - Definition must be a dictionary
    - Must have 'request' and 'response' keys
    - request must be a dict with 'url' key
    - response must be a dict OR a list of dicts
    - If response is a list, it cannot be empty and all elements must be dicts

This early validation provides clear error messages to help users fix
configuration problems quickly.
"""
from typing import Any, List


def validate_definition_structure(definition: Any, index: int) -> List[str]:
    """
    Validate the structure of a single endpoint definition.

    This function performs structural validation on an endpoint definition dictionary
    before it's processed by the builder. It checks for required keys and correct types
    but does NOT validate:
        - Regex pattern syntax (done by config.builder)
        - File existence (done by config.builder)
        - Semantic correctness (done by config.builder)

    The validation ensures the definition has the minimal structure required for
    build_mock_definitions() to process it safely.

    Validation Checks:
        1. Definition must be a dictionary
        2. Must contain 'request' key with dict value
        3. Must contain 'response' key with dict or list value
        4. request dict must contain 'url' key
        5. If response is a list:
           - Cannot be empty
           - All elements must be dicts

    Args:
        definition: The endpoint definition to validate. Expected to be a dict
                   with 'request' and 'response' keys, but this function accepts
                   Any type to provide helpful error messages for invalid types.
        index: 1-based position in the definitions list, used for clear error
              messages (e.g., "Definition #3 is missing...")

    Returns:
        List of error message strings. Empty list means validation passed.
        Each error message is formatted for display with leading spaces for
        readability when joined with newlines.

    Example:
        >>> definition = {
        ...     "request": {
        ...         "url": r"^/api/test$",
        ...         "methods": ["GET"]
        ...     },
        ...     "response": {
        ...         "status": 200,
        ...         "body": "OK"
        ...     }
        ... }
        >>> errors = validate_definition_structure(definition, 1)
        >>> len(errors)  # 0 (valid definition)
        0

    Example with errors:
        >>> bad_definition = {
        ...     "request": "not a dict",  # Should be dict
        ...     "response": []  # Empty list not allowed
        ... }
        >>> errors = validate_definition_structure(bad_definition, 2)
        >>> len(errors) > 0
        True
        >>> "Definition #2" in errors[0]
        True
    """
    errors = []

    if not isinstance(definition, dict):
        errors.append(
            f"  Definition #{index} must be a dictionary, got {type(definition).__name__}"
        )
        return errors

    # Check for required keys
    if 'request' not in definition:
        errors.append(f"  Definition #{index} is missing required field 'request'")

    if 'response' not in definition:
        errors.append(f"  Definition #{index} is missing required field 'response'")

    # If request exists, validate it has 'url'
    if 'request' in definition:
        request = definition['request']
        if not isinstance(request, dict):
            errors.append(
                f"  Definition #{index}: 'request' must be a dictionary, got {type(request).__name__}"
            )
        elif 'url' not in request:
            errors.append(f"  Definition #{index}: 'request' is missing required field 'url'")

    # If response exists, validate it's a dict or list of dicts
    if 'response' in definition:
        response = definition['response']
        if isinstance(response, dict):
            # Single response - OK
            pass
        elif isinstance(response, list):
            # List of responses - validate each one is a dict
            if len(response) == 0:
                errors.append(f"  Definition #{index}: 'response' list cannot be empty")
            else:
                for resp_idx, resp in enumerate(response, start=1):
                    if not isinstance(resp, dict):
                        errors.append(
                            f"  Definition #{index}: response[{resp_idx}] must be a dictionary, "
                            f"got {type(resp).__name__}"
                        )
        else:
            errors.append(
                f"  Definition #{index}: 'response' must be a dict or list of dicts, "
                f"got {type(response).__name__}"
            )

    return errors
