import unittest
import sys
import re
import io
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from http.server import HTTPServer

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from server.handler import MockRequestHandler
from core.engine import MockEngine
from core.models import MockDefinition, RequestDef, ResponseDef, HTTPRequest
from core.exceptions import NoMatchError


class TestMockRequestHandler(unittest.TestCase):
    def setUp(self):
        # Configure logging for tests
        logging.basicConfig(level=logging.WARNING)

        # Create a simple mock definition
        self.mock_def = MockDefinition(
            request=RequestDef(
                url_pattern="^/test$",
                url_regex=re.compile("^/test$")
            ),
            responses=[
                ResponseDef(
                    status=200,
                    headers={"Content-Type": "text/plain"},
                    body="Test response"
                )
            ]
        )

        # Create mock engine
        self.engine = MockEngine([self.mock_def], ".")

        # Create mock server
        self.server = Mock(spec=HTTPServer)
        self.server.engine = self.engine
        self.server.cors_enabled = True
        self.server.cors_origins = '*'
        self.server.server_address = ('localhost', 9090)

    def create_handler(self, method='GET', path='/', headers=None, body=b''):
        """Helper to create a handler with mocked request/response."""
        if headers is None:
            headers = {}

        # Create mock request
        request = MagicMock()
        request.makefile = Mock(side_effect=[
            io.BytesIO(body),  # rfile
            io.BytesIO()  # wfile
        ])

        # Create handler
        handler = MockRequestHandler(request, ('127.0.0.1', 12345), self.server)

        # Set up handler attributes
        handler.command = method
        handler.path = path
        handler.request_version = 'HTTP/1.1'
        handler.headers = MockHTTPMessage(headers)
        handler.rfile = io.BytesIO(body)
        handler.wfile = io.BytesIO()

        return handler

    def test_log_message_disabled(self):
        """Test that default HTTP logging is disabled."""
        handler = self.create_handler()
        # Should not raise or log anything
        handler.log_message("test %s", "message")

    def test_add_cors_headers_when_enabled(self):
        """Test CORS headers are added when enabled."""
        handler = self.create_handler()
        handler.send_header = Mock()

        handler.add_cors_headers()

        calls = [str(call) for call in handler.send_header.call_args_list]
        self.assertTrue(any('Access-Control-Allow-Origin' in call for call in calls))
        self.assertTrue(any('Access-Control-Allow-Methods' in call for call in calls))
        self.assertTrue(any('Access-Control-Allow-Headers' in call for call in calls))

    def test_add_cors_headers_when_disabled(self):
        """Test CORS headers are not added when disabled."""
        self.server.cors_enabled = False
        handler = self.create_handler()
        handler.send_header = Mock()

        handler.add_cors_headers()

        handler.send_header.assert_not_called()

    def test_do_OPTIONS(self):
        """Test OPTIONS request for CORS preflight."""
        handler = self.create_handler(method='OPTIONS')
        handler.send_response = Mock()
        handler.add_cors_headers = Mock()
        handler.end_headers = Mock()

        handler.do_OPTIONS()

        handler.send_response.assert_called_once_with(200)
        handler.add_cors_headers.assert_called_once()
        handler.end_headers.assert_called_once()

    def test_do_GET_calls_handle_mock_request(self):
        """Test GET method calls handle_mock_request."""
        handler = self.create_handler(method='GET')
        handler.handle_mock_request = Mock()

        handler.do_GET()

        handler.handle_mock_request.assert_called_once()

    def test_do_POST_calls_handle_mock_request(self):
        """Test POST method calls handle_mock_request."""
        handler = self.create_handler(method='POST')
        handler.handle_mock_request = Mock()

        handler.do_POST()

        handler.handle_mock_request.assert_called_once()

    def test_do_PUT_calls_handle_mock_request(self):
        """Test PUT method calls handle_mock_request."""
        handler = self.create_handler(method='PUT')
        handler.handle_mock_request = Mock()

        handler.do_PUT()

        handler.handle_mock_request.assert_called_once()

    def test_do_DELETE_calls_handle_mock_request(self):
        """Test DELETE method calls handle_mock_request."""
        handler = self.create_handler(method='DELETE')
        handler.handle_mock_request = Mock()

        handler.do_DELETE()

        handler.handle_mock_request.assert_called_once()

    def test_do_PATCH_calls_handle_mock_request(self):
        """Test PATCH method calls handle_mock_request."""
        handler = self.create_handler(method='PATCH')
        handler.handle_mock_request = Mock()

        handler.do_PATCH()

        handler.handle_mock_request.assert_called_once()

    def test_parse_http_request_simple(self):
        """Test parsing simple GET request."""
        handler = self.create_handler(
            method='GET',
            path='/test',
            headers={'Host': 'localhost:9090'}
        )

        result = handler.parse_http_request()

        self.assertEqual(result.method, 'GET')
        self.assertEqual(result.url, 'http://localhost:9090/test')
        self.assertEqual(result.body, '')
        self.assertEqual(result.query_params, {})

    def test_parse_http_request_with_body(self):
        """Test parsing request with body."""
        body = b'{"key": "value"}'
        handler = self.create_handler(
            method='POST',
            path='/api/test',
            headers={'Content-Length': str(len(body))},
            body=body
        )

        result = handler.parse_http_request()

        self.assertEqual(result.body, '{"key": "value"}')

    def test_parse_http_request_with_query_params(self):
        """Test parsing request with query parameters."""
        handler = self.create_handler(
            method='GET',
            path='/test?foo=bar&baz=qux'
        )

        result = handler.parse_http_request()

        self.assertEqual(result.query_params['foo'], 'bar')
        self.assertEqual(result.query_params['baz'], 'qux')

    def test_parse_http_request_with_multiple_query_values(self):
        """Test parsing request with multiple values for same parameter."""
        handler = self.create_handler(
            method='GET',
            path='/test?item=a&item=b&item=c'
        )

        result = handler.parse_http_request()

        self.assertIsInstance(result.query_params['item'], list)
        self.assertEqual(result.query_params['item'], ['a', 'b', 'c'])

    def test_parse_http_request_headers(self):
        """Test parsing request headers."""
        handler = self.create_handler(
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer token123'
            }
        )

        result = handler.parse_http_request()

        self.assertEqual(result.headers['Content-Type'], 'application/json')
        self.assertEqual(result.headers['Authorization'], 'Bearer token123')

    def test_send_mock_response(self):
        """Test sending mock response."""
        handler = self.create_handler()
        handler.send_response = Mock()
        handler.add_cors_headers = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        handler.send_mock_response(
            200,
            {'Content-Type': 'application/json'},
            '{"status": "ok"}'
        )

        handler.send_response.assert_called_once_with(200)
        handler.add_cors_headers.assert_called_once()

        # Check Content-Type header was sent
        calls = [str(call) for call in handler.send_header.call_args_list]
        self.assertTrue(any('Content-Type' in call for call in calls))

    def test_handle_mock_request_success(self):
        """Test successful request handling."""
        handler = self.create_handler(
            method='GET',
            path='/test',
            headers={'Host': 'localhost:9090'}
        )
        handler.send_mock_response = Mock()

        with self.assertLogs(level='INFO') as cm:
            handler.handle_mock_request()

        # Check logging
        self.assertTrue(any('GET /test' in msg for msg in cm.output))
        self.assertTrue(any('200' in msg for msg in cm.output))

        # Check response was sent
        handler.send_mock_response.assert_called_once()
        args = handler.send_mock_response.call_args[0]
        self.assertEqual(args[0], 200)  # status
        self.assertEqual(args[2], "Test response")  # body

    def test_handle_mock_request_no_match(self):
        """Test request handling when no mock matches."""
        handler = self.create_handler(
            method='GET',
            path='/nonexistent',
            headers={'Host': 'localhost:9090'}
        )
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        with self.assertLogs(level='ERROR') as cm:
            handler.handle_mock_request()

        # Check error logging
        self.assertTrue(any('No mock definition matched' in msg for msg in cm.output))

        # Check 404 response
        handler.send_response.assert_called_once_with(404)

    def test_handle_mock_request_internal_error(self):
        """Test request handling when internal error occurs."""
        # Make engine raise an exception
        self.server.engine = Mock()
        self.server.engine.handle_request.side_effect = RuntimeError("Test error")

        handler = self.create_handler(
            method='GET',
            path='/test',
            headers={'Host': 'localhost:9090'}
        )
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        with self.assertLogs(level='ERROR') as cm:
            handler.handle_mock_request()

        # Check error logging
        self.assertTrue(any('Error handling request' in msg for msg in cm.output))

        # Check 500 response
        handler.send_response.assert_called_once_with(500)


class MockHTTPMessage(dict):
    """Mock HTTPMessage that behaves like headers."""

    def get(self, key, default=None):
        return super().get(key, default)


if __name__ == "__main__":
    unittest.main()
