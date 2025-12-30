"""Pytest configuration and fixtures for smoke tests."""

from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory path."""
    return PROJECT_ROOT
