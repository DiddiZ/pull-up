"""Pytest fixtures.

The fixtures defined here are available to all tests.
"""

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def data_dir() -> Path:
    """Return the path to the data directory."""
    data_dir = Path(__file__).parent / "data"
    assert data_dir.is_dir()
    return data_dir
