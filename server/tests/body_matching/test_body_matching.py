"""
Unit tests for body_matching module.
"""
import unittest
import tempfile
import os
from pathlib import Path

from body_matching.base import BodyMatcher
from body_matching.matchers import (
    RegexBodyMatcher,
    VerbatimBodyMatcher,
    XMLBodyMatcher,
    JSONBodyMatcher
)
from body_matching.config import (
    BodyMatchingConfig,
    resolve_body_matching_config,
    auto_detect_from_extension
)
from body_matching.factory import create_body_matcher


class TestRegexBodyMatcher(unittest.TestCase):
    """Tests for RegexBodyMatcher."""

    def test_matches_with_pattern(self):
        """Test regex matching with pattern."""
        matcher = RegexBodyMatcher(r".*<login>.*</login>.*")

        self.assertTrue(matcher.matches("", "<user><login>john</login></user>"))
        self.assertFalse(matcher.matches("", "<user><name>john</name></user>"))

    def test_matches_with_simple_string(self):
        """Test regex matching with simple string pattern."""
        matcher = RegexBodyMatcher("hello")

        self.assertTrue(matcher.matches("", "hello world"))
        self.assertTrue(matcher.matches("", "say hello"))
        self.assertFalse(matcher.matches("", "goodbye"))

    def test_invalid_regex_pattern(self):
        """Test that invalid regex pattern raises error."""
        with self.assertRaises(ValueError):
            RegexBodyMatcher("[invalid(")

    def test_validate_always_passes(self):
        """Test that validate always passes for regex."""
        matcher = RegexBodyMatcher(".*")
        matcher.validate("anything")  # Should not raise


class TestVerbatimBodyMatcher(unittest.TestCase):
    """Tests for VerbatimBodyMatcher."""

    def test_exact_match(self):
        """Test exact string matching."""
        matcher = VerbatimBodyMatcher()

        expected = '{"user": "john", "age": 30}'
        self.assertTrue(matcher.matches(expected, expected))

    def test_no_match_with_whitespace_difference(self):
        """Test that whitespace differences cause no match."""
        matcher = VerbatimBodyMatcher()

        expected = '{"user":"john"}'
        actual = '{"user": "john"}'
        self.assertFalse(matcher.matches(expected, actual))

    def test_validate_always_passes(self):
        """Test that validate always passes for verbatim."""
        matcher = VerbatimBodyMatcher()
        matcher.validate("anything")  # Should not raise


class TestXMLBodyMatcher(unittest.TestCase):
    """Tests for XMLBodyMatcher."""

    def test_semantic_match_ignores_whitespace(self):
        """Test that semantic matching ignores whitespace."""
        matcher = XMLBodyMatcher("semantic")

        expected = "<user><login>john</login><password>123</password></user>"
        actual = """<user>
            <login>john</login>
            <password>123</password>
        </user>"""

        self.assertTrue(matcher.matches(expected, actual))

    def test_semantic_match_same_structure(self):
        """Test semantic matching with same structure."""
        matcher = XMLBodyMatcher("semantic")

        xml1 = "<root><a>1</a><b>2</b></root>"
        xml2 = "<root><a>1</a><b>2</b></root>"

        self.assertTrue(matcher.matches(xml1, xml2))

    def test_no_match_different_tags(self):
        """Test no match with different tags."""
        matcher = XMLBodyMatcher("semantic")

        xml1 = "<root><a>1</a></root>"
        xml2 = "<root><b>1</b></root>"

        self.assertFalse(matcher.matches(xml1, xml2))

    def test_no_match_different_text(self):
        """Test no match with different text content."""
        matcher = XMLBodyMatcher("semantic")

        xml1 = "<root><a>1</a></root>"
        xml2 = "<root><a>2</a></root>"

        self.assertFalse(matcher.matches(xml1, xml2))

    def test_no_match_different_attributes(self):
        """Test no match with different attributes."""
        matcher = XMLBodyMatcher("semantic")

        xml1 = '<root><a id="1">text</a></root>'
        xml2 = '<root><a id="2">text</a></root>'

        self.assertFalse(matcher.matches(xml1, xml2))

    def test_validate_valid_xml(self):
        """Test validation of valid XML."""
        matcher = XMLBodyMatcher("semantic")
        matcher.validate("<root><a>1</a></root>")  # Should not raise

    def test_validate_invalid_xml(self):
        """Test validation of invalid XML."""
        matcher = XMLBodyMatcher("semantic")

        with self.assertRaises(ValueError) as cm:
            matcher.validate("<root><a>1</a>")

        self.assertIn("XML inválido", str(cm.exception))

    def test_invalid_matching_mode(self):
        """Test that invalid matching mode raises error."""
        with self.assertRaises(ValueError):
            XMLBodyMatcher("invalid_mode")


class TestJSONBodyMatcher(unittest.TestCase):
    """Tests for JSONBodyMatcher."""

    def test_semantic_match_ignores_whitespace(self):
        """Test that semantic matching ignores whitespace."""
        matcher = JSONBodyMatcher("semantic")

        expected = '{"user":"john","age":30}'
        actual = '{\n  "user": "john",\n  "age": 30\n}'

        self.assertTrue(matcher.matches(expected, actual))

    def test_semantic_match_ignores_key_order(self):
        """Test that semantic matching ignores key order."""
        matcher = JSONBodyMatcher("semantic")

        json1 = '{"user":"john","age":30}'
        json2 = '{"age":30,"user":"john"}'

        self.assertTrue(matcher.matches(json1, json2))

    def test_no_match_different_values(self):
        """Test no match with different values."""
        matcher = JSONBodyMatcher("semantic")

        json1 = '{"user":"john"}'
        json2 = '{"user":"jane"}'

        self.assertFalse(matcher.matches(json1, json2))

    def test_partial_mode_subset_matches(self):
        """Test partial matching where expected is subset of actual."""
        matcher = JSONBodyMatcher("partial")

        expected = '{"user":"john"}'
        actual = '{"user":"john","age":30,"city":"NYC"}'

        self.assertTrue(matcher.matches(expected, actual))

    def test_partial_mode_no_match_if_key_missing(self):
        """Test partial mode doesn't match if expected key is missing."""
        matcher = JSONBodyMatcher("partial")

        expected = '{"user":"john","age":30}'
        actual = '{"user":"john"}'

        self.assertFalse(matcher.matches(expected, actual))

    def test_validate_valid_json(self):
        """Test validation of valid JSON."""
        matcher = JSONBodyMatcher("semantic")
        matcher.validate('{"user":"john"}')  # Should not raise

    def test_validate_invalid_json(self):
        """Test validation of invalid JSON."""
        matcher = JSONBodyMatcher("semantic")

        with self.assertRaises(ValueError) as cm:
            matcher.validate('{"user":"john"')

        self.assertIn("JSON inválido", str(cm.exception))

    def test_invalid_matching_mode(self):
        """Test that invalid matching mode raises error."""
        with self.assertRaises(ValueError):
            JSONBodyMatcher("invalid_mode")


class TestAutoDetectFromExtension(unittest.TestCase):
    """Tests for auto_detect_from_extension function."""

    def test_xml_extension(self):
        """Test XML file extension detection."""
        format_type, matching_mode = auto_detect_from_extension("file.xml")
        self.assertEqual(format_type, "xml")
        self.assertEqual(matching_mode, "semantic")

    def test_json_extension(self):
        """Test JSON file extension detection."""
        format_type, matching_mode = auto_detect_from_extension("file.json")
        self.assertEqual(format_type, "json")
        self.assertEqual(matching_mode, "semantic")

    def test_yaml_extension(self):
        """Test YAML file extension detection."""
        format_type, matching_mode = auto_detect_from_extension("file.yaml")
        self.assertEqual(format_type, "yaml")
        self.assertEqual(matching_mode, "semantic")

    def test_yml_extension(self):
        """Test YML file extension detection."""
        format_type, matching_mode = auto_detect_from_extension("file.yml")
        self.assertEqual(format_type, "yaml")
        self.assertEqual(matching_mode, "semantic")

    def test_regex_extension(self):
        """Test regex file extension detection."""
        format_type, matching_mode = auto_detect_from_extension("file.regex")
        self.assertIsNone(format_type)
        self.assertEqual(matching_mode, "regex")

    def test_re_extension(self):
        """Test .re file extension detection."""
        format_type, matching_mode = auto_detect_from_extension("file.re")
        self.assertIsNone(format_type)
        self.assertEqual(matching_mode, "regex")

    def test_txt_extension(self):
        """Test .txt file defaults to verbatim."""
        format_type, matching_mode = auto_detect_from_extension("file.txt")
        self.assertIsNone(format_type)
        self.assertEqual(matching_mode, "verbatim")

    def test_unknown_extension(self):
        """Test unknown extension defaults to verbatim."""
        format_type, matching_mode = auto_detect_from_extension("file.unknown")
        self.assertIsNone(format_type)
        self.assertEqual(matching_mode, "verbatim")


class TestResolveBodyMatchingConfig(unittest.TestCase):
    """Tests for resolve_body_matching_config function."""

    def test_string_body_spec_is_regex(self):
        """Test that string body spec is treated as regex."""
        config = resolve_body_matching_config(".*pattern.*")

        self.assertEqual(config.content, ".*pattern.*")
        self.assertIsNone(config.format)
        self.assertEqual(config.matching_mode, "regex")
        self.assertIsNone(config.validator)
        self.assertIsNone(config.processor)

    def test_dict_with_value_and_format_xml(self):
        """Test dict with value and XML format."""
        body_spec = {
            "value": "<user><login>john</login></user>",
            "format": "xml"
        }
        config = resolve_body_matching_config(body_spec)

        self.assertEqual(config.content, "<user><login>john</login></user>")
        self.assertEqual(config.format, "xml")
        self.assertEqual(config.matching_mode, "semantic")

    def test_dict_with_value_and_format_json(self):
        """Test dict with value and JSON format."""
        body_spec = {
            "value": '{"user":"john"}',
            "format": "json"
        }
        config = resolve_body_matching_config(body_spec)

        self.assertEqual(config.content, '{"user":"john"}')
        self.assertEqual(config.format, "json")
        self.assertEqual(config.matching_mode, "semantic")

    def test_dict_with_value_no_format_defaults_to_verbatim(self):
        """Test dict with value but no format defaults to verbatim."""
        body_spec = {
            "value": "exact string to match"
        }
        config = resolve_body_matching_config(body_spec)

        self.assertEqual(config.content, "exact string to match")
        self.assertIsNone(config.format)
        self.assertEqual(config.matching_mode, "verbatim")

    def test_dict_with_explicit_matching_mode(self):
        """Test dict with explicit matching_mode overrides default."""
        body_spec = {
            "value": '{"user":"john"}',
            "matching_mode": "regex"
        }
        config = resolve_body_matching_config(body_spec)

        self.assertEqual(config.matching_mode, "regex")

    def test_dict_with_file_loads_content(self):
        """Test dict with file loads content from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = os.path.join(tmpdir, "test.xml")
            with open(test_file, 'w') as f:
                f.write("<root>content</root>")

            body_spec = {
                "file": "test.xml"
            }
            config = resolve_body_matching_config(body_spec, base_dir=tmpdir)

            self.assertEqual(config.content, "<root>content</root>")
            self.assertEqual(config.format, "xml")
            self.assertEqual(config.matching_mode, "semantic")

    def test_dict_with_file_auto_detects_json(self):
        """Test dict with .json file auto-detects format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = os.path.join(tmpdir, "test.json")
            with open(test_file, 'w') as f:
                f.write('{"key":"value"}')

            body_spec = {
                "file": "test.json"
            }
            config = resolve_body_matching_config(body_spec, base_dir=tmpdir)

            self.assertEqual(config.format, "json")
            self.assertEqual(config.matching_mode, "semantic")

    def test_error_both_file_and_value(self):
        """Test error when both file and value are specified."""
        body_spec = {
            "file": "test.xml",
            "value": "<root/>"
        }

        with self.assertRaises(ValueError) as cm:
            resolve_body_matching_config(body_spec)

        self.assertIn("Cannot specify both 'file' and 'value'", str(cm.exception))

    def test_error_neither_file_nor_value(self):
        """Test error when neither file nor value are specified."""
        body_spec = {
            "format": "xml"
        }

        with self.assertRaises(ValueError) as cm:
            resolve_body_matching_config(body_spec)

        self.assertIn("Must specify either 'file' or 'value'", str(cm.exception))

    def test_error_regex_with_format(self):
        """Test error when regex matching_mode is used with format."""
        body_spec = {
            "value": "<root/>",
            "format": "xml",
            "matching_mode": "regex"
        }

        with self.assertRaises(ValueError) as cm:
            resolve_body_matching_config(body_spec)

        self.assertIn("Cannot use format with matching_mode='regex'", str(cm.exception))

    def test_error_semantic_without_format(self):
        """Test error when semantic matching_mode is used without format."""
        body_spec = {
            "value": "content",
            "matching_mode": "semantic"
        }

        with self.assertRaises(ValueError) as cm:
            resolve_body_matching_config(body_spec)

        self.assertIn("requires 'format' to be specified", str(cm.exception))

    def test_error_unsupported_format(self):
        """Test error with unsupported format."""
        body_spec = {
            "value": "content",
            "format": "unsupported"
        }

        with self.assertRaises(ValueError) as cm:
            resolve_body_matching_config(body_spec)

        self.assertIn("Unsupported format: unsupported", str(cm.exception))


class TestCreateBodyMatcher(unittest.TestCase):
    """Tests for create_body_matcher factory function."""

    def test_create_regex_matcher(self):
        """Test creating regex matcher."""
        config = BodyMatchingConfig(
            content=".*pattern.*",
            format=None,
            matching_mode="regex",
            validator=None,
            processor=None
        )

        matcher, expected_value, validator, processor = create_body_matcher(config)

        self.assertIsInstance(matcher, RegexBodyMatcher)
        self.assertEqual(expected_value, ".*pattern.*")
        self.assertIsNone(validator)
        self.assertIsNone(processor)

    def test_create_verbatim_matcher(self):
        """Test creating verbatim matcher."""
        config = BodyMatchingConfig(
            content="exact string",
            format=None,
            matching_mode="verbatim",
            validator=None,
            processor=None
        )

        matcher, expected_value, validator, processor = create_body_matcher(config)

        self.assertIsInstance(matcher, RegexBodyMatcher)  # Uses escaped regex
        self.assertEqual(expected_value, "exact string")

    def test_create_xml_semantic_matcher(self):
        """Test creating XML semantic matcher."""
        config = BodyMatchingConfig(
            content="<root><a>1</a></root>",
            format="xml",
            matching_mode="semantic",
            validator=None,
            processor=None
        )

        matcher, expected_value, validator, processor = create_body_matcher(config)

        self.assertIsInstance(matcher, XMLBodyMatcher)
        self.assertEqual(expected_value, "<root><a>1</a></root>")

    def test_create_json_semantic_matcher(self):
        """Test creating JSON semantic matcher."""
        config = BodyMatchingConfig(
            content='{"key":"value"}',
            format="json",
            matching_mode="semantic",
            validator=None,
            processor=None
        )

        matcher, expected_value, validator, processor = create_body_matcher(config)

        self.assertIsInstance(matcher, JSONBodyMatcher)
        self.assertEqual(expected_value, '{"key":"value"}')

    def test_create_json_partial_matcher(self):
        """Test creating JSON partial matcher."""
        config = BodyMatchingConfig(
            content='{"key":"value"}',
            format="json",
            matching_mode="partial",
            validator=None,
            processor=None
        )

        matcher, expected_value, validator, processor = create_body_matcher(config)

        self.assertIsInstance(matcher, JSONBodyMatcher)
        self.assertEqual(matcher.matching_mode, "partial")

    def test_validates_mock_body_on_creation(self):
        """Test that invalid mock body raises error on matcher creation."""
        config = BodyMatchingConfig(
            content="<invalid xml",
            format="xml",
            matching_mode="semantic",
            validator=None,
            processor=None
        )

        with self.assertRaises(ValueError) as cm:
            create_body_matcher(config)

        self.assertIn("Invalid body value", str(cm.exception))

    def test_validator_function_is_preserved(self):
        """Test that validator function is preserved."""
        def my_validator(body):
            pass

        config = BodyMatchingConfig(
            content='{"key":"value"}',
            format="json",
            matching_mode="semantic",
            validator=my_validator,
            processor=None
        )

        matcher, expected_value, validator, processor = create_body_matcher(config)

        self.assertEqual(validator, my_validator)

    def test_processor_function_is_preserved(self):
        """Test that processor function is preserved."""
        def my_processor(body):
            return {"extracted": "value"}

        config = BodyMatchingConfig(
            content='{"key":"value"}',
            format="json",
            matching_mode="semantic",
            validator=None,
            processor=my_processor
        )

        matcher, expected_value, validator, processor = create_body_matcher(config)

        self.assertEqual(processor, my_processor)

    def test_error_if_validator_not_callable(self):
        """Test error if validator is not callable."""
        config = BodyMatchingConfig(
            content='{"key":"value"}',
            format="json",
            matching_mode="semantic",
            validator="not_callable",
            processor=None
        )

        with self.assertRaises(ValueError) as cm:
            create_body_matcher(config)

        self.assertIn("Validator must be callable", str(cm.exception))

    def test_error_if_processor_not_callable(self):
        """Test error if processor is not callable."""
        config = BodyMatchingConfig(
            content='{"key":"value"}',
            format="json",
            matching_mode="semantic",
            validator=None,
            processor="not_callable"
        )

        with self.assertRaises(ValueError) as cm:
            create_body_matcher(config)

        self.assertIn("Processor must be callable", str(cm.exception))

    def test_error_if_processor_returns_non_dict(self):
        """Test error if processor returns non-dict."""
        def bad_processor(body):
            return "not a dict"

        config = BodyMatchingConfig(
            content='{"key":"value"}',
            format="json",
            matching_mode="semantic",
            validator=None,
            processor=bad_processor
        )

        with self.assertRaises(ValueError) as cm:
            create_body_matcher(config)

        self.assertIn("Processor must return dict", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
