"""
Error handling middleware for the JWT authentication system.

This module provides middleware to catch and format errors consistently
across all API endpoints, ensuring standardized error responses and
secure error logging.
"""

import traceback
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
import jwt

from app.core.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    MissingTokenError,
    UserNotFoundError,
    DuplicateEmailError,
    ValidationError as CustomValidationError,
    SystemError,
    ErrorResponseFormatter,
    SecureLogger
)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch and format all application errors consistently.
    
    This middleware ensures that all errors are returned in the standardized
    response format and that sensitive information is not exposed in error
    messages or logs.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle any errors that occur.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or endpoint handler
            
        Returns:
            Response: HTTP response with standardized error format if error occurs
        """
        try:
            # Process the request
            response = await call_next(request)
            return response
            
        except AuthenticationError as auth_error:
            # Handle custom authentication errors
            return await self._handle_authentication_error(auth_error, request)
            
        except HTTPException as http_error:
            # Handle FastAPI HTTP exceptions
            return await self._handle_http_exception(http_error, request)
            
        except RequestValidationError as validation_error:
            # Handle Pydantic request validation errors
            return await self._handle_validation_error(validation_error, request)
            
        except ValidationError as pydantic_error:
            # Handle Pydantic validation errors
            return await self._handle_pydantic_validation_error(pydantic_error, request)
            
        except jwt.ExpiredSignatureError:
            # Handle JWT expiration errors
            error = TokenExpiredError()
            return await self._handle_authentication_error(error, request)
            
        except jwt.InvalidTokenError:
            # Handle JWT validation errors
            error = InvalidTokenError()
            return await self._handle_authentication_error(error, request)
            
        except Exception as system_error:
            # Handle unexpected system errors
            return await self._handle_system_error(system_error, request)
    
    async def _handle_authentication_error(
        self, 
        error: AuthenticationError, 
        request: Request
    ) -> JSONResponse:
        """
        Handle authentication-related errors.
        
        Args:
            error: The authentication error that occurred
            request: The HTTP request that caused the error
            
        Returns:
            JSONResponse with standardized error format
        """
        # Log the authentication error securely
        self._log_authentication_error(error, request)
        
        # Format the error response
        error_response = ErrorResponseFormatter.format_error_response(error)
        
        # Set appropriate headers for authentication errors
        headers = {}
        if error.status_code == status.HTTP_401_UNAUTHORIZED:
            headers["WWW-Authenticate"] = "Bearer"
        
        return JSONResponse(
            status_code=error.status_code,
            content=error_response,
            headers=headers
        )
    
    async def _handle_http_exception(
        self, 
        error: HTTPException, 
        request: Request
    ) -> JSONResponse:
        """
        Handle FastAPI HTTP exceptions.
        
        Args:
            error: The HTTP exception that occurred
            request: The HTTP request that caused the error
            
        Returns:
            JSONResponse with standardized error format
        """
        # Log the HTTP error
        SecureLogger.log_system_error(
            f"HTTP {error.status_code}: {error.detail}",
            context=f"{request.method} {request.url.path}"
        )
        
        # Format the error response
        error_response = ErrorResponseFormatter.format_http_exception(error)
        
        return JSONResponse(
            status_code=error.status_code,
            content=error_response,
            headers=getattr(error, 'headers', {})
        )
    
    async def _handle_validation_error(
        self, 
        error: RequestValidationError, 
        request: Request
    ) -> JSONResponse:
        """
        Handle Pydantic request validation errors.
        
        Args:
            error: The validation error that occurred
            request: The HTTP request that caused the error
            
        Returns:
            JSONResponse with standardized validation error format
        """
        # Log the validation error
        SecureLogger.log_system_error(
            f"Request validation failed: {len(error.errors())} errors",
            context=f"{request.method} {request.url.path}"
        )
        
        # Format field-level validation errors
        field_errors = {}
        for validation_error in error.errors():
            field_name = ".".join(str(loc) for loc in validation_error["loc"][1:])  # Skip 'body'
            error_message = validation_error["msg"]
            
            if field_name not in field_errors:
                field_errors[field_name] = []
            field_errors[field_name].append(error_message)
        
        error_response = {
            "status": "error",
            "data": None,
            "message": "Request validation failed.",
            "error_code": "VALIDATION_ERROR",
            "details": {
                "field_errors": field_errors
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response
        )
    
    async def _handle_pydantic_validation_error(
        self, 
        error: ValidationError, 
        request: Request
    ) -> JSONResponse:
        """
        Handle Pydantic model validation errors.
        
        Args:
            error: The Pydantic validation error that occurred
            request: The HTTP request that caused the error
            
        Returns:
            JSONResponse with standardized validation error format
        """
        # Log the validation error
        SecureLogger.log_system_error(
            f"Model validation failed: {len(error.errors())} errors",
            context=f"{request.method} {request.url.path}"
        )
        
        # Format the error response
        error_response = ErrorResponseFormatter.format_validation_error(error)
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response
        )
    
    async def _handle_system_error(
        self, 
        error: Exception, 
        request: Request
    ) -> JSONResponse:
        """
        Handle unexpected system errors.
        
        Args:
            error: The system error that occurred
            request: The HTTP request that caused the error
            
        Returns:
            JSONResponse with standardized system error format
        """
        # Log the full error details for debugging (sanitized)
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "request_path": request.url.path,
            "request_method": request.method,
            "traceback": traceback.format_exc()
        }
        
        SecureLogger.log_system_error(
            f"Unexpected error: {type(error).__name__}: {str(error)}",
            context=f"{request.method} {request.url.path}"
        )
        
        # Create a generic system error
        system_error = SystemError()
        error_response = ErrorResponseFormatter.format_error_response(system_error)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )
    
    def _log_authentication_error(self, error: AuthenticationError, request: Request):
        """
        Log authentication errors securely.
        
        Args:
            error: The authentication error to log
            request: The HTTP request that caused the error
        """
        # Extract client IP if available
        client_ip = self._get_client_ip(request)
        
        # Log based on error type
        if isinstance(error, (InvalidCredentialsError, MissingTokenError)):
            # These are common authentication failures
            SecureLogger.log_token_validation_error(
                error_type=error.error_code,
                user_id=None
            )
        elif isinstance(error, (TokenExpiredError, InvalidTokenError, UserNotFoundError)):
            # These involve token validation
            SecureLogger.log_token_validation_error(
                error_type=error.error_code,
                user_id=None  # Don't log user_id for security
            )
        elif isinstance(error, DuplicateEmailError):
            # Registration attempt with duplicate email
            SecureLogger.log_registration_attempt(
                email="[REDACTED]",  # Don't log actual email
                success=False,
                error_type=error.error_code
            )
        else:
            # Generic authentication error
            SecureLogger.log_system_error(
                error_message=error.message,
                context=f"{request.method} {request.url.path}"
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.
        
        Args:
            request: The HTTP request
            
        Returns:
            Client IP address or 'unknown'
        """
        # Check for forwarded headers first (for reverse proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


# Exception handler functions for specific error types
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """
    Handle authentication errors specifically.
    
    This can be used as a FastAPI exception handler for AuthenticationError.
    """
    middleware = ErrorHandlingMiddleware(None)
    return await middleware._handle_authentication_error(exc, request)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors specifically.
    
    This can be used as a FastAPI exception handler for RequestValidationError.
    """
    middleware = ErrorHandlingMiddleware(None)
    return await middleware._handle_validation_error(exc, request)


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions specifically.
    
    This can be used as a FastAPI exception handler for HTTPException.
    """
    middleware = ErrorHandlingMiddleware(None)
    return await middleware._handle_http_exception(exc, request)


async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions.
    
    This can be used as a FastAPI exception handler for Exception.
    """
    middleware = ErrorHandlingMiddleware(None)
    return await middleware._handle_system_error(exc, request)