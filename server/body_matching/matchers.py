"""
Concrete implementations of body matching strategies.

This module provides four concrete BodyMatcher implementations, each with a
different matching strategy:

1. RegexBodyMatcher:
   - Uses regular expressions to match body content
   - Most flexible, supports pattern-based matching
   - Use case: Matching bodies with variable data (timestamps, IDs, etc.)

2. VerbatimBodyMatcher:
   - Exact byte-for-byte string comparison
   - Strictest matching mode
   - Use case: When exact body match is required (no formatting differences)

3. XMLBodyMatcher:
   - Semantic XML tree comparison
   - Ignores whitespace, formatting, and attribute order
   - Supports three matching modes: semantic, strict, partial
   - Use case: Matching SOAP requests, XML APIs where formatting varies

4. JSONBodyMatcher:
   - Semantic JSON structure comparison
   - Ignores key order and whitespace
   - Supports three matching modes: semantic, strict, partial
   - Use case: Matching REST API requests with JSON bodies

Matching Modes:
    - semantic: Full equality comparison (default for XML/JSON)
    - strict: Same as semantic for now (future: enforce ordering)
    - partial: Expected is subset of actual (useful for flexible matching)

All matchers follow the BodyMatcher contract: matches(), validate(), normalize().
"""
import re
import json
import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

from .base import BodyMatcher


class RegexBodyMatcher(BodyMatcher):
    """
    Matches request body using regular expression patterns.

    This matcher uses Python's re module to perform pattern-based matching on
    request bodies. It's the most flexible matcher, suitable for matching bodies
    with variable data like timestamps, UUIDs, or dynamically generated content.

    The pattern is compiled once during initialization for performance. Matching
    uses re.search(), so the pattern can match anywhere in the body (use ^ and $
    for full-body matching).

    Characteristics:
        - No validation: Any string is a valid body
        - No normalization: Bodies used as-is
        - Partial matching: Pattern can match substring (use anchors if needed)
        - Case-sensitive: Use (?i) flag for case-insensitive matching

    Example:
        >>> # Match body containing timestamp
        >>> matcher = RegexBodyMatcher(r'"timestamp":\s*"\d{4}-\d{2}-\d{2}')
        >>> matcher.matches("", '{"timestamp": "2024-01-15"}')
        True
        >>> matcher.matches("", '{"timestamp": "invalid"}')
        False

    Example with full-body match:
        >>> # Match exact structure with variable values
        >>> matcher = RegexBodyMatcher(r'^{"id":\s*\d+,\s*"name":\s*".*"}$')
        >>> matcher.matches("", '{"id": 123, "name": "Alice"}')
        True
    """

    def __init__(self, pattern: str):
        """
        Initialize regex matcher with a compiled pattern.

        Args:
            pattern: Regular expression pattern to match request bodies against.
                    The pattern is compiled once during initialization.

        Raises:
            ValueError: If the pattern is not a valid regular expression.

        Example:
            >>> matcher = RegexBodyMatcher(r'\d{3}-\d{3}-\d{4}')  # Phone number
            >>> matcher = RegexBodyMatcher(r'[invalid(')  # Raises ValueError
            Traceback (most recent call last):
                ...
            ValueError: Invalid regex pattern: ...
        """
        try:
            self.pattern = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

    def matches(self, expected: str, actual: str) -> bool:
        """
        Return True if actual body matches the regex pattern.

        Uses re.search() to find the pattern anywhere in the actual body.
        The expected parameter is ignored for regex matching (the pattern
        itself is the expected value).

        Args:
            expected: Not used for regex matching (pattern is stored in self.pattern)
            actual: Actual request body to search for pattern

        Returns:
            True if pattern is found in actual body, False otherwise

        Example:
            >>> matcher = RegexBodyMatcher(r'"status":\s*"active"')
            >>> matcher.matches("", '{"status": "active", "user": "bob"}')
            True
            >>> matcher.matches("", '{"status": "inactive"}')
            False
        """
        return self.pattern.search(actual) is not None

    def validate(self, body: str) -> None:
        """
        No validation needed for regex matching.

        Regex patterns can match any string, so there's no validation to perform.
        This method exists to satisfy the BodyMatcher interface.

        Args:
            body: Body to validate (ignored)
        """
        pass

    def normalize(self, body: str) -> Any:
        """
        Return body as-is without normalization.

        Regex matching operates directly on the raw string, so no normalization
        is needed or performed.

        Args:
            body: Body to normalize

        Returns:
            The body unchanged
        """
        return body


class VerbatimBodyMatcher(BodyMatcher):
    """
    Matches request body with exact byte-for-byte string comparison.

    This is the strictest matching mode - it requires the actual request body
    to be character-for-character identical to the expected body. No normalization,
    no whitespace trimming, no semantic comparison.

    Use this matcher when you need exact matching including:
        - Exact whitespace (spaces, tabs, newlines)
        - Exact character casing
        - Exact formatting

    This is useful for binary data, pre-formatted text, or when you want to ensure
    clients send precisely formatted requests.

    Characteristics:
        - No validation: Any string is valid
        - No normalization: Bodies compared as-is
        - Exact matching: Even one different character causes mismatch
        - Fast: Simple string equality (O(n))

    Example:
        >>> matcher = VerbatimBodyMatcher()
        >>> expected = '{"name":"Alice"}'
        >>> matcher.matches(expected, '{"name":"Alice"}')  # Exact match
        True
        >>> matcher.matches(expected, '{"name": "Alice"}')  # Extra space!
        False
        >>> matcher.matches(expected, '{"name":"alice"}')  # Different case!
        False
    """

    def matches(self, expected: str, actual: str) -> bool:
        """
        Return True if bodies are exactly identical.

        Performs simple string equality check with no preprocessing.

        Args:
            expected: Expected body from mock definition
            actual: Actual request body

        Returns:
            True only if strings are byte-for-byte identical

        Example:
            >>> matcher = VerbatimBodyMatcher()
            >>> matcher.matches("hello", "hello")
            True
            >>> matcher.matches("hello", "Hello")  # Case matters
            False
            >>> matcher.matches("hello", "hello ")  # Whitespace matters
            False
        """
        return expected == actual

    def validate(self, body: str) -> None:
        """
        No validation needed for verbatim matching.

        Any string is a valid body for verbatim comparison.

        Args:
            body: Body to validate (ignored)
        """
        pass

    def normalize(self, body: str) -> Any:
        """
        Return body as-is without any normalization.

        Verbatim matching requires exact string, so no normalization is applied.

        Args:
            body: Body to normalize

        Returns:
            The body unchanged
        """
        return body


class XMLBodyMatcher(BodyMatcher):
    """
    Matches XML request bodies with semantic comparison.

    This matcher parses XML bodies into element trees and performs semantic
    comparison, ignoring:
        - Whitespace between elements
        - Text content whitespace (leading/trailing)
        - XML declaration differences
        - Namespace prefix variations (if URIs match)

    The matcher ensures:
        - Element tags match
        - Text content matches (after whitespace normalization)
        - Attributes match (exact key-value pairs)
        - Child elements match (order matters in XML)

    This is ideal for SOAP APIs, XML-RPC, or any XML-based request matching where
    formatting can vary but structure must match exactly.

    Matching Modes:
        - semantic: Full tree equality (default)
        - strict: Same as semantic (future: namespace-aware)
        - partial: Not yet implemented

    Example:
        >>> matcher = XMLBodyMatcher()
        >>> expected = '<user><name>Alice</name><age>30</age></user>'
        >>> actual = '''
        ... <user>
        ...   <name>Alice</name>
        ...   <age>30</age>
        ... </user>
        ... '''
        >>> matcher.matches(expected, actual)  # Whitespace ignored
        True

    Example with attributes:
        >>> expected = '<user id="123" role="admin"/>'
        >>> actual = '<user role="admin" id="123"/>'  # Different order
        >>> matcher.matches(expected, actual)  # Attribute order doesn't matter
        True
    """

    def __init__(self, matching_mode: str = "semantic"):
        """
        Initialize XML matcher with specified matching mode.

        Args:
            matching_mode: Matching strategy to use. Options:
                          - "semantic": Full tree equality (default)
                          - "strict": Same as semantic for now
                          - "partial": Not yet implemented

        Raises:
            ValueError: If matching_mode is not one of the valid options.

        Example:
            >>> matcher = XMLBodyMatcher("semantic")
            >>> matcher = XMLBodyMatcher("invalid")  # Raises ValueError
            Traceback (most recent call last):
                ...
            ValueError: Invalid matching_mode for XML: invalid. Must be 'semantic', 'strict', or 'partial'
        """
        if matching_mode not in ("semantic", "strict", "partial"):
            raise ValueError(
                f"Invalid matching_mode for XML: {matching_mode}. "
                f"Must be 'semantic', 'strict', or 'partial'"
            )
        self.matching_mode = matching_mode

    def validate(self, body: str) -> None:
        """
        Validate that body is well-formed XML.

        Attempts to parse the XML to verify it's syntactically correct.

        Args:
            body: XML string to validate

        Raises:
            ValueError: If XML parsing fails

        Example:
            >>> matcher = XMLBodyMatcher()
            >>> matcher.validate('<valid><xml/></valid>')  # No error
            >>> matcher.validate('<invalid xml')  # Raises ValueError
            Traceback (most recent call last):
                ...
            ValueError: XML inválido: ...
        """
        try:
            ET.fromstring(body)
        except ET.ParseError as e:
            raise ValueError(f"XML inválido: {e}")

    def normalize(self, body: str) -> ET.Element:
        """
        Parse XML string to ElementTree.Element.

        Args:
            body: XML string to parse

        Returns:
            Parsed XML element tree root

        Raises:
            ET.ParseError: If XML is malformed

        Example:
            >>> matcher = XMLBodyMatcher()
            >>> elem = matcher.normalize('<user><name>Alice</name></user>')
            >>> elem.tag
            'user'
            >>> elem[0].tag
            'name'
        """
        return ET.fromstring(body)

    def matches(self, expected: str, actual: str) -> bool:
        """
        Compare XML trees semantically.

        Parses both expected and actual XML strings and compares their
        element trees recursively. Returns False if parsing fails or
        trees don't match.

        Args:
            expected: Expected XML from mock definition
            actual: Actual XML from incoming request

        Returns:
            True if XML trees are semantically equal, False otherwise

        Example:
            >>> matcher = XMLBodyMatcher()
            >>> expected = '<a>  <b>1</b>  </a>'  # Extra whitespace
            >>> actual = '<a><b>1</b></a>'
            >>> matcher.matches(expected, actual)
            True
        """
        try:
            expected_tree = self.normalize(expected)
            actual_tree = self.normalize(actual)
            return self._compare_elements(expected_tree, actual_tree)
        except Exception as e:
            logging.debug(f"XML matching failed: {e}")
            return False

    def _compare_elements(self, e1: ET.Element, e2: ET.Element) -> bool:
        """
        Recursively compare two XML elements for equality.

        Compares element tags, text content (whitespace-normalized), tail content,
        attributes, and recursively compares all child elements.

        Element order matters in XML, so children must appear in the same order.

        Args:
            e1: First XML element to compare
            e2: Second XML element to compare

        Returns:
            True if elements are semantically equal according to matching rules

        Example:
            >>> matcher = XMLBodyMatcher()
            >>> e1 = ET.fromstring('<a><b>1</b><c>2</c></a>')
            >>> e2 = ET.fromstring('<a><b>1</b><c>2</c></a>')
            >>> matcher._compare_elements(e1, e2)
            True
            >>> e3 = ET.fromstring('<a><c>2</c><b>1</b></a>')  # Different order
            >>> matcher._compare_elements(e1, e3)
            False
        """
        # Tag must match
        if e1.tag != e2.tag:
            return False

        # Text content must match (stripped)
        if (e1.text or '').strip() != (e2.text or '').strip():
            return False

        # Tail content must match (stripped)
        if (e1.tail or '').strip() != (e2.tail or '').strip():
            return False

        # Attributes must match
        if e1.attrib != e2.attrib:
            return False

        # Number of children must match
        if len(e1) != len(e2):
            return False

        # Compare children (order matters in XML)
        for child1, child2 in zip(e1, e2):
            if not self._compare_elements(child1, child2):
                return False

        return True


class JSONBodyMatcher(BodyMatcher):
    """
    Matches JSON request bodies with semantic comparison.

    This matcher parses JSON bodies into Python objects (dicts/lists) and performs
    semantic comparison, ignoring:
        - Key order in objects ({"a":1,"b":2} == {"b":2,"a":1})
        - Whitespace and formatting
        - Float precision differences (within Python's equality)

    The matcher supports three matching modes:
        1. semantic: Full equality (default) - structures must match exactly
        2. strict: Same as semantic (future: could enforce key order)
        3. partial: Subset matching - expected is subset of actual

    Partial matching is powerful for flexible request validation where you only
    care about certain fields being present.

    Example (semantic mode):
        >>> matcher = JSONBodyMatcher()
        >>> expected = '{"name": "Alice", "age": 30}'
        >>> actual = '{"age": 30, "name": "Alice"}'  # Different key order
        >>> matcher.matches(expected, actual)
        True

    Example (partial mode):
        >>> matcher = JSONBodyMatcher("partial")
        >>> expected = '{"name": "Alice"}'  # Only care about name
        >>> actual = '{"name": "Alice", "age": 30, "city": "NYC"}'
        >>> matcher.matches(expected, actual)  # Extra fields OK
        True

    Example (nested structures):
        >>> matcher = JSONBodyMatcher()
        >>> expected = '{"user": {"id": 1, "name": "Bob"}, "active": true}'
        >>> actual = '{"active": true, "user": {"name": "Bob", "id": 1}}'
        >>> matcher.matches(expected, actual)
        True
    """

    def __init__(self, matching_mode: str = "semantic"):
        """
        Initialize JSON matcher with specified matching mode.

        Args:
            matching_mode: Matching strategy to use. Options:
                          - "semantic": Full equality (default)
                          - "strict": Same as semantic for now
                          - "partial": Expected is subset of actual

        Raises:
            ValueError: If matching_mode is not one of the valid options.

        Example:
            >>> matcher = JSONBodyMatcher("semantic")
            >>> partial_matcher = JSONBodyMatcher("partial")
            >>> matcher = JSONBodyMatcher("invalid")  # Raises ValueError
            Traceback (most recent call last):
                ...
            ValueError: Invalid matching_mode for JSON: invalid. Must be 'semantic', 'strict', or 'partial'
        """
        if matching_mode not in ("semantic", "strict", "partial"):
            raise ValueError(
                f"Invalid matching_mode for JSON: {matching_mode}. "
                f"Must be 'semantic', 'strict', or 'partial'"
            )
        self.matching_mode = matching_mode

    def validate(self, body: str) -> None:
        """
        Validate that body is well-formed JSON.

        Attempts to parse the JSON to verify it's syntactically correct.

        Args:
            body: JSON string to validate

        Raises:
            ValueError: If JSON parsing fails

        Example:
            >>> matcher = JSONBodyMatcher()
            >>> matcher.validate('{"valid": "json"}')  # No error
            >>> matcher.validate('{invalid json}')  # Raises ValueError
            Traceback (most recent call last):
                ...
            ValueError: JSON inválido: ...
        """
        try:
            json.loads(body)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido: {e}")

    def normalize(self, body: str) -> Dict[str, Any]:
        """
        Parse JSON string to Python dict/list.

        Args:
            body: JSON string to parse

        Returns:
            Parsed Python object (typically dict, but can be list, str, etc.)

        Raises:
            json.JSONDecodeError: If JSON is malformed

        Example:
            >>> matcher = JSONBodyMatcher()
            >>> obj = matcher.normalize('{"a": 1, "b": [2, 3]}')
            >>> obj
            {'a': 1, 'b': [2, 3]}
            >>> type(obj)
            <class 'dict'>
        """
        return json.loads(body)

    def matches(self, expected: str, actual: str) -> bool:
        """
        Compare JSON structures according to matching mode.

        Parses both expected and actual JSON strings and compares them:
            - semantic/strict: Full equality (==)
            - partial: Expected is subset of actual

        Returns False if parsing fails or structures don't match.

        Args:
            expected: Expected JSON from mock definition
            actual: Actual JSON from incoming request

        Returns:
            True if JSON structures match according to matching_mode

        Example (semantic):
            >>> matcher = JSONBodyMatcher("semantic")
            >>> matcher.matches('{"a": 1}', '{"a": 1}')
            True
            >>> matcher.matches('{"a": 1}', '{"a": 1, "b": 2}')  # Extra field
            False

        Example (partial):
            >>> matcher = JSONBodyMatcher("partial")
            >>> matcher.matches('{"a": 1}', '{"a": 1, "b": 2}')  # Extra field OK
            True
        """
        try:
            expected_obj = self.normalize(expected)
            actual_obj = self.normalize(actual)

            if self.matching_mode == "semantic":
                return expected_obj == actual_obj
            elif self.matching_mode == "partial":
                return self._is_subset(expected_obj, actual_obj)
            else:  # strict
                # For strict mode, we could enforce key ordering, but Python
                # dicts don't preserve insertion order in comparison
                # So strict is same as semantic for now
                return expected_obj == actual_obj
        except Exception as e:
            logging.debug(f"JSON matching failed: {e}")
            return False

    def _is_subset(self, expected: Any, actual: Any) -> bool:
        """
        Recursively check if expected structure is a subset of actual.

        For dictionaries:
            - All keys in expected must exist in actual
            - Values must match recursively (can also be subsets)

        For lists:
            - All items in expected must have a matching item in actual
            - Order doesn't matter

        For primitives:
            - Must be equal

        Args:
            expected: Expected value/structure (subset)
            actual: Actual value/structure (superset)

        Returns:
            True if expected is contained in actual

        Example (dict subset):
            >>> matcher = JSONBodyMatcher("partial")
            >>> matcher._is_subset({"a": 1}, {"a": 1, "b": 2})
            True
            >>> matcher._is_subset({"a": 1, "b": 2}, {"a": 1})
            False

        Example (nested subset):
            >>> expected = {"user": {"name": "Alice"}}
            >>> actual = {"user": {"name": "Alice", "age": 30}, "active": True}
            >>> matcher._is_subset(expected, actual)
            True

        Example (list subset):
            >>> matcher._is_subset([1, 2], [1, 2, 3])
            True
        """
        if isinstance(expected, dict) and isinstance(actual, dict):
            for key, value in expected.items():
                if key not in actual:
                    return False
                if not self._is_subset(value, actual[key]):
                    return False
            return True
        elif isinstance(expected, list) and isinstance(actual, list):
            # For lists, check if all expected items are in actual
            return all(any(self._is_subset(e, a) for a in actual) for e in expected)
        else:
            return expected == actual
