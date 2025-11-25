import unittest
import sys
import re
import socket
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from server.lifecycle import create_server
from core.models import MockDefinition, RequestDef, ResponseDef


class TestCreateServer(unittest.TestCase):
    def setUp(self):
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

    def test_create_server_returns_httpserver(self):
        """Test that create_server returns an HTTPServer instance."""
        import http.server

        server = create_server(
            definitions=[self.mock_def],
            base_dir=".",
            host="127.0.0.1",
            port=0  # Use port 0 to get a random available port
        )

        try:
            self.assertIsInstance(server, http.server.HTTPServer)
        finally:
            server.server_close()

    def test_create_server_injects_engine(self):
        """Test that engine is injected into server."""
        server = create_server(
            definitions=[self.mock_def],
            base_dir=".",
            host="127.0.0.1",
            port=0
        )

        try:
            self.assertTrue(hasattr(server, 'engine'))
            self.assertIsNotNone(server.engine)
        finally:
            server.server_close()

    def test_create_server_injects_cors_config(self):
        """Test that CORS configuration is injected."""
        server = create_server(
            definitions=[self.mock_def],
            base_dir=".",
            host="127.0.0.1",
            port=0,
            cors_enabled=True,
            cors_origins="https://example.com"
        )

        try:
            self.assertTrue(hasattr(server, 'cors_enabled'))
            self.assertTrue(server.cors_enabled)
            self.assertEqual(server.cors_origins, "https://example.com")
        finally:
            server.server_close()

    def test_create_server_cors_disabled(self):
        """Test that CORS can be disabled."""
        server = create_server(
            definitions=[self.mock_def],
            base_dir=".",
            host="127.0.0.1",
            port=0,
            cors_enabled=False
        )

        try:
            self.assertFalse(server.cors_enabled)
        finally:
            server.server_close()

    def test_create_server_injects_log_level(self):
        """Test that log level is injected."""
        server = create_server(
            definitions=[self.mock_def],
            base_dir=".",
            host="127.0.0.1",
            port=0,
            log_level="DEBUG"
        )

        try:
            self.assertTrue(hasattr(server, 'log_level'))
            self.assertEqual(server.log_level, "DEBUG")
        finally:
            server.server_close()

    def test_create_server_socket_reuse_addr(self):
        """Test that SO_REUSEADDR is set on socket."""
        server = create_server(
            definitions=[self.mock_def],
            base_dir=".",
            host="127.0.0.1",
            port=0
        )

        try:
            # Get socket option value (platform-dependent: 1 on Linux, 4 on macOS)
            reuse_addr = server.socket.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
            self.assertTrue(reuse_addr)  # Non-zero means enabled
        finally:
            server.server_close()

    def test_create_server_sets_timeout(self):
        """Test that server timeout is set."""
        server = create_server(
            definitions=[self.mock_def],
            base_dir=".",
            host="127.0.0.1",
            port=0
        )

        try:
            self.assertEqual(server.timeout, 60)
        finally:
            server.server_close()

    def test_create_server_with_multiple_definitions(self):
        """Test creating server with multiple definitions."""
        mock_def2 = MockDefinition(
            request=RequestDef(
                url_pattern="^/api$",
                url_regex=re.compile("^/api$")
            ),
            responses=[
                ResponseDef(status=200, body="API")
            ]
        )

        server = create_server(
            definitions=[self.mock_def, mock_def2],
            base_dir=".",
            host="127.0.0.1",
            port=0
        )

        try:
            # Engine should have both definitions
            self.assertEqual(len(server.engine.definitions), 2)
        finally:
            server.server_close()

    def test_create_server_binds_to_specified_port(self):
        """Test that server binds to the specified address."""
        # Find an available port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            available_port = s.getsockname()[1]

        server = create_server(
            definitions=[self.mock_def],
            base_dir=".",
            host="127.0.0.1",
            port=available_port
        )

        try:
            host, port = server.server_address
            self.assertEqual(host, "127.0.0.1")
            self.assertEqual(port, available_port)
        finally:
            server.server_close()

    def test_create_server_raises_on_port_in_use(self):
        """Test that creating server on used port raises OSError."""
        # Create first server
        server1 = create_server(
            definitions=[self.mock_def],
            base_dir=".",
            host="127.0.0.1",
            port=0
        )

        try:
            # Get the port that was assigned
            used_port = server1.server_address[1]

            # Try to create second server on same port
            with self.assertRaises(OSError):
                server2 = create_server(
                    definitions=[self.mock_def],
                    base_dir=".",
                    host="127.0.0.1",
                    port=used_port
                )
                server2.server_close()
        finally:
            server1.server_close()

    def test_create_server_default_cors_values(self):
        """Test that default CORS values are set correctly."""
        server = create_server(
            definitions=[self.mock_def],
            base_dir=".",
            host="127.0.0.1",
            port=0
        )

        try:
            self.assertTrue(server.cors_enabled)
            self.assertEqual(server.cors_origins, '*')
        finally:
            server.server_close()


if __name__ == "__main__":
    unittest.main()
