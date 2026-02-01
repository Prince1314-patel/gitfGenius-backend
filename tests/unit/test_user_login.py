"""
Unit tests for user login endpoint.

Tests the POST /login endpoint to ensure proper user authentication,
JWT token generation, error handling, and response formatting.
"""

import pytest
import uuid
from unittest.mock import Mock
from fastapi.testclient import TestClient
from sqlmodel import Session
from datetime import datetime

from app.main import app
from app.models import User
from app.schemas import UserLoginRequest, StandardResponse, AuthenticationResponse
from app.core.security import password_manager, jwt_manager
from app.database import get_session


class TestUserLogin:
    """Test cases for user login endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def valid_login_data(self):
        """Valid user login data."""
        return {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
    
    @pytest.fixture
    def existing_user(self, valid_login_data):
        """Create an existing user with hashed password."""
        hashed_password = password_manager.hash_password(valid_login_data["password"])
        return User(
            id=uuid.uuid4(),
            email=valid_login_data["email"],
            password_hash=hashed_password,
            full_name="Test User",
            created_at=datetime.now()
        )
    
    def test_successful_login_with_valid_credentials(self, client, valid_login_data, existing_user):
        """Test successful login with valid credentials and JWT token generation."""
        mock_db = Mock(spec=Session)
        
        # Mock database query to return existing user
        mock_result = Mock()
        mock_result.first.return_value = existing_user
        mock_db.exec.return_value = mock_result
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            # Make request
            response = client.post("/auth/login", json=valid_login_data)
            
            # Should return 200 with success response
            assert response.status_code == 200
            
            response_data = response.json()
            assert response_data["status"] == "success"
            assert response_data["message"] == "Login successful."
            assert response_data["data"] is not None
            
            # Verify response contains user info and JWT token
            auth_data = response_data["data"]
            assert "user" in auth_data
            assert "access_token" in auth_data
            assert "token_type" in auth_data
            
            user_data = auth_data["user"]
            assert user_data["email"] == valid_login_data["email"]
            assert user_data["full_name"] == existing_user.full_name
            assert user_data["id"] == str(existing_user.id)
            assert "created_at" in user_data
            
            assert auth_data["token_type"] == "bearer"
            assert len(auth_data["access_token"]) > 0
            
            # Verify database query was called
            mock_db.exec.assert_called_once()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_login_failure_with_incorrect_email(self, client, valid_login_data):
        """Test login failure with incorrect email."""
        mock_db = Mock(spec=Session)
        
        # Mock database query to return None (user not found)
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db.exec.return_value = mock_result
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            # Use incorrect email
            login_data = valid_login_data.copy()
            login_data["email"] = "nonexistent@example.com"
            
            # Make request
            response = client.post("/auth/login", json=login_data)
            
            # Should return 401 with error response
            assert response.status_code == 401
            
            response_data = response.json()
            detail = response_data["detail"]
            assert detail["status"] == "error"
            assert detail["data"] is None
            assert "invalid email or password" in detail["message"].lower()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_login_failure_with_incorrect_password(self, client, valid_login_data, existing_user):
        """Test login failure with incorrect password."""
        mock_db = Mock(spec=Session)
        
        # Mock database query to return existing user
        mock_result = Mock()
        mock_result.first.return_value = existing_user
        mock_db.exec.return_value = mock_result
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            # Use incorrect password
            login_data = valid_login_data.copy()
            login_data["password"] = "WrongPassword123!"
            
            # Make request
            response = client.post("/auth/login", json=login_data)
            
            # Should return 401 with error response
            assert response.status_code == 401
            
            response_data = response.json()
            detail = response_data["detail"]
            assert detail["status"] == "error"
            assert detail["data"] is None
            assert "invalid email or password" in detail["message"].lower()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_login_response_format_consistency_success(self, client, valid_login_data, existing_user):
        """Test login response format consistency for success cases."""
        mock_db = Mock(spec=Session)
        
        # Mock successful login
        mock_result = Mock()
        mock_result.first.return_value = existing_user
        mock_db.exec.return_value = mock_result
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            response = client.post("/auth/login", json=valid_login_data)
            
            assert response.status_code == 200
            response_data = response.json()
            
            # Verify standardized response format
            assert "status" in response_data
            assert "data" in response_data
            assert "message" in response_data
            
            assert response_data["status"] == "success"
            assert response_data["data"] is not None
            assert isinstance(response_data["message"], str)
            assert len(response_data["message"]) > 0
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_login_response_format_consistency_error(self, client, valid_login_data):
        """Test login response format consistency for error cases."""
        mock_db = Mock(spec=Session)
        
        # Mock user not found scenario
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db.exec.return_value = mock_result
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            response = client.post("/auth/login", json=valid_login_data)
            
            assert response.status_code == 401
            response_data = response.json()
            
            # HTTPException wraps the detail in a "detail" key
            detail = response_data["detail"]
            
            # Verify standardized response format
            assert "status" in detail
            assert "data" in detail
            assert "message" in detail
            
            assert detail["status"] == "error"
            assert detail["data"] is None
            assert isinstance(detail["message"], str)
            assert len(detail["message"]) > 0
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_jwt_token_properties(self, client, valid_login_data, existing_user):
        """Test JWT token properties (expiration, payload content)."""
        mock_db = Mock(spec=Session)
        
        # Mock successful login
        mock_result = Mock()
        mock_result.first.return_value = existing_user
        mock_db.exec.return_value = mock_result
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            response = client.post("/auth/login", json=valid_login_data)
            
            assert response.status_code == 200
            response_data = response.json()
            
            # Extract JWT token
            access_token = response_data["data"]["access_token"]
            assert len(access_token) > 0
            
            # Verify token can be decoded and contains correct data
            payload = jwt_manager.verify_token(access_token)
            assert "user_id" in payload
            assert "email" in payload
            assert "exp" in payload
            
            assert payload["email"] == existing_user.email
            assert payload["user_id"] == str(existing_user.id)
            
            # Verify token expiration (should be 24 hours from now)
            import time
            current_time = time.time()
            token_exp = payload["exp"]
            
            # Token should expire in approximately 24 hours (86400 seconds)
            # Allow some tolerance for test execution time
            time_diff = token_exp - current_time
            assert 86300 < time_diff < 86500  # 24 hours ± 100 seconds
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_authentication_failure_error_messages(self, client, valid_login_data, existing_user):
        """Test authentication failure error messages."""
        mock_db = Mock(spec=Session)
        
        # Test cases for different authentication failures
        test_cases = [
            {
                "name": "user_not_found",
                "mock_user": None,
                "login_data": valid_login_data,
                "expected_message": "invalid email or password"
            },
            {
                "name": "wrong_password",
                "mock_user": existing_user,
                "login_data": {**valid_login_data, "password": "WrongPassword123!"},
                "expected_message": "invalid email or password"
            }
        ]
        
        for test_case in test_cases:
            # Mock database query
            mock_result = Mock()
            mock_result.first.return_value = test_case["mock_user"]
            mock_db.exec.return_value = mock_result
            
            # Override the dependency
            app.dependency_overrides[get_session] = lambda: mock_db
            
            try:
                response = client.post("/auth/login", json=test_case["login_data"])
                
                assert response.status_code == 401
                response_data = response.json()
                detail = response_data["detail"]
                
                assert detail["status"] == "error"
                assert detail["data"] is None
                assert test_case["expected_message"] in detail["message"].lower()
            finally:
                # Clean up dependency override
                app.dependency_overrides.clear()
    
    def test_database_integration_for_credential_verification(self, client, valid_login_data, existing_user):
        """Test database integration for credential verification."""
        mock_db = Mock(spec=Session)
        
        # Mock database query
        mock_result = Mock()
        mock_result.first.return_value = existing_user
        mock_db.exec.return_value = mock_result
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            response = client.post("/auth/login", json=valid_login_data)
            
            assert response.status_code == 200
            
            # Verify database session was used
            mock_db.exec.assert_called_once()
            
            # Verify correct SQL query was constructed
            call_args = mock_db.exec.call_args[0][0]
            # The query should be a select statement for User table filtering by email
            assert hasattr(call_args, 'column_descriptions') or hasattr(call_args, 'columns')
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_password_verification_integration(self, client, valid_login_data, existing_user):
        """Test password verification integration with bcrypt."""
        mock_db = Mock(spec=Session)
        
        # Mock database query to return user
        mock_result = Mock()
        mock_result.first.return_value = existing_user
        mock_db.exec.return_value = mock_result
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            # Test with correct password
            response = client.post("/auth/login", json=valid_login_data)
            assert response.status_code == 200
            
            # Test with incorrect password
            wrong_login_data = valid_login_data.copy()
            wrong_login_data["password"] = "WrongPassword123!"
            
            response = client.post("/auth/login", json=wrong_login_data)
            assert response.status_code == 401
            
            # Verify the password verification was called (indirectly through response)
            response_data = response.json()
            detail = response_data["detail"]
            assert "invalid email or password" in detail["message"].lower()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_missing_required_fields(self, client):
        """Test validation when required fields are missing."""
        test_cases = [
            {},  # All fields missing
            {"email": "test@example.com"},  # Missing password
            {"password": "SecurePass123!"},  # Missing email
        ]
        
        for test_data in test_cases:
            response = client.post("/auth/login", json=test_data)
            
            # Should return 422 for validation error
            assert response.status_code == 422
            
            response_data = response.json()
            assert "detail" in response_data
            assert isinstance(response_data["detail"], list)
            assert len(response_data["detail"]) > 0
    
    def test_invalid_email_format(self, client, valid_login_data):
        """Test login with invalid email format."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test@.com"
        ]
        
        for invalid_email in invalid_emails:
            login_data = valid_login_data.copy()
            login_data["email"] = invalid_email
            
            response = client.post("/auth/login", json=login_data)
            
            # Should return 422 for validation error
            assert response.status_code == 422
            
            response_data = response.json()
            assert "detail" in response_data
            assert isinstance(response_data["detail"], list)
            assert any("email" in str(error).lower() for error in response_data["detail"])
    
    def test_system_error_handling(self, client, valid_login_data):
        """Test system error handling during login."""
        mock_db = Mock(spec=Session)
        
        # Mock database to raise an exception
        mock_db.exec.side_effect = Exception("Database connection error")
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            response = client.post("/auth/login", json=valid_login_data)
            
            # Should return 500 for internal server error
            assert response.status_code == 500
            
            response_data = response.json()
            detail = response_data["detail"]
            assert detail["status"] == "error"
            assert detail["data"] is None
            assert "error occurred during login" in detail["message"].lower()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_user_data_preservation_in_response(self, client, valid_login_data, existing_user):
        """Test that user data is correctly preserved in login response."""
        mock_db = Mock(spec=Session)
        
        # Mock successful login
        mock_result = Mock()
        mock_result.first.return_value = existing_user
        mock_db.exec.return_value = mock_result
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            response = client.post("/auth/login", json=valid_login_data)
            
            assert response.status_code == 200
            response_data = response.json()
            
            user_data = response_data["data"]["user"]
            
            # Verify all user data is correctly preserved
            assert user_data["id"] == str(existing_user.id)
            assert user_data["email"] == existing_user.email
            assert user_data["full_name"] == existing_user.full_name
            assert user_data["created_at"] == existing_user.created_at.isoformat()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()