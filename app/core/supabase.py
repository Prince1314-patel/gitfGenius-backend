"""
Supabase client initialization
"""

from supabase import create_client, Client
from app.core.config import settings


def get_supabase_client() -> Client:
    """
    Create and return Supabase client instance
    
    Returns:
        Client: Configured Supabase client
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


# Global Supabase client instance
supabase: Client = get_supabase_client()
