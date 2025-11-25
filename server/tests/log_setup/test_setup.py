import logging
import unittest
import sys
from pathlib import Path
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from log_setup.setup import setup_logging, setup_bootstrap_logging, ColoredFormatter
from main import VERSION


class TestSetupBootstrapLogging(unittest.TestCase):
    def tearDown(self):
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.NOTSET)

    def test_setup_bootstrap_logging_creates_handler(self):
        setup_bootstrap_logging()
        logger = logging.getLogger()
        self.assertEqual(len(logger.handlers), 1)
        self.assertIsInstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_bootstrap_logging_sets_info_level(self):
        setup_bootstrap_logging()
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.INFO)

    def test_setup_bootstrap_logging_uses_simple_formatter(self):
        setup_bootstrap_logging()
        logger = logging.getLogger()
        handler = logger.handlers[0]
        self.assertIsInstance(handler.formatter, logging.Formatter)
        self.assertNotIsInstance(handler.formatter, ColoredFormatter)

    def test_setup_bootstrap_logging_clears_handlers(self):
        logger = logging.getLogger()
        logger.addHandler(logging.StreamHandler())
        self.assertEqual(len(logger.handlers), 1)

        setup_bootstrap_logging()
        self.assertEqual(len(logger.handlers), 1)

    def test_bootstrap_logging_works_for_error_logging(self):
        setup_bootstrap_logging()

        try:
            logging.info("Testing bootstrap logging")
            logging.error("This is an error during config loading")
        except Exception as e:
            self.fail(f"Bootstrap logging should not raise exception: {e}")


class TestSetupLogging(unittest.TestCase):
    def tearDown(self):
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.NOTSET)

    def test_setup_logging_default_level(self):
        setup_logging()
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.INFO)

    def test_setup_logging_debug_level(self):
        setup_logging("DEBUG")
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.DEBUG)

    def test_setup_logging_error_level(self):
        setup_logging("ERROR")
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.ERROR)

    def test_setup_logging_case_insensitive(self):
        setup_logging("info")
        logger = logging.getLogger()
        self.assertEqual(logger.level, logging.INFO)

        setup_logging("DeBuG")
        self.assertEqual(logger.level, logging.DEBUG)

    def test_setup_logging_invalid_level_raises_error(self):
        with self.assertRaises(ValueError) as cm:
            setup_logging("INVALID")

        self.assertIn("Invalid log level", str(cm.exception))

    def test_setup_logging_creates_handler(self):
        setup_logging()
        logger = logging.getLogger()
        self.assertEqual(len(logger.handlers), 1)
        self.assertIsInstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_logging_clears_existing_handlers(self):
        logger = logging.getLogger()
        logger.addHandler(logging.StreamHandler())
        logger.addHandler(logging.StreamHandler())
        self.assertEqual(len(logger.handlers), 2)

        setup_logging()
        self.assertEqual(len(logger.handlers), 1)

    def test_setup_logging_configures_formatter(self):
        setup_logging()
        logger = logging.getLogger()
        handler = logger.handlers[0]
        self.assertIsInstance(handler.formatter, ColoredFormatter)

    def test_setup_logging_configures_dependency_levels(self):
        setup_logging("DEBUG")

        jinja2_logger = logging.getLogger("jinja2")
        urllib3_logger = logging.getLogger("urllib3")
        watchdog_logger = logging.getLogger("watchdog")

        self.assertEqual(jinja2_logger.level, logging.WARNING)
        self.assertEqual(urllib3_logger.level, logging.WARNING)
        self.assertEqual(watchdog_logger.level, logging.WARNING)

    def test_setup_logging_with_log_config(self):
        log_config = {
            "format": "%(levelname)s - %(message)s",
            "date_format": "%H:%M:%S"
        }
        setup_logging("INFO", log_config)
        logger = logging.getLogger()
        handler = logger.handlers[0]
        self.assertIsInstance(handler.formatter, ColoredFormatter)

    def test_setup_logging_without_log_config_uses_defaults(self):
        setup_logging("INFO", None)
        logger = logging.getLogger()
        self.assertEqual(len(logger.handlers), 1)
        handler = logger.handlers[0]
        self.assertIsInstance(handler.formatter, ColoredFormatter)

    def test_setup_logging_replaces_bootstrap_logging(self):
        setup_bootstrap_logging()
        logger = logging.getLogger()
        self.assertEqual(len(logger.handlers), 1)
        bootstrap_handler = logger.handlers[0]
        self.assertNotIsInstance(bootstrap_handler.formatter, ColoredFormatter)

        setup_logging("DEBUG")
        self.assertEqual(len(logger.handlers), 1)
        full_handler = logger.handlers[0]
        self.assertIsInstance(full_handler.formatter, ColoredFormatter)
        self.assertEqual(logger.level, logging.DEBUG)


class TestColoredFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = ColoredFormatter(
            fmt='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def test_format_debug_message(self):
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="Debug message",
            args=(),
            exc_info=None
        )
        formatted = self.formatter.format(record)
        self.assertIn("Debug message", formatted)
        self.assertIn("[", formatted)
        self.assertIn("]", formatted)

    def test_format_info_message(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Info message",
            args=(),
            exc_info=None
        )
        formatted = self.formatter.format(record)
        self.assertIn("Info message", formatted)

    def test_format_warning_message(self):
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="Warning message",
            args=(),
            exc_info=None
        )
        formatted = self.formatter.format(record)
        self.assertIn("Warning message", formatted)

    def test_format_error_message(self):
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Error message",
            args=(),
            exc_info=None
        )
        formatted = self.formatter.format(record)
        self.assertIn("Error message", formatted)

    def test_format_critical_message(self):
        record = logging.LogRecord(
            name="test",
            level=logging.CRITICAL,
            pathname="",
            lineno=0,
            msg="Critical message",
            args=(),
            exc_info=None
        )
        formatted = self.formatter.format(record)
        self.assertIn("Critical message", formatted)

    def test_timestamp_format(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None
        )
        formatted = self.formatter.format(record)

        import re
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        self.assertIsNotNone(re.search(timestamp_pattern, formatted))

    def test_colors_applied_to_levelname(self):
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Error message",
            args=(),
            exc_info=None
        )
        formatted = self.formatter.format(record)

        from colorama import Fore, Style
        self.assertIn(Fore.RED, formatted)
        self.assertIn(Style.RESET_ALL, formatted)


class TestLoggingIntegration(unittest.TestCase):
    def setUp(self):
        self.log_stream = StringIO()

    def tearDown(self):
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.NOTSET)

    def test_log_filtering_info_level(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(self.log_stream)
        handler.setLevel(logging.INFO)

        formatter = ColoredFormatter(
            fmt='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        output = self.log_stream.getvalue()

        self.assertNotIn("Debug message", output)
        self.assertIn("Info message", output)
        self.assertIn("Warning message", output)
        self.assertIn("Error message", output)

    def test_log_filtering_error_level(self):
        logger = logging.getLogger()
        logger.setLevel(logging.ERROR)

        handler = logging.StreamHandler(self.log_stream)
        handler.setLevel(logging.ERROR)

        formatter = ColoredFormatter(
            fmt='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        output = self.log_stream.getvalue()

        self.assertNotIn("Debug message", output)
        self.assertNotIn("Info message", output)
        self.assertNotIn("Warning message", output)
        self.assertIn("Error message", output)

    def test_log_filtering_debug_level(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(self.log_stream)
        handler.setLevel(logging.DEBUG)

        formatter = ColoredFormatter(
            fmt='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.debug("Debug message")
        logger.info("Info message")

        output = self.log_stream.getvalue()

        self.assertIn("Debug message", output)
        self.assertIn("Info message", output)


class TestVersionConstant(unittest.TestCase):
    def test_version_is_string(self):
        self.assertIsInstance(VERSION, str)

    def test_version_format(self):
        import re
        version_pattern = r'^\d+\.\d+\.\d+$'
        self.assertIsNotNone(re.match(version_pattern, VERSION))


if __name__ == "__main__":
    unittest.main()
