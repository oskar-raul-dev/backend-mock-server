"""
Request matching logic for the mockserver.

This module implements the RequestMatcher class which handles matching of incoming
HTTP requests against mock request definitions. It supports comprehensive matching
across all HTTP request components:

- URL path matching with regex and parameter extraction
- HTTP method filtering
- Query parameter matching with regex patterns
- Header matching with case-insensitive names
- Request body matching (both legacy and semantic)

The matcher returns a RequestContext containing all extracted values that can be
used as template variables in response generation.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any
from urllib.parse import urlparse

from .models import RequestDef, HTTPRequest, RequestContext
from server.utils import CaseInsensitiveDict


class RequestMatcher:
    """
    Matches incoming HTTP requests against mock request definitions.

    The RequestMatcher provides fine-grained matching capabilities for all components
    of an HTTP request. Each match method is independent and returns a boolean or
    extracted data. The main `match()` method orchestrates all matching steps and
    constructs a RequestContext with extracted values.

    Matching Components:
        - URL: Regex pattern matching with capture groups for path parameters
        - Method: HTTP method filtering (GET, POST, etc.)
        - Query params: Name and value matching with regex support
        - Headers: Case-insensitive header matching with regex
        - Body: Legacy pattern/file matching OR semantic matching (XML, JSON)

    Body Matching Systems:
        1. New Semantic System (preferred):
           - Uses BodyMatcher for format-aware matching (XML, JSON, etc.)
           - Supports validation and processing callbacks
           - Returns processed body data for template use

        2. Legacy System (backwards compatible):
           - Simple regex pattern matching (body_pattern)
           - Exact file content matching (body_file)

    Example:
        >>> matcher = RequestMatcher()
        >>> request_def = RequestDef(
        ...     url_pattern=r"^/api/users/(\d+)$",
        ...     url_regex=re.compile(r"^/api/users/(\d+)$"),
        ...     methods=["GET"],
        ...     headers=[{"name": "Authorization", "value": r"Bearer .+"}]
        ... )
        >>> http_request = HTTPRequest(
        ...     method="GET",
        ...     url="/api/users/123",
        ...     headers={"Authorization": "Bearer token123"},
        ...     query_params={},
        ...     body=""
        ... )
        >>> context = matcher.match(request_def, http_request, "config/")
        >>> print(context.PATH_PARAMS)  # ["123"]
    """

    def match_url(self, url_regex: re.Pattern, actual_url: str) -> Optional[List[str]]:
        """
        Match URL path against regex pattern.

        Args:
            url_regex: Compiled regex pattern for URL matching
            actual_url: Full HTTP URL to match

        Returns:
            List of captured groups from regex, or None if no match
        """
        parsed_url = urlparse(actual_url)
        path = parsed_url.path

        match = url_regex.match(path)
        if not match:
            return None

        return list(match.groups())

    def match_method(self, allowed_methods: Optional[List[str]], actual_method: str) -> bool:
        """
        Match HTTP method against allowed methods.

        Args:
            allowed_methods: List of allowed methods (e.g., ["GET", "POST"]), or None to allow all
            actual_method: HTTP method from request

        Returns:
            True if method matches, False otherwise
        """
        if allowed_methods is None:
            return True

        return actual_method.upper() in [m.upper() for m in allowed_methods]

    def match_queryparams(
        self,
        specs: List[Dict[str, str]],
        actual_params: Dict[str, Union[str, List[str]]]
    ) -> bool:
        """
        Match query parameters against specification.

        Each spec can have 'name' (regex) and optional 'value' (regex).
        All specs must match (AND logic).

        Args:
            specs: List of query parameter specifications
            actual_params: Actual query parameters from request

        Returns:
            True if all specs match, False otherwise
        """
        for spec in specs:
            name_pattern = re.compile(spec['name'])
            matched = False

            for param_name, param_value in actual_params.items():
                if name_pattern.match(param_name):
                    if 'value' in spec:
                        value_pattern = re.compile(spec['value'])
                        value_to_check = param_value if isinstance(param_value, str) else param_value[0]
                        if value_pattern.match(value_to_check):
                            matched = True
                            break
                    else:
                        matched = True
                        break

            if not matched:
                return False

        return True

    def match_headers(
        self,
        specs: List[Dict[str, str]],
        actual_headers: Dict[str, str]
    ) -> bool:
        """
        Match headers against specification.

        Each spec can have 'name' (regex) and optional 'value' (regex).
        All specs must match (AND logic).
        Header names are case-insensitive per RFC 7230.

        Args:
            specs: List of header specifications
            actual_headers: Actual headers from request

        Returns:
            True if all specs match, False otherwise
        """
        for spec in specs:
            name_pattern = re.compile(spec['name'], re.IGNORECASE)
            matched = False

            for header_name, header_value in actual_headers.items():
                if name_pattern.match(header_name):
                    if 'value' in spec:
                        value_pattern = re.compile(spec['value'])
                        if value_pattern.match(header_value):
                            matched = True
                            break
                    else:
                        matched = True
                        break

            if not matched:
                return False

        return True

    def match_body(
        self,
        request_def: RequestDef,
        actual_body: str,
        requests_dir: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Match request body against definition using semantic or legacy matching.

        This method supports two distinct matching systems for backwards compatibility:

        New Semantic Matching System (preferred):
            Uses a BodyMatcher instance (body_matcher) for format-aware matching.
            Matching flow:
            1. Validate body format (raises exception if invalid XML/JSON/etc.)
            2. Check if body matches expected value using matcher
            3. Run optional validator callback (for custom validation logic)
            4. Run optional processor callback (to extract data for templates)

            The processor can parse and transform the body (e.g., XML to dict) which
            is then available in response templates as BODY_PROCESSED.

        Legacy Matching System (backwards compatible):
            Simple pattern-based or file-based matching:
            - body_file: Load expected content from file and compare exactly
            - body_pattern: Regex pattern search in body
            - No processing: processed_body is always None

        Args:
            request_def: Request definition with body matching configuration
            actual_body: Raw request body string from HTTP request
            requests_dir: Directory for loading body_file content

        Returns:
            Tuple of (matches, processed_body):
            - matches: True if body matches all criteria, False otherwise
            - processed_body: Dict from processor function (new system) or None (legacy)

        Example (new semantic matching):
            >>> from body_matching.matchers import JSONBodyMatcher
            >>> def extract_user(body):
            ...     import json
            ...     return json.loads(body)
            >>> request_def = RequestDef(
            ...     url_pattern=r"^/api/users$",
            ...     url_regex=re.compile(r"^/api/users$"),
            ...     body_matcher=JSONBodyMatcher(),
            ...     body_expected_value='{"name": ".*"}',
            ...     body_processor=extract_user
            ... )
            >>> matches, processed = matcher.match_body(request_def, '{"name": "John"}', "config/")
            >>> print(matches)  # True
            >>> print(processed)  # {"name": "John"}

        Example (legacy pattern matching):
            >>> request_def = RequestDef(
            ...     url_pattern=r"^/api/test$",
            ...     url_regex=re.compile(r"^/api/test$"),
            ...     body_pattern=r'"id":\s*\d+'
            ... )
            >>> matches, processed = matcher.match_body(request_def, '{"id": 123}', "config/")
            >>> print(matches)  # True
            >>> print(processed)  # None (legacy system doesn't process)
        """
        # New body matching system (preferred)
        if request_def.body_matcher is not None:
            # Validate actual body
            try:
                request_def.body_matcher.validate(actual_body)
            except Exception:
                return (False, None)

            # Check if body matches
            if not request_def.body_matcher.matches(
                request_def.body_expected_value,
                actual_body
            ):
                return (False, None)

            # Run validator if present
            if request_def.body_validator is not None:
                try:
                    request_def.body_validator(actual_body)
                except Exception:
                    return (False, None)

            # Run processor if present
            processed_body = None
            if request_def.body_processor is not None:
                try:
                    processed_body = request_def.body_processor(actual_body)
                except Exception:
                    return (False, None)

            return (True, processed_body)

        # Legacy body matching system (backwards compatibility)
        if request_def.body_file:
            file_path = Path(requests_dir) / request_def.body_file
            if not file_path.exists():
                return (False, None)

            with open(file_path, 'r', encoding='utf-8') as f:
                expected_content = f.read()

            return (actual_body == expected_content, None)

        elif request_def.body_pattern:
            pattern = re.compile(request_def.body_pattern)
            return (pattern.search(actual_body) is not None, None)

        return (True, None)

    def match(
        self,
        request_def: RequestDef,
        http_request: HTTPRequest,
        requests_dir: str
    ) -> Optional[RequestContext]:
        """
        Match a complete HTTP request against a request definition.

        This is the main orchestration method that performs all matching steps in order.
        All criteria must match (AND logic) for the request to be considered a match.

        Matching Order:
            1. URL path (extracts path parameters from regex groups)
            2. HTTP method (if specified in definition)
            3. Query parameters (all specs must match)
            4. Headers (all specs must match, case-insensitive)
            5. Body (legacy pattern/file OR semantic matching)

        If any step fails, returns None immediately (short-circuit evaluation).
        If all steps pass, constructs and returns a RequestContext containing:
            - PATH_PARAMS: List of captured URL regex groups
            - QUERY_PARAMS: Dict of query parameters
            - HEADERS: Dict of request headers (case-insensitive)
            - BODY: Raw request body string
            - BODY_PROCESSED: Processed body from processor (if configured)

        Args:
            request_def: Request definition to match against
            http_request: Incoming HTTP request to evaluate
            requests_dir: Directory for loading request body files (legacy system)

        Returns:
            RequestContext with extracted values if all criteria match, None otherwise

        Example:
            >>> matcher = RequestMatcher()
            >>> request_def = RequestDef(
            ...     url_pattern=r"^/hello/(\w+)/(\w+)$",
            ...     url_regex=re.compile(r"^/hello/(\w+)/(\w+)$"),
            ...     methods=["GET"]
            ... )
            >>> http_request = HTTPRequest(
            ...     method="GET",
            ...     url="/hello/juan/perez?age=30",
            ...     headers={"Content-Type": "application/json"},
            ...     query_params={"age": "30"},
            ...     body=""
            ... )
            >>> context = matcher.match(request_def, http_request, "config/")
            >>> print(context.PATH_PARAMS)  # ["juan", "perez"]
            >>> print(context.QUERY_PARAMS)  # {"age": "30"}
            >>> print(context.HEADERS)  # {"content-type": "application/json"}
        """
        path_params = self.match_url(request_def.url_regex, http_request.url)
        if path_params is None:
            return None

        if not self.match_method(request_def.methods, http_request.method):
            return None

        if not self.match_queryparams(request_def.queryparams, http_request.query_params):
            return None

        if not self.match_headers(request_def.headers, http_request.headers):
            return None

        body_matches, body_processed = self.match_body(
            request_def,
            http_request.body,
            requests_dir
        )

        if not body_matches:
            return None

        headers_ci = CaseInsensitiveDict(http_request.headers)

        return RequestContext(
            PATH_PARAMS=path_params,
            QUERY_PARAMS=http_request.query_params,
            HEADERS=dict(headers_ci),
            BODY=http_request.body if http_request.body else None,
            BODY_PROCESSED=body_processed
        )
