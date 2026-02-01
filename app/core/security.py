"""
Security utilities for JWT authentication system.

This module provides core security functionality including:
- Password hashing and verification using bcrypt
- JWT token creation and validation
- FastAPI authentication dependencies

Implementation will be completed in task 3.
"""

from app.core.config import settings

# Security utilities will be implemented in task 3:
# - PasswordManager class (task 3.1)
# - JWTManager class (task 3.3)  
# - FastAPI dependencies (task 4.1)

# JWT configuration from settings
JWT_SECRET_KEY = settings.SECRET_KEY
JWT_ALGORITHM = settings.ALGORITHM
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES