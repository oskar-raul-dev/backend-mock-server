"""
Builder for creating MockDefinition objects from configuration dictionaries.

This module provides the build_mock_definitions function which transforms raw
configuration dictionaries (loaded from endpoints.py) into fully-validated
MockDefinition objects ready for use by the MockEngine.

The builder performs comprehensive validation:
    - URL regex pattern compilation
    - Query parameter and header regex validation
    - Body matching configuration resolution (legacy and new formats)
    - File existence checks for request/response body files
    - Error aggregation and reporting

Supports both legacy and new body matching systems:
    - Legacy: body as string pattern or body_file reference
    - New: body as dict with semantic matching configuration (XML, JSON, etc.)

All validation errors are collected and reported together to help users fix
multiple issues at once, rather than failing on the first error.
"""
import re
import os
import logging
from typing import List, Dict, Any

from core.models import RequestDef, ResponseDef, MockDefinition
from body_matching.config import resolve_body_matching_config
from body_matching.factory import create_body_matcher


def build_mock_definitions(
    definitions: List[Dict[str, Any]],
    requests_dir: str,
    responses_dir: str
) -> List[MockDefinition]:
    """
    Build and validate MockDefinition objects from raw configuration dictionaries.

    This function is the main entry point for transforming endpoint configuration
    (loaded from endpoints.py) into MockDefinition objects. It performs comprehensive
    validation and error collection to provide helpful feedback when configuration is invalid.

    Processing Steps for Each Definition:
        1. Extract and compile URL regex pattern
        2. Extract optional methods, queryparams, headers
        3. Validate all regex patterns (URL, queryparams, headers)
        4. Process body specification (legacy or new format)
        5. Validate file references exist
        6. Create RequestDef with all fields
        7. Process response(s) and create ResponseDef objects
        8. Create MockDefinition combining request and responses

    Body Matching Support:
        Legacy Format:
            - body: "regex pattern string" → Creates body_pattern
            - body_file: "filename.txt" → Legacy file-based matching

        New Semantic Format:
            - body: {"type": "json", "expected": {...}} → Creates body_matcher
            - Calls resolve_body_matching_config() and create_body_matcher()
            - Supports XML, JSON, verbatim, and regex matchers

    Validation Performed:
        - URL regex compilation
        - Query parameter name and value regex patterns
        - Header name and value regex patterns
        - Body pattern regex (if legacy string)
        - Request body file existence (if body_file specified)
        - Response body file existence (for each response with body_file)

    Error Handling:
        Errors are collected (not immediately raised) to report all issues at once:
        - regex_errors: Invalid regex patterns with context
        - missing_files: Referenced files that don't exist
        All errors are combined into a single ValueError with detailed messages.

    Args:
        definitions: List of endpoint definition dicts from endpoints.py
                    Each dict must have 'request' and 'response' keys
        requests_dir: Directory path for request body files (legacy body_file matching)
        responses_dir: Directory path for response body files

    Returns:
        List of MockDefinition objects, one per valid definition
        Order is preserved from input definitions list

    Raises:
        ValueError: If any validation fails (regex errors, missing files, etc.)
                   Error message includes all validation failures with context

    Example:
        >>> definitions = [
        ...     {
        ...         "request": {
        ...             "url": r"^/api/users$",
        ...             "methods": ["GET"],
        ...             "body": {"type": "json", "expected": {"name": ".*"}}
        ...         },
        ...         "response": {
        ...             "status": 200,
        ...             "headers": {"Content-Type": "application/json"},
        ...             "body": '{"users": []}'
        ...         }
        ...     }
        ... ]
        >>> mock_defs = build_mock_definitions(definitions, "config/requests", "config/responses")
        >>> len(mock_defs)  # 1
    """
    logger = logging.getLogger()

    mock_definitions = []
    regex_errors = []
    missing_files = []

    for idx, definition in enumerate(definitions, start=1):
        try:
            # Build RequestDef
            request_dict = definition['request']
            url_pattern = request_dict['url']

            # Compile URL regex
            try:
                url_regex = re.compile(url_pattern)
            except re.error as e:
                regex_errors.append(
                    f"Invalid regex in definition #{idx}:\n"
                    f"  URL pattern: {url_pattern}\n"
                    f"  Error: {e}"
                )
                continue

            # Extract optional request fields
            methods = request_dict.get('methods')
            queryparams = request_dict.get('queryparams', [])
            headers = request_dict.get('headers', [])

            # Body matching - support both legacy and new format
            body_spec = request_dict.get('body')
            body_file = request_dict.get('body_file')

            # Initialize body matching fields
            body_pattern = None
            body_matcher = None
            body_expected_value = None
            body_validator = None
            body_processor = None

            # Validate queryparams regex
            for qp_idx, qp in enumerate(queryparams):
                try:
                    re.compile(qp['name'])
                    if 'value' in qp:
                        re.compile(qp['value'])
                except re.error as e:
                    regex_errors.append(
                        f"Invalid regex in definition #{idx}, queryparam #{qp_idx + 1}:\n"
                        f"  Pattern: {qp}\n"
                        f"  Error: {e}"
                    )
                    continue

            # Validate headers regex
            for hdr_idx, hdr in enumerate(headers):
                try:
                    re.compile(hdr['name'])
                    if 'value' in hdr:
                        re.compile(hdr['value'])
                except re.error as e:
                    regex_errors.append(
                        f"Invalid regex in definition #{idx}, header #{hdr_idx + 1}:\n"
                        f"  Pattern: {hdr}\n"
                        f"  Error: {e}"
                    )
                    continue

            # Process body specification
            if body_spec is not None:
                # Check if new format (dict) or legacy format (string)
                if isinstance(body_spec, dict):
                    # New body matching system
                    try:
                        config = resolve_body_matching_config(body_spec, requests_dir)
                        body_matcher, body_expected_value, body_validator, body_processor = \
                            create_body_matcher(config)
                    except Exception as e:
                        regex_errors.append(
                            f"Invalid body specification in definition #{idx}:\n"
                            f"  Error: {e}"
                        )
                        continue
                else:
                    # Legacy string pattern - treat as regex
                    body_pattern = body_spec
                    # Validate regex
                    try:
                        re.compile(body_pattern)
                    except re.error as e:
                        regex_errors.append(
                            f"Invalid regex in definition #{idx}, body pattern:\n"
                            f"  Pattern: {body_pattern}\n"
                            f"  Error: {e}"
                        )
                        continue

            # Check request body_file exists (legacy support)
            if body_file:
                body_file_path = os.path.join(requests_dir, body_file)
                if not os.path.exists(body_file_path):
                    missing_files.append(
                        f"  Definition #{idx}: {body_file} (not found in {requests_dir})"
                    )

            # Create RequestDef
            request_def = RequestDef(
                url_pattern=url_pattern,
                url_regex=url_regex,
                methods=methods,
                queryparams=queryparams,
                headers=headers,
                # Legacy fields
                body_pattern=body_pattern,
                body_file=body_file,
                # New body matching fields
                body_matcher=body_matcher,
                body_expected_value=body_expected_value,
                body_validator=body_validator,
                body_processor=body_processor
            )

            # Build ResponseDef list
            response = definition['response']

            # Normalize response to list
            if isinstance(response, dict):
                response_list = [response]
            else:
                response_list = response

            response_defs = []
            for resp_idx, resp_dict in enumerate(response_list, start=1):
                status = resp_dict.get('status', 200)
                resp_headers = resp_dict.get('headers', {})
                resp_body = resp_dict.get('body')
                resp_body_file = resp_dict.get('body_file')

                # Check response body_file exists
                if resp_body_file:
                    resp_file_path = os.path.join(responses_dir, resp_body_file)
                    if not os.path.exists(resp_file_path):
                        missing_files.append(
                            f"  Definition #{idx}, response #{resp_idx}: {resp_body_file} "
                            f"(not found in {responses_dir})"
                        )

                response_def = ResponseDef(
                    status=status,
                    headers=resp_headers,
                    body=resp_body,
                    body_file=resp_body_file
                )
                response_defs.append(response_def)

            # Create MockDefinition
            mock_def = MockDefinition(
                request=request_def,
                responses=response_defs
            )
            mock_definitions.append(mock_def)

        except Exception as e:
            logger.error(f"Error building definition #{idx}: {e}")
            raise ValueError(f"Error building definition #{idx}: {e}") from e

    # Report all errors if any
    if regex_errors or missing_files:
        error_msg = "Configuration validation failed:\n\n"

        if regex_errors:
            error_msg += "\n\n".join(regex_errors)
            error_msg += "\n\n"

        if missing_files:
            error_msg += "Missing files referenced in definitions:\n"
            error_msg += "\n".join(missing_files)

        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Built {len(mock_definitions)} mock definition(s)")
    return mock_definitions
