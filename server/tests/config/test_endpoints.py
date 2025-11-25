import unittest
import sys
import os
import tempfile
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.loader import load_endpoints
from config.validator import validate_definition_structure


class TestValidateDefinitionStructure(unittest.TestCase):
    def test_valid_definition_with_single_response(self):
        definition = {
            "request": {"url": "^/users$"},
            "response": {"status": 200, "body": "OK"}
        }
        errors = validate_definition_structure(definition, 1)
        self.assertEqual(errors, [])

    def test_valid_definition_with_multiple_responses(self):
        definition = {
            "request": {"url": "^/users$"},
            "response": [
                {"status": 200, "body": "OK"},
                {"status": 201, "body": "Created"}
            ]
        }
        errors = validate_definition_structure(definition, 1)
        self.assertEqual(errors, [])

    def test_definition_not_dict(self):
        definition = "not a dict"
        errors = validate_definition_structure(definition, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("must be a dictionary", errors[0])
        self.assertIn("#1", errors[0])

    def test_definition_missing_request(self):
        definition = {
            "response": {"status": 200}
        }
        errors = validate_definition_structure(definition, 2)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing required field 'request'", errors[0])
        self.assertIn("#2", errors[0])

    def test_definition_missing_response(self):
        definition = {
            "request": {"url": "^/test$"}
        }
        errors = validate_definition_structure(definition, 3)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing required field 'response'", errors[0])
        self.assertIn("#3", errors[0])

    def test_definition_missing_both_request_and_response(self):
        definition = {}
        errors = validate_definition_structure(definition, 1)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("request" in err for err in errors))
        self.assertTrue(any("response" in err for err in errors))

    def test_request_not_dict(self):
        definition = {
            "request": "not a dict",
            "response": {"status": 200}
        }
        errors = validate_definition_structure(definition, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("'request' must be a dictionary", errors[0])

    def test_request_missing_url(self):
        definition = {
            "request": {"methods": "GET"},
            "response": {"status": 200}
        }
        errors = validate_definition_structure(definition, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("'request' is missing required field 'url'", errors[0])

    def test_response_invalid_type(self):
        definition = {
            "request": {"url": "^/test$"},
            "response": "not a dict or list"
        }
        errors = validate_definition_structure(definition, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("'response' must be a dict or list of dicts", errors[0])

    def test_response_empty_list(self):
        definition = {
            "request": {"url": "^/test$"},
            "response": []
        }
        errors = validate_definition_structure(definition, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("'response' list cannot be empty", errors[0])

    def test_response_list_with_non_dict_element(self):
        definition = {
            "request": {"url": "^/test$"},
            "response": [
                {"status": 200},
                "not a dict",
                {"status": 201}
            ]
        }
        errors = validate_definition_structure(definition, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("response[2] must be a dictionary", errors[0])

    def test_multiple_errors(self):
        definition = {
            "request": "not a dict",
            "response": "not valid"
        }
        errors = validate_definition_structure(definition, 1)
        # Should have errors for both request and response
        self.assertGreaterEqual(len(errors), 2)


class TestLoadEndpoints(unittest.TestCase):
    def setUp(self):
        # Configure logging for tests
        logging.basicConfig(level=logging.WARNING)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_nonexistent_file(self):
        endpoints_path = os.path.join(self.temp_dir, 'nonexistent.py')

        with self.assertRaises(FileNotFoundError) as cm:
            load_endpoints(endpoints_path)

        self.assertIn('not found', str(cm.exception))

    def test_load_file_without_definitions(self):
        endpoints_path = os.path.join(self.temp_dir, 'endpoints.py')

        with open(endpoints_path, 'w') as f:
            f.write('# Empty file\n')

        with self.assertRaises(ValueError) as cm:
            load_endpoints(endpoints_path)

        self.assertIn("must define a 'definitions' list", str(cm.exception))

    def test_load_file_definitions_not_list(self):
        endpoints_path = os.path.join(self.temp_dir, 'endpoints.py')

        with open(endpoints_path, 'w') as f:
            f.write('definitions = {"not": "a list"}\n')

        with self.assertRaises(ValueError) as cm:
            load_endpoints(endpoints_path)

        self.assertIn("must be a list", str(cm.exception))

    def test_load_file_definitions_empty(self):
        endpoints_path = os.path.join(self.temp_dir, 'endpoints.py')

        with open(endpoints_path, 'w') as f:
            f.write('definitions = []\n')

        with self.assertRaises(ValueError) as cm:
            load_endpoints(endpoints_path)

        self.assertIn("is empty", str(cm.exception))

    def test_load_valid_single_definition(self):
        endpoints_path = os.path.join(self.temp_dir, 'endpoints.py')

        with open(endpoints_path, 'w') as f:
            f.write('''
definitions = [
    {
        "request": {"url": "^/users$"},
        "response": {"status": 200, "body": "Users"}
    }
]
''')

        with self.assertLogs(level='INFO') as cm:
            result = load_endpoints(endpoints_path)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['request']['url'], '^/users$')
        self.assertEqual(result[0]['response']['status'], 200)
        self.assertTrue(any('Loaded 1 endpoint' in msg for msg in cm.output))

    def test_load_valid_multiple_definitions(self):
        endpoints_path = os.path.join(self.temp_dir, 'endpoints.py')

        with open(endpoints_path, 'w') as f:
            f.write('''
definitions = [
    {
        "request": {"url": "^/users$"},
        "response": {"status": 200, "body": "Users"}
    },
    {
        "request": {"url": "^/products$"},
        "response": {"status": 200, "body": "Products"}
    },
    {
        "request": {"url": "^/orders$"},
        "response": [
            {"status": 200, "body": "Order 1"},
            {"status": 201, "body": "Order 2"}
        ]
    }
]
''')

        result = load_endpoints(endpoints_path)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['request']['url'], '^/users$')
        self.assertEqual(result[1]['request']['url'], '^/products$')
        self.assertEqual(result[2]['request']['url'], '^/orders$')
        self.assertIsInstance(result[2]['response'], list)

    def test_load_definition_missing_request(self):
        endpoints_path = os.path.join(self.temp_dir, 'endpoints.py')

        with open(endpoints_path, 'w') as f:
            f.write('''
definitions = [
    {
        "response": {"status": 200}
    }
]
''')

        with self.assertRaises(ValueError) as cm:
            load_endpoints(endpoints_path)

        self.assertIn("missing required field 'request'", str(cm.exception))

    def test_load_definition_missing_response(self):
        endpoints_path = os.path.join(self.temp_dir, 'endpoints.py')

        with open(endpoints_path, 'w') as f:
            f.write('''
definitions = [
    {
        "request": {"url": "^/test$"}
    }
]
''')

        with self.assertRaises(ValueError) as cm:
            load_endpoints(endpoints_path)

        self.assertIn("missing required field 'response'", str(cm.exception))

    def test_load_definition_missing_url_in_request(self):
        endpoints_path = os.path.join(self.temp_dir, 'endpoints.py')

        with open(endpoints_path, 'w') as f:
            f.write('''
definitions = [
    {
        "request": {"methods": "GET"},
        "response": {"status": 200}
    }
]
''')

        with self.assertRaises(ValueError) as cm:
            load_endpoints(endpoints_path)

        self.assertIn("'request' is missing required field 'url'", str(cm.exception))

    def test_load_definition_invalid_response_type(self):
        endpoints_path = os.path.join(self.temp_dir, 'endpoints.py')

        with open(endpoints_path, 'w') as f:
            f.write('''
definitions = [
    {
        "request": {"url": "^/test$"},
        "response": "invalid"
    }
]
''')

        with self.assertRaises(ValueError) as cm:
            load_endpoints(endpoints_path)

        self.assertIn("'response' must be a dict or list", str(cm.exception))

    def test_load_multiple_definitions_with_errors(self):
        endpoints_path = os.path.join(self.temp_dir, 'endpoints.py')

        with open(endpoints_path, 'w') as f:
            f.write('''
definitions = [
    {
        "request": {"url": "^/users$"},
        "response": {"status": 200}
    },
    {
        "request": {"methods": "GET"},
        "response": {"status": 200}
    },
    {
        "request": {"url": "^/products$"},
        "response": []
    }
]
''')

        with self.assertRaises(ValueError) as cm:
            load_endpoints(endpoints_path)

        error_msg = str(cm.exception)
        # Should report errors for definitions #2 and #3
        self.assertIn("#2", error_msg)
        self.assertIn("#3", error_msg)
        self.assertIn("missing required field 'url'", error_msg)
        self.assertIn("cannot be empty", error_msg)

    def test_load_definition_with_syntax_error(self):
        endpoints_path = os.path.join(self.temp_dir, 'endpoints.py')

        with open(endpoints_path, 'w') as f:
            f.write('definitions = [{invalid python')

        with self.assertRaises(ValueError) as cm:
            load_endpoints(endpoints_path)

        self.assertIn("Error loading endpoints file", str(cm.exception))

    def test_load_complete_definition(self):
        endpoints_path = os.path.join(self.temp_dir, 'endpoints.py')

        with open(endpoints_path, 'w') as f:
            f.write('''
definitions = [
    {
        "request": {
            "url": "^/api/users/(\\\\d+)$",
            "method": ["GET", "POST"],
            "queryparams": [{"name": "limit"}],
            "headers": [{"name": "Authorization"}],
            "body": ".*user.*"
        },
        "response": [
            {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": "{\\"user\\": \\"data\\"}"
            },
            {
                "status": 201,
                "body": "Created"
            }
        ]
    }
]
''')

        result = load_endpoints(endpoints_path)

        self.assertEqual(len(result), 1)
        definition = result[0]

        # Validate request
        self.assertIn('url', definition['request'])
        self.assertIn('method', definition['request'])
        self.assertIn('queryparams', definition['request'])
        self.assertIn('headers', definition['request'])
        self.assertIn('body', definition['request'])

        # Validate response
        self.assertIsInstance(definition['response'], list)
        self.assertEqual(len(definition['response']), 2)
        self.assertEqual(definition['response'][0]['status'], 200)
        self.assertEqual(definition['response'][1]['status'], 201)


if __name__ == "__main__":
    unittest.main()
