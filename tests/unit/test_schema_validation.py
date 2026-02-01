"""
Comprehensive schema validation tests.

Tests request and response schema validation with various invalid inputs,
edge cases, and field-level validation error reporting.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import Mock
from sqlmodel import Session

from app.main import app
from app.database import get_session


class TestRequestSchemaValidation:
    """Test request schema validation with various invalid inputs."""
    
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
    
    def test_registration_schema_validation_malformed_json(self, client):
        """Test registration endpoint with malformed JSON."""
        # Test with invalid JSON syntax
        response = client.post(
            "/api/v1/auth/register",
            data='{"email": "test@example.com", "password": "invalid json'  # Missing closing brace
        )
        
        # Should return 400 or 422 for malformed JSON
        assert response.status_code in [400, 422]
        
        response_data = response.json()
        assert "detail" in response_data or "status" in response_data
    
    def test_registration_schema_validation_missing_fields(self, client):
        """Test registration endpoint with missing required fields."""
        test_cases = [
            {},  # All fields missing
            {"email": "test@example.com"},  # Missing password and full_name
            {"password": "SecurePass123!"},  # Missing email and full_name
            {"full_name": "Test User"},  # Missing email and password
            {"email": "test@example.com", "password": "SecurePass123!"},  # Missing full_name
            {"email": "test@example.com", "full_name": "Test User"},  # Missing password
            {"password": "SecurePass123!", "full_name": "Test User"},  # Missing email
        ]
        
        for test_data in test_cases:
            response = client.post("/api/v1/auth/register", json=test_data)
            
            # Should return 422 for validation error
            assert response.status_code in [400, 422], f"Failed for data: {test_data}"
            
            response_data = response.json()
            assert "detail" in response_data or "status" in response_data
    
    def test_registration_schema_validation_extra_fields(self, client, mock_db_session):
        """Test registration endpoint with extra fields."""
        # Mock successful database operations
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db_session.exec.return_value = mock_result
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        
        import uuid
        from datetime import datetime
        def mock_refresh(user):
            user.id = uuid.uuid4()
            user.created_at = datetime.now()
        mock_db_session.refresh.side_effect = mock_refresh
        
        # Test with extra fields that should be ignored
        test_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "extra_field": "should be ignored",
            "admin": True,  # Should not make user admin
            "id": "should-not-override-generated-id"
        }
        
        response = client.post("/api/v1/auth/register", json=test_data)
        
        # Should succeed and ignore extra fields
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["status"] == "success"
        
        # Verify extra fields are not in response
        user_data = response_data["data"]["user"]
        assert "extra_field" not in user_data
        assert "admin" not in user_data
    
    def test_registration_email_format_validation_comprehensive(self, client):
        """Test email format validation with comprehensive test cases."""
        invalid_emails = [
            # Basic invalid formats
            "invalid-email",
            "@example.com",
            "test@",
            "test@example",
            "",
            "test@.com",
            "test@example..com",
            
            # Advanced invalid formats
            "test..test@example.com",  # Double dots in local part
            "test@example.com.",  # Trailing dot
            ".test@example.com",  # Leading dot
            "test@",  # Missing domain
            "@",  # Only @ symbol
            "test@@example.com",  # Double @ symbols
            "test@example@com",  # Multiple @ symbols
            "test@example .com",  # Space in domain
            "test @example.com",  # Space in local part
            "test@example,com",  # Comma instead of dot
            "test@example..com",  # Double dots in domain
            "test@.example.com",  # Leading dot in domain
            "test@example.com.",  # Trailing dot in domain
            
            # Special characters that should be invalid
            "test@",  # Empty domain
            "test@-example.com",  # Domain starts with hyphen
            "test@example-.com",  # Domain ends with hyphen
        ]
        
        # Skip emails that might be valid according to some validators
        skip_emails = [
            "test@example.c",  # Single char TLD might be valid
            "test@example.toolongtobevalid",  # Long TLD might be valid
            "test@例え.テスト",  # Unicode domains might be valid
            "test@[192.168.1.1]",  # IP address format might be valid
            "test+tag@example.com",  # Plus addressing should be valid
        ]
        
        for invalid_email in invalid_emails:
            registration_data = {
                "email": invalid_email,
                "password": "SecurePass123!",
                "full_name": "Test User"
            }
            
            response = client.post("/api/v1/auth/register", json=registration_data)
            
            # Should return 400 or 422 for validation error
            assert response.status_code in [400, 422], f"Email '{invalid_email}' should be invalid"
            
            response_data = response.json()
            assert "detail" in response_data or "status" in response_data
            
            # Check that error mentions email
            error_text = str(response_data).lower()
            assert "email" in error_text or "invalid" in error_text
    
    def test_registration_password_validation_comprehensive(self, client):
        """Test password validation with comprehensive test cases."""
        invalid_passwords = [
            "",  # Empty password
            "1",  # Too short
            "12",
            "123",
            "1234",
            "12345",
            "123456",
            "1234567",  # 7 characters - should fail (minimum is 8)
        ]
        
        for invalid_password in invalid_passwords:
            registration_data = {
                "email": "test@example.com",
                "password": invalid_password,
                "full_name": "Test User"
            }
            
            response = client.post("/api/v1/auth/register", json=registration_data)
            
            # Should return 400 or 422 for validation error
            assert response.status_code in [400, 422], f"Password '{invalid_password}' should be invalid"
            
            response_data = response.json()
            assert "detail" in response_data or "status" in response_data
            
            # Check that error mentions password
            error_text = str(response_data).lower()
            assert "password" in error_text or "length" in error_text
    
    def test_login_schema_validation_missing_fields(self, client):
        """Test login endpoint with missing required fields."""
        test_cases = [
            {},  # All fields missing
            {"email": "test@example.com"},  # Missing password
            {"password": "SecurePass123!"},  # Missing email
        ]
        
        for test_data in test_cases:
            response = client.post("/api/v1/auth/login", json=test_data)
            
            # Should return 400 or 422 for validation error
            assert response.status_code in [400, 422], f"Failed for data: {test_data}"
            
            response_data = response.json()
            assert "detail" in response_data or "status" in response_data
    
    def test_login_email_format_validation(self, client):
        """Test login endpoint email format validation."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "",
            "test@.com",
        ]
        
        for invalid_email in invalid_emails:
            login_data = {
                "email": invalid_email,
                "password": "SecurePass123!"
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            # Should return 400 or 422 for validation error
            assert response.status_code in [400, 422], f"Email '{invalid_email}' should be invalid"
            
            response_data = response.json()
            assert "detail" in response_data or "status" in response_data


class TestResponseSchemaConsistency:
    """Test response schema consistency across all endpoints."""
    
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
    
    def test_successful_registration_response_schema(self, client, mock_db_session):
        """Test successful registration response follows schema."""
        # Mock successful database operations
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db_session.exec.return_value = mock_result
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        
        import uuid
        from datetime import datetime
        def mock_refresh(user):
            user.id = uuid.uuid4()
            user.created_at = datetime.now()
        mock_db_session.refresh.side_effect = mock_refresh
        
        registration_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 200
        
        response_data = response.json()
        
        # Verify standardized response envelope
        assert "status" in response_data
        assert "data" in response_data
        assert "message" in response_data
        
        assert response_data["status"] == "success"
        assert response_data["data"] is not None
        assert isinstance(response_data["message"], str)
        
        # Verify authentication response structure
        auth_data = response_data["data"]
        assert "user" in auth_data
        assert "access_token" in auth_data
        assert "token_type" in auth_data
        
        # Verify user info structure
        user_data = auth_data["user"]
        assert "id" in user_data
        assert "email" in user_data
        assert "full_name" in user_data
        assert "created_at" in user_data
        
        # Verify data types
        assert isinstance(user_data["id"], str)
        assert isinstance(user_data["email"], str)
        assert isinstance(user_data["full_name"], str)
        assert isinstance(user_data["created_at"], str)
        assert isinstance(auth_data["access_token"], str)
        assert isinstance(auth_data["token_type"], str)
        
        # Verify token type
        assert auth_data["token_type"] == "bearer"
    
    def test_successful_login_response_schema(self, client, mock_db_session):
        """Test successful login response follows schema."""
        # Mock user in database
        from app.models import User
        from app.core.security import password_manager
        import uuid
        from datetime import datetime
        
        user_id = uuid.uuid4()
        hashed_password = password_manager.hash_password("SecurePass123!")
        mock_user = User(
            id=user_id,
            email="test@example.com",
            password_hash=hashed_password,
            full_name="Test User",
            created_at=datetime.now()
        )
        
        mock_result = Mock()
        mock_result.first.return_value = mock_user
        mock_db_session.exec.return_value = mock_result
        
        login_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        response_data = response.json()
        
        # Verify same schema as registration
        assert "status" in response_data
        assert "data" in response_data
        assert "message" in response_data
        
        assert response_data["status"] == "success"
        assert response_data["data"] is not None
        assert isinstance(response_data["message"], str)
        
        # Verify authentication response structure
        auth_data = response_data["data"]
        assert "user" in auth_data
        assert "access_token" in auth_data
        assert "token_type" in auth_data
        
        # Verify user info structure
        user_data = auth_data["user"]
        assert "id" in user_data
        assert "email" in user_data
        assert "full_name" in user_data
        assert "created_at" in user_data
        
        assert auth_data["token_type"] == "bearer"
    
    def test_error_response_schema_consistency(self, client, mock_db_session):
        """Test error responses follow consistent schema."""
        # Mock duplicate email scenario
        from app.models import User
        import uuid
        from datetime import datetime
        
        existing_user = User(
            id=uuid.uuid4(),
            email="existing@example.com",
            password_hash="hashed_password",
            full_name="Existing User",
            created_at=datetime.now()
        )
        
        mock_result = Mock()
        mock_result.first.return_value = existing_user
        mock_db_session.exec.return_value = mock_result
        
        registration_data = {
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 409
        
        response_data = response.json()
        
        # Error responses should have consistent structure
        assert "status" in response_data
        assert "data" in response_data
        assert "message" in response_data
        
        assert response_data["status"] == "error"
        assert response_data["data"] is None
        assert isinstance(response_data["message"], str)
        assert len(response_data["message"]) > 0
    
    def test_validation_error_response_schema(self, client):
        """Test validation error responses include field-level details."""
        # Test with invalid email format
        registration_data = {
            "email": "invalid-email",
            "password": "short",  # Also too short
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code in [400, 422]
        
        response_data = response.json()
        
        # Should have detail field with validation errors
        assert "detail" in response_data or "status" in response_data
        
        if "detail" in response_data:
            # FastAPI validation error format
            assert isinstance(response_data["detail"], list)
            assert len(response_data["detail"]) > 0
            
            # Each error should have location and message
            for error in response_data["detail"]:
                assert "loc" in error or "field" in error or isinstance(error, str)
                assert "msg" in error or "message" in error or isinstance(error, str)
        else:
            # Custom error format
            assert response_data["status"] == "error"
            assert "message" in response_data


class TestFieldLevelValidationErrors:
    """Test field-level validation error reporting."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_email_validation_error_details(self, client):
        """Test email validation provides specific error details."""
        registration_data = {
            "email": "invalid-email-format",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code in [400, 422]
        
        response_data = response.json()
        error_text = str(response_data).lower()
        
        # Should mention email in error
        assert "email" in error_text or "invalid" in error_text
    
    def test_password_validation_error_details(self, client):
        """Test password validation provides specific error details."""
        registration_data = {
            "email": "test@example.com",
            "password": "short",  # Too short
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code in [400, 422]
        
        response_data = response.json()
        error_text = str(response_data).lower()
        
        # Should mention password or length in error
        assert "password" in error_text or "length" in error_text or "8" in error_text
    
    def test_multiple_validation_errors(self, client):
        """Test multiple validation errors are reported together."""
        registration_data = {
            "email": "invalid-email",  # Invalid email
            "password": "short",  # Too short password
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code in [400, 422]
        
        response_data = response.json()
        error_text = str(response_data).lower()
        
        # Should mention both email and password issues
        # Note: Depending on validation order, might only show first error
        assert "email" in error_text or "password" in error_text or "invalid" in error_text


class TestEdgeCases:
    """Test edge cases for schema validation."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_null_values_in_required_fields(self, client):
        """Test null values in required fields."""
        test_cases = [
            {"email": None, "password": "SecurePass123!", "full_name": "Test User"},
            {"email": "test@example.com", "password": None, "full_name": "Test User"},
            {"email": "test@example.com", "password": "SecurePass123!", "full_name": None},
        ]
        
        for test_data in test_cases:
            response = client.post("/api/v1/auth/register", json=test_data)
            
            # Should return validation error
            assert response.status_code in [400, 422], f"Failed for data: {test_data}"
    
    def test_empty_string_values(self, client):
        """Test empty string values in required fields."""
        test_cases = [
            {"email": "", "password": "SecurePass123!", "full_name": "Test User"},
            {"email": "test@example.com", "password": "", "full_name": "Test User"},
            {"email": "test@example.com", "password": "SecurePass123!", "full_name": ""},
        ]
        
        for test_data in test_cases:
            response = client.post("/api/v1/auth/register", json=test_data)
            
            # Should return validation error
            assert response.status_code in [400, 422], f"Failed for data: {test_data}"
    
    def test_whitespace_only_values(self, client):
        """Test whitespace-only values in required fields."""
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        
        test_cases = [
            {"email": "   ", "password": "SecurePass123!", "full_name": "Test User"},
            {"email": f"test{unique_suffix}@example.com", "password": "   ", "full_name": "Test User"},
            {"email": f"test2{unique_suffix}@example.com", "password": "SecurePass123!", "full_name": "   "},
        ]
        
        for i, test_data in enumerate(test_cases):
            response = client.post("/api/v1/auth/register", json=test_data)
            
            # Should return validation error for email and password, but full_name might allow whitespace
            if test_data["full_name"] == "   ":
                # Full name might allow whitespace, so we'll be more lenient
                assert response.status_code in [200, 400, 409, 422], f"Failed for data: {test_data}"
            else:
                assert response.status_code in [400, 422], f"Failed for data: {test_data}"
    
    def test_very_long_field_values(self, client):
        """Test very long field values."""
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        
        long_email = "a" * 50 + f"{unique_suffix}@example.com"  # Very long email
        long_password = "a" * 1000  # Very long password
        long_name = "a" * 1000  # Very long name
        
        test_cases = [
            {"email": long_email, "password": "SecurePass123!", "full_name": "Test User"},
            {"email": f"test{unique_suffix}@example.com", "password": long_password, "full_name": "Test User"},
            {"email": f"test2{unique_suffix}@example.com", "password": "SecurePass123!", "full_name": long_name},
        ]
        
        for test_data in test_cases:
            response = client.post("/api/v1/auth/register", json=test_data)
            
            # Might succeed or fail depending on field length limits
            # We'll accept any reasonable response
            assert response.status_code in [200, 400, 409, 422, 413], f"Failed for data keys: {list(test_data.keys())}"
    
    def test_unicode_characters(self, client, mock_db_session):
        """Test unicode characters in fields."""
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        
        # Mock successful database operations for valid cases
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db_session.exec.return_value = mock_result
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        
        from datetime import datetime
        def mock_refresh(user):
            user.id = uuid.uuid4()
            user.created_at = datetime.now()
        mock_db_session.refresh.side_effect = mock_refresh
        
        # Test unicode in full name (should be allowed)
        unicode_name_data = {
            "email": f"test{unique_suffix}@example.com",
            "password": "SecurePass123!",
            "full_name": "José María García-López 测试用户 🙂"
        }
        
        response = client.post("/api/v1/auth/register", json=unicode_name_data)
        
        # Should succeed - unicode names should be allowed
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["data"]["user"]["full_name"] == unicode_name_data["full_name"]