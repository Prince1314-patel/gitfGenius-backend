"""
Database initialization and table creation module.
Automatically creates tables if they don't exist in Supabase.
"""

from supabase import Client
from app.core.config import settings
import logging
import os

logger = logging.getLogger(__name__)


# SQL scripts for table creation
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


def check_table_exists(supabase_client: Client, table_name: str) -> bool:
    """
    Check if a table exists by attempting to query it.
    
    Args:
        supabase_client: Supabase client instance
        table_name: Name of the table to check
        
    Returns:
        bool: True if table exists, False otherwise
    """
    try:
        supabase_client.table(table_name).select("id").limit(1).execute()
        return True
    except Exception as e:
        error_msg = str(e).lower()
        # Check if error is about missing table
        if "pgrst205" in error_msg or "could not find" in error_msg or "does not exist" in error_msg:
            return False
        # If it's a different error, log it but assume table doesn't exist
        logger.debug(f"Error checking table '{table_name}': {str(e)}")
        return False


def create_sql_migration_file() -> str:
    """
    Create a SQL migration file with all table creation scripts.
    
    Returns:
        str: Path to the created SQL file
    """
    sql_content = f"""-- GiftGenius Database Schema
-- Run this SQL in your Supabase SQL Editor to create all required tables

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
    
    # Create migrations directory if it doesn't exist
    migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "migrations")
    os.makedirs(migrations_dir, exist_ok=True)
    
    # Write SQL file
    sql_file_path = os.path.join(migrations_dir, "001_create_tables.sql")
    with open(sql_file_path, "w", encoding="utf-8") as f:
        f.write(sql_content)
    
    return sql_file_path


def init_database(supabase_client: Client) -> None:
    """
    Initialize database by checking if required tables exist.
    If tables don't exist, creates a SQL migration file for manual execution.
    
    Args:
        supabase_client: Supabase client instance
    """
    logger.info("🚀 Initializing database...")
    
    tables_to_check = ["users", "contacts", "memories"]
    table_status = {}
    missing_tables = []
    
    # Check each table
    for table_name in tables_to_check:
        exists = check_table_exists(supabase_client, table_name)
        table_status[table_name] = exists
        
        if exists:
            logger.info(f"✅ Table '{table_name}' exists")
        else:
            logger.warning(f"⚠️  Table '{table_name}' not found")
            missing_tables.append(table_name)
    
    # Summary
    existing_count = sum(1 for exists in table_status.values() if exists)
    missing_count = len(missing_tables)
    
    logger.info(f"📊 Database status: {existing_count}/{len(tables_to_check)} tables exist")
    
    if missing_tables:
        logger.warning(f"⚠️  Missing tables: {', '.join(missing_tables)}")
        
        # Create SQL migration file
        try:
            sql_file = create_sql_migration_file()
            logger.info(f"📝 Created SQL migration file: {sql_file}")
            logger.info("=" * 70)
            logger.info("⚠️  ACTION REQUIRED: Tables are missing!")
            logger.info("=" * 70)
            logger.info("Please follow these steps:")
            logger.info("1. Go to your Supabase Dashboard: https://supabase.com")
            logger.info("2. Navigate to: SQL Editor (left sidebar)")
            logger.info(f"3. Open and run the SQL file: {sql_file}")
            logger.info("4. Restart this application")
            logger.info("=" * 70)
        except Exception as e:
            logger.error(f"❌ Failed to create migration file: {str(e)}")
    else:
        logger.info("✅ All required tables exist - database ready!")

