"""
Database connection and session management.
"""

from sqlmodel import create_engine, Session
from app.core.config import settings

# Create database engine
# echo=True enables SQL logging for debugging
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)


def get_session():
    """
    Dependency to get a database session.
    Yields a session and closes it after use.
    """
    with Session(engine) as session:
        yield session
