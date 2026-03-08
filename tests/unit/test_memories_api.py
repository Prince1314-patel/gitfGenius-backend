"""
Unit tests for Memories API endpoints.

Uses mocked get_session and get_current_user to test create, list
and 404/403 behavior without a real database.
"""

import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_session
from app.core.security import get_current_user
from app.models import User, Contact, Memory


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


class TestCreateMemory:
    """Test POST /api/v1/contacts/{contact_id}/memories."""

    def test_create_memory_success(self, mock_user):
        """Create memory returns 201 and memory in envelope."""
        contact_id = uuid.uuid4()
        contact = Contact(
            id=contact_id,
            name="Alice",
            relationship_type="Friend",
            birthday=None,
            user_id=mock_user.id,
            created_at=datetime.now(),
        )
        new_memory = Memory(
            id=uuid.uuid4(),
            content="Loves matcha tea",
            contact_id=contact_id,
            created_at=datetime.now(),
        )
        mock_db = Mock()
        mock_db.get.return_value = contact
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda m: setattr(m, "id", new_memory.id))

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.post(
                f"/api/v1/contacts/{contact_id}/memories",
                json={"content": "Loves matcha tea"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["content"] == "Loves matcha tea"
        assert data["message"] == "Memory saved"

    def test_create_memory_contact_not_found_returns_404(self, mock_user):
        """Create memory for non-existent contact returns 404."""
        mock_db = Mock()
        mock_db.get.return_value = None

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.post(
                f"/api/v1/contacts/{uuid.uuid4()}/memories",
                json={"content": "A note"},
            )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_memory_forbidden_returns_403(self, mock_user):
        """Create memory for contact owned by another user returns 403."""
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
            response = client.post(
                f"/api/v1/contacts/{contact.id}/memories",
                json={"content": "A note"},
            )

        assert response.status_code == 403
        assert "access" in response.json()["detail"].lower()

    def test_create_memory_empty_content_returns_422(self, mock_user):
        """Empty content returns 422."""
        contact_id = uuid.uuid4()
        contact = Contact(
            id=contact_id,
            name="Alice",
            relationship_type="Friend",
            birthday=None,
            user_id=mock_user.id,
            created_at=datetime.now(),
        )
        mock_db = Mock()
        mock_db.get.return_value = contact

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.post(
                f"/api/v1/contacts/{contact_id}/memories",
                json={"content": ""},
            )

        assert response.status_code == 422


class TestListMemories:
    """Test GET /api/v1/contacts/{contact_id}/memories."""

    def test_list_memories_success(self, mock_user):
        """List returns 200 and memories array."""
        contact_id = uuid.uuid4()
        contact = Contact(
            id=contact_id,
            name="Alice",
            relationship_type="Friend",
            birthday=None,
            user_id=mock_user.id,
            created_at=datetime.now(),
        )
        memory = Memory(
            id=uuid.uuid4(),
            content="First note",
            contact_id=contact_id,
            created_at=datetime.now(),
        )
        mock_db = Mock()
        mock_db.get.return_value = contact
        exec_return = Mock()
        exec_return.all.return_value = [memory]
        mock_db.exec.return_value = exec_return

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.get(f"/api/v1/contacts/{contact_id}/memories")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "memories" in data["data"]
        assert len(data["data"]["memories"]) == 1
        assert data["data"]["memories"][0]["content"] == "First note"

    def test_list_memories_contact_not_found_returns_404(self, mock_user):
        """List memories for non-existent contact returns 404."""
        mock_db = Mock()
        mock_db.get.return_value = None

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.get(f"/api/v1/contacts/{uuid.uuid4()}/memories")

        assert response.status_code == 404

    def test_list_memories_forbidden_returns_403(self, mock_user):
        """List memories for contact owned by another user returns 403."""
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
            response = client.get(f"/api/v1/contacts/{contact.id}/memories")

        assert response.status_code == 403


class TestMemoriesRequireAuth:
    """Memories endpoints require authentication."""

    def test_list_memories_without_auth_returns_401(self):
        """GET .../memories without token returns 401."""
        client = TestClient(app)
        if get_session in app.dependency_overrides:
            del app.dependency_overrides[get_session]
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        response = client.get(f"/api/v1/contacts/{uuid.uuid4()}/memories")
        assert response.status_code == 401
