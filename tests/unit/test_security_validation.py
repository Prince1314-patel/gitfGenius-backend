"""
Comprehensive security validation tests.

Tests security requirements including password hashing, JWT token security,
expiration handling, and information leakage prevention.
"""

import pytest
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.models import User
from app.core.security import password_manager, jwt_manager
from app.database import get_session


class TestPasswordSecurity:
    """Test password security requirements."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        mock_db = Mock(spec=Session)
        app.dependency_overrides[get_session] = lambda: mock_db
        yield mock_db
        app.dependency_overrides.clear()
    
    def test_no_plain_text_passwords_in_database(self, client, mock_db_session):
        """Verify no plain text passwords are stored in database."""
        # Mock successful database operations
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db_session.exec.return_value = mock_result
        
        # Capture the user object passed to db.add
        added_user = None
        def capture_add(user):
            nonlocal added_user
            added_user = user
        
        mock_db_session.add.side_effect = capture_add
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        
        def mock_refresh(user):
            user.id = uuid.uuid4()
            user.created_at = datetime.now()
        mock_db_session.refresh.side_effect = mock_refresh
        
        # Register a user
        registration_data = {
            "email": f"security{uuid.uuid4().hex[:8]}@example.com",
            "password": "MySecretPassword123!",
            "full_name": "Security Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 200
        
        # Verify password is hashed, not plain text
        assert added_user is not None
        assert added_user.password_hash != registration_data["password"]
        assert added_user.password_hash.startswith("$2b$")  # bcrypt format
        assert len(added_user.password_hash) > 50  # bcrypt hashes are long
        
        # Verify password can be verified with bcrypt
        assert password_manager.verify_password(
            registration_data["password"], 
            added_user.password_hash
        )
        
        # Verify wrong password doesn't verify
        assert not password_manager.verify_password(
            "WrongPassword", 
            added_user.password_hash
        )
    
    def test_password_hashing_strength_and_salt_uniqueness(self):
        """Test password hashing strength and salt uniqueness."""
        password = "TestPassword123!"
        
        # Hash the same password multiple times
        hash1 = password_manager.hash_password(password)
        hash2 = password_manager.hash_password(password)
        hash3 = password_manager.hash_password(password)
        
        # All hashes should be different due to unique salts
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3
        
        # All should be bcrypt format
        assert hash1.startswith("$2b$")
        assert hash2.startswith("$2b$")
        assert hash3.startswith("$2b$")
        
        # All should verify against the original password
        assert password_manager.verify_password(password, hash1)
        assert password_manager.verify_password(password, hash2)
        assert password_manager.verify_password(password, hash3)
        
        # None should verify against wrong password
        wrong_password = "WrongPassword123!"
        assert not password_manager.verify_password(wrong_password, hash1)
        assert not password_manager.verify_password(wrong_password, hash2)
        assert not password_manager.verify_password(wrong_password, hash3)


class TestJWTTokenSecurity:
    """Test JWT token security requirements."""
    
    def test_jwt_tokens_expire_after_24_hours(self):
        """Confirm JWT tokens expire after 24 hours."""
        user_data = {
            "user_id": str(uuid.uuid4()),
            "email": "test@example.com"
        }
        
        # Create token
        token = jwt_manager.create_access_token(user_data)
        
        # Verify token is valid now
        payload = jwt_manager.verify_token(token)
        assert payload["user_id"] == user_data["user_id"]
        assert payload["email"] == user_data["email"]
        
        # Check expiration time
        current_time = time.time()
        token_exp = payload["exp"]
        
        # Token should expire in approximately 24 hours (86400 seconds)
        # Allow some tolerance for test execution time
        time_diff = token_exp - current_time
        assert 86300 < time_diff < 86500  # 24 hours ± 100 seconds
    
    def test_token_validation_rejects_expired_tokens(self):
        """Test token validation rejects expired tokens."""
        # Create a token with past expiration
        past_time = int(time.time()) - 3600  # 1 hour ago
        
        import jwt
        from app.core.config import settings
        
        expired_payload = {
            "user_id": str(uuid.uuid4()),
            "email": "test@example.com",
            "exp": past_time
        }
        
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Token validation should reject expired token
        with pytest.raises(Exception) as exc_info:
            jwt_manager.verify_token(expired_token)
        
        # Should raise an expiration-related exception
        assert "expired" in str(exc_info.value).lower() or "signature" in str(exc_info.value).lower()
    
    def test_token_validation_rejects_invalid_tokens(self):
        """Test token validation rejects malformed/invalid tokens."""
        invalid_tokens = [
            "invalid-token",
            "not.a.valid.jwt.token",
            "",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",  # Malformed JWT
            "Bearer valid-looking-but-fake-token",
        ]
        
        for invalid_token in invalid_tokens:
            with pytest.raises(Exception) as exc_info:
                jwt_manager.verify_token(invalid_token)
            
            # Should raise a validation-related exception
            error_msg = str(exc_info.value).lower()
            assert any(keyword in error_msg for keyword in [
                "invalid", "malformed", "decode", "token", "format", "empty"
            ])
    
    def test_jwt_secret_key_security(self, client):
        """Test JWT secret key is never exposed."""
        # Register a user to get a token
        mock_db = Mock(spec=Session)
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db.exec.return_value = mock_result
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        def mock_refresh(user):
            user.id = uuid.uuid4()
            user.created_at = datetime.now()
        mock_db.refresh.side_effect = mock_refresh
        
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            registration_data = {
                "email": f"secret{uuid.uuid4().hex[:8]}@example.com",
                "password": "SecurePass123!",
                "full_name": "Secret Test User"
            }
            
            response = client.post("/api/v1/auth/register", json=registration_data)
            assert response.status_code == 200
            
            response_data = response.json()
            
            # Check that secret key is not in response
            response_text = str(response_data).lower()
            
            # Import settings to get the actual secret key
            from app.core.config import settings
            secret_key = settings.SECRET_KEY.lower()
            
            # Secret key should not appear in response
            assert secret_key not in response_text
            
            # JWT token should be present but not the secret
            assert "access_token" in response_text
            
        finally:
            app.dependency_overrides.clear()
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

class TestErrorMessageSecurity:
    """Test that error messages don't leak sensitive information."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_error_messages_dont_leak_sensitive_information(self, client):
        """Verify error messages don't expose sensitive data."""
        # Test with various invalid requests
        test_cases = [
            # Invalid login
            {
                "endpoint": "/api/v1/auth/login",
                "data": {"email": "nonexistent@example.com", "password": "wrongpassword"}
            },
            # Invalid registration
            {
                "endpoint": "/api/v1/auth/register", 
                "data": {"email": "invalid-email", "password": "short", "full_name": "Test"}
            },
        ]
        
        sensitive_patterns = [
            # Database-related
            "database", "sql", "postgres", "supabase", "connection",
            # System paths
            "/app/", "/home/", "c:\\", "d:\\",
            # Internal errors
            "traceback", "exception", "stack trace",
            # Secrets (but allow common words)
            "secret_key", "jwt_secret", "private_key",
            # Internal implementation details
            "bcrypt", "pydantic"
        ]
        
        for test_case in test_cases:
            response = client.post(test_case["endpoint"], json=test_case["data"])
            
            # Should return error status
            assert response.status_code >= 400
            
            response_text = str(response.json()).lower()
            
            # Check that sensitive information is not leaked
            for pattern in sensitive_patterns:
                assert pattern not in response_text, f"Sensitive pattern '{pattern}' found in error response"
            
            # Error messages should be user-friendly
            assert len(response_text) > 0
            assert "error" in response_text or "invalid" in response_text or "failed" in response_text


class TestProtectedRoutesSecurity:
    """Test security of protected routes."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_protected_routes_require_authentication(self, client):
        """Test that protected routes require valid authentication."""
        protected_endpoints = [
            "/api/v1/auth/profile",
        ]
        
        for endpoint in protected_endpoints:
            # Test without token
            response = client.get(endpoint)
            assert response.status_code == 401
            
            # Test with invalid token
            headers = {"Authorization": "Bearer invalid-token"}
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 401
            
            # Test with malformed authorization header
            headers = {"Authorization": "invalid-format"}
            response = client.get(endpoint, headers=headers)
            assert response.status_code in [401, 403]
    
    def test_expired_tokens_rejected_on_protected_routes(self, client):
        """Test that expired tokens are rejected on protected routes."""
        # Create expired token
        import jwt
        from app.core.config import settings
        
        expired_payload = {
            "user_id": str(uuid.uuid4()),
            "email": "test@example.com",
            "exp": int(time.time()) - 3600  # Expired 1 hour ago
        }
        
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/profile", headers=headers)
        
        assert response.status_code == 401
        
        response_data = response.json()
        error_text = str(response_data).lower()
        assert "expired" in error_text or "invalid" in error_text or "token" in error_text


class TestDataValidationSecurity:
    """Test data validation security aspects."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_sql_injection_prevention(self, client):
        """Test that SQL injection attempts are prevented."""
        # Note: Since we're using SQLModel/SQLAlchemy with parameterized queries,
        # SQL injection should be prevented by default
        
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
        ]
        
        for payload in sql_injection_payloads:
            # Try SQL injection in login
            login_data = {
                "email": f"test{uuid.uuid4().hex[:4]}@example.com",
                "password": payload
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            # Should handle safely - not cause internal server error
            assert response.status_code in [400, 401, 422]
            
            # Should not cause system to crash or leak information
            if response.status_code == 500:
                response_text = str(response.json()).lower()
                assert "drop table" not in response_text
                assert "sql" not in response_text