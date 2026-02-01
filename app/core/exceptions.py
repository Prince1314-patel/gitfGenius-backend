"""
Custom exception classes and error handling utilities for the JWT authentication system.

This module provides:
- Custom exception classes for different authentication error types
- Error response formatting with field-level details
- Secure error logging utilities (no password exposure)
- HTTP status code mapping for different error types
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from pydantic import ValidationError


# Configure secure logger for authentication errors
auth_logger = logging.getLogger("auth_security")
auth_logger.setLevel(logging.INFO)

# Create formatter that excludes sensitive data
class SecureFormatter(logging.Formatter):
    """Custom formatter that sanitizes sensitive information from logs."""
    
    SENSITIVE_FIELDS = {'password', 'token', 'secret', 'key', 'hash'}
    
    def format(self, record):
        # Create a copy of the record to avoid modifying the original
        record_copy = logging.makeLogRecord(record.__dict__)
        
        # Sanitize the message if it contains sensitive data
        if hasattr(record_copy, 'msg') and isinstance(record_copy.msg, str):
            record_copy.msg = self._sanitize_message(record_copy.msg)
        
        return super().format(record_copy)
    
    def _sanitize_message(self, message: str) -> str:
        """Remove or mask sensitive information from log messages."""
        # Simple sanitization - replace common sensitive patterns
        import re
        
        # Mask JWT tokens (typically long base64 strings)
        message = re.sub(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*', '[JWT_TOKEN]', message)
        
        # Mask password-like patterns
        message = re.sub(r'"password":\s*"[^"]*"', '"password": "[REDACTED]"', message)
        message = re.sub(r'password=\w+', 'password=[REDACTED]', message)
        
        return message


# Set up secure formatter for auth logger
handler = logging.StreamHandler()
handler.setFormatter(SecureFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
auth_logger.addHandler(handler)
auth_logger.propagate = False  # Prevent duplicate logs


class AuthenticationError(Exception):
    """Base class for authentication-related errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        error_code: str = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class InvalidCredentialsError(AuthenticationError):
    """Raised when user provides invalid login credentials."""
    
    def __init__(self, message: str = "Invalid email or password."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_CREDENTIALS"
        )


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""
    
    def __init__(self, message: str = "Token has expired. Please login again."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="TOKEN_EXPIRED"
        )


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is malformed or invalid."""
    
    def __init__(self, message: str = "Invalid token format. Please provide a valid JWT token."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_TOKEN"
        )


class MissingTokenError(AuthenticationError):
    """Raised when JWT token is missing from request."""
    
    def __init__(self, message: str = "Authentication required. Please provide a valid JWT token."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="MISSING_TOKEN"
        )


class UserNotFoundError(AuthenticationError):
    """Raised when user referenced in token is not found in database."""
    
    def __init__(self, message: str = "Invalid token: user not found."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="USER_NOT_FOUND"
        )


class DuplicateEmailError(AuthenticationError):
    """Raised when attempting to register with an email that already exists."""
    
    def __init__(self, message: str = "An account with this email address already exists."):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="DUPLICATE_EMAIL"
        )


class ValidationError(AuthenticationError):
    """Raised when request data fails validation."""
    
    def __init__(
        self, 
        message: str = "Request validation failed.",
        field_errors: Optional[Dict[str, List[str]]] = None
    ):
        details = {"field_errors": field_errors} if field_errors else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details
        )


class SystemError(AuthenticationError):
    """Raised for internal system errors."""
    
    def __init__(self, message: str = "An internal error occurred. Please try again."):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="SYSTEM_ERROR"
        )


class ErrorResponseFormatter:
    """Utility class for formatting error responses consistently."""
    
    @staticmethod
    def format_error_response(
        error: AuthenticationError,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Format an authentication error into a standardized response.
        
        Args:
            error: The authentication error to format
            include_details: Whether to include error details in response
            
        Returns:
            Dict containing standardized error response
        """
        response = {
            "status": "error",
            "data": None,
            "message": error.message,
            "error_code": error.error_code
        }
        
        if include_details and error.details:
            response["details"] = error.details
            
        return response
    
    @staticmethod
    def format_validation_error(validation_error: ValidationError) -> Dict[str, Any]:
        """
        Format a Pydantic validation error into standardized response.
        
        Args:
            validation_error: Pydantic ValidationError instance
            
        Returns:
            Dict containing standardized validation error response
        """
        field_errors = {}
        
        for error in validation_error.errors():
            field_name = ".".join(str(loc) for loc in error["loc"])
            error_message = error["msg"]
            
            if field_name not in field_errors:
                field_errors[field_name] = []
            field_errors[field_name].append(error_message)
        
        return {
            "status": "error",
            "data": None,
            "message": "Request validation failed.",
            "error_code": "VALIDATION_ERROR",
            "details": {
                "field_errors": field_errors
            }
        }
    
    @staticmethod
    def format_http_exception(http_exception: HTTPException) -> Dict[str, Any]:
        """
        Format an HTTPException into standardized response.
        
        Args:
            http_exception: FastAPI HTTPException instance
            
        Returns:
            Dict containing standardized error response
        """
        # If the detail is already a dict (our custom format), return it
        if isinstance(http_exception.detail, dict):
            return http_exception.detail
        
        # Otherwise, format it as a standard error
        return {
            "status": "error",
            "data": None,
            "message": str(http_exception.detail),
            "error_code": "HTTP_ERROR"
        }


class SecureLogger:
    """Utility class for secure logging of authentication events."""
    
    @staticmethod
    def log_authentication_attempt(email: str, success: bool, ip_address: str = None):
        """
        Log authentication attempt with sanitized information.
        
        Args:
            email: User email (will be partially masked)
            success: Whether authentication was successful
            ip_address: Client IP address (optional)
        """
        # Mask email for privacy (show first 2 chars and domain)
        masked_email = SecureLogger._mask_email(email)
        
        log_data = {
            "event": "authentication_attempt",
            "email": masked_email,
            "success": success,
            "ip_address": ip_address
        }
        
        if success:
            auth_logger.info(f"Authentication successful: {log_data}")
        else:
            auth_logger.warning(f"Authentication failed: {log_data}")
    
    @staticmethod
    def log_registration_attempt(email: str, success: bool, error_type: str = None):
        """
        Log user registration attempt with sanitized information.
        
        Args:
            email: User email (will be partially masked)
            success: Whether registration was successful
            error_type: Type of error if registration failed
        """
        masked_email = SecureLogger._mask_email(email)
        
        log_data = {
            "event": "registration_attempt",
            "email": masked_email,
            "success": success,
            "error_type": error_type
        }
        
        if success:
            auth_logger.info(f"Registration successful: {log_data}")
        else:
            auth_logger.warning(f"Registration failed: {log_data}")
    
    @staticmethod
    def log_token_validation_error(error_type: str, user_id: str = None):
        """
        Log token validation errors.
        
        Args:
            error_type: Type of token validation error
            user_id: User ID from token (if available)
        """
        log_data = {
            "event": "token_validation_error",
            "error_type": error_type,
            "user_id": user_id
        }
        
        auth_logger.warning(f"Token validation failed: {log_data}")
    
    @staticmethod
    def log_system_error(error_message: str, context: str = None):
        """
        Log system errors with context.
        
        Args:
            error_message: Error message (will be sanitized)
            context: Additional context about where error occurred
        """
        # Sanitize error message
        sanitized_message = SecureLogger._sanitize_error_message(error_message)
        
        log_data = {
            "event": "system_error",
            "error": sanitized_message,
            "context": context
        }
        
        auth_logger.error(f"System error: {log_data}")
    
    @staticmethod
    def _mask_email(email: str) -> str:
        """
        Mask email address for privacy in logs.
        
        Args:
            email: Email address to mask
            
        Returns:
            Masked email address (e.g., "jo***@example.com")
        """
        if not email or "@" not in email:
            return "[INVALID_EMAIL]"
        
        local, domain = email.split("@", 1)
        
        if len(local) <= 2:
            masked_local = local[0] + "*"
        else:
            masked_local = local[:2] + "*" * (len(local) - 2)
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def _sanitize_error_message(message: str) -> str:
        """
        Remove sensitive information from error messages.
        
        Args:
            message: Error message to sanitize
            
        Returns:
            Sanitized error message
        """
        import re
        
        # Remove JWT tokens
        message = re.sub(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*', '[JWT_TOKEN]', message)
        
        # Remove password-like patterns
        message = re.sub(r'password["\s]*[:=]["\s]*[^\s"]+', 'password=[REDACTED]', message, flags=re.IGNORECASE)
        
        # Remove hash-like patterns (long hex strings)
        message = re.sub(r'\b[a-fA-F0-9]{32,}\b', '[HASH]', message)
        
        return message


# Global formatter instance
error_formatter = ErrorResponseFormatter()

# Global secure logger instance
secure_logger = SecureLogger()