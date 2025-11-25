import unittest
import sys
import os
import re
import time
import tempfile
import shutil
import logging
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from server.lifecycle import setup_reload_watcher, create_server
from core.models import MockDefinition, RequestDef, ResponseDef
from config.loader import load_endpoints
from config.builder import build_mock_definitions


class TestSetupReloadWatcher(unittest.TestCase):
    def setUp(self):
        # Configure logging for tests
        logging.basicConfig(level=logging.WARNING)

        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, 'config')
        self.requests_dir = os.path.join(self.config_dir, 'requests')
        self.responses_dir = os.path.join(self.config_dir, 'responses')
        os.makedirs(self.requests_dir)
        os.makedirs(self.responses_dir)

        # Create endpoints file
        self.endpoints_file = os.path.join(self.config_dir, 'endpoints.py')
        with open(self.endpoints_file, 'w') as f:
            f.write('''
definitions = [
    {
        "request": {"url": "^/test$"},
        "response": {"status": 200, "body": "OK"}
    }
]
''')

        # Create config file
        self.config_file = os.path.join(self.config_dir, 'config.py')
        with open(self.config_file, 'w') as f:
            f.write('CONFIG = {"server": {"port": 9090}}')

        # Create mock definition
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
            base_dir=self.config_dir,
            host="127.0.0.1",
            port=0
        )

    def tearDown(self):
        # Clean up
        self.server.server_close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_setup_reload_watcher_returns_observer(self):
        """Test that setup_reload_watcher returns an Observer."""
        from watchdog.observers import Observer

        reload_callback = Mock(return_value=[self.mock_def])

        observer = setup_reload_watcher(
            server=self.server,
            endpoints_file=self.endpoints_file,
            config_file=self.config_file,
            requests_dir=self.requests_dir,
            responses_dir=self.responses_dir,
            reload_callback=reload_callback
        )

        try:
            self.assertIsInstance(observer, Observer)
            self.assertTrue(observer.is_alive())
        finally:
            observer.stop()
            observer.join(timeout=1)

    def test_reload_on_endpoints_file_change(self):
        """Test that changing endpoints file triggers reload."""
        reload_count = {'count': 0}

        def reload_callback():
            reload_count['count'] += 1
            # Return new definitions
            return [self.mock_def]

        observer = setup_reload_watcher(
            server=self.server,
            endpoints_file=self.endpoints_file,
            config_file=self.config_file,
            requests_dir=self.requests_dir,
            responses_dir=self.responses_dir,
            reload_callback=reload_callback
        )

        try:
            # Modify endpoints file
            with open(self.endpoints_file, 'a') as f:
                f.write('\n# Comment\n')

            # Wait for debounce + processing
            time.sleep(1.0)

            # Should have triggered reload
            self.assertGreater(reload_count['count'], 0)

        finally:
            observer.stop()
            observer.join(timeout=1)

    def test_reload_on_request_file_change(self):
        """Test that changing request file triggers reload."""
        reload_count = {'count': 0}

        def reload_callback():
            reload_count['count'] += 1
            return [self.mock_def]

        observer = setup_reload_watcher(
            server=self.server,
            endpoints_file=self.endpoints_file,
            config_file=self.config_file,
            requests_dir=self.requests_dir,
            responses_dir=self.responses_dir,
            reload_callback=reload_callback
        )

        try:
            # Create new file in requests dir
            request_file = os.path.join(self.requests_dir, 'test.xml')
            with open(request_file, 'w') as f:
                f.write('<request></request>')

            # Wait for debounce + processing
            time.sleep(1.0)

            # Should have triggered reload
            self.assertGreater(reload_count['count'], 0)

        finally:
            observer.stop()
            observer.join(timeout=1)

    def test_reload_on_response_file_change(self):
        """Test that changing response file triggers reload."""
        reload_count = {'count': 0}

        def reload_callback():
            reload_count['count'] += 1
            return [self.mock_def]

        observer = setup_reload_watcher(
            server=self.server,
            endpoints_file=self.endpoints_file,
            config_file=self.config_file,
            requests_dir=self.requests_dir,
            responses_dir=self.responses_dir,
            reload_callback=reload_callback
        )

        try:
            # Create new file in responses dir
            response_file = os.path.join(self.responses_dir, 'test.json')
            with open(response_file, 'w') as f:
                f.write('{"result": "ok"}')

            # Wait for debounce + processing
            time.sleep(1.0)

            # Should have triggered reload
            self.assertGreater(reload_count['count'], 0)

        finally:
            observer.stop()
            observer.join(timeout=1)

    def test_debouncing_prevents_multiple_reloads(self):
        """Test that debouncing prevents multiple rapid reloads."""
        reload_count = {'count': 0}

        def reload_callback():
            reload_count['count'] += 1
            return [self.mock_def]

        observer = setup_reload_watcher(
            server=self.server,
            endpoints_file=self.endpoints_file,
            config_file=self.config_file,
            requests_dir=self.requests_dir,
            responses_dir=self.responses_dir,
            reload_callback=reload_callback
        )

        try:
            # Make multiple rapid changes
            for i in range(5):
                with open(self.endpoints_file, 'a') as f:
                    f.write(f'\n# Comment {i}\n')
                time.sleep(0.1)  # Less than debounce time

            # Wait for debounce + processing
            time.sleep(1.0)

            # Should have only triggered once due to debouncing
            self.assertEqual(reload_count['count'], 1)

        finally:
            observer.stop()
            observer.join(timeout=1)

    def test_reload_failure_keeps_previous_definitions(self):
        """Test that reload failure doesn't crash and keeps previous definitions."""
        reload_attempts = []

        def reload_callback():
            reload_attempts.append(True)
            # Simulate reload failure
            return None

        # Save initial engine
        initial_engine = self.server.engine

        observer = setup_reload_watcher(
            server=self.server,
            endpoints_file=self.endpoints_file,
            config_file=self.config_file,
            requests_dir=self.requests_dir,
            responses_dir=self.responses_dir,
            reload_callback=reload_callback
        )

        try:
            # Modify file to trigger reload
            with open(self.endpoints_file, 'a') as f:
                f.write('\n# Trigger reload\n')

            # Wait for reload attempt
            time.sleep(1.0)

            # Should have attempted reload
            self.assertGreater(len(reload_attempts), 0)

            # Engine should still be the same (or same class)
            self.assertIsNotNone(self.server.engine)

        finally:
            observer.stop()
            observer.join(timeout=1)

    def test_reload_updates_engine_on_success(self):
        """Test that successful reload updates the engine."""
        new_def = MockDefinition(
            request=RequestDef(
                url_pattern="^/new$",
                url_regex=re.compile("^/new$")
            ),
            responses=[
                ResponseDef(status=200, body="New")
            ]
        )

        def reload_callback():
            return [self.mock_def, new_def]  # Two definitions now

        # Initial engine has 1 definition
        self.assertEqual(len(self.server.engine.definitions), 1)

        observer = setup_reload_watcher(
            server=self.server,
            endpoints_file=self.endpoints_file,
            config_file=self.config_file,
            requests_dir=self.requests_dir,
            responses_dir=self.responses_dir,
            reload_callback=reload_callback
        )

        try:
            # Trigger reload
            with open(self.endpoints_file, 'a') as f:
                f.write('\n# Trigger\n')

            # Wait for reload
            time.sleep(1.0)

            # Engine should have 2 definitions now
            self.assertEqual(len(self.server.engine.definitions), 2)

        finally:
            observer.stop()
            observer.join(timeout=1)

    def test_observer_can_be_stopped(self):
        """Test that observer can be stopped cleanly."""
        reload_callback = Mock(return_value=[self.mock_def])

        observer = setup_reload_watcher(
            server=self.server,
            endpoints_file=self.endpoints_file,
            config_file=self.config_file,
            requests_dir=self.requests_dir,
            responses_dir=self.responses_dir,
            reload_callback=reload_callback
        )

        # Observer should be running
        self.assertTrue(observer.is_alive())

        # Stop observer
        observer.stop()
        observer.join(timeout=1)

        # Observer should be stopped
        self.assertFalse(observer.is_alive())


if __name__ == "__main__":
    unittest.main()
