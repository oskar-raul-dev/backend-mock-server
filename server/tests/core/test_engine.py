import re
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.engine import MockEngine
from core.models import MockDefinition, RequestDef, ResponseDef, HTTPRequest
from core.exceptions import NoMatchError


class TestMockEngine(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = str(Path(__file__).parent.parent / "fixtures")

    def test_find_match_first_definition(self):
        definitions = [
            MockDefinition(
                request=RequestDef(
                    url_pattern=r"^/users$",
                    url_regex=re.compile(r"^/users$")
                ),
                responses=[ResponseDef(status=200, body="Users")]
            ),
            MockDefinition(
                request=RequestDef(
                    url_pattern=r"^/products$",
                    url_regex=re.compile(r"^/products$")
                ),
                responses=[ResponseDef(status=200, body="Products")]
            )
        ]

        engine = MockEngine(definitions, self.fixtures_dir)

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/users",
            headers={},
            query_params={},
            body=""
        )

        mock_def, context = engine.find_match(http_request)

        self.assertIsNotNone(mock_def)
        self.assertEqual(mock_def, definitions[0])
        self.assertIsNotNone(context)

    def test_find_match_second_definition(self):
        definitions = [
            MockDefinition(
                request=RequestDef(
                    url_pattern=r"^/users$",
                    url_regex=re.compile(r"^/users$")
                ),
                responses=[ResponseDef(status=200, body="Users")]
            ),
            MockDefinition(
                request=RequestDef(
                    url_pattern=r"^/products$",
                    url_regex=re.compile(r"^/products$")
                ),
                responses=[ResponseDef(status=200, body="Products")]
            )
        ]

        engine = MockEngine(definitions, self.fixtures_dir)

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/products",
            headers={},
            query_params={},
            body=""
        )

        mock_def, context = engine.find_match(http_request)

        self.assertIsNotNone(mock_def)
        self.assertEqual(mock_def, definitions[1])

    def test_find_match_first_match_wins(self):
        definitions = [
            MockDefinition(
                request=RequestDef(
                    url_pattern=r"^/api/.*$",
                    url_regex=re.compile(r"^/api/.*$")
                ),
                responses=[ResponseDef(status=200, body="Generic API")]
            ),
            MockDefinition(
                request=RequestDef(
                    url_pattern=r"^/api/users$",
                    url_regex=re.compile(r"^/api/users$")
                ),
                responses=[ResponseDef(status=200, body="Specific Users")]
            )
        ]

        engine = MockEngine(definitions, self.fixtures_dir)

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/api/users",
            headers={},
            query_params={},
            body=""
        )

        mock_def, context = engine.find_match(http_request)

        self.assertEqual(mock_def, definitions[0])

    def test_find_match_no_match(self):
        definitions = [
            MockDefinition(
                request=RequestDef(
                    url_pattern=r"^/users$",
                    url_regex=re.compile(r"^/users$")
                ),
                responses=[ResponseDef(status=200, body="Users")]
            )
        ]

        engine = MockEngine(definitions, self.fixtures_dir)

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/products",
            headers={},
            query_params={},
            body=""
        )

        result = engine.find_match(http_request)

        self.assertIsNone(result)

    def test_get_next_response_single_response(self):
        mock_def = MockDefinition(
            request=RequestDef(
                url_pattern=r"^/test$",
                url_regex=re.compile(r"^/test$")
            ),
            responses=[ResponseDef(status=200, body="Response")]
        )

        engine = MockEngine([mock_def], self.fixtures_dir)

        response1 = engine.get_next_response(mock_def)
        response2 = engine.get_next_response(mock_def)
        response3 = engine.get_next_response(mock_def)

        self.assertEqual(response1.body, "Response")
        self.assertEqual(response2.body, "Response")
        self.assertEqual(response3.body, "Response")

    def test_get_next_response_multiple_responses_cycling(self):
        mock_def = MockDefinition(
            request=RequestDef(
                url_pattern=r"^/test$",
                url_regex=re.compile(r"^/test$")
            ),
            responses=[
                ResponseDef(status=200, body="Response A"),
                ResponseDef(status=201, body="Response B"),
                ResponseDef(status=202, body="Response C")
            ]
        )

        engine = MockEngine([mock_def], self.fixtures_dir)

        response1 = engine.get_next_response(mock_def)
        response2 = engine.get_next_response(mock_def)
        response3 = engine.get_next_response(mock_def)
        response4 = engine.get_next_response(mock_def)

        self.assertEqual(response1.body, "Response A")
        self.assertEqual(response2.body, "Response B")
        self.assertEqual(response3.body, "Response C")
        self.assertEqual(response4.body, "Response A")

    def test_handle_request_success(self):
        definitions = [
            MockDefinition(
                request=RequestDef(
                    url_pattern=r"^/users/(\d+)$",
                    url_regex=re.compile(r"^/users/(\d+)$")
                ),
                responses=[
                    ResponseDef(
                        status=200,
                        headers={"Content-Type": "application/json"},
                        body='{"user_id": "{{ PATH_PARAMS[0] }}"}'
                    )
                ]
            )
        ]

        engine = MockEngine(definitions, self.fixtures_dir)

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/users/123",
            headers={},
            query_params={},
            body=""
        )

        status, headers, body = engine.handle_request(http_request)

        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(body, '{"user_id": "123"}')

    def test_handle_request_no_match_raises_error(self):
        definitions = [
            MockDefinition(
                request=RequestDef(
                    url_pattern=r"^/users$",
                    url_regex=re.compile(r"^/users$")
                ),
                responses=[ResponseDef(status=200, body="Users")]
            )
        ]

        engine = MockEngine(definitions, self.fixtures_dir)

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/products",
            headers={},
            query_params={},
            body=""
        )

        with self.assertRaises(NoMatchError) as cm:
            engine.handle_request(http_request)

        self.assertIn("No mock definition matched", str(cm.exception))
        self.assertIn("GET", str(cm.exception))
        self.assertIn("/products", str(cm.exception))

    def test_handle_request_cycling_responses(self):
        definitions = [
            MockDefinition(
                request=RequestDef(
                    url_pattern=r"^/status$",
                    url_regex=re.compile(r"^/status$")
                ),
                responses=[
                    ResponseDef(status=200, body="OK"),
                    ResponseDef(status=503, body="Unavailable")
                ]
            )
        ]

        engine = MockEngine(definitions, self.fixtures_dir)

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/status",
            headers={},
            query_params={},
            body=""
        )

        status1, _, body1 = engine.handle_request(http_request)
        status2, _, body2 = engine.handle_request(http_request)
        status3, _, body3 = engine.handle_request(http_request)

        self.assertEqual(status1, 200)
        self.assertEqual(body1, "OK")
        self.assertEqual(status2, 503)
        self.assertEqual(body2, "Unavailable")
        self.assertEqual(status3, 200)
        self.assertEqual(body3, "OK")

    def test_handle_request_with_all_context_variables(self):
        definitions = [
            MockDefinition(
                request=RequestDef(
                    url_pattern=r"^/api/orders/(\w+)$",
                    url_regex=re.compile(r"^/api/orders/(\w+)$"),
                    methods=["POST"],
                    queryparams=[{"name": "user_id"}],
                    headers=[{"name": "Authorization"}]
                ),
                responses=[
                    ResponseDef(
                        status=201,
                        headers={"Content-Type": "application/json"},
                        body='''{
  "order_id": "{{ PATH_PARAMS[0] }}",
  "user_id": "{{ QUERY_PARAMS.user_id }}",
  "auth": "{{ HEADERS.authorization }}",
  "body": "{{ BODY }}"
}'''
                    )
                ]
            )
        ]

        engine = MockEngine(definitions, self.fixtures_dir)

        http_request = HTTPRequest(
            method="POST",
            url="http://example.com/api/orders/ORD123?user_id=USER456",
            headers={"Authorization": "Bearer token"},
            query_params={"user_id": "USER456"},
            body='{"item": "product"}'
        )

        status, headers, body = engine.handle_request(http_request)

        self.assertEqual(status, 201)
        self.assertIn('"order_id": "ORD123"', body)
        self.assertIn('"user_id": "USER456"', body)
        self.assertIn('"auth": "Bearer token"', body)
        self.assertIn('"body": "{"item": "product"}"', body)


if __name__ == "__main__":
    unittest.main()
