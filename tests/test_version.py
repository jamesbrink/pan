"""Tests for version module."""

import re
from version import __version__


def test_version_format():
    """Test that the version string follows semantic versioning."""
    assert re.match(r"^\d+\.\d+\.\d+$", __version__)