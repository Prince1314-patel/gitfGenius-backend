"""
Unit tests for PasswordManager class.

Tests specific password hashing and verification scenarios to ensure
the bcrypt implementation works correctly with proper error handling.
"""

import pytest
from app.core.security import password_manager


class TestPasswordManager:
    """Test cases for PasswordManager functionality."""
    
    def test_hash_password_creates_valid_hash(self):
        """Test that hash_password creates a valid bcrypt hash."""
        password = "test_password_123"
        hashed = password_manager.hash_password(password)
        
        # Bcrypt hashes start with $2b$ and are 60 characters long
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60
        assert hashed != password  # Hash should not equal plain text
    
    def test_hash_password_generates_unique_salts(self):
        """Test that each password hash gets a unique salt."""
        password = "same_password"
        hash1 = password_manager.hash_password(password)
        hash2 = password_manager.hash_password(password)
        
        # Same password should produce different hashes due to unique salts
        assert hash1 != hash2
        assert hash1.startswith("$2b$")
        assert hash2.startswith("$2b$")
    
    def test_verify_password_with_correct_password(self):
        """Test password verification with correct password."""
        password = "correct_password_456"
        hashed = password_manager.hash_password(password)
        
        # Correct password should verify successfully
        assert password_manager.verify_password(password, hashed) is True
    
    def test_verify_password_with_incorrect_password(self):
        """Test password verification with incorrect password."""
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        hashed = password_manager.hash_password(correct_password)
        
        # Wrong password should fail verification
        assert password_manager.verify_password(wrong_password, hashed) is False
    
    def test_hash_password_with_empty_string(self):
        """Test that empty password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            password_manager.hash_password("")
    
    def test_hash_password_with_none(self):
        """Test that None password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            password_manager.hash_password(None)
    
    def test_verify_password_with_empty_password(self):
        """Test that empty password in verification raises ValueError."""
        hashed = password_manager.hash_password("test")
        
        with pytest.raises(ValueError, match="Password and hash cannot be empty"):
            password_manager.verify_password("", hashed)
    
    def test_verify_password_with_empty_hash(self):
        """Test that empty hash in verification raises ValueError."""
        with pytest.raises(ValueError, match="Password and hash cannot be empty"):
            password_manager.verify_password("test", "")
    
    def test_verify_password_with_none_values(self):
        """Test that None values in verification raise ValueError."""
        with pytest.raises(ValueError, match="Password and hash cannot be empty"):
            password_manager.verify_password(None, "hash")
            
        with pytest.raises(ValueError, match="Password and hash cannot be empty"):
            password_manager.verify_password("password", None)
    
    def test_password_round_trip(self):
        """Test complete password hash and verify cycle."""
        original_password = "my_secure_password_789"
        
        # Hash the password
        hashed = password_manager.hash_password(original_password)
        
        # Verify it works
        assert password_manager.verify_password(original_password, hashed) is True
        
        # Verify wrong password fails
        assert password_manager.verify_password("wrong_password", hashed) is False
    
    def test_special_characters_in_password(self):
        """Test password with special characters."""
        password = "p@ssw0rd!#$%^&*()"
        hashed = password_manager.hash_password(password)
        
        assert password_manager.verify_password(password, hashed) is True
        assert hashed != password
    
    def test_unicode_characters_in_password(self):
        """Test password with unicode characters."""
        password = "пароль123密码"
        hashed = password_manager.hash_password(password)
        
        assert password_manager.verify_password(password, hashed) is True
        assert hashed != password
    
    def test_long_password_truncation(self):
        """Test very long password (bcrypt has 72 byte limit)."""
        # Create a password longer than 72 bytes when encoded as UTF-8
        password = "a" * 100  # 100 character password
        hashed = password_manager.hash_password(password)
        
        # Should still work (bcrypt will truncate internally)
        assert password_manager.verify_password(password, hashed) is True
        assert len(hashed) == 60  # Bcrypt hash is always 60 chars regardless of input length
    
    def test_password_with_newlines_and_spaces(self):
        """Test password with whitespace characters."""
        password = "  password with spaces  \n\t"
        hashed = password_manager.hash_password(password)
        
        # Should preserve exact whitespace
        assert password_manager.verify_password(password, hashed) is True
        assert password_manager.verify_password("password with spaces", hashed) is False