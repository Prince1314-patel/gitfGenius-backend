"""
Security utilities for JWT authentication system.

This module provides core security functionality including:
- Password hashing and verification using bcrypt
- JWT token creation and validation
- FastAPI authentication dependencies
"""

import bcrypt
from app.core.config import settings


class PasswordManager:
    """
    Password management utilities using bcrypt for secure hashing.
    
    This class provides secure password hashing and verification using bcrypt
    algorithm with automatic salt generation. Each password gets a unique salt
    to prevent rainbow table attacks.
    
    Requirements implemented:
    - 3.1: Uses bcrypt algorithm for password hashing
    - 3.2: Compares plain text passwords against bcrypt hashes
    - 3.3: Generates unique salt for each password
    - 1.5: Hashes passwords before database storage
    """
    
    def hash_password(self, password: str) -> str:
        """
        Hash a plain text password using bcrypt with automatic salt generation.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            str: Bcrypt hash string with embedded salt
            
        Raises:
            ValueError: If password is empty or None
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Convert password to bytes
        password_bytes = password.encode('utf-8')
        
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a bcrypt hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Bcrypt hash to verify against
            
        Returns:
            bool: True if password matches hash, False otherwise
            
        Raises:
            ValueError: If either parameter is empty or None
        """
        if not plain_password or not hashed_password:
            raise ValueError("Password and hash cannot be empty")
        
        # Convert to bytes
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        
        # Verify password
        return bcrypt.checkpw(password_bytes, hash_bytes)


# Global password manager instance
password_manager = PasswordManager()

# JWT configuration from settings (for future JWT implementation)
JWT_SECRET_KEY = settings.SECRET_KEY
JWT_ALGORITHM = settings.ALGORITHM
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES