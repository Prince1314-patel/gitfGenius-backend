"""
Integration tests for authentication endpoints.

These tests use a real test database (SQLite in-memory) to test
the complete authentication flow including database operations.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.models import User
from app.core.security import password_manager, jwt_manager


class TestAuthenticationIntegration:
    """Integration tests for authentication endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing."""
        return {
            "email": "integration@test.com",
            "password": "SecurePass123!",
            "full_name": "Integration Test User"
        }
    
    def test_complete_registration_flow(self, client, test_session: Session, clean_database, sample_user_data):
        """Test complete user registration flow with real database."""
        # Make registration request
        response = client.post("/auth/register", json=sample_user_data)
        
        # Should return 200 with success response
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["message"] == "User registered successfully."
        assert response_data["data"] is not None
        
        # Verify response structure
        auth_data = response_data["data"]
        assert "user" in auth_data
        assert "access_token" in auth_data
        assert "token_type" in auth_data
        
        user_data = auth_data["user"]
        assert user_data["email"] == sample_user_data["email"]
        assert user_data["full_name"] == sample_user_data["full_name"]
        assert "id" in user_data
        assert "created_at" in user_data
        
        # Verify JWT token
        access_token = auth_data["access_token"]
        assert len(access_token) > 0
        assert auth_data["token_type"] == "bearer"
        
        # Verify token can be decoded
        payload = jwt_manager.verify_token(access_token)
        assert "user_id" in payload
        assert "email" in payload
        assert payload["email"] == sample_user_data["email"]
        
        # Verify user was actually created in database
        statement = select(User).where(User.email == sample_user_data["email"])
        db_user = test_session.exec(statement).first()
        
        assert db_user is not None
        assert db_user.email == sample_user_data["email"]
        assert db_user.full_name == sample_user_data["full_name"]
        assert db_user.password_hash != sample_user_data["password"]  # Should be hashed
        assert db_user.password_hash.startswith("$2b$")  # bcrypt format
        
        # Verify password can be verified
        assert password_manager.verify_password(sample_user_data["password"], db_user.password_hash)
    
    def test_complete_login_flow(self, client, test_session: Session, clean_database, sample_user_data):
        """Test complete user login flow with real database."""
        # First, create a user in the database
        hashed_password = password_manager.hash_password(sample_user_data["password"])
        user = User(
            email=sample_user_data["email"],
            password_hash=hashed_password,
            full_name=sample_user_data["full_name"]
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)
        
        # Make login request
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = client.post("/auth/login", json=login_data)
        
        # Should return 200 with success response
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["message"] == "Login successful."
        assert response_data["data"] is not None
        
        # Verify response structure
        auth_data = response_data["data"]
        assert "user" in auth_data
        assert "access_token" in auth_data
        assert "token_type" in auth_data
        
        user_data = auth_data["user"]
        assert user_data["email"] == sample_user_data["email"]
        assert user_data["full_name"] == sample_user_data["full_name"]
        assert user_data["id"] == str(user.id)
        
        # Verify JWT token
        access_token = auth_data["access_token"]
        assert len(access_token) > 0
        assert auth_data["token_type"] == "bearer"
        
        # Verify token can be decoded and contains correct data
        payload = jwt_manager.verify_token(access_token)
        assert payload["user_id"] == str(user.id)
        assert payload["email"] == user.email
    
    def test_registration_then_login_flow(self, client, test_session: Session, clean_database, sample_user_data):
        """Test complete flow: register user, then login with same credentials."""
        # Step 1: Register user
        reg_response = client.post("/auth/register", json=sample_user_data)
        assert reg_response.status_code == 200
        
        reg_data = reg_response.json()
        registered_user_id = reg_data["data"]["user"]["id"]
        
        # Step 2: Login with same credentials
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        logged_in_user_id = login_data["data"]["user"]["id"]
        
        # Should be the same user
        assert registered_user_id == logged_in_user_id
        
        # Both tokens should be valid but different (different timestamps)
        reg_token = reg_data["data"]["access_token"]
        login_token = login_data["data"]["access_token"]
        
        # Both should be valid
        reg_payload = jwt_manager.verify_token(reg_token)
        login_payload = jwt_manager.verify_token(login_token)
        
        assert reg_payload["user_id"] == login_payload["user_id"]
        assert reg_payload["email"] == login_payload["email"]
        
        # Note: Tokens might be identical if created within the same second
        # This is acceptable behavior - what matters is that both are valid
    
    def test_duplicate_registration_prevention(self, client, test_session: Session, clean_database, sample_user_data):
        """Test that duplicate email registration is prevented."""
        # First registration should succeed
        response1 = client.post("/auth/register", json=sample_user_data)
        assert response1.status_code == 200
        
        # Second registration with same email should fail
        response2 = client.post("/auth/register", json=sample_user_data)
        assert response2.status_code == 409
        
        response_data = response2.json()
        assert response_data["status"] == "error"
        assert response_data["data"] is None
        assert "already exists" in response_data["message"].lower()
        assert response_data["error_code"] == "DUPLICATE_EMAIL"
        
        # Verify only one user exists in database
        statement = select(User).where(User.email == sample_user_data["email"])
        users = test_session.exec(statement).all()
        assert len(users) == 1
    
    def test_login_with_wrong_credentials(self, client, test_session: Session, clean_database, sample_user_data):
        """Test login failure with wrong credentials."""
        # Create a user in the database
        hashed_password = password_manager.hash_password(sample_user_data["password"])
        user = User(
            email=sample_user_data["email"],
            password_hash=hashed_password,
            full_name=sample_user_data["full_name"]
        )
        test_session.add(user)
        test_session.commit()
        
        # Test wrong password
        wrong_login_data = {
            "email": sample_user_data["email"],
            "password": "WrongPassword123!"
        }
        response = client.post("/auth/login", json=wrong_login_data)
        assert response.status_code == 401
        
        response_data = response.json()
        assert response_data["status"] == "error"
        assert response_data["data"] is None
        assert "invalid email or password" in response_data["message"].lower()
        assert response_data["error_code"] == "INVALID_CREDENTIALS"
        
        # Test wrong email
        wrong_email_data = {
            "email": "wrong@email.com",
            "password": sample_user_data["password"]
        }
        response = client.post("/auth/login", json=wrong_email_data)
        assert response.status_code == 401
        
        response_data = response.json()
        assert response_data["status"] == "error"
        assert "invalid email or password" in response_data["message"].lower()
        assert response_data["error_code"] == "INVALID_CREDENTIALS"
    
    def test_database_isolation_between_tests(self, client, test_session: Session, clean_database):
        """Test that database is properly isolated between tests."""
        # This test should start with empty database
        users = test_session.exec(select(User)).all()
        assert len(users) == 0
        
        # Create a user
        sample_data = {
            "email": "isolation@test.com",
            "password": "TestPass123!",
            "full_name": "Isolation Test"
        }
        response = client.post("/auth/register", json=sample_data)
        assert response.status_code == 200
        
        # Verify user was created
        users = test_session.exec(select(User)).all()
        assert len(users) == 1
    
    def test_password_security(self, client, test_session: Session, clean_database, sample_user_data):
        """Test that passwords are properly hashed and never stored in plain text."""
        # Register user
        response = client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 200
        
        # Check database directly
        statement = select(User).where(User.email == sample_user_data["email"])
        db_user = test_session.exec(statement).first()
        
        # Password should be hashed, not plain text
        assert db_user.password_hash != sample_user_data["password"]
        assert db_user.password_hash.startswith("$2b$")  # bcrypt format
        assert len(db_user.password_hash) > 50  # bcrypt hashes are long
        
        # Should be able to verify the password
        assert password_manager.verify_password(sample_user_data["password"], db_user.password_hash)
        
        # Wrong password should not verify
        assert not password_manager.verify_password("WrongPassword", db_user.password_hash)
    
    def test_jwt_token_properties(self, client, test_session: Session, clean_database, sample_user_data):
        """Test JWT token properties and validation."""
        # Register user
        response = client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 200
        
        response_data = response.json()
        access_token = response_data["data"]["access_token"]
        
        # Verify token structure and content
        payload = jwt_manager.verify_token(access_token)
        
        # Should contain required fields
        assert "user_id" in payload
        assert "email" in payload
        assert "exp" in payload  # expiration
        
        # Should contain correct data
        assert payload["email"] == sample_user_data["email"]
        
        # Expiration should be approximately 24 hours from now
        import time
        current_time = time.time()
        token_exp = payload["exp"]
        time_diff = token_exp - current_time
        
        # Should be close to 24 hours (86400 seconds), allow some tolerance
        assert 86300 < time_diff < 86500