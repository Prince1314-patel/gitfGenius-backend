"""
Unit tests for FastAPI authentication dependencies.

Tests the get_current_user dependency and HTTPBearer security scheme
to ensure proper JWT token validation and error handling.
"""

import pytest
import uuid
import asyncio
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session, select
from datetime import datetime, timedelta
import jwt as jwt_lib

from app.core.security import get_current_user, oauth2_scheme, jwt_manager
from app.models import User


# Configure pytest for async tests
pytestmark = pytest.mark.asyncio


class TestOAuth2Scheme:
    """Test cases for HTTPBearer security scheme configuration."""
    
    def test_oauth2_scheme_configuration(self):
        """Test HTTPBearer security scheme is properly configured."""
        assert oauth2_scheme.scheme_name == "JWT"
        assert oauth2_scheme.auto_error is False  # Manual error handling
        # HTTPBearer doesn't have description attribute, but we can test the scheme type
        assert hasattr(oauth2_scheme, 'scheme_name')
        assert hasattr(oauth2_scheme, 'auto_error')


class TestGetCurrentUser:
    """Test cases for get_current_user dependency."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        user_id = uuid.uuid4()
        return User(
            id=user_id,
            email="test@example.com",
            password_hash="hashed_password",
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def valid_credentials(self, sample_user):
        """Create valid HTTP Bearer credentials with JWT token."""
        token_data = {"user_id": str(sample_user.id), "email": sample_user.email}
        token = jwt_manager.create_access_token(token_data)
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    @pytest.fixture
    def expired_credentials(self, sample_user):
        """Create expired HTTP Bearer credentials."""
        # Create token that expired 1 hour ago
        expired_data = {
            "user_id": str(sample_user.id),
            "email": sample_user.email,
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt_lib.encode(expired_data, jwt_manager.secret_key, algorithm=jwt_manager.algorithm)
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)
    
    @pytest.fixture
    def malformed_credentials(self):
        """Create malformed HTTP Bearer credentials."""
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.here")
    
    async def test_get_current_user_with_valid_token(self, valid_credentials, sample_user, mock_db_session):
        """Test get_current_user with valid JWT token."""
        # Mock database query to return the user
        mock_result = Mock()
        mock_result.first.return_value = sample_user
        mock_db_session.exec.return_value = mock_result
        
        # Call the dependency
        result = await get_current_user(valid_credentials, mock_db_session)
        
        # Should return the user
        assert result == sample_user
        
        # Verify database was queried correctly
        mock_db_session.exec.assert_called_once()
        call_args = mock_db_session.exec.call_args[0][0]
        assert isinstance(call_args, type(select(User).where(User.id == sample_user.id)))
    
    async def test_get_current_user_with_expired_token(self, expired_credentials, mock_db_session):
        """Test get_current_user with expired JWT token."""
        from app.core.exceptions import TokenExpiredError
        
        with pytest.raises(TokenExpiredError) as exc_info:
            await get_current_user(expired_credentials, mock_db_session)
        
        # Should raise TokenExpiredError with appropriate message
        assert "expired" in str(exc_info.value).lower()
    
    async def test_get_current_user_with_malformed_token(self, malformed_credentials, mock_db_session):
        """Test get_current_user with malformed JWT token."""
        from app.core.exceptions import InvalidTokenError
        
        with pytest.raises(InvalidTokenError) as exc_info:
            await get_current_user(malformed_credentials, mock_db_session)
        
        # Should raise InvalidTokenError with appropriate message
        assert "invalid" in str(exc_info.value).lower() or "token" in str(exc_info.value).lower()
    
    async def test_get_current_user_with_missing_token(self, mock_db_session):
        """Test get_current_user with missing token (None credentials)."""
        from app.core.exceptions import MissingTokenError
        
        with pytest.raises(MissingTokenError) as exc_info:
            await get_current_user(None, mock_db_session)
        
        # Should raise MissingTokenError with appropriate message
        assert "authentication required" in str(exc_info.value).lower() or "token" in str(exc_info.value).lower()
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
    
    async def test_get_current_user_with_empty_token(self, mock_db_session):
        """Test get_current_user with empty token."""
        from app.core.exceptions import InvalidTokenError
        
        empty_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")
        
        with pytest.raises(InvalidTokenError) as exc_info:
            await get_current_user(empty_credentials, mock_db_session)
        
        # Should raise InvalidTokenError with appropriate message
        assert "token" in str(exc_info.value).lower()
    
    async def test_get_current_user_with_token_missing_user_id(self, mock_db_session):
        """Test get_current_user with token missing user_id."""
        from app.core.exceptions import InvalidTokenError
        
        # Create token without user_id
        token_data = {"email": "test@example.com"}  # Missing user_id
        token = jwt_manager.create_access_token(token_data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        with pytest.raises(InvalidTokenError) as exc_info:
            await get_current_user(credentials, mock_db_session)
        
        # Should raise InvalidTokenError with appropriate message
        assert "user identification" in str(exc_info.value).lower()
    
    async def test_get_current_user_with_user_not_found_in_database(self, sample_user, mock_db_session):
        """Test get_current_user when user is not found in database."""
        from app.core.exceptions import UserNotFoundError
        
        # Create valid token
        token_data = {"user_id": str(sample_user.id), "email": sample_user.email}
        token = jwt_manager.create_access_token(token_data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Mock database query to return None (user not found)
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db_session.exec.return_value = mock_result
        
        with pytest.raises(UserNotFoundError) as exc_info:
            await get_current_user(credentials, mock_db_session)
        
        # Should raise UserNotFoundError with appropriate message
        assert "user not found" in str(exc_info.value).lower()
    
    async def test_get_current_user_database_integration(self, valid_credentials, sample_user, mock_db_session):
        """Test database integration in get_current_user dependency."""
        # Mock database query
        mock_result = Mock()
        mock_result.first.return_value = sample_user
        mock_db_session.exec.return_value = mock_result
        
        # Call the dependency
        result = await get_current_user(valid_credentials, mock_db_session)
        
        # Verify database session was used
        mock_db_session.exec.assert_called_once()
        
        # Verify correct SQL query was constructed
        call_args = mock_db_session.exec.call_args[0][0]
        # The query should be a select statement for User table
        assert hasattr(call_args, 'column_descriptions') or hasattr(call_args, 'columns')
        
        # Result should be the user
        assert result == sample_user
    
    async def test_get_current_user_with_wrong_signature_token(self, sample_user, mock_db_session):
        """Test get_current_user with token signed with wrong secret."""
        from app.core.exceptions import InvalidTokenError
        
        # Create token with wrong secret
        token_data = {"user_id": str(sample_user.id), "email": sample_user.email}
        wrong_secret_token = jwt_lib.encode(token_data, "wrong_secret", algorithm=jwt_manager.algorithm)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=wrong_secret_token)
        
        with pytest.raises(InvalidTokenError) as exc_info:
            await get_current_user(credentials, mock_db_session)
        
        # Should raise InvalidTokenError with appropriate message
        assert "invalid" in str(exc_info.value).lower() or "token" in str(exc_info.value).lower()
    
    async def test_get_current_user_error_response_format(self, mock_db_session):
        """Test that all error responses follow standardized format."""
        from app.core.exceptions import MissingTokenError
        
        # Test with missing credentials - should raise custom exception
        with pytest.raises(MissingTokenError):
            await get_current_user(None, mock_db_session)
    
    @patch('app.core.security.jwt_manager.verify_token')
    async def test_get_current_user_handles_unexpected_errors(self, mock_verify_token, valid_credentials, mock_db_session):
        """Test get_current_user handles unexpected errors gracefully."""
        from app.core.exceptions import InvalidTokenError
        
        # Mock verify_token to raise an unexpected error
        mock_verify_token.side_effect = RuntimeError("Unexpected error")
        
        with pytest.raises(InvalidTokenError) as exc_info:
            await get_current_user(valid_credentials, mock_db_session)
        
        # Should raise InvalidTokenError for unexpected errors
        assert "internal server error" in str(exc_info.value).lower()
    
    async def test_get_current_user_preserves_user_data(self, sample_user, mock_db_session):
        """Test that get_current_user preserves all user data correctly."""
        # Create token with user data
        token_data = {
            "user_id": str(sample_user.id),
            "email": sample_user.email,
            "extra_field": "extra_value"
        }
        token = jwt_manager.create_access_token(token_data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Mock database query
        mock_result = Mock()
        mock_result.first.return_value = sample_user
        mock_db_session.exec.return_value = mock_result
        
        # Call the dependency
        result = await get_current_user(credentials, mock_db_session)
        
        # Should return the complete user object
        assert result.id == sample_user.id
        assert result.email == sample_user.email
        assert result.password_hash == sample_user.password_hash
        assert result.created_at == sample_user.created_at