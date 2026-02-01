"""
Unit test configuration.

Unit tests should use mocked dependencies to test individual components
in isolation, separate from integration tests that use real databases.
"""

import pytest
from unittest.mock import Mock
from sqlmodel import Session
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_session


@pytest.fixture(scope="function")
def mock_db_session():
    """Create a mock database session for unit tests."""
    return Mock(spec=Session)


@pytest.fixture(scope="function")
def unit_test_client(mock_db_session):
    """
    Create a test client with mocked database for unit tests.
    
    This client uses mocked database sessions to test individual
    components in isolation without database dependencies.
    """
    # Override database dependency with mock
    app.dependency_overrides[get_session] = lambda: mock_db_session
    
    client = TestClient(app)
    
    yield client, mock_db_session
    
    # Clean up override
    if get_session in app.dependency_overrides:
        del app.dependency_overrides[get_session]