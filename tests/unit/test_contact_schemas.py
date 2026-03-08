"""
Unit tests for Contact and Memory request/response schemas.

Validates ContactCreate, MemoryCreate, and response schema field constraints.
"""

import pytest
from datetime import date
from pydantic import ValidationError

from app.schemas import (
    ContactCreate,
    ContactResponse,
    ContactListData,
    MemoryCreate,
    MemoryResponse,
    MemoryListData,
)


class TestContactCreate:
    """Test ContactCreate request schema validation."""

    def test_valid_minimal(self):
        """Name only is valid; relationship_type and birthday optional."""
        data = ContactCreate(name="Alice")
        assert data.name == "Alice"
        assert data.relationship_type is None
        assert data.birthday is None

    def test_valid_full(self):
        """All fields valid."""
        data = ContactCreate(
            name="Bob",
            relationship_type="Friend",
            birthday=date(1990, 5, 15),
        )
        assert data.name == "Bob"
        assert data.relationship_type == "Friend"
        assert data.birthday == date(1990, 5, 15)

    def test_missing_name_raises(self):
        """Missing required name raises ValidationError."""
        with pytest.raises(ValidationError):
            ContactCreate()

    def test_name_max_length(self):
        """Name up to 255 characters is valid."""
        ContactCreate(name="a" * 255)

    def test_name_over_max_length_raises(self):
        """Name over 255 characters raises ValidationError."""
        with pytest.raises(ValidationError):
            ContactCreate(name="a" * 256)

    def test_relationship_type_max_length(self):
        """relationship_type up to 100 characters is valid."""
        ContactCreate(name="Test", relationship_type="a" * 100)

    def test_relationship_type_over_max_raises(self):
        """relationship_type over 100 raises ValidationError."""
        with pytest.raises(ValidationError):
            ContactCreate(name="Test", relationship_type="a" * 101)


class TestMemoryCreate:
    """Test MemoryCreate request schema validation."""

    def test_valid(self):
        """Non-empty content within limit is valid."""
        data = MemoryCreate(content="She loves matcha tea.")
        assert data.content == "She loves matcha tea."

    def test_missing_content_raises(self):
        """Missing content raises ValidationError."""
        with pytest.raises(ValidationError):
            MemoryCreate()

    def test_empty_content_raises(self):
        """Empty string content raises ValidationError (min_length=1)."""
        with pytest.raises(ValidationError):
            MemoryCreate(content="")

    def test_content_max_length(self):
        """Content up to 5000 characters is valid."""
        MemoryCreate(content="x" * 5000)

    def test_content_over_max_raises(self):
        """Content over 5000 raises ValidationError."""
        with pytest.raises(ValidationError):
            MemoryCreate(content="x" * 5001)


class TestContactResponse:
    """Test ContactResponse and ContactListData."""

    def test_contact_response_fields(self):
        """ContactResponse has expected fields."""
        r = ContactResponse(
            id="123",
            name="Alice",
            relationship_type="Friend",
            birthday="1990-05-15",
            created_at="2025-01-01T00:00:00",
            memory_count=3,
        )
        assert r.id == "123"
        assert r.name == "Alice"
        assert r.memory_count == 3

    def test_contact_response_optional_none(self):
        """Optional fields can be None."""
        r = ContactResponse(
            id="123",
            name="Alice",
            relationship_type=None,
            birthday=None,
            created_at="2025-01-01T00:00:00",
            memory_count=None,
        )
        assert r.relationship_type is None
        assert r.birthday is None
        assert r.memory_count is None

    def test_contact_list_data(self):
        """ContactListData holds list of ContactResponse."""
        data = ContactListData(contacts=[])
        assert data.contacts == []


class TestMemoryResponse:
    """Test MemoryResponse and MemoryListData."""

    def test_memory_response_fields(self):
        """MemoryResponse has id, content, created_at."""
        r = MemoryResponse(
            id="456",
            content="A note",
            created_at="2025-01-01T00:00:00",
        )
        assert r.id == "456"
        assert r.content == "A note"
        assert r.created_at == "2025-01-01T00:00:00"

    def test_memory_list_data(self):
        """MemoryListData holds list of MemoryResponse."""
        data = MemoryListData(memories=[])
        assert data.memories == []
