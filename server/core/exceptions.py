"""
Custom exceptions for the mockserver.

This module defines all custom exceptions used throughout the mockserver.
Currently contains only NoMatchError, but can be extended with more
specific exceptions for different error scenarios.
"""


class NoMatchError(Exception):
    """
    Raised when no mock definition matches the incoming request.

    This exception is raised by MockEngine.handle_request() when none of the
    configured mock definitions match the incoming HTTP request. The request
    handler catches this exception and returns a 404 Not Found response.

    Attributes:
        message: Error message describing which request didn't match

    Example:
        >>> engine = MockEngine(definitions=[...], requests_dir="...")
        >>> try:
        ...     engine.handle_request(http_request)
        ... except NoMatchError as e:
        ...     print(f"No match found: {e}")
        ...     # Return 404 response
    """
    pass
