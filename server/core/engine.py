"""
Mock engine - coordinates request matching and response generation.

This module implements the MockEngine class which serves as the central orchestrator
for the mockserver. The engine manages a collection of mock definitions and handles
the complete request-response cycle:

1. Receives incoming HTTP requests
2. Finds matching mock definition (first-match wins)
3. Selects appropriate response (round-robin for multiple responses)
4. Generates response with template rendering
5. Returns HTTP response tuple

The engine delegates to:
    - RequestMatcher: For matching requests against definitions
    - ResponseGenerator: For rendering responses with templates

Key Behaviors:
    - First-match strategy: Definitions are checked in order, first match wins
    - Round-robin responses: MockDefinitions with multiple responses cycle through them
    - Separate directories: Supports different paths for request/response body files
    - NoMatchError: Raises exception if no definition matches (converted to 404 by handler)
"""
from typing import List, Optional, Tuple, Dict

from .models import MockDefinition, HTTPRequest, ResponseDef, RequestContext
from .matcher import RequestMatcher
from .generator import ResponseGenerator
from .exceptions import NoMatchError


class MockEngine:
    """
    Main mock engine that coordinates request matching and response generation.

    The MockEngine is the heart of the mockserver. It maintains a list of mock definitions
    and processes incoming HTTP requests through a complete matching and response cycle.

    Workflow:
        1. handle_request() is called with an HTTPRequest
        2. find_match() iterates through definitions to find first match
        3. For matching definition, get_next_response() selects response (round-robin)
        4. ResponseGenerator renders the response with template variables
        5. Returns (status, headers, body) tuple or raises NoMatchError

    Matching Strategy:
        First-match wins: Definitions are checked in order. The first definition
        whose RequestDef matches the incoming request is used. Order matters!

    Response Selection:
        Round-robin: If a MockDefinition has multiple responses, they are returned
        in sequence on successive matching requests. The response_index cycles back
        to 0 after the last response.

    Directory Structure:
        - requests_dir: Base directory for request body files (legacy body_file matching)
        - responses_dir: Base directory for response body files (body_file in ResponseDef)
        - Defaults to same directory for backwards compatibility

    Attributes:
        definitions: List of mock definitions to match against
        requests_dir: Directory for request body files
        responses_dir: Directory for response body files
        matcher: RequestMatcher instance for request matching
        generator: ResponseGenerator instance for response rendering

    Example:
        >>> definitions = [
        ...     MockDefinition(
        ...         request=RequestDef(
        ...             url_pattern=r"^/api/users$",
        ...             url_regex=re.compile(r"^/api/users$"),
        ...             methods=["GET"]
        ...         ),
        ...         responses=[
        ...             ResponseDef(status=200, body='{"users": []}')
        ...         ]
        ...     )
        ... ]
        >>> engine = MockEngine(definitions, "config/requests", "config/responses")
        >>> http_request = HTTPRequest(
        ...     method="GET",
        ...     url="/api/users",
        ...     headers={},
        ...     query_params={},
        ...     body=""
        ... )
        >>> status, headers, body = engine.handle_request(http_request)
        >>> print(status)  # 200
        >>> print(body)  # {"users": []}
    """

    def __init__(self, definitions: List[MockDefinition], requests_dir: str, responses_dir: str = None):
        """
        Initialize mock engine with definitions and directory paths.

        Args:
            definitions: List of mock definitions to use for matching. Order matters
                        as first-match strategy is used.
            requests_dir: Directory for loading request body files used in legacy
                         body matching (body_file in RequestDef)
            responses_dir: Directory for loading response body files (body_file in
                          ResponseDef). If None, defaults to requests_dir for
                          backwards compatibility.

        Example:
            >>> engine = MockEngine(
            ...     definitions=[mock_def1, mock_def2],
            ...     requests_dir="config/requests",
            ...     responses_dir="config/responses"
            ... )
        """
        self.definitions = definitions
        self.requests_dir = requests_dir
        self.responses_dir = responses_dir if responses_dir is not None else requests_dir
        self.matcher = RequestMatcher()
        self.generator = ResponseGenerator()

    def find_match(
        self,
        http_request: HTTPRequest
    ) -> Optional[Tuple[MockDefinition, RequestContext]]:
        """
        Find first matching mock definition for the incoming request.

        Iterates through all mock definitions in order and returns the first one
        that matches the request. Uses RequestMatcher to evaluate each definition's
        RequestDef against the HTTPRequest.

        First-match strategy means:
            - Order of definitions matters
            - More specific patterns should come before general patterns
            - Once a match is found, subsequent definitions are not checked

        Args:
            http_request: Incoming HTTP request to match against definitions

        Returns:
            Tuple of (MockDefinition, RequestContext) if a match is found:
                - MockDefinition: The matching mock definition
                - RequestContext: Extracted context (path params, query params, etc.)
            None if no definition matches the request

        Example:
            >>> engine = MockEngine([def1, def2, def3], "config/", "config/responses/")
            >>> http_request = HTTPRequest(method="GET", url="/api/users", ...)
            >>> result = engine.find_match(http_request)
            >>> if result:
            ...     mock_def, context = result
            ...     print(f"Matched! Path params: {context.PATH_PARAMS}")
            ... else:
            ...     print("No match found")
        """
        for definition in self.definitions:
            context = self.matcher.match(
                definition.request,
                http_request,
                self.requests_dir
            )

            if context is not None:
                return (definition, context)

        return None

    def get_next_response(self, mock_def: MockDefinition) -> ResponseDef:
        """
        Get next response from definition using round-robin selection.

        For MockDefinitions with multiple responses, this method cycles through them
        in order. The response_index is incremented after each call and wraps back
        to 0 after the last response.

        This enables simulation of:
            - Stateful APIs that change responses over time
            - Sequential test scenarios
            - Alternating success/failure responses

        Note: This method modifies mock_def.response_index as a side effect.

        Args:
            mock_def: Mock definition containing one or more responses

        Returns:
            The next ResponseDef to use (cycles through mock_def.responses)

        Example with single response:
            >>> mock_def = MockDefinition(
            ...     request=request_def,
            ...     responses=[ResponseDef(body="same every time")]
            ... )
            >>> r1 = engine.get_next_response(mock_def)  # response_index: 0 -> 0
            >>> r2 = engine.get_next_response(mock_def)  # response_index: 0 -> 0
            >>> # Always returns same response

        Example with multiple responses:
            >>> mock_def = MockDefinition(
            ...     request=request_def,
            ...     responses=[
            ...         ResponseDef(body='{"count": 1}'),
            ...         ResponseDef(body='{"count": 2}'),
            ...         ResponseDef(body='{"count": 3}')
            ...     ]
            ... )
            >>> r1 = engine.get_next_response(mock_def)  # Returns count:1, index: 0 -> 1
            >>> r2 = engine.get_next_response(mock_def)  # Returns count:2, index: 1 -> 2
            >>> r3 = engine.get_next_response(mock_def)  # Returns count:3, index: 2 -> 0
            >>> r4 = engine.get_next_response(mock_def)  # Returns count:1, index: 0 -> 1
        """
        response = mock_def.responses[mock_def.response_index]

        mock_def.response_index = (mock_def.response_index + 1) % len(mock_def.responses)

        return response

    def handle_request(
        self,
        http_request: HTTPRequest
    ) -> Tuple[int, Dict[str, str], str]:
        """
        Handle incoming HTTP request and generate mock response.

        This is the main entry point for request processing. It orchestrates the
        complete request-response cycle:
            1. Find matching mock definition (or raise NoMatchError)
            2. Extract request context from the match
            3. Select next response (round-robin if multiple responses)
            4. Render response with template variables from context
            5. Return complete HTTP response tuple

        The request handler (server.handler.MockRequestHandler) calls this method
        for each incoming HTTP request and uses the returned values to send the
        HTTP response back to the client.

        Args:
            http_request: Incoming HTTP request with method, url, headers, query_params, body

        Returns:
            Tuple of (status_code, headers_dict, body_string):
                - status_code: HTTP status code (int) from ResponseDef
                - headers_dict: Response headers with rendered template values
                - body_string: Response body with rendered template values

        Raises:
            NoMatchError: If no mock definition matches the request. The exception
                         message includes the request method and URL for debugging.
                         The HTTP handler catches this and returns a 404 response.

        Example successful match:
            >>> engine = MockEngine([mock_def], "config/", "config/responses/")
            >>> request = HTTPRequest(
            ...     method="GET",
            ...     url="/api/users/123",
            ...     headers={},
            ...     query_params={},
            ...     body=""
            ... )
            >>> status, headers, body = engine.handle_request(request)
            >>> print(status)  # 200
            >>> print(body)  # {"user_id": "123"}

        Example no match (raises exception):
            >>> engine = MockEngine([mock_def], "config/", "config/responses/")
            >>> request = HTTPRequest(method="GET", url="/unknown", ...)
            >>> try:
            ...     engine.handle_request(request)
            ... except NoMatchError as e:
            ...     print(f"Not found: {e}")
            ...     # Handler will return 404
        """
        match_result = self.find_match(http_request)

        if match_result is None:
            raise NoMatchError(f"No mock definition matched the request: {http_request.method} {http_request.url}")

        mock_def, context = match_result
        response_def = self.get_next_response(mock_def)

        return self.generator.render(response_def, context, self.responses_dir)
