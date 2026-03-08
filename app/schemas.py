"""
Request and response schemas for the GiftGenius API.

This module defines Pydantic models for API request validation and response formatting.
Authentication schemas will be implemented in task 2.1.
"""

from datetime import date
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

    Aligns with frontend contract: only email and password are required.
    full_name is optional (defaults to empty string) for frontend compatibility.
    """
    email: EmailStr = Field(..., description="Valid email address for user account")
    password: str = Field(
        ...,
        min_length=8,
        description="Password must be at least 8 characters long",
    )
    full_name: Optional[str] = Field(
        default="",
        max_length=100,
        description="User's full name (optional); frontend may omit.",
    )


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
    id: str  # UUID as string
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


# Contact schemas

class ContactCreate(BaseModel):
    """Request schema for creating a contact."""
    name: str = Field(..., min_length=1, max_length=255, description="Contact name")
    relationship_type: Optional[str] = Field(default=None, max_length=100)
    birthday: Optional[date] = Field(default=None)


class ContactResponse(BaseModel):
    """Response schema for a single contact."""
    id: str
    name: str
    relationship_type: Optional[str] = None
    birthday: Optional[str] = None
    created_at: str
    memory_count: Optional[int] = None


class ContactListData(BaseModel):
    """Data wrapper for list of contacts."""
    contacts: list[ContactResponse]


# Memory schemas

class MemoryCreate(BaseModel):
    """Request schema for creating a memory."""
    content: str = Field(..., min_length=1, max_length=5000)


class MemoryResponse(BaseModel):
    """Response schema for a single memory."""
    id: str
    content: str
    created_at: str


class MemoryListData(BaseModel):
    """Data wrapper for list of memories."""
    memories: list[MemoryResponse]


# Calendar schemas

class BirthdayEventResponse(BaseModel):
    """Response schema for a single birthday event in the calendar view."""
    contact_id: str = Field(..., description="UUID of the contact")
    contact_name: str = Field(..., description="Display name of the contact")
    birthday: str = Field(..., description="Original birthday in ISO date format (YYYY-MM-DD)")
    next_occurrence: str = Field(..., description="Next occurrence of birthday (this year or next)")
    days_until: int = Field(..., description="Days until next_occurrence (0 = today)")


class CalendarData(BaseModel):
    """Data wrapper for calendar birthday events."""
    events: list[BirthdayEventResponse]