"""
Logging configuration and setup for the mockserver.

This module provides two-phase logging setup for the mockserver:

1. Bootstrap Logging (setup_bootstrap_logging):
   - Basic logging for early startup phase
   - Used before config files are loaded
   - Always INFO level with simple format
   - No colors for compatibility

2. Full Logging (setup_logging):
   - Complete logging with ANSI color support
   - Used after config loading
   - Configurable level and format
   - ColoredFormatter for readable terminal output

The two-phase approach ensures we can log errors during config loading while
still allowing full configuration flexibility once the config is loaded.

ANSI Color Scheme:
    DEBUG: Dim white
    INFO: Normal white
    WARNING: Yellow
    ERROR: Red
    CRITICAL: Bright red

Third-party Library Noise Reduction:
    The setup_logging() function automatically reduces log noise from:
    - jinja2: Set to WARNING
    - urllib3: Set to WARNING
    - watchdog: Set to WARNING
"""
import logging
import sys
from typing import Optional, Dict
from colorama import Fore, Style, init as colorama_init


class ColoredFormatter(logging.Formatter):
    """
    Custom logging formatter with ANSI color codes for terminal output.

    This formatter extends Python's logging.Formatter to add color to log level
    names based on severity. Colors are applied using colorama for cross-platform
    compatibility (Windows, Linux, macOS).

    The formatter preserves all standard logging.Formatter functionality while
    adding color only to the levelname field (DEBUG, INFO, WARNING, etc.).

    Color Mapping:
        DEBUG: Dim white (subtle, for detailed debugging)
        INFO: Normal white (standard output)
        WARNING: Yellow (attention needed)
        ERROR: Red (error occurred)
        CRITICAL: Bright red (urgent issue)

    Usage:
        >>> formatter = ColoredFormatter(
        ...     fmt='%(asctime)s [%(levelname)s] %(message)s',
        ...     datefmt='%Y-%m-%d %H:%M:%S'
        ... )
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(formatter)
        >>> logger = logging.getLogger()
        >>> logger.addHandler(handler)
        >>> logger.warning("This will be yellow")

    Note:
        The colors are ANSI escape sequences that work in most modern terminals.
        On Windows, colorama translates these to Windows console API calls.
    """

    COLORS = {
        'DEBUG': Style.DIM + Fore.WHITE,
        'INFO': Style.NORMAL + Fore.WHITE,
        'WARNING': Style.NORMAL + Fore.YELLOW,
        'ERROR': Style.NORMAL + Fore.RED,
        'CRITICAL': Style.BRIGHT + Fore.RED
    }

    RESET = Style.RESET_ALL

    def format(self, record):
        """
        Format log record with colored level name.

        Applies ANSI color codes to the levelname field before formatting.
        The color is chosen based on the log level severity.

        Args:
            record: LogRecord instance to format

        Returns:
            Formatted log message string with colored level name

        Example:
            >>> formatter = ColoredFormatter(fmt='[%(levelname)s] %(message)s')
            >>> record = logging.LogRecord(
            ...     name='test', level=logging.WARNING, pathname='', lineno=0,
            ...     msg='Test message', args=(), exc_info=None
            ... )
            >>> formatted = formatter.format(record)
            >>> 'WARNING' in formatted  # Color codes added
            True
        """
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_bootstrap_logging():
    """
    Setup basic logging for the early startup phase.

    This function configures minimal logging before any configuration files are
    loaded. It's called at the very beginning of main.py to ensure we can log
    errors that occur during config file loading and parsing.

    Bootstrap Configuration:
        - Level: INFO (hardcoded)
        - Format: '%(asctime)s [%(levelname)s] %(message)s'
        - Date format: '%Y-%m-%d %H:%M:%S'
        - Output: stdout (not stderr)
        - Colors: No (simple formatter for compatibility)

    The configuration is intentionally simple and doesn't rely on any user
    configuration files, ensuring reliable logging even if config loading fails.

    This logging setup is replaced by setup_logging() once the configuration
    is loaded successfully.

    Example:
        >>> # In main.py startup sequence:
        >>> setup_bootstrap_logging()
        >>> logger = logging.getLogger()
        >>> logger.info("Loading configuration...")
        >>> # Config loading happens here
        >>> # Then setup_logging() is called to reconfigure
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)


def setup_logging(log_level: str = "INFO", log_config: Optional[Dict] = None):
    """
    Configure full production logging with ANSI colors and custom format.

    This function is called AFTER configuration files are loaded and replaces
    the bootstrap logging with a fully-configured logging system. It supports:
        - Configurable log levels
        - Custom format strings from config
        - ANSI color-coded output via ColoredFormatter
        - Third-party library noise reduction

    The function initializes colorama for cross-platform ANSI support and
    configures the root logger with a StreamHandler using ColoredFormatter.

    Full Configuration:
        - Level: Configurable via log_level parameter
        - Format: From log_config or default
        - Date format: From log_config or default
        - Output: stdout (not stderr)
        - Colors: Yes (via ColoredFormatter)
        - Third-party loggers: Reduced to WARNING

    Third-party Noise Reduction:
        To keep logs clean, the following loggers are set to WARNING:
        - jinja2: Template rendering details
        - urllib3: HTTP request details
        - watchdog: File watching events

    Args:
        log_level: Logging level as string. Must be one of:
                  DEBUG, INFO, WARNING, ERROR, CRITICAL
                  Case-insensitive. Default: INFO
        log_config: Optional configuration dict from config.py with keys:
                   - 'format': Log format string (default: '%(asctime)s [%(levelname)s] %(message)s')
                   - 'date_format': Date format string (default: '%Y-%m-%d %H:%M:%S')

    Raises:
        ValueError: If log_level is not a valid Python logging level name

    Example (basic usage):
        >>> setup_logging("DEBUG")
        >>> logger = logging.getLogger()
        >>> logger.debug("This will appear")  # DEBUG level enabled

    Example (with custom config):
        >>> log_config = {
        ...     'format': '[%(levelname)s] %(name)s: %(message)s',
        ...     'date_format': '%H:%M:%S'
        ... }
        >>> setup_logging("INFO", log_config)
        >>> logger = logging.getLogger()
        >>> logger.info("Custom format")

    Example (invalid level):
        >>> setup_logging("INVALID")
        Traceback (most recent call last):
            ...
        ValueError: Invalid log level: INVALID
    """
    colorama_init(autoreset=True)

    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    log_format = '%(asctime)s [%(levelname)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    if log_config:
        log_format = log_config.get('format', log_format)
        date_format = log_config.get('date_format', date_format)

    formatter = ColoredFormatter(
        fmt=log_format,
        datefmt=date_format
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger('jinja2').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('watchdog').setLevel(logging.WARNING)
