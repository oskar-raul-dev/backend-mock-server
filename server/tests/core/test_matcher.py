import re
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.matcher import RequestMatcher
from core.models import RequestDef, HTTPRequest
from server.utils import CaseInsensitiveDict


class TestRequestMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = RequestMatcher()
        self.fixtures_dir = str(Path(__file__).parent.parent / "fixtures")

    def test_match_url_simple_pattern(self):
        url_regex = re.compile(r"^/users$")
        result = self.matcher.match_url(url_regex, "http://example.com/users")
        self.assertEqual(result, [])

    def test_match_url_with_path_params(self):
        url_regex = re.compile(r"^/users/(\d+)$")
        result = self.matcher.match_url(url_regex, "http://example.com/users/123")
        self.assertEqual(result, ["123"])

    def test_match_url_with_multiple_path_params(self):
        url_regex = re.compile(r"^/orders/(\w+)/product/(\w+)$")
        result = self.matcher.match_url(url_regex, "http://example.com/orders/ABC123/product/PROD456")
        self.assertEqual(result, ["ABC123", "PROD456"])

    def test_match_url_no_match(self):
        url_regex = re.compile(r"^/users$")
        result = self.matcher.match_url(url_regex, "http://example.com/products")
        self.assertIsNone(result)

    def test_match_url_query_params_ignored(self):
        url_regex = re.compile(r"^/users$")
        result = self.matcher.match_url(url_regex, "http://example.com/users?page=1")
        self.assertEqual(result, [])

    def test_match_method_none_accepts_all(self):
        self.assertTrue(self.matcher.match_method(None, "GET"))
        self.assertTrue(self.matcher.match_method(None, "POST"))
        self.assertTrue(self.matcher.match_method(None, "PUT"))

    def test_match_method_single_method(self):
        self.assertTrue(self.matcher.match_method(["GET"], "GET"))
        self.assertFalse(self.matcher.match_method(["GET"], "POST"))

    def test_match_method_multiple_methods(self):
        self.assertTrue(self.matcher.match_method(["GET", "POST"], "GET"))
        self.assertTrue(self.matcher.match_method(["GET", "POST"], "POST"))
        self.assertFalse(self.matcher.match_method(["GET", "POST"], "PUT"))

    def test_match_method_case_insensitive(self):
        self.assertTrue(self.matcher.match_method(["GET"], "get"))
        self.assertTrue(self.matcher.match_method(["post"], "POST"))

    def test_match_queryparams_name_only(self):
        specs = [{"name": "user_id"}]
        actual = {"user_id": "123", "other": "value"}
        self.assertTrue(self.matcher.match_queryparams(specs, actual))

    def test_match_queryparams_name_and_value(self):
        specs = [{"name": "user_id", "value": r"\d+"}]
        actual = {"user_id": "123"}
        self.assertTrue(self.matcher.match_queryparams(specs, actual))

    def test_match_queryparams_value_mismatch(self):
        specs = [{"name": "user_id", "value": r"\d+"}]
        actual = {"user_id": "abc"}
        self.assertFalse(self.matcher.match_queryparams(specs, actual))

    def test_match_queryparams_missing_param(self):
        specs = [{"name": "user_id"}]
        actual = {"other": "value"}
        self.assertFalse(self.matcher.match_queryparams(specs, actual))

    def test_match_queryparams_multiple_and_logic(self):
        specs = [
            {"name": "user_id", "value": r"\d+"},
            {"name": "status", "value": "active"}
        ]
        actual = {"user_id": "123", "status": "active"}
        self.assertTrue(self.matcher.match_queryparams(specs, actual))

        actual_missing = {"user_id": "123"}
        self.assertFalse(self.matcher.match_queryparams(specs, actual_missing))

    def test_match_queryparams_list_value(self):
        specs = [{"name": "tag", "value": "test"}]
        actual = {"tag": ["test", "prod"]}
        self.assertTrue(self.matcher.match_queryparams(specs, actual))

    def test_match_headers_name_only(self):
        specs = [{"name": "Authorization"}]
        actual = {"Authorization": "Bearer token123"}
        self.assertTrue(self.matcher.match_headers(specs, actual))

    def test_match_headers_name_and_value(self):
        specs = [{"name": "Content-Type", "value": r"application/json"}]
        actual = {"Content-Type": "application/json"}
        self.assertTrue(self.matcher.match_headers(specs, actual))

    def test_match_headers_case_insensitive_name(self):
        specs = [{"name": "authorization"}]
        actual = {"Authorization": "Bearer token123"}
        self.assertTrue(self.matcher.match_headers(specs, actual))

    def test_match_headers_value_mismatch(self):
        specs = [{"name": "Content-Type", "value": r"application/json"}]
        actual = {"Content-Type": "application/xml"}
        self.assertFalse(self.matcher.match_headers(specs, actual))

    def test_match_headers_missing_header(self):
        specs = [{"name": "Authorization"}]
        actual = {"Content-Type": "application/json"}
        self.assertFalse(self.matcher.match_headers(specs, actual))

    def test_match_headers_multiple_and_logic(self):
        specs = [
            {"name": "Authorization"},
            {"name": "Content-Type", "value": r"application/json"}
        ]
        actual = {"Authorization": "Bearer token", "Content-Type": "application/json"}
        self.assertTrue(self.matcher.match_headers(specs, actual))

        actual_missing = {"Authorization": "Bearer token"}
        self.assertFalse(self.matcher.match_headers(specs, actual_missing))

    def test_match_body_pattern_match(self):
        body_spec = r".*transactionId.*"
        actual_body = '{"transactionId": "TXN-001"}'
        request_def = RequestDef(
            url_pattern="",
            url_regex=re.compile(""),
            body_pattern=body_spec
        )
        matches, processed = self.matcher.match_body(request_def, actual_body, self.fixtures_dir)
        self.assertTrue(matches)

    def test_match_body_pattern_no_match(self):
        body_spec = r".*transactionId.*"
        actual_body = '{"orderId": "ORD-001"}'
        request_def = RequestDef(
            url_pattern="",
            url_regex=re.compile(""),
            body_pattern=body_spec
        )
        matches, processed = self.matcher.match_body(request_def, actual_body, self.fixtures_dir)
        self.assertFalse(matches)

    def test_match_body_file_exact_match(self):
        body_file = "requests/sample_request.xml"
        with open(Path(self.fixtures_dir) / body_file, 'r') as f:
            expected_content = f.read()
        request_def = RequestDef(
            url_pattern="",
            url_regex=re.compile(""),
            body_file=body_file
        )
        matches, processed = self.matcher.match_body(request_def, expected_content, self.fixtures_dir)
        self.assertTrue(matches)

    def test_match_body_file_mismatch(self):
        body_file = "requests/sample_request.xml"
        actual_body = "<different>content</different>"
        request_def = RequestDef(
            url_pattern="",
            url_regex=re.compile(""),
            body_file=body_file
        )
        matches, processed = self.matcher.match_body(request_def, actual_body, self.fixtures_dir)
        self.assertFalse(matches)

    def test_match_body_file_not_found(self):
        body_file = "requests/nonexistent.xml"
        actual_body = "any content"
        request_def = RequestDef(
            url_pattern="",
            url_regex=re.compile(""),
            body_file=body_file
        )
        matches, processed = self.matcher.match_body(request_def, actual_body, self.fixtures_dir)
        self.assertFalse(matches)

    def test_match_body_none_always_true(self):
        request_def = RequestDef(
            url_pattern="",
            url_regex=re.compile("")
        )
        matches1, processed1 = self.matcher.match_body(request_def, "any content", self.fixtures_dir)
        matches2, processed2 = self.matcher.match_body(request_def, "", self.fixtures_dir)
        self.assertTrue(matches1)
        self.assertTrue(matches2)

    def test_match_complete_success(self):
        request_def = RequestDef(
            url_pattern=r"^/users/(\d+)$",
            url_regex=re.compile(r"^/users/(\d+)$"),
            methods=["GET"],
            queryparams=[{"name": "active", "value": "true"}],
            headers=[{"name": "Authorization"}],
            body_pattern=None
        )

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/users/123?active=true",
            headers={"Authorization": "Bearer token"},
            query_params={"active": "true"},
            body=""
        )

        context = self.matcher.match(request_def, http_request, self.fixtures_dir)

        self.assertIsNotNone(context)
        self.assertEqual(context.PATH_PARAMS, ["123"])
        self.assertEqual(context.QUERY_PARAMS, {"active": "true"})
        self.assertIn("authorization", context.HEADERS)

    def test_match_url_fails(self):
        request_def = RequestDef(
            url_pattern=r"^/users$",
            url_regex=re.compile(r"^/users$")
        )

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/products",
            headers={},
            query_params={},
            body=""
        )

        context = self.matcher.match(request_def, http_request, self.fixtures_dir)
        self.assertIsNone(context)

    def test_match_method_fails(self):
        request_def = RequestDef(
            url_pattern=r"^/users$",
            url_regex=re.compile(r"^/users$"),
            methods=["POST"]
        )

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/users",
            headers={},
            query_params={},
            body=""
        )

        context = self.matcher.match(request_def, http_request, self.fixtures_dir)
        self.assertIsNone(context)

    def test_match_queryparams_fails(self):
        request_def = RequestDef(
            url_pattern=r"^/users$",
            url_regex=re.compile(r"^/users$"),
            queryparams=[{"name": "active"}]
        )

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/users",
            headers={},
            query_params={},
            body=""
        )

        context = self.matcher.match(request_def, http_request, self.fixtures_dir)
        self.assertIsNone(context)

    def test_match_headers_fails(self):
        request_def = RequestDef(
            url_pattern=r"^/users$",
            url_regex=re.compile(r"^/users$"),
            headers=[{"name": "Authorization"}]
        )

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/users",
            headers={},
            query_params={},
            body=""
        )

        context = self.matcher.match(request_def, http_request, self.fixtures_dir)
        self.assertIsNone(context)

    def test_match_body_fails(self):
        request_def = RequestDef(
            url_pattern=r"^/users$",
            url_regex=re.compile(r"^/users$"),
            body_pattern=r".*user_id.*"
        )

        http_request = HTTPRequest(
            method="GET",
            url="http://example.com/users",
            headers={},
            query_params={},
            body='{"name": "John"}'
        )

        context = self.matcher.match(request_def, http_request, self.fixtures_dir)
        self.assertIsNone(context)


class TestCaseInsensitiveDict(unittest.TestCase):
    def test_setitem_getitem(self):
        d = CaseInsensitiveDict()
        d["Content-Type"] = "application/json"
        self.assertEqual(d["content-type"], "application/json")
        self.assertEqual(d["CONTENT-TYPE"], "application/json")

    def test_init_with_data(self):
        d = CaseInsensitiveDict({"Authorization": "Bearer token"})
        self.assertEqual(d["authorization"], "Bearer token")

    def test_contains(self):
        d = CaseInsensitiveDict({"Authorization": "Bearer token"})
        self.assertTrue("authorization" in d)
        self.assertTrue("AUTHORIZATION" in d)
        self.assertFalse("content-type" in d)

    def test_get_with_default(self):
        d = CaseInsensitiveDict({"Authorization": "Bearer token"})
        self.assertEqual(d.get("authorization"), "Bearer token")
        self.assertEqual(d.get("missing", "default"), "default")
        self.assertIsNone(d.get("missing"))


if __name__ == "__main__":
    unittest.main()
