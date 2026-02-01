"""
Security utilities for JWT authentication system.

This module provides core security functionality including:
- Password hashing and verification using bcrypt
- JWT token creation and validation
- FastAPI authentication dependencies
"""

import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
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
            
        Note:
            Bcrypt has a 72-byte limit. Passwords longer than 72 bytes when
            encoded as UTF-8 will be truncated to 72 bytes.
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Convert password to bytes
        password_bytes = password.encode('utf-8')
        
        # Bcrypt has a 72-byte limit, truncate if necessary
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
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
            
        Note:
            Bcrypt has a 72-byte limit. Passwords longer than 72 bytes when
            encoded as UTF-8 will be truncated to 72 bytes for verification.
        """
        if not plain_password or not hashed_password:
            raise ValueError("Password and hash cannot be empty")
        
        # Convert to bytes
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        
        # Bcrypt has a 72-byte limit, truncate if necessary
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Verify password
        return bcrypt.checkpw(password_bytes, hash_bytes)


class JWTManager:
    """
    JWT token management utilities for authentication.
    
    This class provides JWT token creation and validation functionality
    with 24-hour expiration and comprehensive error handling.
    
    Requirements implemented:
    - 2.3: Sets JWT token expiration to 24 hours from creation
    - 2.4: Includes user identification information in token payload
    - 4.1: Extracts user information from validated tokens
    - 4.2: Rejects expired JWT tokens
    - 4.3: Rejects malformed JWT tokens
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize JWT manager with secret key and algorithm.
        
        Args:
            secret_key: Secret key for JWT signing and verification
            algorithm: JWT algorithm (default: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_hours = 24
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT token with 24-hour expiration.
        
        Args:
            data: Dictionary containing user data to encode in token
            
        Returns:
            str: JWT token string
            
        Raises:
            ValueError: If data is empty or None
            
        Note:
            Token expires exactly 24 hours from creation time.
            The 'exp' claim is automatically added to the payload.
        """
        if not data:
            raise ValueError("Token data cannot be empty")
        
        # Create a copy to avoid modifying the original data
        to_encode = data.copy()
        
        # Add expiration time (24 hours from now)
        expire = datetime.utcnow() + timedelta(hours=self.access_token_expire_hours)
        to_encode.update({"exp": expire})
        
        # Create and return JWT token
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token with comprehensive error handling.
        
        Args:
            token: JWT token string to verify
            
        Returns:
            Dict[str, Any]: Decoded token payload
            
        Raises:
            ValueError: If token is empty or None
            jwt.ExpiredSignatureError: If token has expired
            jwt.InvalidTokenError: If token is malformed or invalid
            
        Note:
            This method validates token signature, expiration, and format.
            The 'exp' claim is automatically validated by PyJWT.
        """
        if not token:
            raise ValueError("Token cannot be empty")
        
        try:
            # Decode and verify the token
            # PyJWT automatically validates expiration if 'exp' claim is present
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            # Token has expired
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidTokenError:
            # Token is malformed or invalid
            raise jwt.InvalidTokenError("Invalid token")


# Global password manager instance
password_manager = PasswordManager()

# Global JWT manager instance
jwt_manager = JWTManager(
    secret_key=settings.SECRET_KEY,
    algorithm=settings.ALGORITHM
)


# FastAPI Authentication Dependencies
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from app.core.exceptions import (
    MissingTokenError,
    InvalidTokenError,
    TokenExpiredError,
    UserNotFoundError,
    SecureLogger
)
import jwt as jwt_lib
import uuid


# HTTPBearer security scheme for JWT token authentication
oauth2_scheme = HTTPBearer(
    scheme_name="JWT",
    description="Enter JWT token",
    auto_error=False  # We'll handle errors manually for better control
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
) -> User:
    """
    FastAPI dependency to extract and validate current user from JWT token.
    
    This dependency provides route protection by validating JWT tokens and
    returning the authenticated user. It handles all token validation errors
    and database lookups.
    
    Args:
        credentials: HTTP Bearer credentials containing JWT token
        db: Database session for user lookup
        
    Returns:
        User: Authenticated user object from database
        
    Raises:
        MissingTokenError: If token is missing from request
        InvalidTokenError: If token is malformed or invalid
        TokenExpiredError: If token has expired
        UserNotFoundError: If user referenced in token is not found
        
    Requirements implemented:
    - 4.1: Extracts user information from validated tokens
    - 4.2: Rejects expired JWT tokens with appropriate error
    - 4.3: Rejects malformed JWT tokens with appropriate error
    - 4.4: Rejects requests lacking JWT tokens
    - 4.5: Returns authentication errors in standardized format
    """
    
    # Check if credentials are provided
    if not credentials:
        raise MissingTokenError()
    
    # Extract token from credentials
    token = credentials.credentials
    
    try:
        # Verify and decode the JWT token
        payload = jwt_manager.verify_token(token)
        
        # Extract user ID from token payload
        user_id = payload.get("user_id")
        if user_id is None:
            SecureLogger.log_token_validation_error("missing_user_id")
            raise InvalidTokenError("Invalid token: missing user identification.")
        
        # Convert user_id to UUID (handle conversion errors)
        try:
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
        except (ValueError, TypeError):
            SecureLogger.log_token_validation_error("malformed_user_id")
            raise InvalidTokenError("Invalid token: malformed user identification.")
        
        # Look up user in database
        statement = select(User).where(User.id == user_id)
        user = db.exec(statement).first()
        
        if user is None:
            SecureLogger.log_token_validation_error("user_not_found", str(user_id))
            raise UserNotFoundError()
        
        return user
        
    except jwt_lib.ExpiredSignatureError:
        SecureLogger.log_token_validation_error("token_expired")
        raise TokenExpiredError()
    
    except jwt_lib.InvalidTokenError:
        SecureLogger.log_token_validation_error("invalid_token_format")
        raise InvalidTokenError()
    
    except ValueError as e:
        # Handle empty token or other validation errors
        SecureLogger.log_token_validation_error("token_validation_error")
        raise InvalidTokenError(f"Token validation error: {str(e)}")
    
    except (MissingTokenError, InvalidTokenError, TokenExpiredError, UserNotFoundError):
        # Re-raise custom authentication errors
        raise
    
    except Exception as e:
        # Handle any unexpected errors
        SecureLogger.log_system_error(
            error_message=str(e),
            context="token_validation"
        )
        raise InvalidTokenError("Internal server error during authentication.")