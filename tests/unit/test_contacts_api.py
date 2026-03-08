"""
Unit tests for Contacts API endpoints.

Uses mocked get_session and get_current_user to test create, list, get, delete
and 404/403 behavior without a real database.
"""

import uuid
from contextlib import contextmanager
from datetime import date, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_session
from app.core.security import get_current_user
from app.models import User, Contact


@pytest.fixture
def mock_user():
    """Authenticated user for protected route tests."""
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed",
        full_name="Test User",
        created_at=datetime.now(),
    )


@pytest.fixture
def auth_headers(mock_user):
    """Not used when get_current_user is overridden; kept for consistency."""
    return {}


@contextmanager
def _override_deps(client, mock_db, current_user):
    """Override get_session and get_current_user."""
    def get_session_override():
        yield mock_db

    async def get_current_user_override():
        return current_user

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override
    yield
    app.dependency_overrides.pop(get_session, None)
    app.dependency_overrides.pop(get_current_user, None)


class TestCreateContact:
    """Test POST /api/v1/contacts."""

    def test_create_contact_success(self, mock_user):
        """Create contact returns 201 and contact in envelope."""
        mock_db = Mock()
        new_contact = Contact(
            id=uuid.uuid4(),
            name="Alice",
            relationship_type="Friend",
            birthday=date(1995, 10, 20),
            user_id=mock_user.id,
            created_at=datetime.now(),
        )
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda c: setattr(c, "id", new_contact.id))

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.post(
                "/api/v1/contacts",
                json={
                    "name": "Alice",
                    "relationship_type": "Friend",
                    "birthday": "1995-10-20",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == "Alice"
        assert data["data"]["relationship_type"] == "Friend"
        assert data["message"] == "Contact added successfully"

    def test_create_contact_missing_name_returns_400(self, mock_user):
        """Missing name returns 400 with validation envelope."""
        mock_db = Mock()
        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.post("/api/v1/contacts", json={})
        assert response.status_code == 400
        data = response.json()
        assert data.get("status") == "error"
        assert data.get("error_code") == "VALIDATION_ERROR"

    def test_create_contact_empty_name_returns_400(self, mock_user):
        """Empty string name is rejected with 400 and validation envelope."""
        mock_db = Mock()
        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.post("/api/v1/contacts", json={"name": ""})
        assert response.status_code == 400
        data = response.json()
        assert data.get("status") == "error"
        assert data.get("error_code") == "VALIDATION_ERROR"
        assert "details" in data and "field_errors" in data["details"]
        assert "name" in data["details"]["field_errors"]


class TestListContacts:
    """Test GET /api/v1/contacts."""

    def test_list_contacts_success(self, mock_user):
        """List returns 200 and contacts array with memory_count."""
        contact = Contact(
            id=uuid.uuid4(),
            name="Bob",
            relationship_type="Colleague",
            birthday=None,
            user_id=mock_user.id,
            created_at=datetime.now(),
        )
        mock_db = Mock()
        first_exec = Mock()
        first_exec.all.return_value = [contact]
        count_exec = Mock()
        count_exec.one.return_value = 0
        mock_db.exec.side_effect = [first_exec, count_exec]

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.get("/api/v1/contacts")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "contacts" in data["data"]
        assert len(data["data"]["contacts"]) == 1
        assert data["data"]["contacts"][0]["name"] == "Bob"
        assert data["data"]["contacts"][0]["memory_count"] == 0


class TestGetContact:
    """Test GET /api/v1/contacts/{contact_id}."""

    def test_get_contact_success(self, mock_user):
        """Get existing owned contact returns 200."""
        contact_id = uuid.uuid4()
        contact = Contact(
            id=contact_id,
            name="Carol",
            relationship_type="Family",
            birthday=date(2000, 1, 1),
            user_id=mock_user.id,
            created_at=datetime.now(),
        )
        mock_db = Mock()
        mock_db.get.return_value = contact

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.get(f"/api/v1/contacts/{contact_id}")

        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Carol"

    def test_get_contact_not_found_returns_404_with_envelope(self, mock_user):
        """Get non-existent contact returns 404 with standardized envelope."""
        mock_db = Mock()
        mock_db.get.return_value = None

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.get(f"/api/v1/contacts/{uuid.uuid4()}")

        assert response.status_code == 404
        data = response.json()
        assert data.get("status") == "error"
        assert data.get("error_code") == "NOT_FOUND"
        assert "not found" in data.get("message", "").lower()

    def test_get_contact_forbidden_returns_403_with_envelope(self, mock_user):
        """Get contact owned by another user returns 403 with standardized envelope."""
        other_user_id = uuid.uuid4()
        contact = Contact(
            id=uuid.uuid4(),
            name="Other",
            relationship_type="Friend",
            birthday=None,
            user_id=other_user_id,
            created_at=datetime.now(),
        )
        mock_db = Mock()
        mock_db.get.return_value = contact

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.get(f"/api/v1/contacts/{contact.id}")

        assert response.status_code == 403
        data = response.json()
        assert data.get("status") == "error"
        assert data.get("error_code") == "FORBIDDEN"
        assert "access" in data.get("message", "").lower()


class TestDeleteContact:
    """Test DELETE /api/v1/contacts/{contact_id}."""

    def test_delete_contact_success(self, mock_user):
        """Delete owned contact returns 200."""
        contact_id = uuid.uuid4()
        contact = Contact(
            id=contact_id,
            name="ToDelete",
            relationship_type="Friend",
            birthday=None,
            user_id=mock_user.id,
            created_at=datetime.now(),
        )
        mock_db = Mock()
        mock_db.get.return_value = contact

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.delete(f"/api/v1/contacts/{contact_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["data"] is None
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_delete_contact_not_found_returns_404_with_envelope(self, mock_user):
        """Delete non-existent contact returns 404 with standardized envelope."""
        mock_db = Mock()
        mock_db.get.return_value = None

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.delete(f"/api/v1/contacts/{uuid.uuid4()}")

        assert response.status_code == 404
        data = response.json()
        assert data.get("status") == "error"
        assert data.get("error_code") == "NOT_FOUND"

    def test_delete_contact_forbidden_returns_403_with_envelope(self, mock_user):
        """Delete contact owned by another user returns 403 with standardized envelope."""
        contact = Contact(
            id=uuid.uuid4(),
            name="Other",
            relationship_type="Friend",
            birthday=None,
            user_id=uuid.uuid4(),
            created_at=datetime.now(),
        )
        mock_db = Mock()
        mock_db.get.return_value = contact

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.delete(f"/api/v1/contacts/{contact.id}")

        assert response.status_code == 403
        data = response.json()
        assert data.get("status") == "error"
        assert data.get("error_code") == "FORBIDDEN"


class TestContactsRequireAuth:
    """Contacts endpoints require authentication."""

    def test_list_contacts_without_auth_returns_401(self):
        """GET /contacts without token returns 401."""
        client = TestClient(app)
        if get_session in app.dependency_overrides:
            del app.dependency_overrides[get_session]
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        response = client.get("/api/v1/contacts")
        assert response.status_code == 401

    def test_delete_contact_without_auth_returns_401(self):
        """DELETE /contacts/{id} without token returns 401 (not 307 redirect)."""
        client = TestClient(app)
        if get_session in app.dependency_overrides:
            del app.dependency_overrides[get_session]
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        response = client.delete(f"/api/v1/contacts/{uuid.uuid4()}")
        assert response.status_code == 401
