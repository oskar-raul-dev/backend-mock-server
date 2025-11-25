import unittest
import sys
import os
import tempfile
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.builder import build_mock_definitions
from core.models import MockDefinition, RequestDef, ResponseDef


class TestBuildMockDefinitions(unittest.TestCase):
    def setUp(self):
        # Configure logging for tests
        logging.basicConfig(level=logging.WARNING)
        self.temp_dir = tempfile.mkdtemp()
        self.requests_dir = os.path.join(self.temp_dir, 'requests')
        self.responses_dir = os.path.join(self.temp_dir, 'responses')
        os.makedirs(self.requests_dir)
        os.makedirs(self.responses_dir)

    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_simple_definition(self):
        definitions = [
            {
                "request": {"url": "^/users$"},
                "response": {"status": 200, "body": "Users"}
            }
        ]

        result = build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], MockDefinition)
        self.assertIsInstance(result[0].request, RequestDef)
        self.assertEqual(result[0].request.url_pattern, "^/users$")
        self.assertEqual(len(result[0].responses), 1)
        self.assertIsInstance(result[0].responses[0], ResponseDef)
        self.assertEqual(result[0].responses[0].status, 200)
        self.assertEqual(result[0].responses[0].body, "Users")

    def test_build_multiple_definitions(self):
        definitions = [
            {
                "request": {"url": "^/users$"},
                "response": {"status": 200, "body": "Users"}
            },
            {
                "request": {"url": "^/products$"},
                "response": {"status": 200, "body": "Products"}
            }
        ]

        result = build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].request.url_pattern, "^/users$")
        self.assertEqual(result[1].request.url_pattern, "^/products$")

    def test_build_normalizes_single_response_to_list(self):
        definitions = [
            {
                "request": {"url": "^/test$"},
                "response": {"status": 200, "body": "OK"}
            }
        ]

        result = build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertEqual(len(result[0].responses), 1)
        self.assertIsInstance(result[0].responses, list)

    def test_build_keeps_multiple_responses_as_list(self):
        definitions = [
            {
                "request": {"url": "^/test$"},
                "response": [
                    {"status": 200, "body": "OK"},
                    {"status": 201, "body": "Created"}
                ]
            }
        ]

        result = build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertEqual(len(result[0].responses), 2)
        self.assertEqual(result[0].responses[0].status, 200)
        self.assertEqual(result[0].responses[1].status, 201)

    def test_build_with_optional_request_fields(self):
        definitions = [
            {
                "request": {
                    "url": "^/api/users/(\\d+)$",
                    "methods": ["GET", "POST"],
                    "queryparams": [{"name": "limit"}],
                    "headers": [{"name": "Authorization", "value": "Bearer .*"}],
                    "body": ".*user.*"
                },
                "response": {"status": 200}
            }
        ]

        result = build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        request = result[0].request
        self.assertEqual(request.methods, ["GET", "POST"])
        self.assertEqual(len(request.queryparams), 1)
        self.assertEqual(request.queryparams[0]['name'], "limit")
        self.assertEqual(len(request.headers), 1)
        self.assertEqual(request.headers[0]['name'], "Authorization")
        self.assertEqual(request.body_pattern, ".*user.*")

    def test_build_with_optional_response_fields(self):
        definitions = [
            {
                "request": {"url": "^/test$"},
                "response": {
                    "status": 201,
                    "headers": {"Content-Type": "application/json"},
                    "body": '{"result": "ok"}'
                }
            }
        ]

        result = build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        response = result[0].responses[0]
        self.assertEqual(response.status, 201)
        self.assertEqual(response.headers['Content-Type'], "application/json")
        self.assertEqual(response.body, '{"result": "ok"}')

    def test_build_response_default_status(self):
        definitions = [
            {
                "request": {"url": "^/test$"},
                "response": {"body": "OK"}  # No status
            }
        ]

        result = build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertEqual(result[0].responses[0].status, 200)

    def test_build_compiles_url_regex(self):
        definitions = [
            {
                "request": {"url": "^/users/(\\d+)$"},
                "response": {"status": 200}
            }
        ]

        result = build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        import re
        self.assertIsInstance(result[0].request.url_regex, re.Pattern)
        # Test the regex works
        self.assertIsNotNone(result[0].request.url_regex.match("/users/123"))
        self.assertIsNone(result[0].request.url_regex.match("/users/abc"))

    def test_build_invalid_url_regex(self):
        definitions = [
            {
                "request": {"url": "^/users/(\\d+"},  # Unclosed parenthesis
                "response": {"status": 200}
            }
        ]

        with self.assertRaises(ValueError) as cm:
            build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertIn("Invalid regex", str(cm.exception))
        self.assertIn("#1", str(cm.exception))
        self.assertIn("URL pattern", str(cm.exception))

    def test_build_invalid_queryparam_regex(self):
        definitions = [
            {
                "request": {
                    "url": "^/test$",
                    "queryparams": [{"name": "[invalid"}]  # Invalid regex
                },
                "response": {"status": 200}
            }
        ]

        with self.assertRaises(ValueError) as cm:
            build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertIn("Invalid regex", str(cm.exception))
        self.assertIn("queryparam", str(cm.exception))

    def test_build_invalid_header_regex(self):
        definitions = [
            {
                "request": {
                    "url": "^/test$",
                    "headers": [{"name": "Auth", "value": "(invalid"}]  # Invalid regex
                },
                "response": {"status": 200}
            }
        ]

        with self.assertRaises(ValueError) as cm:
            build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertIn("Invalid regex", str(cm.exception))
        self.assertIn("header", str(cm.exception))

    def test_build_invalid_body_regex(self):
        definitions = [
            {
                "request": {
                    "url": "^/test$",
                    "body": "(?P<invalid"  # Invalid regex
                },
                "response": {"status": 200}
            }
        ]

        with self.assertRaises(ValueError) as cm:
            build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertIn("Invalid regex", str(cm.exception))
        self.assertIn("body pattern", str(cm.exception))

    def test_build_with_request_body_file(self):
        # Create a test file
        request_file = os.path.join(self.requests_dir, 'request.xml')
        with open(request_file, 'w') as f:
            f.write('<request></request>')

        definitions = [
            {
                "request": {
                    "url": "^/test$",
                    "body_file": "request.xml"
                },
                "response": {"status": 200}
            }
        ]

        result = build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertEqual(result[0].request.body_file, "request.xml")

    def test_build_with_response_body_file(self):
        # Create a test file
        response_file = os.path.join(self.responses_dir, 'response.json')
        with open(response_file, 'w') as f:
            f.write('{"result": "ok"}')

        definitions = [
            {
                "request": {"url": "^/test$"},
                "response": {
                    "status": 200,
                    "body_file": "response.json"
                }
            }
        ]

        result = build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertEqual(result[0].responses[0].body_file, "response.json")

    def test_build_missing_request_body_file(self):
        definitions = [
            {
                "request": {
                    "url": "^/test$",
                    "body_file": "nonexistent.xml"
                },
                "response": {"status": 200}
            }
        ]

        with self.assertRaises(ValueError) as cm:
            build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertIn("Missing files", str(cm.exception))
        self.assertIn("nonexistent.xml", str(cm.exception))
        self.assertIn("not found in", str(cm.exception))

    def test_build_missing_response_body_file(self):
        definitions = [
            {
                "request": {"url": "^/test$"},
                "response": {
                    "status": 200,
                    "body_file": "nonexistent.json"
                }
            }
        ]

        with self.assertRaises(ValueError) as cm:
            build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertIn("Missing files", str(cm.exception))
        self.assertIn("nonexistent.json", str(cm.exception))

    def test_build_multiple_missing_files(self):
        definitions = [
            {
                "request": {
                    "url": "^/test1$",
                    "body_file": "missing1.xml"
                },
                "response": {"status": 200}
            },
            {
                "request": {"url": "^/test2$"},
                "response": {
                    "status": 200,
                    "body_file": "missing2.json"
                }
            }
        ]

        with self.assertRaises(ValueError) as cm:
            build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        error_msg = str(cm.exception)
        self.assertIn("missing1.xml", error_msg)
        self.assertIn("missing2.json", error_msg)
        self.assertIn("#1", error_msg)
        self.assertIn("#2", error_msg)

    def test_build_multiple_errors_regex_and_files(self):
        definitions = [
            {
                "request": {"url": "^/invalid("},  # Invalid regex
                "response": {"status": 200}
            },
            {
                "request": {"url": "^/test$"},
                "response": {
                    "status": 200,
                    "body_file": "missing.json"  # Missing file
                }
            }
        ]

        with self.assertRaises(ValueError) as cm:
            build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        error_msg = str(cm.exception)
        # Should report both regex error and missing file
        self.assertIn("Invalid regex", error_msg)
        self.assertIn("Missing files", error_msg)

    def test_build_complete_definition(self):
        # Create test files
        request_file = os.path.join(self.requests_dir, 'payment.xml')
        with open(request_file, 'w') as f:
            f.write('<payment></payment>')

        response_file = os.path.join(self.responses_dir, 'result.json')
        with open(response_file, 'w') as f:
            f.write('{"status": "success"}')

        definitions = [
            {
                "request": {
                    "url": "^/api/payments/(\\d+)$",
                    "methods": ["POST"],
                    "queryparams": [
                        {"name": "user_id", "value": "\\d+"}
                    ],
                    "headers": [
                        {"name": "Content-Type", "value": "application/xml"}
                    ],
                    "body_file": "payment.xml"
                },
                "response": [
                    {
                        "status": 200,
                        "headers": {"Content-Type": "application/json"},
                        "body_file": "result.json"
                    },
                    {
                        "status": 400,
                        "body": "Invalid payment"
                    }
                ]
            }
        ]

        with self.assertLogs(level='INFO') as cm:
            result = build_mock_definitions(definitions, self.requests_dir, self.responses_dir)

        self.assertEqual(len(result), 1)

        # Validate request
        request = result[0].request
        self.assertEqual(request.url_pattern, "^/api/payments/(\\d+)$")
        self.assertEqual(request.methods, ["POST"])
        self.assertEqual(len(request.queryparams), 1)
        self.assertEqual(len(request.headers), 1)
        self.assertEqual(request.body_file, "payment.xml")

        # Validate responses
        self.assertEqual(len(result[0].responses), 2)
        self.assertEqual(result[0].responses[0].status, 200)
        self.assertEqual(result[0].responses[0].body_file, "result.json")
        self.assertEqual(result[0].responses[1].status, 400)
        self.assertEqual(result[0].responses[1].body, "Invalid payment")

        # Check log message
        self.assertTrue(any('Built 1 mock definition' in msg for msg in cm.output))


if __name__ == "__main__":
    unittest.main()
