"""
Base abstract class for body matching strategies.

This module defines the BodyMatcher ABC (Abstract Base Class) that serves as the
contract for all body matching implementations in the mockserver. Body matchers
enable semantic comparison of request bodies beyond simple string matching.

The Strategy Pattern:
    Each concrete BodyMatcher subclass implements a different matching strategy:
    - RegexBodyMatcher: Pattern-based matching with regular expressions
    - VerbatimBodyMatcher: Exact byte-for-byte string comparison
    - XMLBodyMatcher: Semantic XML tree comparison (ignores formatting)
    - JSONBodyMatcher: Semantic JSON structure comparison (ignores key order)

All matchers must implement three core methods:
    - matches(): Compare expected vs actual body content
    - validate(): Verify body is well-formed for this format
    - normalize(): Parse body into canonical representation

This abstraction allows the mockserver to support multiple body matching strategies
while keeping the request matching logic (core.matcher) format-agnostic.
"""
from abc import ABC, abstractmethod
from typing import Any


class BodyMatcher(ABC):
    """
    Abstract base class for body matching strategies.

    This class defines the interface that all body matchers must implement.
    Subclasses provide concrete implementations for specific formats (XML, JSON)
    or matching modes (regex, verbatim).

    The BodyMatcher is used during request matching to determine if an incoming
    request's body content matches the expected content defined in a mock definition.

    Lifecycle During Request Matching:
        1. validate() is called on the incoming request body
        2. normalize() is called on both expected and actual bodies
        3. matches() performs the comparison using normalized forms

    Subclass Implementation Requirements:
        - Implement all three abstract methods
        - Ensure validate() raises ValueError for malformed content
        - Ensure normalize() returns a consistent canonical form
        - Ensure matches() is symmetric and deterministic

    Example:
        >>> class SimpleBodyMatcher(BodyMatcher):
        ...     def matches(self, expected: str, actual: str) -> bool:
        ...         return expected.strip() == actual.strip()
        ...     def validate(self, body: str) -> None:
        ...         pass  # No validation needed
        ...     def normalize(self, body: str) -> str:
        ...         return body.strip()
    """

    @abstractmethod
    def matches(self, expected: str, actual: str) -> bool:
        """
        Return True if actual body matches expected according to this strategy.

        This method implements the core matching logic. It should perform the
        comparison appropriate for this matcher's type (regex search, semantic
        comparison, exact equality, etc.).

        The method receives both bodies as strings and is responsible for parsing,
        normalizing, and comparing them. It should handle comparison errors gracefully
        and return False if the bodies don't match for any reason.

        Args:
            expected: Expected body content from the mock definition. This is the
                     baseline value that incoming requests will be compared against.
            actual: Actual body content from the incoming HTTP request that needs
                   to be validated against the expected value.

        Returns:
            True if the actual body matches the expected body according to this
            matcher's strategy. False if they don't match or if any error occurs
            during comparison.

        Example:
            >>> matcher = JSONBodyMatcher()
            >>> expected = '{"name": "Alice", "age": 30}'
            >>> actual = '{"age": 30, "name": "Alice"}'  # Different key order
            >>> matcher.matches(expected, actual)  # True (semantic match)
            True
        """
        pass

    @abstractmethod
    def validate(self, body: str) -> None:
        """
        Validate that body is well-formed according to this matcher's format.

        This method performs format-specific validation to ensure the body content
        is syntactically correct. For example, XML matchers check XML validity,
        JSON matchers check JSON syntax, etc.

        This validation is called on incoming request bodies before matching to
        provide early error detection. It's also called on mock definition bodies
        during configuration loading.

        The method should raise ValueError with a descriptive message if validation
        fails. If the body is valid, it should return None without error.

        Args:
            body: Body content to validate. This should be a string in the format
                 expected by this matcher (XML, JSON, etc.).

        Raises:
            ValueError: If the body is not well-formed or contains syntax errors.
                       The error message should clearly describe what's wrong.

        Example:
            >>> matcher = JSONBodyMatcher()
            >>> matcher.validate('{"valid": "json"}')  # No error
            >>> matcher.validate('{invalid json}')  # Raises ValueError
            Traceback (most recent call last):
                ...
            ValueError: JSON inválido: ...
        """
        pass

    @abstractmethod
    def normalize(self, body: str) -> Any:
        """
        Parse and normalize body to canonical form for comparison.

        This method transforms the raw body string into a normalized representation
        that can be used for semantic comparison. The return type depends on the
        matcher type:
            - XML matchers: Return xml.etree.ElementTree.Element
            - JSON matchers: Return parsed dict/list
            - Regex matchers: Return original string
            - Verbatim matchers: Return original string

        Normalization enables semantic comparison by abstracting away formatting
        differences (whitespace, key order, etc.) that don't affect meaning.

        Args:
            body: Raw body content as string to parse and normalize.

        Returns:
            Normalized representation of the body. The specific type depends on
            the matcher implementation:
                - ET.Element for XML
                - dict/list for JSON
                - str for regex/verbatim

        Raises:
            May raise parsing exceptions if the body cannot be normalized.
            Implementations should handle errors appropriately.

        Example:
            >>> matcher = JSONBodyMatcher()
            >>> normalized = matcher.normalize('{"a": 1, "b": 2}')
            >>> type(normalized)  # <class 'dict'>
            <class 'dict'>
            >>> normalized
            {'a': 1, 'b': 2}
        """
        pass
