import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.generator import ResponseGenerator
from core.models import ResponseDef, RequestContext


class TestResponseGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ResponseGenerator()
        self.fixtures_dir = str(Path(__file__).parent.parent / "fixtures")

    def test_render_simple_body(self):
        response_def = ResponseDef(
            status=200,
            headers={"Content-Type": "application/json"},
            body='{"message": "Hello"}'
        )

        context = RequestContext(
            PATH_PARAMS=[],
            QUERY_PARAMS={},
            HEADERS={},
            BODY=None
        )

        status, headers, body = self.generator.render(response_def, context, self.fixtures_dir)

        self.assertEqual(status, 200)
        self.assertEqual(headers, {"Content-Type": "application/json"})
        self.assertEqual(body, '{"message": "Hello"}')

    def test_render_body_with_path_params(self):
        response_def = ResponseDef(
            status=200,
            body='{"user_id": "{{ PATH_PARAMS[0] }}"}'
        )

        context = RequestContext(
            PATH_PARAMS=["123"],
            QUERY_PARAMS={},
            HEADERS={},
            BODY=None
        )

        status, headers, body = self.generator.render(response_def, context, self.fixtures_dir)

        self.assertEqual(body, '{"user_id": "123"}')

    def test_render_body_with_query_params(self):
        response_def = ResponseDef(
            status=200,
            body='{"query": "{{ QUERY_PARAMS.q }}", "limit": "{{ QUERY_PARAMS.limit }}"}'
        )

        context = RequestContext(
            PATH_PARAMS=[],
            QUERY_PARAMS={"q": "search", "limit": "10"},
            HEADERS={},
            BODY=None
        )

        status, headers, body = self.generator.render(response_def, context, self.fixtures_dir)

        self.assertEqual(body, '{"query": "search", "limit": "10"}')

    def test_render_body_with_headers(self):
        response_def = ResponseDef(
            status=200,
            body='{"auth": "{{ HEADERS.authorization }}"}'
        )

        context = RequestContext(
            PATH_PARAMS=[],
            QUERY_PARAMS={},
            HEADERS={"authorization": "Bearer token123"},
            BODY=None
        )

        status, headers, body = self.generator.render(response_def, context, self.fixtures_dir)

        self.assertEqual(body, '{"auth": "Bearer token123"}')

    def test_render_body_with_request_body(self):
        response_def = ResponseDef(
            status=200,
            body='{"received": "{{ BODY }}"}'
        )

        context = RequestContext(
            PATH_PARAMS=[],
            QUERY_PARAMS={},
            HEADERS={},
            BODY='{"test": "data"}'
        )

        status, headers, body = self.generator.render(response_def, context, self.fixtures_dir)

        self.assertEqual(body, '{"received": "{"test": "data"}"}')

    def test_render_body_with_jinja_filters(self):
        response_def = ResponseDef(
            status=200,
            body='{"user": "{{ QUERY_PARAMS.get(\'user\', \'anonymous\') }}"}'
        )

        context = RequestContext(
            PATH_PARAMS=[],
            QUERY_PARAMS={},
            HEADERS={},
            BODY=None
        )

        status, headers, body = self.generator.render(response_def, context, self.fixtures_dir)

        self.assertEqual(body, '{"user": "anonymous"}')

    def test_render_body_with_default_filter(self):
        response_def = ResponseDef(
            status=200,
            body='{"value": "{{ QUERY_PARAMS.missing|default(\'N/A\') }}"}'
        )

        context = RequestContext(
            PATH_PARAMS=[],
            QUERY_PARAMS={},
            HEADERS={},
            BODY=None
        )

        status, headers, body = self.generator.render(response_def, context, self.fixtures_dir)

        self.assertEqual(body, '{"value": "N/A"}')

    def test_render_headers_with_templates(self):
        response_def = ResponseDef(
            status=200,
            headers={
                "Content-Type": "application/json",
                "X-User-Id": "{{ PATH_PARAMS[0] }}",
                "X-Query": "{{ QUERY_PARAMS.q }}"
            },
            body=""
        )

        context = RequestContext(
            PATH_PARAMS=["456"],
            QUERY_PARAMS={"q": "test"},
            HEADERS={},
            BODY=None
        )

        status, headers, body = self.generator.render(response_def, context, self.fixtures_dir)

        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["X-User-Id"], "456")
        self.assertEqual(headers["X-Query"], "test")

    def test_render_body_from_file(self):
        response_def = ResponseDef(
            status=200,
            body_file="responses/template_response.json"
        )

        context = RequestContext(
            PATH_PARAMS=["789"],
            QUERY_PARAMS={"q": "search"},
            HEADERS={"authorization": "Bearer token"},
            BODY=None
        )

        status, headers, body = self.generator.render(response_def, context, self.fixtures_dir)

        self.assertIn('"user_id": "789"', body)
        self.assertIn('"query": "search"', body)
        self.assertIn('"auth": "Bearer token"', body)

    def test_render_empty_body(self):
        response_def = ResponseDef(status=200)

        context = RequestContext(
            PATH_PARAMS=[],
            QUERY_PARAMS={},
            HEADERS={},
            BODY=None
        )

        status, headers, body = self.generator.render(response_def, context, self.fixtures_dir)

        self.assertEqual(status, 200)
        self.assertEqual(body, "")

    def test_load_body_template_from_body_attr(self):
        response_def = ResponseDef(body="test content")
        template = self.generator.load_body_template(response_def, self.fixtures_dir)
        self.assertEqual(template, "test content")

    def test_load_body_template_from_file(self):
        response_def = ResponseDef(body_file="responses/template_response.json")
        template = self.generator.load_body_template(response_def, self.fixtures_dir)
        self.assertIn("PATH_PARAMS", template)
        self.assertIn("QUERY_PARAMS", template)

    def test_load_body_template_empty(self):
        response_def = ResponseDef()
        template = self.generator.load_body_template(response_def, self.fixtures_dir)
        self.assertEqual(template, "")

    def test_render_complex_json_response(self):
        response_def = ResponseDef(
            status=201,
            headers={"Content-Type": "application/json"},
            body='''{
  "id": "{{ PATH_PARAMS[0] }}",
  "status": "{{ QUERY_PARAMS.get('status', 'pending') }}",
  "user": {
    "auth": "{{ HEADERS.get('authorization', 'none') }}"
  },
  "data": {{ BODY if BODY else 'null' }}
}'''
        )

        context = RequestContext(
            PATH_PARAMS=["ORDER-123"],
            QUERY_PARAMS={"status": "approved"},
            HEADERS={"authorization": "Bearer xyz"},
            BODY='{"item": "product"}'
        )

        status, headers, body = self.generator.render(response_def, context, self.fixtures_dir)

        self.assertEqual(status, 201)
        self.assertIn('"id": "ORDER-123"', body)
        self.assertIn('"status": "approved"', body)
        self.assertIn('"auth": "Bearer xyz"', body)
        self.assertIn('"data": {"item": "product"}', body)


if __name__ == "__main__":
    unittest.main()
