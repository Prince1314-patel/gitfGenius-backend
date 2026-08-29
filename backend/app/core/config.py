"""
Configuration settings loaded from environment variables
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)
    
    # Database
    DATABASE_URL: str = "sqlite:///./giftgenius.db"
    
    # JWT
    SECRET_KEY: str = "dev-only-secret-change-before-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # AI
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openrouter/free"
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    

# Global settings instance
settings = Settings()
