"""
HTTP request handler for the mockserver.

This module implements the MockRequestHandler which processes incoming HTTP requests
and generates mock responses. It extends Python's built-in BaseHTTPRequestHandler
to provide:

- Multi-method support (GET, POST, PUT, DELETE, PATCH, OPTIONS)
- CORS support with configurable origins
- Health check endpoint (/_health)
- Request parsing (headers, query params, body)
- Response generation via MockEngine
- Error handling (404 for NoMatchError, 500 for exceptions)
- Custom logging integration

The handler works in conjunction with MockEngine to:
1. Parse incoming HTTP requests into HTTPRequest objects
2. Pass requests to MockEngine for matching and response generation
3. Send generated responses back to the client
4. Handle errors gracefully with appropriate HTTP status codes

Special Endpoints:
    - /_health: Returns server health information (status, version, uptime, config)
                Does not go through mock matching engine.
"""
import time
import json
import logging
import traceback
import http.server
from typing import Dict
from urllib.parse import parse_qs, urlparse

from core.models import HTTPRequest
from core.exceptions import NoMatchError


# Version constant
VERSION = "1.0.0"


class MockRequestHandler(http.server.BaseHTTPRequestHandler):
    """
    HTTP request handler with CORS support and mock response generation.

    This handler extends Python's BaseHTTPRequestHandler to provide mockserver-specific
    functionality. It delegates HTTP method handling to handle_mock_request() which
    orchestrates the complete request-response cycle.

    Request Flow:
        1. HTTP method handler (do_GET, do_POST, etc.) is called
        2. handle_mock_request() parses the request
        3. Health check endpoint (/_health) is handled specially
        4. Request is passed to MockEngine for matching and response generation
        5. Response is sent back to client with CORS headers

    Server Instance Attributes Required:
        - engine: MockEngine instance for request handling
        - cors_enabled: Boolean flag to enable/disable CORS
        - cors_origins: CORS origins value (default: '*')
        - start_time: Server start timestamp for uptime calculation
        - config_dir: Configuration directory path

    Error Handling:
        - NoMatchError: Returns 404 with error message
        - Other exceptions: Returns 500 with error details (stack trace in DEBUG mode)

    Logging:
        Overrides default BaseHTTPRequestHandler logging to use Python's logging
        framework instead of stderr output.
    """

    def log_message(self, format, *args):
        """
        Override to disable default request logging.

        BaseHTTPRequestHandler logs to stderr by default. We override this to do
        nothing since we have our own logging in handle_mock_request().
        """
        pass

    def add_cors_headers(self):
        """
        Add CORS headers to response if CORS is enabled on the server.

        Checks server.cors_enabled attribute and adds appropriate Access-Control
        headers for cross-origin requests. Used by all response methods.

        Headers added when CORS is enabled:
            - Access-Control-Allow-Origin: From server.cors_origins (default: '*')
            - Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
            - Access-Control-Allow-Headers: * (all headers allowed)
            - Access-Control-Max-Age: 86400 (preflight cache for 24 hours)
        """
        if hasattr(self.server, 'cors_enabled') and self.server.cors_enabled:
            cors_origins = getattr(self.server, 'cors_origins', '*')
            self.send_header("Access-Control-Allow-Origin", cors_origins)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.add_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        self.handle_mock_request()

    def do_POST(self):
        """Handle POST requests."""
        self.handle_mock_request()

    def do_PUT(self):
        """Handle PUT requests."""
        self.handle_mock_request()

    def do_DELETE(self):
        """Handle DELETE requests."""
        self.handle_mock_request()

    def do_PATCH(self):
        """Handle PATCH requests."""
        self.handle_mock_request()

    def parse_http_request(self) -> HTTPRequest:
        """
        Parse incoming HTTP request into HTTPRequest dataclass.

        Extracts all components of the HTTP request and constructs an HTTPRequest
        object for use by the MockEngine. Handles:
            - Request body with UTF-8 decoding (gracefully handles decode errors)
            - Query parameter parsing from URL
            - Header extraction as dictionary
            - Full URL reconstruction

        Query Parameter Handling:
            - Uses urllib.parse.parse_qs for standard URL query string parsing
            - Single-value params converted from [value] to value
            - Multi-value params kept as lists
            - Invalid query strings logged as warnings but don't fail the request

        Returns:
            HTTPRequest object with parsed method, url, headers, query_params, body

        Example:
            For request: POST /api/users?page=1&tags=python&tags=web
            Returns HTTPRequest with:
                - method: "POST"
                - url: "http://localhost:8000/api/users?page=1&tags=python&tags=web"
                - query_params: {"page": "1", "tags": ["python", "web"]}
                - headers: {...}
                - body: "..." (request body content)
        """
        # Read body
        content_length = self.headers.get('Content-Length')
        if content_length:
            body_bytes = self.rfile.read(int(content_length))
            try:
                body = body_bytes.decode('utf-8')
            except UnicodeDecodeError:
                body = body_bytes.decode('utf-8', errors='replace')
        else:
            body = ""

        # Parse query params
        parsed_url = urlparse(self.path)
        query_params = {}
        if parsed_url.query:
            try:
                query_params = parse_qs(parsed_url.query)
                # Convert single-element lists to strings
                query_params = {
                    k: v[0] if len(v) == 1 else v
                    for k, v in query_params.items()
                }
            except Exception as e:
                logging.getLogger().warning(f"Failed to parse query string: {e}")

        # Convert headers to dict
        headers = dict(self.headers)

        # Construct full URL
        host = self.headers.get('Host', f"{self.server.server_address[0]}:{self.server.server_address[1]}")
        url = f"http://{host}{self.path}"

        return HTTPRequest(
            method=self.command,
            url=url,
            headers=headers,
            query_params=query_params,
            body=body
        )

    def send_mock_response(self, status: int, headers: Dict[str, str], body: str):
        """
        Send mock response to client.

        Args:
            status: HTTP status code
            headers: Response headers
            body: Response body
        """
        self.send_response(status)
        self.add_cors_headers()

        # Send response headers
        for key, value in headers.items():
            self.send_header(key, value)

        # Set Content-Length if not already set
        if 'Content-Length' not in headers and 'content-length' not in headers:
            body_bytes = body.encode('utf-8')
            self.send_header('Content-Length', str(len(body_bytes)))

        self.end_headers()

        # Send body
        if body:
            self.wfile.write(body.encode('utf-8'))

    def handle_health_check(self):
        """
        Handle health check endpoint /_health.

        Special endpoint that returns server health and configuration information
        without going through the mock matching engine. Always returns 200 OK with
        JSON data.

        This endpoint is useful for:
            - Monitoring and alerting systems
            - Load balancer health checks
            - Development debugging and verification
            - Checking server uptime and configuration

        Response JSON Fields:
            - status: Always "ok" (string)
            - version: Mockserver version from VERSION constant
            - definitions_loaded: Number of mock definitions currently loaded
            - uptime_seconds: Server uptime in seconds since start
            - config_dir: Path to configuration directory
            - reload_enabled: Whether auto-reload is enabled
            - cors_enabled: Whether CORS is enabled

        Returns:
            Sends 200 response with Content-Type: application/json
            Response body: JSON object with health information

        Example Response:
            {
              "status": "ok",
              "version": "1.0.0",
              "definitions_loaded": 8,
              "uptime_seconds": 3600,
              "config_dir": "config",
              "reload_enabled": true,
              "cors_enabled": true
            }
        """
        # Calculate uptime
        uptime_seconds = int(time.time() - self.server.start_time) if hasattr(self.server, 'start_time') else 0

        # Get reload status
        reload_enabled = getattr(self.server, 'reload_enabled', False)

        # Build health response
        health_data = {
            "status": "ok",
            "version": VERSION,
            "definitions_loaded": len(self.server.engine.definitions) if hasattr(self.server, 'engine') else 0,
            "uptime_seconds": uptime_seconds,
            "config_dir": getattr(self.server, 'config_dir', None),
            "reload_enabled": reload_enabled,
            "cors_enabled": getattr(self.server, 'cors_enabled', False)
        }

        # Send JSON response
        body = json.dumps(health_data, indent=2)
        self.send_response(200)
        self.add_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

        # Log health check
        logging.getLogger().debug(f"Health check: {health_data}")

    def handle_mock_request(self):
        """
        Main request handling logic for all HTTP methods.

        This is the central orchestration method called by all HTTP method handlers
        (do_GET, do_POST, etc.). It coordinates the complete request-response cycle:

        Processing Flow:
            1. Log incoming request (method and path)
            2. Check for special /_health endpoint and handle separately
            3. Parse HTTP request into HTTPRequest object
            4. Get MockEngine from server instance
            5. Call engine.handle_request() to get mock response
            6. Send response to client with CORS headers
            7. Log successful response

        Error Handling:
            NoMatchError (404):
                - Logged as error with method and path
                - Returns 404 Not Found with error message in body
                - Includes CORS headers

            General Exceptions (500):
                - Logged as error with exception details
                - Returns 500 Internal Server Error
                - Includes full stack trace in DEBUG log level
                - Body includes exception message
                - Body includes stack trace if DEBUG logging enabled

        Logging Behavior:
            - INFO level: Request method/path and response status
            - DEBUG level: Headers, query params, body preview, response body preview
            - ERROR level: Errors with exception details

        Example successful flow:
            >>> # Request: GET /api/users?page=1
            >>> # Log: INFO - GET /api/users?page=1
            >>> # Engine matches and generates response
            >>> # Send: 200 OK with JSON body
            >>> # Log: INFO - GET /api/users?page=1 -> 200

        Example error flow (no match):
            >>> # Request: GET /unknown
            >>> # Log: INFO - GET /unknown
            >>> # Engine raises NoMatchError
            >>> # Log: ERROR - No mock definition matched: GET /unknown
            >>> # Send: 404 Not Found with error message
        """
        logger = logging.getLogger()

        try:
            # Log incoming request
            logger.info(f"{self.command} {self.path}")

            # Check for health check endpoint BEFORE processing
            if self.path == '/_health' or self.path.startswith('/_health?'):
                self.handle_health_check()
                return

            # Parse HTTP request
            http_request = self.parse_http_request()

            # Log debug details
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Headers: {http_request.headers}")
                logger.debug(f"Query params: {http_request.query_params}")
                logger.debug(f"Body: {http_request.body[:200] if http_request.body else '(empty)'}")

            # Get engine from server
            if not hasattr(self.server, 'engine'):
                raise ValueError("Server does not have MockEngine configured")

            engine = self.server.engine

            # Handle request with engine
            status, resp_headers, resp_body = engine.handle_request(http_request)

            # Send response
            self.send_mock_response(status, resp_headers, resp_body)

            # Log success
            logger.info(f"{self.command} {self.path} -> {status}")

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Response body: {resp_body[:200] if resp_body else '(empty)'}")

        except NoMatchError as e:
            # No matching mock definition
            error_msg = str(e)
            logger.error(f"No mock definition matched: {self.command} {self.path}")

            self.send_response(404)
            self.add_cors_headers()
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(error_msg.encode('utf-8'))

        except Exception as e:
            # Internal server error
            logger.error(f"Error handling request {self.command} {self.path}: {e}")

            if logger.isEnabledFor(logging.DEBUG):
                logger.error(traceback.format_exc())

            error_msg = f"Internal Server Error: {e}"
            if logger.isEnabledFor(logging.DEBUG):
                error_msg += f"\n\n{traceback.format_exc()}"

            self.send_response(500)
            self.add_cors_headers()
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(error_msg.encode('utf-8'))
