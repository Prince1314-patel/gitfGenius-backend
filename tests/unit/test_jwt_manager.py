"""
Unit tests for JWTManager class.

Tests specific JWT token creation and validation scenarios to ensure
security requirements are met and tokens work correctly.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from app.core.security import jwt_manager


class TestJWTManager:
    """Test cases for JWTManager functionality."""
    
    def test_create_access_token_with_valid_data(self):
        """Test that create_access_token creates a valid JWT token."""
        user_data = {"user_id": 123, "email": "test@example.com"}
        token = jwt_manager.create_access_token(user_data)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Token should be decodable
        decoded = jwt.decode(token, jwt_manager.secret_key, algorithms=[jwt_manager.algorithm])
        assert decoded["user_id"] == 123
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded
    
    def test_create_access_token_expiration_24_hours(self):
        """Test that JWT token has 24-hour expiration."""
        user_data = {"user_id": 456}
        before_creation = datetime.utcnow()
        token = jwt_manager.create_access_token(user_data)
        after_creation = datetime.utcnow()
        
        # Decode token to check expiration
        decoded = jwt.decode(token, jwt_manager.secret_key, algorithms=[jwt_manager.algorithm])
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        
        # Expiration should be approximately 24 hours from creation (with some tolerance)
        expected_exp_min = before_creation + timedelta(hours=24) - timedelta(seconds=1)
        expected_exp_max = after_creation + timedelta(hours=24) + timedelta(seconds=1)
        
        assert expected_exp_min <= exp_datetime <= expected_exp_max
    
    def test_verify_token_with_valid_token(self):
        """Test JWT token validation with valid tokens."""
        user_data = {"user_id": 789, "email": "valid@example.com"}
        token = jwt_manager.create_access_token(user_data)
        
        # Token should verify successfully
        decoded = jwt_manager.verify_token(token)
        assert decoded["user_id"] == 789
        assert decoded["email"] == "valid@example.com"
        assert "exp" in decoded
    
    def test_verify_token_rejects_expired_token(self):
        """Test JWT token validation rejects expired tokens."""
        # Create a token that expires immediately
        user_data = {"user_id": 999}
        expired_data = user_data.copy()
        expired_data["exp"] = datetime.utcnow() - timedelta(seconds=1)  # Expired 1 second ago
        
        expired_token = jwt.encode(expired_data, jwt_manager.secret_key, algorithm=jwt_manager.algorithm)
        
        # Expired token should raise ExpiredSignatureError
        with pytest.raises(jwt.ExpiredSignatureError, match="Token has expired"):
            jwt_manager.verify_token(expired_token)
    
    def test_verify_token_rejects_malformed_token(self):
        """Test JWT token validation rejects malformed tokens."""
        malformed_tokens = [
            "invalid.token.here",
            "not_a_jwt_token",
            "header.payload",  # Missing signature
            "a.b.c.d.e",  # Too many parts
        ]
        
        for malformed_token in malformed_tokens:
            with pytest.raises(jwt.InvalidTokenError, match="Invalid token"):
                jwt_manager.verify_token(malformed_token)
        
        # Test empty token separately (raises ValueError)
        with pytest.raises(ValueError, match="Token cannot be empty"):
            jwt_manager.verify_token("")
    
    def test_verify_token_rejects_wrong_signature(self):
        """Test JWT token validation rejects tokens with wrong signature."""
        user_data = {"user_id": 111}
        
        # Create token with different secret
        wrong_secret_token = jwt.encode(user_data, "wrong_secret", algorithm=jwt_manager.algorithm)
        
        # Token with wrong signature should raise InvalidTokenError
        with pytest.raises(jwt.InvalidTokenError, match="Invalid token"):
            jwt_manager.verify_token(wrong_secret_token)
    
    def test_token_payload_contains_correct_user_information(self):
        """Test JWT token payload contains correct user information."""
        user_data = {
            "user_id": 555,
            "email": "user@test.com",
            "role": "user",
            "custom_field": "custom_value"
        }
        
        token = jwt_manager.create_access_token(user_data)
        decoded = jwt_manager.verify_token(token)
        
        # All original data should be preserved
        assert decoded["user_id"] == 555
        assert decoded["email"] == "user@test.com"
        assert decoded["role"] == "user"
        assert decoded["custom_field"] == "custom_value"
        
        # Expiration should be added automatically
        assert "exp" in decoded
        assert isinstance(decoded["exp"], int)
    
    def test_jwt_secret_key_security(self):
        """Test JWT secret key security (never exposed in responses)."""
        user_data = {"user_id": 777}
        token = jwt_manager.create_access_token(user_data)
        decoded = jwt_manager.verify_token(token)
        
        # Secret key should never appear in token or decoded payload
        assert jwt_manager.secret_key not in token
        assert jwt_manager.secret_key not in str(decoded)
        
        # Token should not contain secret key in any form
        for key, value in decoded.items():
            assert jwt_manager.secret_key != str(value)
    
    def test_create_access_token_with_empty_data(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="Token data cannot be empty"):
            jwt_manager.create_access_token({})
        
        with pytest.raises(ValueError, match="Token data cannot be empty"):
            jwt_manager.create_access_token(None)
    
    def test_verify_token_with_empty_token(self):
        """Test that empty token raises ValueError."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            jwt_manager.verify_token("")
        
        with pytest.raises(ValueError, match="Token cannot be empty"):
            jwt_manager.verify_token(None)
    
    def test_token_round_trip(self):
        """Test complete token creation and verification cycle."""
        original_data = {
            "user_id": 888,
            "email": "roundtrip@test.com",
            "permissions": ["read", "write"]
        }
        
        # Create token
        token = jwt_manager.create_access_token(original_data)
        
        # Verify token
        decoded_data = jwt_manager.verify_token(token)
        
        # Original data should be preserved (except exp is added)
        for key, value in original_data.items():
            assert decoded_data[key] == value
        
        # Expiration should be present and valid
        assert "exp" in decoded_data
        exp_datetime = datetime.utcfromtimestamp(decoded_data["exp"])
        assert exp_datetime > datetime.utcnow()
    
    def test_different_tokens_for_same_data(self):
        """Test that same data produces different tokens due to timing."""
        user_data = {"user_id": 999}
        
        token1 = jwt_manager.create_access_token(user_data)
        # Small delay to ensure different timestamps
        import time
        time.sleep(1.1)  # Sleep for more than 1 second to ensure different exp timestamps
        token2 = jwt_manager.create_access_token(user_data)
        
        # Tokens should be different due to different exp timestamps
        assert token1 != token2
        
        # But both should verify successfully
        decoded1 = jwt_manager.verify_token(token1)
        decoded2 = jwt_manager.verify_token(token2)
        
        assert decoded1["user_id"] == decoded2["user_id"] == 999
        # Expiration times should be different
        assert decoded1["exp"] != decoded2["exp"]