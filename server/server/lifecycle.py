"""
Server lifecycle management for the mockserver.

This module provides server factory functions and auto-reload capabilities for the
mockserver. It handles:

Server Creation (create_server):
    - Creates HTTP server instance with MockEngine
    - Configures CORS settings
    - Sets up socket options for proper behavior
    - Injects configuration into server instance

Auto-Reload (setup_reload_watcher):
    - Watches configuration files and directories for changes
    - Debounces file system events (500ms) to avoid rapid reloads
    - Reloads mock definitions automatically when files change
    - Preserves server state across reloads (engine is replaced, server continues)
    - Thread-safe reload using threading.Lock

The auto-reload functionality uses the watchdog library to monitor:
    - Endpoints file (endpoints.py)
    - Config file (config.py)
    - Requests directory (for request body files)
    - Responses directory (for response body files)

This enables a fast development workflow where changes to mock definitions take
effect immediately without manual server restart.
"""
import time
import socket
import logging
import threading
import http.server
from typing import List, Optional, Callable
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from colorama import Fore, Style

from core.models import MockDefinition
from core.engine import MockEngine
from server.handler import MockRequestHandler


def create_server(
    definitions: List[MockDefinition],
    base_dir: str,
    host: str,
    port: int,
    cors_enabled: bool = True,
    cors_origins: str = '*',
    log_level: str = 'INFO',
    responses_dir: str = None
) -> http.server.HTTPServer:
    """
    Create and configure HTTP server with MockEngine and request handler.

    This factory function creates a Python http.server.HTTPServer instance and
    configures it with:
        - MockEngine for request processing
        - MockRequestHandler for HTTP handling
        - CORS configuration
        - Socket options (SO_REUSEADDR for quick restart)
        - Server metadata (start time, config directory)

    The returned server is ready to use with server.serve_forever() or
    server.handle_request().

    Configuration Injection:
        The server instance receives these attributes for use by the request handler:
        - engine: MockEngine instance
        - cors_enabled: CORS flag
        - cors_origins: CORS origins value
        - log_level: Logging level string
        - start_time: Timestamp when server was created (for uptime)
        - config_dir: Base directory path (for health check)

    Socket Configuration:
        - SO_REUSEADDR: Allows immediate port rebinding after server restart
        - Timeout: 60 seconds for socket operations

    Args:
        definitions: List of mock definitions to load into the engine
        base_dir: Base directory for request body files (legacy body_file matching)
        host: Server host/IP (e.g., '0.0.0.0', 'localhost', '127.0.0.1')
        port: Server port number (e.g., 8000)
        cors_enabled: Enable CORS headers in responses (default: True)
        cors_origins: CORS Access-Control-Allow-Origin value (default: '*')
        log_level: Logging level for the server (default: 'INFO')
        responses_dir: Directory for response body files. If None, defaults to
                      base_dir for backwards compatibility.

    Returns:
        Configured HTTPServer instance ready to call serve_forever()

    Raises:
        OSError: If the port is already in use or cannot be bound

    Example:
        >>> from core.models import MockDefinition, RequestDef, ResponseDef
        >>> import re
        >>> definitions = [
        ...     MockDefinition(
        ...         request=RequestDef(
        ...             url_pattern=r"^/test$",
        ...             url_regex=re.compile(r"^/test$")
        ...         ),
        ...         responses=[ResponseDef(body="OK")]
        ...     )
        ... ]
        >>> server = create_server(
        ...     definitions=definitions,
        ...     base_dir="config",
        ...     host="0.0.0.0",
        ...     port=8000,
        ...     responses_dir="config/responses"
        ... )
        >>> # server.serve_forever()  # Start serving requests
    """
    # Create mock engine
    engine = MockEngine(definitions, base_dir, responses_dir)

    # Create request handler with bound engine
    class BoundMockRequestHandler(MockRequestHandler):
        """Request handler with engine reference."""
        pass

    # Create HTTP server
    server = http.server.HTTPServer((host, port), BoundMockRequestHandler)

    # Inject configuration into server instance
    server.engine = engine
    server.cors_enabled = cors_enabled
    server.cors_origins = cors_origins
    server.log_level = log_level
    server.start_time = time.time()  # Track server start time for uptime
    server.config_dir = base_dir  # Store config dir for health check

    # Configure socket options for better behavior
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Set reasonable timeout
    server.timeout = 60  # 60 seconds

    return server


def setup_reload_watcher(
    server: http.server.HTTPServer,
    endpoints_file: str,
    config_file: Optional[str],
    requests_dir: str,
    responses_dir: str,
    reload_callback: Callable[[], Optional[List[MockDefinition]]]
) -> Observer:
    """
    Setup file watcher for auto-reload functionality with debouncing.

    Creates a watchdog Observer that monitors configuration files and directories
    for changes. When changes are detected, reloads mock definitions and rebuilds
    the MockEngine without restarting the HTTP server.

    Watched Paths:
        - endpoints_file parent directory (for endpoints.py changes)
        - config_file parent directory (for config.py changes, if specified)
        - requests_dir (recursive, for request body file changes)
        - responses_dir (recursive, for response body file changes)

    Debouncing Behavior:
        File system events are debounced with a 500ms delay to avoid rapid
        successive reloads when multiple files change (e.g., editor autosave).
        Each new event cancels the pending reload timer and starts a new one.

    Reload Process:
        1. File change detected
        2. Wait 500ms for additional changes (debounce)
        3. Call reload_callback() to get new definitions
        4. If successful, create new MockEngine with new definitions
        5. Replace server.engine with new engine (preserves requests_dir/responses_dir)
        6. Log success with definition count
        7. If failed, log error and keep previous definitions

    Thread Safety:
        Uses threading.Lock to ensure only one reload happens at a time.
        The reload happens in a separate timer thread.

    Error Handling:
        If reload_callback returns None or raises an exception, the error is
        logged and the previous mock definitions continue to be used.

    Args:
        server: HTTP server instance whose engine will be updated on reload
        endpoints_file: Absolute path to endpoints.py file
        config_file: Absolute path to config.py file (None to skip watching)
        requests_dir: Directory path containing request body files
        responses_dir: Directory path containing response body files
        reload_callback: Callable that reloads and returns new definitions.
                        Should return List[MockDefinition] on success or None on error.

    Returns:
        Observer instance from watchdog library. Call observer.stop() to stop watching.
        The observer is already started when returned.

    Example:
        >>> def my_reload_callback():
        ...     try:
        ...         # Reload logic here
        ...         return load_new_definitions()
        ...     except Exception as e:
        ...         logger.error(f"Reload failed: {e}")
        ...         return None
        >>>
        >>> observer = setup_reload_watcher(
        ...     server=server,
        ...     endpoints_file="config/endpoints.py",
        ...     config_file="config/config.py",
        ...     requests_dir="config/requests",
        ...     responses_dir="config/responses",
        ...     reload_callback=my_reload_callback
        ... )
        >>> # Server now auto-reloads when files change
        >>> # Later: observer.stop() to disable auto-reload
    """
    logger = logging.getLogger(__name__)

    class ReloadHandler(FileSystemEventHandler):
        """File system event handler with debouncing."""

        def __init__(self):
            super().__init__()
            self.reload_timer: Optional[threading.Timer] = None
            self.lock = threading.Lock()

        def on_any_event(self, event: FileSystemEvent):
            """Handle file system events with debouncing."""
            # Ignore directory events and non-modify/create events
            if event.is_directory:
                return

            # Only care about modified, created, or moved events
            if event.event_type not in ('modified', 'created', 'moved'):
                return

            # Cancel existing timer if any
            with self.lock:
                if self.reload_timer is not None:
                    self.reload_timer.cancel()

                # Start new timer for 500ms debounce
                self.reload_timer = threading.Timer(0.5, self.do_reload)
                self.reload_timer.start()

        def do_reload(self):
            """Perform the actual reload."""
            try:
                logger.info(f"{Fore.CYAN}File change detected, reloading...{Style.RESET_ALL}")

                # Call reload callback to get new definitions
                new_definitions = reload_callback()

                if new_definitions is not None:
                    # Rebuild engine with new definitions
                    old_engine = server.engine
                    server.engine = MockEngine(new_definitions, old_engine.requests_dir, old_engine.responses_dir)

                    logger.info(
                        f"{Fore.GREEN}Reload complete, loaded {len(new_definitions)} definitions{Style.RESET_ALL}"
                    )
                else:
                    logger.error(
                        f"{Fore.RED}Reload failed, keeping previous definitions{Style.RESET_ALL}"
                    )

            except Exception as e:
                logger.error(
                    f"{Fore.RED}Error during reload: {e}{Style.RESET_ALL}",
                    exc_info=logger.isEnabledFor(logging.DEBUG)
                )

    # Create event handler
    event_handler = ReloadHandler()

    # Create observer
    observer = Observer()

    # Watch endpoints file directory
    endpoints_path = Path(endpoints_file).resolve()
    if endpoints_path.exists():
        observer.schedule(event_handler, str(endpoints_path.parent), recursive=False)
        logger.debug(f"Watching endpoints file: {endpoints_path}")

    # Watch config file directory if specified
    if config_file:
        config_path = Path(config_file).resolve()
        if config_path.exists():
            observer.schedule(event_handler, str(config_path.parent), recursive=False)
            logger.debug(f"Watching config file: {config_path}")

    # Watch requests directory
    requests_path = Path(requests_dir).resolve()
    if requests_path.exists():
        observer.schedule(event_handler, str(requests_path), recursive=True)
        logger.debug(f"Watching requests directory: {requests_path}")

    # Watch responses directory
    responses_path = Path(responses_dir).resolve()
    if responses_path.exists():
        observer.schedule(event_handler, str(responses_path), recursive=True)
        logger.debug(f"Watching responses directory: {responses_path}")

    # Start observer
    observer.start()
    logger.info(f"{Fore.GREEN}Auto-reload enabled{Style.RESET_ALL}")

    return observer
