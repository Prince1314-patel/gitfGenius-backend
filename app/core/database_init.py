"""
Database initialization and table existence checks for PostgreSQL.
Uses the SQLModel/SQLAlchemy engine; no Supabase dependency.
"""

import logging
import os
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# SQL scripts for table creation (used when generating migration file)
USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
"""

CONTACTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS public.contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    relationship_type VARCHAR(100),
    birthday DATE,
    user_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
);

-- Create index on user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON public.contacts(user_id);
"""

MEMORIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS public.memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    contact_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_contact FOREIGN KEY (contact_id) REFERENCES public.contacts(id) ON DELETE CASCADE
);

-- Create index on contact_id for faster queries
CREATE INDEX IF NOT EXISTS idx_memories_contact_id ON public.memories(contact_id);
"""


def check_table_exists(engine: Engine, table_name: str) -> bool:
    """
    Check if a table exists in the public schema using information_schema.

    Args:
        engine: SQLAlchemy engine (from app.database).
        table_name: Name of the table to check.

    Returns:
        bool: True if table exists, False otherwise.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = :name"
                ),
                {"name": table_name},
            )
            return result.fetchone() is not None
    except Exception as e:
        logger.debug("Error checking table '%s': %s", table_name, e)
        return False


def create_sql_migration_file() -> str:
    """
    Create a SQL migration file with all table creation scripts.

    Returns:
        str: Path to the created SQL file.
    """
    sql_content = f"""-- GiftGenius Database Schema
-- Run this in any PostgreSQL client (psql, DBeaver, or: docker exec -i giftgenius-postgres psql -U prince1314 -d giftgenius < migrations/001_create_tables.sql)

-- 1. Users Table
{USERS_TABLE_SQL}

-- 2. Contacts Table
{CONTACTS_TABLE_SQL}

-- 3. Memories Table
{MEMORIES_TABLE_SQL}

-- Verification query
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
    AND table_name IN ('users', 'contacts', 'memories')
ORDER BY table_name;
"""
    migrations_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "migrations"
    )
    os.makedirs(migrations_dir, exist_ok=True)
    sql_file_path = os.path.join(migrations_dir, "001_create_tables.sql")
    with open(sql_file_path, "w", encoding="utf-8") as f:
        f.write(sql_content)
    return sql_file_path


def init_database(engine: Engine) -> None:
    """
    Initialize database: check if required tables exist.
    If any are missing, create a SQL migration file and log instructions.

    Args:
        engine: SQLAlchemy engine (from app.database).
    """
    logger.info("Initializing database...")
    tables_to_check = ["users", "contacts", "memories"]
    table_status = {}
    missing_tables = []

    for table_name in tables_to_check:
        exists = check_table_exists(engine, table_name)
        table_status[table_name] = exists
        if exists:
            logger.info("Table '%s' exists", table_name)
        else:
            logger.warning("Table '%s' not found", table_name)
            missing_tables.append(table_name)

    existing_count = sum(1 for v in table_status.values() if v)
    logger.info("Database status: %s/%s tables exist", existing_count, len(tables_to_check))

    if missing_tables:
        logger.warning("Missing tables: %s", ", ".join(missing_tables))
        try:
            sql_file = create_sql_migration_file()
            logger.info("Created SQL migration file: %s", sql_file)
            logger.info(
                "Run the SQL file against PostgreSQL (e.g. docker exec -i giftgenius-postgres psql -U prince1314 -d giftgenius < %s)",
                sql_file,
            )
        except Exception as e:
            logger.error("Failed to create migration file: %s", e)
    else:
        logger.info("All required tables exist - database ready.")
