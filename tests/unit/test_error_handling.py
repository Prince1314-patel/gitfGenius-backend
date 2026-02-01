"""
Unit tests for error handling middleware and utilities.

This module tests:
- Custom exception classes and their properties
- Error response formatting consistency
- HTTP status code accuracy
- Field-level validation error reporting
- Secure error logging functionality
- System error handling and graceful degradation
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import Response
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
    SecureLogger,
    SecureFormatter
)
from app.core.middleware import ErrorHandlingMiddleware


class TestCustomExceptions:
    """Test custom exception classes and their properties."""
    
    def test_authentication_error_base_class(self):
        """Test AuthenticationError base class properties."""
        error = AuthenticationError(
            message="Test error",
            status_code=401,
            error_code="TEST_ERROR",
            details={"field": "value"}
        )
        
        assert error.message == "Test error"
        assert error.status_code == 401
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"field": "value"}
        assert str(error) == "Test error"
    
    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError properties."""
        error = InvalidCredentialsError()
        
        assert error.message == "Invalid email or password."
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.error_code == "INVALID_CREDENTIALS"
        assert error.details == {}
    
    def test_invalid_credentials_error_custom_message(self):
        """Test InvalidCredentialsError with custom message."""
        error = InvalidCredentialsError("Custom message")
        
        assert error.message == "Custom message"
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.error_code == "INVALID_CREDENTIALS"
    
    def test_token_expired_error(self):
        """Test TokenExpiredError properties."""
        error = TokenExpiredError()
        
        assert error.message == "Token has expired. Please login again."
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.error_code == "TOKEN_EXPIRED"
    
    def test_invalid_token_error(self):
        """Test InvalidTokenError properties."""
        error = InvalidTokenError()
        
        assert error.message == "Invalid token format. Please provide a valid JWT token."
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.error_code == "INVALID_TOKEN"
    
    def test_missing_token_error(self):
        """Test MissingTokenError properties."""
        error = MissingTokenError()
        
        assert error.message == "Authentication required. Please provide a valid JWT token."
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.error_code == "MISSING_TOKEN"
    
    def test_user_not_found_error(self):
        """Test UserNotFoundError properties."""
        error = UserNotFoundError()
        
        assert error.message == "Invalid token: user not found."
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.error_code == "USER_NOT_FOUND"
    
    def test_duplicate_email_error(self):
        """Test DuplicateEmailError properties."""
        error = DuplicateEmailError()
        
        assert error.message == "An account with this email address already exists."
        assert error.status_code == status.HTTP_409_CONFLICT
        assert error.error_code == "DUPLICATE_EMAIL"
    
    def test_validation_error(self):
        """Test ValidationError properties."""
        field_errors = {"email": ["Invalid format"], "password": ["Too short"]}
        error = CustomValidationError(
            message="Validation failed",
            field_errors=field_errors
        )
        
        assert error.message == "Validation failed"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details == {"field_errors": field_errors}
    
    def test_system_error(self):
        """Test SystemError properties."""
        error = SystemError()
        
        assert error.message == "An internal error occurred. Please try again."
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert error.error_code == "SYSTEM_ERROR"


class TestErrorResponseFormatter:
    """Test error response formatting utilities."""
    
    def test_format_error_response_basic(self):
        """Test basic error response formatting."""
        error = InvalidCredentialsError()
        response = ErrorResponseFormatter.format_error_response(error)
        
        expected = {
            "status": "error",
            "data": None,
            "message": "Invalid email or password.",
            "error_code": "INVALID_CREDENTIALS"
        }
        
        assert response == expected
    
    def test_format_error_response_with_details(self):
        """Test error response formatting with details."""
        field_errors = {"email": ["Invalid format"]}
        error = CustomValidationError(field_errors=field_errors)
        response = ErrorResponseFormatter.format_error_response(error, include_details=True)
        
        assert response["status"] == "error"
        assert response["data"] is None
        assert response["message"] == "Request validation failed."
        assert response["error_code"] == "VALIDATION_ERROR"
        assert response["details"] == {"field_errors": field_errors}
    
    def test_format_error_response_exclude_details(self):
        """Test error response formatting excluding details."""
        field_errors = {"email": ["Invalid format"]}
        error = CustomValidationError(field_errors=field_errors)
        response = ErrorResponseFormatter.format_error_response(error, include_details=False)
        
        assert "details" not in response
        assert response["status"] == "error"
        assert response["error_code"] == "VALIDATION_ERROR"
    
    def test_format_validation_error(self):
        """Test Pydantic validation error formatting."""
        # Create a mock ValidationError
        mock_error = Mock()
        mock_error.errors.return_value = [
            {"loc": ("email",), "msg": "field required"},
            {"loc": ("password",), "msg": "ensure this value has at least 8 characters"},
            {"loc": ("nested", "field"), "msg": "invalid value"}
        ]
        
        response = ErrorResponseFormatter.format_validation_error(mock_error)
        
        expected = {
            "status": "error",
            "data": None,
            "message": "Request validation failed.",
            "error_code": "VALIDATION_ERROR",
            "details": {
                "field_errors": {
                    "email": ["field required"],
                    "password": ["ensure this value has at least 8 characters"],
                    "nested.field": ["invalid value"]
                }
            }
        }
        
        assert response == expected
    
    def test_format_http_exception_with_dict_detail(self):
        """Test HTTP exception formatting when detail is already a dict."""
        detail = {
            "status": "error",
            "data": None,
            "message": "Custom error",
            "error_code": "CUSTOM_ERROR"
        }
        
        http_error = HTTPException(status_code=400, detail=detail)
        response = ErrorResponseFormatter.format_http_exception(http_error)
        
        assert response == detail
    
    def test_format_http_exception_with_string_detail(self):
        """Test HTTP exception formatting when detail is a string."""
        http_error = HTTPException(status_code=404, detail="Not found")
        response = ErrorResponseFormatter.format_http_exception(http_error)
        
        expected = {
            "status": "error",
            "data": None,
            "message": "Not found",
            "error_code": "HTTP_ERROR"
        }
        
        assert response == expected


class TestSecureLogger:
    """Test secure logging functionality."""
    
    @patch('app.core.exceptions.auth_logger')
    def test_log_authentication_attempt_success(self, mock_logger):
        """Test logging successful authentication attempt."""
        SecureLogger.log_authentication_attempt(
            email="test@example.com",
            success=True,
            ip_address="192.168.1.1"
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "Authentication successful" in call_args
        assert "te**@example.com" in call_args  # Masked email
        assert "192.168.1.1" in call_args
    
    @patch('app.core.exceptions.auth_logger')
    def test_log_authentication_attempt_failure(self, mock_logger):
        """Test logging failed authentication attempt."""
        SecureLogger.log_authentication_attempt(
            email="test@example.com",
            success=False
        )
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Authentication failed" in call_args
        assert "te**@example.com" in call_args  # Masked email
    
    @patch('app.core.exceptions.auth_logger')
    def test_log_registration_attempt_success(self, mock_logger):
        """Test logging successful registration attempt."""
        SecureLogger.log_registration_attempt(
            email="test@example.com",
            success=True
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "Registration successful" in call_args
        assert "te**@example.com" in call_args  # Masked email
    
    @patch('app.core.exceptions.auth_logger')
    def test_log_registration_attempt_failure(self, mock_logger):
        """Test logging failed registration attempt."""
        SecureLogger.log_registration_attempt(
            email="test@example.com",
            success=False,
            error_type="DUPLICATE_EMAIL"
        )
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Registration failed" in call_args
        assert "DUPLICATE_EMAIL" in call_args
    
    @patch('app.core.exceptions.auth_logger')
    def test_log_token_validation_error(self, mock_logger):
        """Test logging token validation errors."""
        SecureLogger.log_token_validation_error(
            error_type="TOKEN_EXPIRED",
            user_id="123e4567-e89b-12d3-a456-426614174000"
        )
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Token validation failed" in call_args
        assert "TOKEN_EXPIRED" in call_args
    
    @patch('app.core.exceptions.auth_logger')
    def test_log_system_error(self, mock_logger):
        """Test logging system errors."""
        SecureLogger.log_system_error(
            error_message="Database connection failed",
            context="user_registration"
        )
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "System error" in call_args
        assert "user_registration" in call_args
    
    def test_mask_email_normal(self):
        """Test email masking for normal emails."""
        masked = SecureLogger._mask_email("test@example.com")
        assert masked == "te**@example.com"
    
    def test_mask_email_short(self):
        """Test email masking for short emails."""
        masked = SecureLogger._mask_email("a@example.com")
        assert masked == "a*@example.com"
    
    def test_mask_email_two_chars(self):
        """Test email masking for two character emails."""
        masked = SecureLogger._mask_email("ab@example.com")
        assert masked == "a*@example.com"
    
    def test_mask_email_invalid(self):
        """Test email masking for invalid emails."""
        masked = SecureLogger._mask_email("invalid-email")
        assert masked == "[INVALID_EMAIL]"
        
        masked = SecureLogger._mask_email("")
        assert masked == "[INVALID_EMAIL]"
    
    def test_sanitize_error_message_jwt_token(self):
        """Test sanitizing JWT tokens from error messages."""
        message = "Invalid token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        sanitized = SecureLogger._sanitize_error_message(message)
        assert "[JWT_TOKEN]" in sanitized
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
    
    def test_sanitize_error_message_password(self):
        """Test sanitizing passwords from error messages."""
        message = 'Error with password="secret123" in request'
        sanitized = SecureLogger._sanitize_error_message(message)
        assert "password=[REDACTED]" in sanitized
        assert "secret123" not in sanitized
    
    def test_sanitize_error_message_hash(self):
        """Test sanitizing hash values from error messages."""
        message = "Hash validation failed: a1b2c3d4e5f6789012345678901234567890abcdef"
        sanitized = SecureLogger._sanitize_error_message(message)
        assert "[HASH]" in sanitized
        assert "a1b2c3d4e5f6789012345678901234567890abcdef" not in sanitized


class TestSecureFormatter:
    """Test secure log formatter."""
    
    def test_secure_formatter_sanitizes_jwt_tokens(self):
        """Test that SecureFormatter sanitizes JWT tokens."""
        formatter = SecureFormatter('%(message)s')
        
        # Create a mock log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert "[JWT_TOKEN]" in formatted
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in formatted
    
    def test_secure_formatter_sanitizes_passwords(self):
        """Test that SecureFormatter sanitizes passwords."""
        formatter = SecureFormatter('%(message)s')
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='Login attempt with "password": "secret123"',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert '"password": "[REDACTED]"' in formatted
        assert "secret123" not in formatted


class TestErrorHandlingMiddleware:
    """Test error handling middleware functionality."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance for testing."""
        return ErrorHandlingMiddleware(app=Mock())
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/v1/auth/login"
        request.client.host = "127.0.0.1"
        request.headers = {}
        return request
    
    @pytest.mark.asyncio
    async def test_middleware_handles_authentication_error(self, middleware, mock_request):
        """Test middleware handling of authentication errors."""
        error = InvalidCredentialsError()
        
        with patch.object(middleware, '_log_authentication_error'):
            response = await middleware._handle_authentication_error(error, mock_request)
        
        assert response.status_code == 401
        response_data = response.body.decode()
        assert '"status":"error"' in response_data
        assert '"error_code":"INVALID_CREDENTIALS"' in response_data
        assert "WWW-Authenticate" in response.headers
    
    @pytest.mark.asyncio
    async def test_middleware_handles_http_exception(self, middleware, mock_request):
        """Test middleware handling of HTTP exceptions."""
        http_error = HTTPException(status_code=404, detail="Not found")
        
        with patch('app.core.middleware.SecureLogger.log_system_error'):
            response = await middleware._handle_http_exception(http_error, mock_request)
        
        assert response.status_code == 404
        response_data = response.body.decode()
        assert '"status":"error"' in response_data
        assert '"message":"Not found"' in response_data
    
    @pytest.mark.asyncio
    async def test_middleware_handles_validation_error(self, middleware, mock_request):
        """Test middleware handling of validation errors."""
        # Create mock validation error
        mock_error = Mock()
        mock_error.errors.return_value = [
            {"loc": ("body", "email"), "msg": "field required"}
        ]
        
        with patch('app.core.middleware.SecureLogger.log_system_error'):
            response = await middleware._handle_validation_error(mock_error, mock_request)
        
        assert response.status_code == 400
        response_data = response.body.decode()
        assert '"status":"error"' in response_data
        assert '"error_code":"VALIDATION_ERROR"' in response_data
        assert '"field_errors"' in response_data
    
    @pytest.mark.asyncio
    async def test_middleware_handles_system_error(self, middleware, mock_request):
        """Test middleware handling of system errors."""
        system_error = Exception("Database connection failed")
        
        with patch('app.core.middleware.SecureLogger.log_system_error'):
            response = await middleware._handle_system_error(system_error, mock_request)
        
        assert response.status_code == 500
        response_data = response.body.decode()
        assert '"status":"error"' in response_data
        assert '"error_code":"SYSTEM_ERROR"' in response_data
    
    def test_get_client_ip_forwarded_for(self, middleware, mock_request):
        """Test client IP extraction from X-Forwarded-For header."""
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_real_ip(self, middleware, mock_request):
        """Test client IP extraction from X-Real-IP header."""
        mock_request.headers = {"X-Real-IP": "192.168.1.1"}
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_client_host(self, middleware, mock_request):
        """Test client IP extraction from client host."""
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "127.0.0.1"
    
    def test_get_client_ip_unknown(self, middleware):
        """Test client IP extraction when no source available."""
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client = None
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "unknown"


class TestHTTPStatusCodes:
    """Test HTTP status code accuracy for different error types."""
    
    def test_authentication_errors_return_401(self):
        """Test that authentication errors return 401 status code."""
        errors = [
            InvalidCredentialsError(),
            TokenExpiredError(),
            InvalidTokenError(),
            MissingTokenError(),
            UserNotFoundError()
        ]
        
        for error in errors:
            assert error.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_duplicate_email_returns_409(self):
        """Test that duplicate email error returns 409 status code."""
        error = DuplicateEmailError()
        assert error.status_code == status.HTTP_409_CONFLICT
    
    def test_validation_error_returns_400(self):
        """Test that validation errors return 400 status code."""
        error = CustomValidationError()
        assert error.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_system_error_returns_500(self):
        """Test that system errors return 500 status code."""
        error = SystemError()
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestResponseEnvelopeConsistency:
    """Test response envelope consistency for all error types."""
    
    def test_all_errors_have_consistent_envelope(self):
        """Test that all error types produce consistent response envelopes."""
        errors = [
            InvalidCredentialsError(),
            TokenExpiredError(),
            InvalidTokenError(),
            MissingTokenError(),
            UserNotFoundError(),
            DuplicateEmailError(),
            CustomValidationError(),
            SystemError()
        ]
        
        for error in errors:
            response = ErrorResponseFormatter.format_error_response(error)
            
            # Check required fields
            assert "status" in response
            assert "data" in response
            assert "message" in response
            assert "error_code" in response
            
            # Check field values
            assert response["status"] == "error"
            assert response["data"] is None
            assert isinstance(response["message"], str)
            assert isinstance(response["error_code"], str)
            assert len(response["message"]) > 0
            assert len(response["error_code"]) > 0
    
    def test_validation_errors_include_field_details(self):
        """Test that validation errors include field-level details."""
        field_errors = {"email": ["Invalid format"], "password": ["Too short"]}
        error = CustomValidationError(field_errors=field_errors)
        response = ErrorResponseFormatter.format_error_response(error)
        
        assert "details" in response
        assert "field_errors" in response["details"]
        assert response["details"]["field_errors"] == field_errors


class TestUserFriendlyErrorMessages:
    """Test that error messages are user-friendly and don't expose sensitive data."""
    
    def test_error_messages_are_user_friendly(self):
        """Test that error messages are clear and user-friendly."""
        errors_and_messages = [
            (InvalidCredentialsError(), "Invalid email or password."),
            (TokenExpiredError(), "Token has expired. Please login again."),
            (InvalidTokenError(), "Invalid token format. Please provide a valid JWT token."),
            (MissingTokenError(), "Authentication required. Please provide a valid JWT token."),
            (UserNotFoundError(), "Invalid token: user not found."),
            (DuplicateEmailError(), "An account with this email address already exists."),
            (SystemError(), "An internal error occurred. Please try again.")
        ]
        
        for error, expected_message in errors_and_messages:
            assert error.message == expected_message
            # Ensure message doesn't contain technical jargon
            assert "exception" not in error.message.lower()
            assert "traceback" not in error.message.lower()
            assert "stack" not in error.message.lower()
    
    def test_error_messages_dont_expose_sensitive_data(self):
        """Test that error messages don't expose sensitive information."""
        errors = [
            InvalidCredentialsError(),
            TokenExpiredError(),
            InvalidTokenError(),
            MissingTokenError(),
            UserNotFoundError(),
            DuplicateEmailError(),
            SystemError()
        ]
        
        sensitive_patterns = [
            "hash",
            "secret",
            "key",
            "database",
            "connection",
            "sql"
        ]
        
        for error in errors:
            message_lower = error.message.lower()
            for pattern in sensitive_patterns:
                assert pattern not in message_lower, f"Sensitive pattern '{pattern}' found in message: {error.message}"