import unittest
import sys
import json
import re
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock
import io

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from server.handler import MockRequestHandler
from server.lifecycle import create_server
from core.models import MockDefinition, RequestDef, ResponseDef


class TestHealthCheckEndpoint(unittest.TestCase):
    def setUp(self):
        # Create a simple mock definition
        self.mock_def = MockDefinition(
            request=RequestDef(
                url_pattern="^/test$",
                url_regex=re.compile("^/test$")
            ),
            responses=[
                ResponseDef(status=200, body="OK")
            ]
        )

        # Create server
        self.server = create_server(
            definitions=[self.mock_def],
            base_dir="/tmp/test",
            host="127.0.0.1",
            port=0
        )
        self.server.reload_enabled = True  # For testing

    def tearDown(self):
        self.server.server_close()

    def create_handler(self, path='/_health'):
        """Helper to create a handler for health check."""
        request = MagicMock()
        request.makefile = Mock(side_effect=[
            io.BytesIO(b''),  # rfile
            io.BytesIO()  # wfile
        ])

        handler = MockRequestHandler(request, ('127.0.0.1', 12345), self.server)
        handler.command = 'GET'
        handler.path = path
        handler.request_version = 'HTTP/1.1'
        handler.headers = {}
        handler.rfile = io.BytesIO(b'')
        handler.wfile = io.BytesIO()

        return handler

    def test_health_check_returns_200(self):
        """Test that health check endpoint returns 200 OK."""
        handler = self.create_handler('/_health')
        handler.send_response = Mock()
        handler.add_cors_headers = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        handler.handle_health_check()

        handler.send_response.assert_called_once_with(200)

    def test_health_check_returns_json(self):
        """Test that health check returns JSON content type."""
        handler = self.create_handler('/_health')
        handler.send_response = Mock()
        handler.add_cors_headers = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        handler.handle_health_check()

        # Check Content-Type header
        calls = [str(call) for call in handler.send_header.call_args_list]
        self.assertTrue(any('application/json' in call for call in calls))

    def test_health_check_includes_cors_headers(self):
        """Test that CORS headers are added to health check."""
        handler = self.create_handler('/_health')
        handler.send_response = Mock()
        handler.add_cors_headers = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        handler.handle_health_check()

        handler.add_cors_headers.assert_called_once()

    def test_health_check_response_structure(self):
        """Test that health check response has correct structure."""
        handler = self.create_handler('/_health')

        # Capture wfile output
        wfile = io.BytesIO()
        handler.wfile = wfile
        handler.send_response = Mock()
        handler.add_cors_headers = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        handler.handle_health_check()

        # Parse response body
        response_body = wfile.getvalue().decode('utf-8')
        health_data = json.loads(response_body)

        # Verify structure
        self.assertIn('status', health_data)
        self.assertIn('version', health_data)
        self.assertIn('definitions_loaded', health_data)
        self.assertIn('uptime_seconds', health_data)
        self.assertIn('config_dir', health_data)
        self.assertIn('reload_enabled', health_data)
        self.assertIn('cors_enabled', health_data)

    def test_health_check_status_ok(self):
        """Test that health check status is 'ok'."""
        handler = self.create_handler('/_health')

        wfile = io.BytesIO()
        handler.wfile = wfile
        handler.send_response = Mock()
        handler.add_cors_headers = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        handler.handle_health_check()

        response_body = wfile.getvalue().decode('utf-8')
        health_data = json.loads(response_body)

        self.assertEqual(health_data['status'], 'ok')

    def test_health_check_definitions_count(self):
        """Test that health check reports correct number of definitions."""
        handler = self.create_handler('/_health')

        wfile = io.BytesIO()
        handler.wfile = wfile
        handler.send_response = Mock()
        handler.add_cors_headers = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        handler.handle_health_check()

        response_body = wfile.getvalue().decode('utf-8')
        health_data = json.loads(response_body)

        self.assertEqual(health_data['definitions_loaded'], 1)

    def test_health_check_uptime(self):
        """Test that health check reports uptime."""
        handler = self.create_handler('/_health')

        # Wait a bit to ensure uptime > 0
        time.sleep(0.1)

        wfile = io.BytesIO()
        handler.wfile = wfile
        handler.send_response = Mock()
        handler.add_cors_headers = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        handler.handle_health_check()

        response_body = wfile.getvalue().decode('utf-8')
        health_data = json.loads(response_body)

        self.assertGreaterEqual(health_data['uptime_seconds'], 0)
        self.assertIsInstance(health_data['uptime_seconds'], int)

    def test_health_check_reload_enabled(self):
        """Test that health check reports reload status."""
        handler = self.create_handler('/_health')

        wfile = io.BytesIO()
        handler.wfile = wfile
        handler.send_response = Mock()
        handler.add_cors_headers = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        handler.handle_health_check()

        response_body = wfile.getvalue().decode('utf-8')
        health_data = json.loads(response_body)

        self.assertTrue(health_data['reload_enabled'])

    def test_health_check_cors_enabled(self):
        """Test that health check reports CORS status."""
        handler = self.create_handler('/_health')

        wfile = io.BytesIO()
        handler.wfile = wfile
        handler.send_response = Mock()
        handler.add_cors_headers = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        handler.handle_health_check()

        response_body = wfile.getvalue().decode('utf-8')
        health_data = json.loads(response_body)

        self.assertTrue(health_data['cors_enabled'])

    def test_health_check_called_before_engine(self):
        """Test that health check is handled before engine processing."""
        handler = self.create_handler('/_health')
        handler.handle_health_check = Mock()

        # Call handle_mock_request which should check for /_health
        handler.handle_mock_request()

        # Should have called handle_health_check
        handler.handle_health_check.assert_called_once()

    def test_health_check_with_query_params(self):
        """Test that health check works with query parameters."""
        handler = self.create_handler('/_health?foo=bar')
        handler.handle_health_check = Mock()

        handler.handle_mock_request()

        # Should still handle as health check
        handler.handle_health_check.assert_called_once()

    def test_normal_request_not_treated_as_health(self):
        """Test that normal requests are not treated as health checks."""
        handler = self.create_handler('/test')
        handler.handle_health_check = Mock()
        handler.parse_http_request = Mock()
        handler.send_mock_response = Mock()

        # Mock the engine to avoid NoMatchError
        mock_engine = Mock()
        mock_engine.handle_request = Mock(return_value=(200, {}, "OK"))
        handler.server.engine = mock_engine

        handler.handle_mock_request()

        # Should NOT have called handle_health_check
        handler.handle_health_check.assert_not_called()


if __name__ == "__main__":
    unittest.main()
