"""
Utility classes and functions for the server.

This module provides general-purpose utilities used by the server module:

- CaseInsensitiveDict: Dictionary with case-insensitive string keys for HTTP headers
- is_port_available: Port availability checker for server startup validation

These utilities are used throughout the mockserver for HTTP header handling and
server initialization.
"""
import socket


class CaseInsensitiveDict(dict):
    """
    Dictionary with case-insensitive string keys for HTTP header handling.

    This class extends Python's built-in dict to provide case-insensitive key access.
    All string keys are automatically converted to lowercase for storage and lookup,
    ensuring that "Content-Type", "content-type", and "CONTENT-TYPE" all access the
    same value.

    This behavior conforms to RFC 7230 which specifies that HTTP header field names
    are case-insensitive.

    All standard dict operations work as expected:
        - Assignment: d["Key"] = value
        - Lookup: d["key"] or d.get("KEY")
        - Membership: "KEY" in d
        - Iteration: for key in d (keys are lowercase)

    Example:
        >>> headers = CaseInsensitiveDict()
        >>> headers["Content-Type"] = "application/json"
        >>> headers["content-type"]  # 'application/json'
        >>> headers["CONTENT-TYPE"]  # 'application/json'
        >>> "content-type" in headers  # True
        >>> "Content-Type" in headers  # True
        >>> list(headers.keys())  # ['content-type']

    Example with initialization:
        >>> headers = CaseInsensitiveDict({
        ...     "Content-Type": "application/json",
        ...     "AUTHORIZATION": "Bearer token123"
        ... })
        >>> headers["authorization"]  # 'Bearer token123'
        >>> list(headers.keys())  # ['content-type', 'authorization']
    """

    def __init__(self, data=None):
        """
        Initialize case-insensitive dictionary.

        Args:
            data: Optional dict-like object with initial key-value pairs.
                  All keys will be converted to lowercase.
        """
        super().__init__()
        if data:
            for key, value in data.items():
                self[key] = value

    def __setitem__(self, key, value):
        """Set item with lowercase key."""
        super().__setitem__(key.lower(), value)

    def __getitem__(self, key):
        """Get item using lowercase key."""
        return super().__getitem__(key.lower())

    def __contains__(self, key):
        """Check membership using lowercase key."""
        return super().__contains__(key.lower())

    def get(self, key, default=None):
        """Get item with default using lowercase key."""
        return super().get(key.lower(), default)


def is_port_available(host: str, port: int) -> bool:
    """
    Check if a port is available for binding on the specified host.

    Attempts to create a TCP socket and bind it to the given host and port.
    Uses SO_REUSEADDR socket option to match the server's socket configuration.

    This function is useful for:
        - Validating port availability before starting the server
        - Checking for port conflicts with other processes
        - Finding alternative ports if the preferred port is unavailable

    Socket Configuration:
        - Socket family: AF_INET (IPv4)
        - Socket type: SOCK_STREAM (TCP)
        - Socket option: SO_REUSEADDR enabled (matches server behavior)

    Args:
        host: The host address to check (e.g., '0.0.0.0', 'localhost', '127.0.0.1')
        port: The port number to check (0-65535)

    Returns:
        True if the port is available and can be bound, False otherwise

    Example:
        >>> if is_port_available('0.0.0.0', 8000):
        ...     print("Port 8000 is available")
        ... else:
        ...     print("Port 8000 is already in use")

    Example finding available port:
        >>> port = 8000
        >>> while not is_port_available('0.0.0.0', port):
        ...     port += 1
        >>> print(f"Using port {port}")
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
    except OSError:
        return False
