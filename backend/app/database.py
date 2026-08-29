"""
Database connection and session management.
"""

from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

# Create database engine
# echo=True enables SQL logging for debugging
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG, connect_args=connect_args)


def create_db_and_tables():
    import app.models

    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Dependency to get a database session.
    Yields a session and closes it after use.
    """
    with Session(engine) as session:
        yield session
