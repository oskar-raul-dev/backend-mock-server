import unittest
import sys
import socket
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.args import parse_args
from server.utils import is_port_available
# VERSION = "1.0.0"  # Moved to main.py


class TestIsPortAvailable(unittest.TestCase):
    def test_port_available_on_localhost(self):
        # Find an available port by binding to port 0
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            _, port = s.getsockname()

        # Port should be available after socket is closed
        self.assertTrue(is_port_available('localhost', port))

    def test_port_not_available(self):
        # Bind to a port and keep it bound
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            _, port = s.getsockname()

            # Port should not be available while socket is bound
            self.assertFalse(is_port_available('localhost', port))

    def test_port_available_on_any_interface(self):
        # Find an available port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', 0))
            _, port = s.getsockname()

        # Port should be available after socket is closed
        self.assertTrue(is_port_available('0.0.0.0', port))

    def test_invalid_host(self):
        # Invalid host should return False
        self.assertFalse(is_port_available('invalid.host.name', 9090))


class TestParseArgs(unittest.TestCase):
    def setUp(self):
        # Save original sys.argv
        self.original_argv = sys.argv.copy()

    def tearDown(self):
        # Restore original sys.argv
        sys.argv = self.original_argv

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_defaults(self, mock_port):
        sys.argv = ['server.py']
        args = parse_args()

        self.assertEqual(args.config_dir, 'config')
        self.assertEqual(args.port, 9090)
        self.assertEqual(args.host, '0.0.0.0')
        self.assertEqual(args.log_level, 'INFO')
        self.assertEqual(args.requests_dir, 'requests')
        self.assertEqual(args.responses_dir, 'responses')
        self.assertEqual(args.endpoints_file, 'endpoints.py')
        self.assertEqual(args.config_file, 'config.py')
        self.assertTrue(args.reload)
        self.assertTrue(args.cors)

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_custom_port(self, mock_port):
        sys.argv = ['server.py', '--port', '8080']
        args = parse_args()

        self.assertEqual(args.port, 8080)
        mock_port.assert_called_once_with('0.0.0.0', 8080)

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_custom_host(self, mock_port):
        sys.argv = ['server.py', '--host', 'localhost']
        args = parse_args()

        self.assertEqual(args.host, 'localhost')
        mock_port.assert_called_once_with('localhost', 9090)

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_custom_log_level(self, mock_port):
        sys.argv = ['server.py', '--log-level', 'DEBUG']
        args = parse_args()

        self.assertEqual(args.log_level, 'DEBUG')

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_all_log_levels(self, mock_port):
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            with self.subTest(level=level):
                sys.argv = ['server.py', '--log-level', level]
                args = parse_args()
                self.assertEqual(args.log_level, level)

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_custom_config_dir(self, mock_port):
        sys.argv = ['server.py', '--config-dir', '/custom/path']
        args = parse_args()

        self.assertEqual(args.config_dir, '/custom/path')

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_custom_requests_dir(self, mock_port):
        sys.argv = ['server.py', '--requests-dir', 'custom_requests']
        args = parse_args()

        self.assertEqual(args.requests_dir, 'custom_requests')

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_custom_responses_dir(self, mock_port):
        sys.argv = ['server.py', '--responses-dir', 'custom_responses']
        args = parse_args()

        self.assertEqual(args.responses_dir, 'custom_responses')

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_custom_endpoints_file(self, mock_port):
        sys.argv = ['server.py', '--endpoints-file', 'my_endpoints.py']
        args = parse_args()

        self.assertEqual(args.endpoints_file, 'my_endpoints.py')

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_custom_config_file(self, mock_port):
        sys.argv = ['server.py', '--config-file', 'my_config.py']
        args = parse_args()

        self.assertEqual(args.config_file, 'my_config.py')

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_no_reload(self, mock_port):
        sys.argv = ['server.py', '--no-reload']
        args = parse_args()

        self.assertFalse(args.reload)

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_reload_explicit(self, mock_port):
        sys.argv = ['server.py', '--reload']
        args = parse_args()

        self.assertTrue(args.reload)

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_no_cors(self, mock_port):
        sys.argv = ['server.py', '--no-cors']
        args = parse_args()

        self.assertFalse(args.cors)

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_cors_explicit(self, mock_port):
        sys.argv = ['server.py', '--cors']
        args = parse_args()

        self.assertTrue(args.cors)

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_combined(self, mock_port):
        sys.argv = [
            'server.py',
            '--config-dir', '/my/config',
            '--port', '8000',
            '--host', '127.0.0.1',
            '--log-level', 'ERROR',
            '--requests-dir', 'req',
            '--responses-dir', 'resp',
            '--endpoints-file', 'ep.py',
            '--config-file', 'cf.py',
            '--no-reload',
            '--no-cors'
        ]
        args = parse_args()

        self.assertEqual(args.config_dir, '/my/config')
        self.assertEqual(args.port, 8000)
        self.assertEqual(args.host, '127.0.0.1')
        self.assertEqual(args.log_level, 'ERROR')
        self.assertEqual(args.requests_dir, 'req')
        self.assertEqual(args.responses_dir, 'resp')
        self.assertEqual(args.endpoints_file, 'ep.py')
        self.assertEqual(args.config_file, 'cf.py')
        self.assertFalse(args.reload)
        self.assertFalse(args.cors)

    @patch('cli.args.is_port_available', return_value=False)
    def test_parse_args_port_not_available(self, mock_port):
        sys.argv = ['server.py', '--port', '8080']

        with self.assertRaises(SystemExit) as cm:
            parse_args()

        self.assertEqual(cm.exception.code, 2)

    @patch('cli.args.is_port_available', return_value=True)
    def test_parse_args_invalid_log_level(self, mock_port):
        sys.argv = ['server.py', '--log-level', 'INVALID']

        with self.assertRaises(SystemExit) as cm:
            parse_args()

        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
