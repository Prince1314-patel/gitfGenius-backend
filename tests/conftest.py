"""
Test configuration for property-based tests and database setup.
"""

import os

# Use SQLite for tests if DATABASE_URL not set (e.g. no .env)
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from hypothesis import settings, Verbosity
import pytest
from tests.database import setup_test_database, test_session, clean_database

# Configure Hypothesis for faster testing
settings.register_profile("default", max_examples=50, verbosity=Verbosity.normal)
settings.load_profile("default")

# Import fixtures to make them available to all tests
# These fixtures are automatically discovered by pytest
__all__ = ["setup_test_database", "test_session", "clean_database"]