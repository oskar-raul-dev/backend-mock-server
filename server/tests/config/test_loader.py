import unittest
import sys
import os
import tempfile
import logging
from pathlib import Path
from argparse import Namespace

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.args import get_default_config
from config.loader import load_config_file, merge_config


class TestGetDefaultConfig(unittest.TestCase):
    def test_returns_dict(self):
        config = get_default_config()
        self.assertIsInstance(config, dict)

    def test_has_server_section(self):
        config = get_default_config()
        self.assertIn('server', config)
        self.assertIsInstance(config['server'], dict)

    def test_has_logging_section(self):
        config = get_default_config()
        self.assertIn('logging', config)
        self.assertIsInstance(config['logging'], dict)

    def test_has_paths_section(self):
        config = get_default_config()
        self.assertIn('paths', config)
        self.assertIsInstance(config['paths'], dict)

    def test_has_custom_section(self):
        config = get_default_config()
        self.assertIn('custom', config)
        self.assertIsInstance(config['custom'], dict)

    def test_server_defaults(self):
        config = get_default_config()
        self.assertEqual(config['server']['port'], 9090)
        self.assertEqual(config['server']['host'], '0.0.0.0')
        self.assertTrue(config['server']['cors_enabled'])
        self.assertTrue(config['server']['reload'])

    def test_logging_defaults(self):
        config = get_default_config()
        self.assertEqual(config['logging']['level'], 'INFO')
        self.assertIn('format', config['logging'])
        self.assertIn('date_format', config['logging'])

    def test_paths_defaults(self):
        config = get_default_config()
        self.assertIsNone(config['paths']['requests_dir'])
        self.assertIsNone(config['paths']['responses_dir'])

    def test_custom_defaults(self):
        config = get_default_config()
        self.assertEqual(config['custom'], {})


class TestLoadConfigFile(unittest.TestCase):
    def setUp(self):
        # Configure logging for tests
        logging.basicConfig(level=logging.WARNING)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_nonexistent_file(self):
        config_path = os.path.join(self.temp_dir, 'nonexistent.py')

        with self.assertLogs(level='WARNING') as cm:
            result = load_config_file(config_path)

        self.assertIsNone(result)
        self.assertTrue(any('not found' in msg for msg in cm.output))

    def test_load_valid_config(self):
        config_path = os.path.join(self.temp_dir, 'config.py')

        with open(config_path, 'w') as f:
            f.write('''
CONFIG = {
    "server": {
        "port": 8080,
        "host": "127.0.0.1"
    },
    "logging": {
        "level": "DEBUG"
    }
}
''')

        with self.assertLogs(level='INFO') as cm:
            result = load_config_file(config_path)

        self.assertIsNotNone(result)
        self.assertEqual(result['server']['port'], 8080)
        self.assertEqual(result['server']['host'], '127.0.0.1')
        self.assertEqual(result['logging']['level'], 'DEBUG')
        self.assertTrue(any('Loaded configuration' in msg for msg in cm.output))

    def test_load_config_missing_CONFIG_dict(self):
        config_path = os.path.join(self.temp_dir, 'config.py')

        with open(config_path, 'w') as f:
            f.write('# Empty config file\n')

        with self.assertRaises(ValueError) as cm:
            load_config_file(config_path)

        self.assertIn('must define a CONFIG dictionary', str(cm.exception))

    def test_load_config_CONFIG_not_dict(self):
        config_path = os.path.join(self.temp_dir, 'config.py')

        with open(config_path, 'w') as f:
            f.write('CONFIG = "not a dict"\n')

        with self.assertRaises(ValueError) as cm:
            load_config_file(config_path)

        self.assertIn('must be a dictionary', str(cm.exception))

    def test_load_config_with_unknown_keys(self):
        config_path = os.path.join(self.temp_dir, 'config.py')

        with open(config_path, 'w') as f:
            f.write('''
CONFIG = {
    "server": {"port": 8080},
    "unknown_key": "value",
    "another_unknown": 123
}
''')

        with self.assertLogs(level='WARNING') as cm:
            result = load_config_file(config_path)

        self.assertIsNotNone(result)
        warning_messages = ' '.join(cm.output)
        self.assertIn('Unknown keys', warning_messages)
        self.assertIn('unknown_key', warning_messages)

    def test_load_config_invalid_server_section(self):
        config_path = os.path.join(self.temp_dir, 'config.py')

        with open(config_path, 'w') as f:
            f.write('CONFIG = {"server": "not a dict"}\n')

        with self.assertRaises(ValueError) as cm:
            load_config_file(config_path)

        self.assertIn('server', str(cm.exception))
        self.assertIn('must be a dictionary', str(cm.exception))

    def test_load_config_invalid_logging_section(self):
        config_path = os.path.join(self.temp_dir, 'config.py')

        with open(config_path, 'w') as f:
            f.write('CONFIG = {"logging": [1, 2, 3]}\n')

        with self.assertRaises(ValueError) as cm:
            load_config_file(config_path)

        self.assertIn('logging', str(cm.exception))
        self.assertIn('must be a dictionary', str(cm.exception))

    def test_load_config_invalid_paths_section(self):
        config_path = os.path.join(self.temp_dir, 'config.py')

        with open(config_path, 'w') as f:
            f.write('CONFIG = {"paths": 123}\n')

        with self.assertRaises(ValueError) as cm:
            load_config_file(config_path)

        self.assertIn('paths', str(cm.exception))
        self.assertIn('must be a dictionary', str(cm.exception))

    def test_load_config_with_syntax_error(self):
        config_path = os.path.join(self.temp_dir, 'config.py')

        with open(config_path, 'w') as f:
            f.write('CONFIG = {invalid python syntax')

        with self.assertRaises(Exception):
            load_config_file(config_path)

    def test_load_config_complete_structure(self):
        config_path = os.path.join(self.temp_dir, 'config.py')

        with open(config_path, 'w') as f:
            f.write('''
CONFIG = {
    "server": {
        "port": 8000,
        "host": "localhost",
        "cors_enabled": False,
        "reload": False
    },
    "logging": {
        "level": "ERROR",
        "format": "custom format",
        "date_format": "%H:%M:%S"
    },
    "paths": {
        "requests_dir": "custom_requests",
        "responses_dir": "custom_responses"
    },
    "custom": {
        "api_key": "secret",
        "timeout": 30
    }
}
''')

        result = load_config_file(config_path)

        self.assertEqual(result['server']['port'], 8000)
        self.assertEqual(result['server']['host'], 'localhost')
        self.assertFalse(result['server']['cors_enabled'])
        self.assertFalse(result['server']['reload'])

        self.assertEqual(result['logging']['level'], 'ERROR')
        self.assertEqual(result['logging']['format'], 'custom format')

        self.assertEqual(result['paths']['requests_dir'], 'custom_requests')
        self.assertEqual(result['paths']['responses_dir'], 'custom_responses')

        self.assertEqual(result['custom']['api_key'], 'secret')
        self.assertEqual(result['custom']['timeout'], 30)


class TestMergeConfig(unittest.TestCase):
    def test_merge_with_only_defaults(self):
        cli_args = Namespace(
            port=9090,
            host='0.0.0.0',
            cors=True,
            reload=True,
            log_level='INFO',
            requests_dir='requests',
            responses_dir='responses'
        )
        defaults = get_default_config()

        result = merge_config(cli_args, None, defaults)

        self.assertEqual(result['server']['port'], 9090)
        self.assertEqual(result['server']['host'], '0.0.0.0')
        self.assertTrue(result['server']['cors_enabled'])
        self.assertEqual(result['logging']['level'], 'INFO')

    def test_merge_config_file_overrides_defaults(self):
        cli_args = Namespace(
            port=9090,
            host='0.0.0.0',
            cors=True,
            reload=True,
            log_level='INFO',
            requests_dir='requests',
            responses_dir='responses'
        )
        defaults = get_default_config()
        config_file = {
            "server": {"port": 8080, "host": "127.0.0.1"},
            "logging": {"level": "DEBUG"}
        }

        result = merge_config(cli_args, config_file, defaults)

        # CLI args still override
        self.assertEqual(result['server']['port'], 9090)
        self.assertEqual(result['server']['host'], '0.0.0.0')
        self.assertEqual(result['logging']['level'], 'INFO')

    def test_merge_cli_overrides_config_file(self):
        cli_args = Namespace(
            port=7070,
            host='localhost',
            cors=False,
            reload=False,
            log_level='ERROR',
            requests_dir='custom_req',
            responses_dir='custom_resp'
        )
        defaults = get_default_config()
        config_file = {
            "server": {"port": 8080, "host": "127.0.0.1"},
            "logging": {"level": "DEBUG"}
        }

        result = merge_config(cli_args, config_file, defaults)

        # CLI args have highest priority
        self.assertEqual(result['server']['port'], 7070)
        self.assertEqual(result['server']['host'], 'localhost')
        self.assertFalse(result['server']['cors_enabled'])
        self.assertFalse(result['server']['reload'])
        self.assertEqual(result['logging']['level'], 'ERROR')

    def test_merge_preserves_config_file_custom_section(self):
        cli_args = Namespace(
            port=9090,
            host='0.0.0.0',
            cors=True,
            reload=True,
            log_level='INFO',
            requests_dir='requests',
            responses_dir='responses'
        )
        defaults = get_default_config()
        config_file = {
            "custom": {
                "api_key": "secret123",
                "timeout": 60
            }
        }

        result = merge_config(cli_args, config_file, defaults)

        self.assertEqual(result['custom']['api_key'], 'secret123')
        self.assertEqual(result['custom']['timeout'], 60)

    def test_merge_preserves_logging_format_from_config(self):
        cli_args = Namespace(
            port=9090,
            host='0.0.0.0',
            cors=True,
            reload=True,
            log_level='DEBUG',  # Override level
            requests_dir='requests',
            responses_dir='responses'
        )
        defaults = get_default_config()
        config_file = {
            "logging": {
                "format": "CUSTOM: %(message)s",
                "date_format": "%H:%M"
            }
        }

        result = merge_config(cli_args, config_file, defaults)

        # CLI overrides level
        self.assertEqual(result['logging']['level'], 'DEBUG')
        # Config file values preserved for format
        self.assertEqual(result['logging']['format'], 'CUSTOM: %(message)s')
        self.assertEqual(result['logging']['date_format'], '%H:%M')

    def test_merge_paths_from_config_file(self):
        cli_args = Namespace(
            port=9090,
            host='0.0.0.0',
            cors=True,
            reload=True,
            log_level='INFO',
            requests_dir='requests',  # Default
            responses_dir='responses'  # Default
        )
        defaults = get_default_config()
        config_file = {
            "paths": {
                "requests_dir": "config_requests",
                "responses_dir": "config_responses"
            }
        }

        result = merge_config(cli_args, config_file, defaults)

        # Since CLI has defaults, config file paths should be preserved
        self.assertEqual(result['paths']['requests_dir'], 'config_requests')
        self.assertEqual(result['paths']['responses_dir'], 'config_responses')

    def test_merge_does_not_mutate_inputs(self):
        cli_args = Namespace(
            port=7070,
            host='localhost',
            cors=False,
            reload=False,
            log_level='ERROR',
            requests_dir='req',
            responses_dir='resp'
        )
        defaults = get_default_config()
        original_defaults = get_default_config()

        merge_config(cli_args, None, defaults)

        # Defaults should not be mutated
        self.assertEqual(defaults, original_defaults)


if __name__ == "__main__":
    unittest.main()
