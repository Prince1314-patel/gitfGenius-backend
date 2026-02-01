"""
Test database configuration and utilities.

This module provides test database setup using SQLite in-memory database
for fast, isolated testing without affecting production data.
"""

import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from app.database import get_session
from app.main import app


# Test database URL - Use shared in-memory SQLite database
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with StaticPool to ensure single connection is reused
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    poolclass=StaticPool,  # Use StaticPool to share the same connection
    echo=False  # Set to True for SQL debugging
)


def get_test_session():
    """
    Test database session dependency override.
    
    This function replaces the production get_session dependency
    during testing to use the test database instead.
    """
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Set up test database for the entire test session.
    
    This fixture:
    1. Creates all tables in the test database
    2. Overrides the database dependency in FastAPI
    3. Cleans up after all tests complete
    
    Scope: session - runs once for all tests
    Autouse: True - automatically used by all tests
    """
    # Create all tables in test database
    SQLModel.metadata.create_all(test_engine)
    
    # Override the database dependency
    app.dependency_overrides[get_session] = get_test_session
    
    yield  # This is where tests run
    
    # Cleanup after all tests
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_session():
    """
    Provide a test database session for individual tests.
    
    This fixture provides a fresh database session for each test
    and automatically rolls back transactions to keep tests isolated.
    
    Scope: function - new session for each test
    """
    with Session(test_engine) as session:
        yield session
        # Session automatically closes and rolls back


@pytest.fixture(scope="function")
def clean_database():
    """
    Clean database between tests.
    
    This fixture truncates all tables to ensure each test
    starts with a clean database state.
    """
    from sqlalchemy import text
    
    with Session(test_engine) as session:
        # Get all table names
        tables = SQLModel.metadata.tables.keys()
        
        # Truncate all tables (SQLite doesn't support TRUNCATE, use DELETE)
        for table_name in tables:
            session.exec(text(f"DELETE FROM {table_name}"))
        
        session.commit()
    
    yield
    
    # Cleanup after test
    with Session(test_engine) as session:
        for table_name in tables:
            session.exec(text(f"DELETE FROM {table_name}"))
        session.commit()