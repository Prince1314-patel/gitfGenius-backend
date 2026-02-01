"""
Property-based tests for schema validation.

**Feature: jwt-authentication, Property 8: Request Schema Validation**
**Validates: Requirements 5.5, 7.3**

This module tests that the authentication system correctly validates request schemas
and provides appropriate field-level error information for invalid inputs.
"""

import pytest
from hypothesis import given, strategies as st, assume
from pydantic import ValidationError
from typing import Dict, Any

from app.schemas import UserRegistrationRequest, UserLoginRequest, StandardResponse


class TestSchemaValidationProperties:
    """Property-based tests for request schema validation."""

    @given(
        email=st.one_of(
            # Invalid email formats
            st.text(min_size=1, max_size=50).filter(lambda x: '@' not in x),  # No @ symbol
            st.text(min_size=1, max_size=50).filter(lambda x: x.count('@') > 1),  # Multiple @ symbols
            st.just(""),  # Empty string
            st.just("@"),  # Just @ symbol
            st.just("user@"),  # Missing domain
            st.just("@domain.com"),  # Missing user part
            st.text(min_size=1, max_size=10).map(lambda x: x + "@" + "nodot"),  # No .com
        ),
        password=st.text(min_size=0, max_size=100),
        full_name=st.text(min_size=0, max_size=200)
    )
    def test_user_registration_invalid_email_validation(self, email: str, password: str, full_name: str):
        """
        **Validates: Requirements 5.5, 7.3**
        
        Property: For any invalid email format, the UserRegistrationRequest schema
        should reject the request and provide specific field-level error information.
        """
        # Assume we have an invalid email (not a valid email format)
        assume(not self._is_valid_email_format(email))
        
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationRequest(email=email, password=password, full_name=full_name)
        
        # Verify that validation error contains field-level information
        errors = exc_info.value.errors()
        assert len(errors) > 0, "Should have validation errors for invalid email"
        
        # Check that email field is mentioned in errors
        email_errors = [error for error in errors if 'email' in str(error.get('loc', []))]
        assert len(email_errors) > 0, "Should have specific email field errors"
        
        # Verify error provides descriptive information
        for error in email_errors:
            assert 'msg' in error, "Error should contain descriptive message"
            assert error['msg'] is not None, "Error message should not be None"

    @given(
        email=st.emails(),  # Valid emails
        password=st.text(min_size=0, max_size=7),  # Invalid passwords (too short)
        full_name=st.text(min_size=1, max_size=100)
    )
    def test_user_registration_invalid_password_validation(self, email: str, password: str, full_name: str):
        """
        **Validates: Requirements 5.5, 7.3**
        
        Property: For any password shorter than 8 characters, the UserRegistrationRequest
        schema should reject the request and provide specific field-level error information.
        """
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationRequest(email=email, password=password, full_name=full_name)
        
        # Verify that validation error contains field-level information
        errors = exc_info.value.errors()
        assert len(errors) > 0, "Should have validation errors for short password"
        
        # Check that password field is mentioned in errors
        password_errors = [error for error in errors if 'password' in str(error.get('loc', []))]
        assert len(password_errors) > 0, "Should have specific password field errors"
        
        # Verify error provides descriptive information about password requirements
        for error in password_errors:
            assert 'msg' in error, "Error should contain descriptive message"
            assert error['msg'] is not None, "Error message should not be None"

    @given(
        email=st.emails(),  # Valid emails
        password=st.text(min_size=8, max_size=100),  # Valid passwords
        full_name=st.one_of(
            st.just(""),  # Empty name
            st.text(min_size=101, max_size=200)  # Too long name
        )
    )
    def test_user_registration_invalid_full_name_validation(self, email: str, password: str, full_name: str):
        """
        **Validates: Requirements 5.5, 7.3**
        
        Property: For any invalid full_name (empty or too long), the UserRegistrationRequest
        schema should reject the request and provide specific field-level error information.
        """
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationRequest(email=email, password=password, full_name=full_name)
        
        # Verify that validation error contains field-level information
        errors = exc_info.value.errors()
        assert len(errors) > 0, "Should have validation errors for invalid full_name"
        
        # Check that full_name field is mentioned in errors
        name_errors = [error for error in errors if 'full_name' in str(error.get('loc', []))]
        assert len(name_errors) > 0, "Should have specific full_name field errors"
        
        # Verify error provides descriptive information
        for error in name_errors:
            assert 'msg' in error, "Error should contain descriptive message"
            assert error['msg'] is not None, "Error message should not be None"

    @given(
        email=st.emails(),  # Valid emails
        password=st.text(min_size=8, max_size=100),  # Valid passwords
        full_name=st.text(min_size=1, max_size=100)  # Valid names
    )
    def test_user_registration_valid_data_acceptance(self, email: str, password: str, full_name: str):
        """
        **Validates: Requirements 5.5**
        
        Property: For any valid email, password, and full_name combination,
        the UserRegistrationRequest schema should accept the request without errors.
        """
        # This should not raise any validation errors
        try:
            request = UserRegistrationRequest(email=email, password=password, full_name=full_name)
            
            # Verify the data is properly stored (email may be normalized)
            assert request.email is not None and len(request.email) > 0
            assert '@' in request.email  # Should still be a valid email format
            assert request.password == password
            assert request.full_name == full_name
            
        except ValidationError:
            pytest.fail(f"Valid data should not raise ValidationError: email={email}, password_len={len(password)}, name_len={len(full_name)}")

    @given(
        email=st.one_of(
            st.text(min_size=1, max_size=50).filter(lambda x: '@' not in x),  # Invalid email
            st.just(""),  # Empty email
        ),
        password=st.text(min_size=0, max_size=100)
    )
    def test_user_login_invalid_email_validation(self, email: str, password: str):
        """
        **Validates: Requirements 5.5, 7.3**
        
        Property: For any invalid email format in login request, the UserLoginRequest
        schema should reject the request and provide specific field-level error information.
        """
        # Assume we have an invalid email
        assume(not self._is_valid_email_format(email))
        
        with pytest.raises(ValidationError) as exc_info:
            UserLoginRequest(email=email, password=password)
        
        # Verify that validation error contains field-level information
        errors = exc_info.value.errors()
        assert len(errors) > 0, "Should have validation errors for invalid email"
        
        # Check that email field is mentioned in errors
        email_errors = [error for error in errors if 'email' in str(error.get('loc', []))]
        assert len(email_errors) > 0, "Should have specific email field errors"

    @given(
        email=st.emails(),  # Valid emails
        password=st.text(min_size=0, max_size=100)  # Any password (login doesn't validate length)
    )
    def test_user_login_valid_data_acceptance(self, email: str, password: str):
        """
        **Validates: Requirements 5.5**
        
        Property: For any valid email and any password, the UserLoginRequest
        schema should accept the request without errors.
        """
        # This should not raise any validation errors
        try:
            request = UserLoginRequest(email=email, password=password)
            
            # Verify the data is properly stored (email may be normalized)
            assert request.email is not None and len(request.email) > 0
            assert '@' in request.email  # Should still be a valid email format
            assert request.password == password
            
        except ValidationError:
            pytest.fail(f"Valid login data should not raise ValidationError: email={email}")

    @given(
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans(),
                st.none()
            ),
            min_size=0,
            max_size=10
        )
    )
    def test_schema_validation_with_arbitrary_data(self, data: Dict[str, Any]):
        """
        **Validates: Requirements 5.5, 7.3**
        
        Property: For any arbitrary data dictionary that doesn't match the expected
        schema fields, the schema validation should either accept valid data or
        reject invalid data with appropriate field-level error information.
        """
        # Test UserRegistrationRequest with arbitrary data
        try:
            UserRegistrationRequest(**data)
            # If it succeeds, the data must have contained valid email, password, and full_name
            assert 'email' in data, "Successful validation should have email field"
            assert 'password' in data, "Successful validation should have password field"
            assert 'full_name' in data, "Successful validation should have full_name field"
            
        except ValidationError as e:
            # If it fails, should provide field-level error information
            errors = e.errors()
            assert len(errors) > 0, "Validation errors should be present"
            
            for error in errors:
                assert 'loc' in error, "Error should specify field location"
                assert 'msg' in error, "Error should contain descriptive message"
                assert error['msg'] is not None, "Error message should not be None"
        
        except TypeError:
            # This is acceptable - means the data types don't match at all
            pass

    def _is_valid_email_format(self, email: str) -> bool:
        """
        Helper method to check if an email has a basic valid format.
        This is a simplified check for testing purposes.
        """
        if not email or not isinstance(email, str):
            return False
        
        # Basic email format check
        if email.count('@') != 1:
            return False
        
        local, domain = email.split('@')
        if not local or not domain:
            return False
        
        if '.' not in domain:
            return False
        
        return True

    def _normalize_email(self, email: str) -> str:
        """
        Helper method to normalize email the same way Pydantic EmailStr does.
        Only the domain part is converted to lowercase.
        """
        if '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        return f"{local}@{domain.lower()}"


class TestStandardResponseValidation:
    """Property-based tests for StandardResponse schema validation."""

    @given(
        status=st.sampled_from(["success", "error"]),
        data=st.one_of(st.none(), st.dictionaries(st.text(), st.text())),
        message=st.text(min_size=1, max_size=200)
    )
    def test_standard_response_valid_data(self, status: str, data: Any, message: str):
        """
        **Validates: Requirements 5.5**
        
        Property: For any valid status, data, and message combination,
        the StandardResponse schema should accept the data without errors.
        """
        try:
            response = StandardResponse(status=status, data=data, message=message)
            
            assert response.status == status
            assert response.data == data
            assert response.message == message
            
        except ValidationError:
            pytest.fail(f"Valid StandardResponse data should not raise ValidationError")

    @given(
        status=st.text().filter(lambda x: x not in ["success", "error"]),
        data=st.one_of(st.none(), st.dictionaries(st.text(), st.text())),
        message=st.text(min_size=1, max_size=200)
    )
    def test_standard_response_invalid_status(self, status: str, data: Any, message: str):
        """
        **Validates: Requirements 5.5, 7.3**
        
        Property: For any invalid status value (not "success" or "error"),
        the StandardResponse schema should reject the data with field-level error information.
        """
        with pytest.raises(ValidationError) as exc_info:
            StandardResponse(status=status, data=data, message=message)
        
        # Verify that validation error contains field-level information
        errors = exc_info.value.errors()
        assert len(errors) > 0, "Should have validation errors for invalid status"
        
        # Check that status field is mentioned in errors
        status_errors = [error for error in errors if 'status' in str(error.get('loc', []))]
        assert len(status_errors) > 0, "Should have specific status field errors"