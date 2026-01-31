from sqlmodel import SQLModel, Session, create_engine
from app.core.config import settings

# Create database engine
# Pool size 5, max overflow 10 are good defaults for development
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

def create_db_and_tables():
    """
    Create all tables defined in SQLModel metadata.
    This is called on application startup.
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Dependency to get a database session.
    Yields a session and closes it after use.
    """
    with Session(engine) as session:
        yield session
