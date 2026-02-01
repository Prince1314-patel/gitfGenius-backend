"""
Request and response schemas for the GiftGenius API.

This module defines Pydantic models for API request validation and response formatting.
Authentication schemas will be implemented in task 2.1.
"""

from typing import Optional, Generic, TypeVar, Literal
from pydantic import BaseModel, EmailStr, Field

# Generic type for standardized responses
T = TypeVar('T')


class StandardResponse(BaseModel, Generic[T]):
    """
    Standardized API response format for consistent client integration.
    
    This envelope format ensures all API responses follow the same structure:
    - status: "success" or "error" 
    - data: The actual response payload (null for errors)
    - message: Human-readable description
    """
    status: Literal["success", "error"]
    data: Optional[T] = None
    message: str


# Authentication schemas will be added in task 2.1
# - UserRegistrationRequest
# - UserLoginRequest  
# - AuthenticationResponse


# Authentication Schemas

class UserRegistrationRequest(BaseModel):
    """
    Request schema for user registration.
    
    Validates email format and enforces password security requirements:
    - Minimum 8 characters
    - At least one uppercase letter, lowercase letter, digit, and special character
    """
    email: EmailStr = Field(..., description="Valid email address for user account")
    password: str = Field(
        ..., 
        min_length=8,
        description="Password must be at least 8 characters long"
    )
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")


class UserLoginRequest(BaseModel):
    """
    Request schema for user authentication.
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserInfo(BaseModel):
    """
    User information included in authentication responses.
    """
    id: int
    email: str
    full_name: str
    created_at: str


class AuthenticationResponse(BaseModel):
    """
    Response schema for successful authentication.
    
    Contains user information and JWT access token for API authorization.
    """
    user: UserInfo
    access_token: str = Field(..., description="JWT access token for API authorization")
    token_type: str = Field(default="bearer", description="Token type for Authorization header")