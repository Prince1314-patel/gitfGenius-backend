"""
Unit tests for user registration endpoint.

Tests the POST /register endpoint to ensure proper user registration,
validation, error handling, and response formatting.
"""

import pytest
import uuid
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime

from app.main import app
from app.models import User
from app.schemas import UserRegistrationRequest, StandardResponse, AuthenticationResponse
from app.core.security import password_manager, jwt_manager
from app.database import get_session


class TestUserRegistration:
    """Test cases for user registration endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def valid_registration_data(self):
        """Valid user registration data."""
        return {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
    
    @pytest.fixture
    def existing_user(self):
        """Create an existing user for duplicate email tests."""
        return User(
            id=uuid.uuid4(),
            email="existing@example.com",
            password_hash="hashed_password",
            full_name="Existing User",
            created_at=datetime.now()
        )
    
    def test_successful_registration_with_valid_data(self, client, valid_registration_data):
        """Test successful registration with valid email and password."""
        mock_db = Mock(spec=Session)
        
        # Mock database query to return None (no existing user)
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db.exec.return_value = mock_result
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock the refreshed user
        new_user_id = uuid.uuid4()
        def mock_refresh(user):
            user.id = new_user_id
            user.created_at = datetime.now()
        
        mock_db.refresh.side_effect = mock_refresh
        
        # Override the dependency for this specific test
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            # Make request
            response = client.post("/auth/register", json=valid_registration_data)
            
            # Should return 200 with success response
            assert response.status_code == 200
            
            response_data = response.json()
            assert response_data["status"] == "success"
            assert response_data["message"] == "User registered successfully."
            assert response_data["data"] is not None
            
            # Verify response contains user info and JWT token
            auth_data = response_data["data"]
            assert "user" in auth_data
            assert "access_token" in auth_data
            assert "token_type" in auth_data
            
            user_data = auth_data["user"]
            assert user_data["email"] == valid_registration_data["email"]
            assert user_data["full_name"] == valid_registration_data["full_name"]
            assert "id" in user_data
            assert "created_at" in user_data
            
            assert auth_data["token_type"] == "bearer"
            assert len(auth_data["access_token"]) > 0
            
            # Verify database operations were called
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
        finally:
            # Clean up this test's dependency override
            if get_session in app.dependency_overrides:
                del app.dependency_overrides[get_session]
    
    def test_duplicate_email_prevention(self, client, valid_registration_data, existing_user):
        """Test duplicate email prevention and appropriate error response."""
        mock_db = Mock(spec=Session)
        
        # Mock database query to return existing user
        mock_result = Mock()
        mock_result.first.return_value = existing_user
        mock_db.exec.return_value = mock_result
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            # Use existing user's email
            registration_data = valid_registration_data.copy()
            registration_data["email"] = existing_user.email
            
            # Make request
            response = client.post("/auth/register", json=registration_data)
            
            # Should return 409 with error response
            assert response.status_code == 409
            
            response_data = response.json()
            # HTTPException wraps the detail in a "detail" key
            detail = response_data["detail"]
            assert detail["status"] == "error"
            assert detail["data"] is None
            assert "already exists" in detail["message"].lower()
            
            # Verify database add/commit were not called
            mock_db.add.assert_not_called()
            mock_db.commit.assert_not_called()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_email_format_validation_with_invalid_formats(self, client, valid_registration_data):
        """Test email format validation with various invalid formats."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example",
            "",
            "test@.com",
            "test@example..com"
        ]
        
        for invalid_email in invalid_emails:
            registration_data = valid_registration_data.copy()
            registration_data["email"] = invalid_email
            
            response = client.post("/auth/register", json=registration_data)
            
            # Should return 422 for validation error
            assert response.status_code == 422
            
            response_data = response.json()
            assert "detail" in response_data
            # Pydantic validation error format
            assert isinstance(response_data["detail"], list)
            assert any("email" in str(error).lower() for error in response_data["detail"])
    
    def test_password_length_validation(self, client, valid_registration_data):
        """Test password length validation (minimum 8 characters)."""
        short_passwords = [
            "",
            "1",
            "12",
            "123",
            "1234",
            "12345",
            "123456",
            "1234567"  # 7 characters - should fail
        ]
        
        for short_password in short_passwords:
            registration_data = valid_registration_data.copy()
            registration_data["password"] = short_password
            
            response = client.post("/auth/register", json=registration_data)
            
            # Should return 422 for validation error
            assert response.status_code == 422
            
            response_data = response.json()
            assert "detail" in response_data
            assert isinstance(response_data["detail"], list)
            assert any("password" in str(error).lower() for error in response_data["detail"])
    
    def test_password_hashing_integration(self, client, valid_registration_data):
        """Test password hashing integration (no plain text storage)."""
        mock_db = Mock(spec=Session)
        
        # Mock database query to return None (no existing user)
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db.exec.return_value = mock_result
        
        # Capture the user object passed to db.add
        added_user = None
        def capture_add(user):
            nonlocal added_user
            added_user = user
        
        mock_db.add.side_effect = capture_add
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock the refreshed user
        new_user_id = uuid.uuid4()
        def mock_refresh(user):
            user.id = new_user_id
            user.created_at = datetime.now()
        
        mock_db.refresh.side_effect = mock_refresh
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            # Make request
            response = client.post("/auth/register", json=valid_registration_data)
            
            # Should return 200
            assert response.status_code == 200
            
            # Verify password was hashed
            assert added_user is not None
            assert added_user.password_hash != valid_registration_data["password"]
            assert added_user.password_hash.startswith("$2b$")  # bcrypt format
            
            # Verify password can be verified
            assert password_manager.verify_password(
                valid_registration_data["password"], 
                added_user.password_hash
            )
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_standardized_response_format_success(self, client, valid_registration_data):
        """Test standardized response format for success cases."""
        mock_db = Mock(spec=Session)
        
        # Mock successful registration
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db.exec.return_value = mock_result
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        new_user_id = uuid.uuid4()
        def mock_refresh(user):
            user.id = new_user_id
            user.created_at = datetime.now()
        
        mock_db.refresh.side_effect = mock_refresh
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            response = client.post("/auth/register", json=valid_registration_data)
            
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
    
    def test_standardized_response_format_error(self, client, valid_registration_data, existing_user):
        """Test standardized response format for error cases."""
        mock_db = Mock(spec=Session)
        
        # Mock duplicate email scenario
        mock_result = Mock()
        mock_result.first.return_value = existing_user
        mock_db.exec.return_value = mock_result
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            registration_data = valid_registration_data.copy()
            registration_data["email"] = existing_user.email
            
            response = client.post("/auth/register", json=registration_data)
            
            assert response.status_code == 409
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
    
    def test_database_integration_and_user_model_creation(self, client, valid_registration_data):
        """Test database integration and User model creation."""
        mock_db = Mock(spec=Session)
        
        # Mock database operations
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db.exec.return_value = mock_result
        
        added_user = None
        def capture_add(user):
            nonlocal added_user
            added_user = user
        
        mock_db.add.side_effect = capture_add
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        new_user_id = uuid.uuid4()
        def mock_refresh(user):
            user.id = new_user_id
            user.created_at = datetime.now()
        
        mock_db.refresh.side_effect = mock_refresh
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            response = client.post("/auth/register", json=valid_registration_data)
            
            assert response.status_code == 200
            
            # Verify User model was created correctly
            assert added_user is not None
            assert isinstance(added_user, User)
            assert added_user.email == valid_registration_data["email"]
            assert added_user.full_name == valid_registration_data["full_name"]
            assert added_user.password_hash != valid_registration_data["password"]
            assert added_user.password_hash.startswith("$2b$")
            
            # Verify database operations
            mock_db.exec.assert_called_once()  # Check for existing user
            mock_db.add.assert_called_once_with(added_user)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(added_user)
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_jwt_token_generation_and_properties(self, client, valid_registration_data):
        """Test JWT token generation and properties."""
        mock_db = Mock(spec=Session)
        
        # Mock successful registration
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db.exec.return_value = mock_result
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        new_user_id = uuid.uuid4()
        def mock_refresh(user):
            user.id = new_user_id
            user.created_at = datetime.now()
        
        mock_db.refresh.side_effect = mock_refresh
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            response = client.post("/auth/register", json=valid_registration_data)
            
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
            
            assert payload["email"] == valid_registration_data["email"]
            assert payload["user_id"] == str(new_user_id)
            
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
    
    def test_missing_required_fields(self, client):
        """Test validation when required fields are missing."""
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
            response = client.post("/auth/register", json=test_data)
            
            # Should return 422 for validation error
            assert response.status_code == 422
            
            response_data = response.json()
            assert "detail" in response_data
            assert isinstance(response_data["detail"], list)
            assert len(response_data["detail"]) > 0
    
    def test_database_rollback_on_error(self, client, valid_registration_data):
        """Test database rollback when errors occur during registration."""
        mock_db = Mock(spec=Session)
        
        # Mock database query to return None (no existing user)
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_db.exec.return_value = mock_result
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=Exception("Database error"))
        mock_db.rollback = Mock()
        
        # Override the dependency
        app.dependency_overrides[get_session] = lambda: mock_db
        
        try:
            response = client.post("/auth/register", json=valid_registration_data)
            
            # Should return 500 for internal server error
            assert response.status_code == 500
            
            response_data = response.json()
            # HTTPException wraps the detail in a "detail" key
            detail = response_data["detail"]
            assert detail["status"] == "error"
            assert detail["data"] is None
            assert "error occurred during registration" in detail["message"].lower()
            
            # Verify rollback was called
            mock_db.rollback.assert_called_once()
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()