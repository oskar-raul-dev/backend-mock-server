"""
Body matching module for semantic matching of XML, JSON, and other formats.

This module provides:
- Abstract BodyMatcher base class
- Concrete matchers: XMLBodyMatcher, JSONBodyMatcher, RegexBodyMatcher, VerbatimBodyMatcher
- Configuration resolution with auto-detection from file extensions
- Factory pattern for creating appropriate matchers

Import submodules directly to avoid circular dependencies:
    from body_matching.base import BodyMatcher
    from body_matching.matchers import RegexBodyMatcher, VerbatimBodyMatcher, XMLBodyMatcher, JSONBodyMatcher
    from body_matching.config import BodyMatchingConfig, resolve_body_matching_config, auto_detect_from_extension, load_file_content
    from body_matching.factory import create_body_matcher
"""
