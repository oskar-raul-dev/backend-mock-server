"""
Integration tests for Phase 2: Body matching integration with core mockserver.

This tests the integration of the body_matching module with server.py:
- Legacy body matching (string patterns and body_file) still works
- New body matching (dict specifications) works
- Semantic XML/JSON matching works
- Processor functions work and BODY_PROCESSED is available in templates
"""
import re
import unittest
import tempfile
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.models import RequestDef, RequestContext, HTTPRequest
from core.matcher import RequestMatcher
from core.generator import ResponseGenerator
from config.builder import build_mock_definitions


class TestPhase2Integration(unittest.TestCase):
    """Integration tests for Phase 2 body matching."""

    def setUp(self):
        self.matcher = RequestMatcher()
        self.generator = ResponseGenerator()
        self.temp_dir = tempfile.mkdtemp()

    def test_legacy_body_pattern_still_works(self):
        """Test that legacy string body patterns still work."""
        request_def = RequestDef(
            url_pattern=r"^/test$",
            url_regex=re.compile(r"^/test$"),
            body_pattern=r".*user_id.*"
        )

        http_request = HTTPRequest(
            method="POST",
            url="http://example.com/test",
            headers={},
            query_params={},
            body='{"user_id": "123"}'
        )

        context = self.matcher.match(request_def, http_request, self.temp_dir)
        self.assertIsNotNone(context)
        self.assertIsNone(context.BODY_PROCESSED)  # No processor in legacy mode

    def test_build_mock_definitions_with_legacy_string_body(self):
        """Test build_mock_definitions with legacy string body pattern."""
        definitions = [{
            "request": {
                "url": r"^/users$",
                "body": r".*username.*"
            },
            "response": {
                "status": 200,
                "body": "OK"
            }
        }]

        mock_defs = build_mock_definitions(definitions, self.temp_dir, self.temp_dir)

        self.assertEqual(len(mock_defs), 1)
        self.assertIsNotNone(mock_defs[0].request.body_pattern)
        self.assertIsNone(mock_defs[0].request.body_matcher)

    def test_build_mock_definitions_with_new_json_body(self):
        """Test build_mock_definitions with new JSON body specification."""
        definitions = [{
            "request": {
                "url": r"^/users$",
                "body": {
                    "value": '{"name": "John"}',
                    "format": "json",
                    "matching_mode": "semantic"
                }
            },
            "response": {
                "status": 200,
                "body": "OK"
            }
        }]

        mock_defs = build_mock_definitions(definitions, self.temp_dir, self.temp_dir)

        self.assertEqual(len(mock_defs), 1)
        self.assertIsNotNone(mock_defs[0].request.body_matcher)
        self.assertEqual(mock_defs[0].request.body_expected_value, '{"name": "John"}')
        self.assertIsNone(mock_defs[0].request.body_pattern)

    def test_semantic_json_matching_ignores_whitespace(self):
        """Test that semantic JSON matching ignores whitespace differences."""
        # Create request def with JSON body matcher
        definitions = [{
            "request": {
                "url": r"^/users$",
                "body": {
                    "value": '{"name":"John","age":30}',
                    "format": "json"
                }
            },
            "response": {
                "status": 200,
                "body": "OK"
            }
        }]

        mock_defs = build_mock_definitions(definitions, self.temp_dir, self.temp_dir)
        request_def = mock_defs[0].request

        # Actual body with different whitespace
        http_request = HTTPRequest(
            method="POST",
            url="http://example.com/users",
            headers={},
            query_params={},
            body='{\n  "name": "John",\n  "age": 30\n}'
        )

        context = self.matcher.match(request_def, http_request, self.temp_dir)
        self.assertIsNotNone(context)

    def test_semantic_xml_matching_ignores_whitespace(self):
        """Test that semantic XML matching ignores whitespace differences."""
        definitions = [{
            "request": {
                "url": r"^/users$",
                "body": {
                    "value": '<user><name>John</name><age>30</age></user>',
                    "format": "xml"
                }
            },
            "response": {
                "status": 200,
                "body": "OK"
            }
        }]

        mock_defs = build_mock_definitions(definitions, self.temp_dir, self.temp_dir)
        request_def = mock_defs[0].request

        # Actual body with different whitespace
        http_request = HTTPRequest(
            method="POST",
            url="http://example.com/users",
            headers={},
            query_params={},
            body='''<user>
    <name>John</name>
    <age>30</age>
</user>'''
        )

        context = self.matcher.match(request_def, http_request, self.temp_dir)
        self.assertIsNotNone(context)

    def test_processor_function_extracts_values(self):
        """Test that processor function extracts values into BODY_PROCESSED."""
        import json

        def extract_user_id(body_str):
            data = json.loads(body_str)
            return {"user_id": data["id"]}

        definitions = [{
            "request": {
                "url": r"^/users$",
                "body": {
                    "value": '{"id": "123"}',
                    "format": "json",
                    "matching_mode": "partial",  # Use partial to allow extra fields
                    "processor": extract_user_id
                }
            },
            "response": {
                "status": 200,
                "body": "User ID: {{ BODY_PROCESSED.user_id }}"
            }
        }]

        mock_defs = build_mock_definitions(definitions, self.temp_dir, self.temp_dir)
        request_def = mock_defs[0].request
        response_def = mock_defs[0].responses[0]

        http_request = HTTPRequest(
            method="POST",
            url="http://example.com/users",
            headers={},
            query_params={},
            body='{"id": "123", "name": "John"}'
        )

        context = self.matcher.match(request_def, http_request, self.temp_dir)
        self.assertIsNotNone(context)
        self.assertIsNotNone(context.BODY_PROCESSED)
        self.assertEqual(context.BODY_PROCESSED, {"user_id": "123"})

        # Render response using BODY_PROCESSED
        status, headers, body = self.generator.render(response_def, context, self.temp_dir)
        self.assertEqual(body, "User ID: 123")

    def test_validator_function_rejects_invalid_body(self):
        """Test that validator function rejects invalid bodies."""
        import json

        def validate_has_email(body_str):
            data = json.loads(body_str)
            if "email" not in data:
                raise ValueError("Email is required")

        definitions = [{
            "request": {
                "url": r"^/users$",
                "body": {
                    "value": '{"email": "test@example.com"}',
                    "format": "json",
                    "matching_mode": "partial",  # Use partial to allow extra fields
                    "validator": validate_has_email
                }
            },
            "response": {
                "status": 200,
                "body": "OK"
            }
        }]

        mock_defs = build_mock_definitions(definitions, self.temp_dir, self.temp_dir)
        request_def = mock_defs[0].request

        # Valid request with email (exact match with mock)
        valid_request = HTTPRequest(
            method="POST",
            url="http://example.com/users",
            headers={},
            query_params={},
            body='{"email": "test@example.com"}'
        )

        context = self.matcher.match(request_def, valid_request, self.temp_dir)
        self.assertIsNotNone(context)

        # Invalid request without email
        invalid_request = HTTPRequest(
            method="POST",
            url="http://example.com/users",
            headers={},
            query_params={},
            body='{"name": "John"}'
        )

        context = self.matcher.match(request_def, invalid_request, self.temp_dir)
        self.assertIsNone(context)

    def test_body_file_with_auto_detection(self):
        """Test that body files with auto-detection work."""
        # Create a JSON file
        json_file = os.path.join(self.temp_dir, "test.json")
        with open(json_file, 'w') as f:
            f.write('{"name": "John"}')

        definitions = [{
            "request": {
                "url": r"^/users$",
                "body": {
                    "file": "test.json"
                }
            },
            "response": {
                "status": 200,
                "body": "OK"
            }
        }]

        mock_defs = build_mock_definitions(definitions, self.temp_dir, self.temp_dir)
        request_def = mock_defs[0].request

        # Check that format was auto-detected
        self.assertIsNotNone(request_def.body_matcher)
        self.assertEqual(request_def.body_expected_value, '{"name": "John"}')

        # Test that semantic matching works
        http_request = HTTPRequest(
            method="POST",
            url="http://example.com/users",
            headers={},
            query_params={},
            body='{\n  "name": "John"\n}'  # Different whitespace
        )

        context = self.matcher.match(request_def, http_request, self.temp_dir)
        self.assertIsNotNone(context)


if __name__ == "__main__":
    unittest.main()
