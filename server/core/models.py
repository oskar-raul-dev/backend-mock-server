"""
Data models for mockserver request/response definitions.

This module contains all dataclass models used throughout the mockserver:
- RequestDef: Defines request matching criteria
- ResponseDef: Defines mock response to return
- MockDefinition: Combines request matcher with one or more responses
- RequestContext: Extracted context from matched request (for templating)
- HTTPRequest: Parsed incoming HTTP request

All models are immutable dataclasses for type safety and clarity.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any, Callable

from body_matching.base import BodyMatcher


@dataclass
class RequestDef:
    """
    Definition of a mock request matcher.

    This defines what incoming requests should match this mock definition.
    Supports both legacy body matching (body_pattern, body_file) and new
    semantic body matching (body_matcher, body_validator, body_processor).

    Attributes:
        url_pattern: Regex pattern for URL matching (string)
        url_regex: Compiled regex pattern for URL matching
        methods: HTTP methods to match (e.g., ["GET", "POST"]). None = match all.
        queryparams: List of query parameter matchers with 'name' and optional 'value' regex
        headers: List of header matchers with 'name' and optional 'value' regex

        # Legacy body matching (deprecated but supported)
        body_pattern: Regex pattern to match request body (string)
        body_file: Path to file containing expected body pattern

        # New semantic body matching
        body_matcher: BodyMatcher instance for semantic matching (XML, JSON, etc.)
        body_expected_value: Expected value/pattern for body matching
        body_validator: Callable to validate body before matching
        body_processor: Callable to process matched body for template context

    Example:
        >>> request_def = RequestDef(
        ...     url_pattern=r"^/api/users/(\d+)$",
        ...     url_regex=re.compile(r"^/api/users/(\d+)$"),
        ...     methods=["GET", "PUT"],
        ...     queryparams=[{"name": "include", "value": "profile|settings"}],
        ...     headers=[{"name": "Authorization", "value": r"Bearer .+"}]
        ... )
    """
    url_pattern: str
    url_regex: re.Pattern
    methods: Optional[List[str]] = None
    queryparams: List[Dict[str, str]] = field(default_factory=list)
    headers: List[Dict[str, str]] = field(default_factory=list)

    # Deprecated fields (kept for backwards compatibility)
    body_pattern: Optional[str] = None
    body_file: Optional[str] = None

    # New body matching fields
    body_matcher: Optional[BodyMatcher] = None
    body_expected_value: Optional[str] = None
    body_validator: Optional[Callable] = None
    body_processor: Optional[Callable] = None


@dataclass
class ResponseDef:
    """
    Definition of a mock response.

    Defines what response to return when a request matches.
    Supports Jinja2 templates in headers and body for dynamic responses.

    Attributes:
        status: HTTP status code (default: 200)
        headers: Response headers (key-value pairs). Values support Jinja2 templates.
        body: Inline response body. Supports Jinja2 templates.
        body_file: Path to file containing response body (relative to responses_dir).
                   If set, body is ignored. File content supports Jinja2 templates.

    Template Variables Available in body and headers:
        - PATH_PARAMS: List of captured regex groups from URL
        - QUERY_PARAMS: Dict of query string parameters
        - HEADERS: Dict of request headers (case-insensitive)
        - BODY: Raw request body string
        - BODY_PROCESSED: Processed body from processor function (if configured)

    Example:
        >>> response_def = ResponseDef(
        ...     status=200,
        ...     headers={"Content-Type": "application/json"},
        ...     body='{"user_id": "{{ PATH_PARAMS[0] }}", "name": "{{ QUERY_PARAMS.name }}"}'
        ... )

    Example with file:
        >>> response_def = ResponseDef(
        ...     status=200,
        ...     headers={"Content-Type": "text/html"},
        ...     body_file="welcome.html"  # Loaded from responses_dir/welcome.html
        ... )
    """
    status: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    body_file: Optional[str] = None


@dataclass
class MockDefinition:
    """
    Complete mock definition with request matcher and response(s).

    Combines a RequestDef (matcher) with one or more ResponseDef objects.
    If multiple responses are defined, they will be returned in round-robin fashion,
    allowing simulation of stateful APIs or sequential responses.

    Attributes:
        request: Request matching criteria
        responses: List of possible responses (at least one required)
        response_index: Current index for round-robin response selection (internal state)

    Example with single response:
        >>> mock_def = MockDefinition(
        ...     request=RequestDef(url_pattern=r"^/ping$", url_regex=re.compile(r"^/ping$")),
        ...     responses=[ResponseDef(status=200, body="pong")]
        ... )

    Example with multiple responses (cycling):
        >>> mock_def = MockDefinition(
        ...     request=RequestDef(url_pattern=r"^/counter$", url_regex=re.compile(r"^/counter$")),
        ...     responses=[
        ...         ResponseDef(body='{"count": 1}'),
        ...         ResponseDef(body='{"count": 2}'),
        ...         ResponseDef(body='{"count": 3}')
        ...     ]
        ... )
        >>> # First call returns count:1, second returns count:2, third returns count:3,
        >>> # fourth cycles back to count:1
    """
    request: RequestDef
    responses: List[ResponseDef]
    response_index: int = 0  # Internal state for round-robin


@dataclass
class RequestContext:
    """
    Context extracted from a matched request.

    This context is available as template variables in Jinja2 templates
    for dynamic response generation. All variables are uppercase to
    distinguish them from normal template variables.

    Attributes:
        PATH_PARAMS: List of captured groups from URL regex.
                     Example: URL pattern ^/users/(\d+)/posts/(\d+)$ with request /users/123/posts/456
                     results in PATH_PARAMS = ["123", "456"]

        QUERY_PARAMS: Dict of query string parameters. Values can be string or List[str]
                      for repeated parameters.
                      Example: ?name=john&tag=python&tag=dev results in
                      QUERY_PARAMS = {"name": "john", "tag": ["python", "dev"]}

        HEADERS: Request headers as case-insensitive dict.
                 Example: {"content-type": "application/json", "authorization": "Bearer abc123"}

        BODY: Raw request body as string (may be empty)

        BODY_PROCESSED: Processed/parsed body from processor function (if configured).
                        Typically a dict for JSON/XML bodies after semantic matching.
                        None if no processor was configured.

    Example usage in template:
        >>> # Response template:
        >>> body = '{"user_id": "{{ PATH_PARAMS[0] }}", "email": "{{ QUERY_PARAMS.email }}"}'
        >>> # With context:
        >>> context = RequestContext(
        ...     PATH_PARAMS=["123"],
        ...     QUERY_PARAMS={"email": "john@example.com"},
        ...     HEADERS={"content-type": "application/json"},
        ...     BODY='{"name": "John"}',
        ...     BODY_PROCESSED=None
        ... )
        >>> # Renders to: {"user_id": "123", "email": "john@example.com"}
    """
    PATH_PARAMS: List[str]
    QUERY_PARAMS: Dict[str, Union[str, List[str]]]
    HEADERS: Dict[str, str]
    BODY: Optional[str]
    BODY_PROCESSED: Optional[Dict[str, Any]] = None


@dataclass
class HTTPRequest:
    """
    Parsed HTTP request data from incoming connections.

    This is the internal representation of an HTTP request after parsing
    from the HTTP server. Used as input to the request matcher.

    Attributes:
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        url: Request path including query string (e.g., "/api/users?page=1")
        headers: Request headers as dict (case-insensitive)
        query_params: Parsed query string parameters. Values can be string or List[str].
        body: Raw request body as string

    Example:
        >>> request = HTTPRequest(
        ...     method="POST",
        ...     url="/api/users",
        ...     headers={"content-type": "application/json"},
        ...     query_params={},
        ...     body='{"name": "John", "email": "john@example.com"}'
        ... )
    """
    method: str
    url: str
    headers: Dict[str, str]
    query_params: Dict[str, Union[str, List[str]]]
    body: str
