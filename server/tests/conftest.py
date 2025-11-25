"""
Pytest configuration and shared fixtures for mockserver tests.

This file is automatically discovered by pytest and makes fixtures
available to all test modules.
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers if needed
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


# Shared fixtures can be defined here
# Example:
# import pytest
#
# @pytest.fixture
# def temp_dir():
#     """Create a temporary directory for tests."""
#     temp_dir = tempfile.mkdtemp()
#     yield temp_dir
#     shutil.rmtree(temp_dir)
#
# @pytest.fixture
# def fixtures_dir():
#     """Get path to fixtures directory."""
#     return Path(__file__).parent / "fixtures"
