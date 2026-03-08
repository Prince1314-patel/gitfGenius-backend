"""
Unit tests for Calendar API endpoint.

Uses mocked get_session, get_current_user, and get_today to test
GET /api/v1/calendar without a real database.
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
from app.api.v1.calendar import get_today
from app.models import User, Contact
from tests.database import get_test_session


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


@contextmanager
def _override_deps(client, mock_db, current_user, today=None):
    """Override get_session, get_current_user, and optionally get_today."""
    def get_session_override():
        yield mock_db

    async def get_current_user_override():
        return current_user

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override
    if today is not None:
        def get_today_override():
            return today
        app.dependency_overrides[get_today] = get_today_override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_today, None)
        # Restore test DB session for integration tests (unit tests remove it)
        app.dependency_overrides[get_session] = get_test_session


class TestListCalendarEvents:
    """Test GET /api/v1/calendar."""

    def test_calendar_with_birthdays_returns_200_and_ordered_events(self, mock_user):
        """Calendar returns 200 and events ordered by next_occurrence (today = 2025-06-01)."""
        today = date(2025, 6, 1)
        c1_id = uuid.uuid4()
        c2_id = uuid.uuid4()
        c3_id = uuid.uuid4()
        contacts = [
            Contact(
                id=c1_id,
                name="Alice",
                relationship_type="Friend",
                birthday=date(1990, 8, 15),
                user_id=mock_user.id,
                created_at=datetime.now(),
            ),
            Contact(
                id=c2_id,
                name="Bob",
                relationship_type="Family",
                birthday=date(1985, 6, 10),
                user_id=mock_user.id,
                created_at=datetime.now(),
            ),
            Contact(
                id=c3_id,
                name="Carol",
                relationship_type="Colleague",
                birthday=date(1992, 5, 20),
                user_id=mock_user.id,
                created_at=datetime.now(),
            ),
        ]
        mock_db = Mock()
        exec_mock = Mock()
        exec_mock.all.return_value = contacts
        mock_db.exec.return_value = exec_mock

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user, today=today):
            response = client.get("/api/v1/calendar")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data and "events" in data["data"]
        events = data["data"]["events"]
        assert len(events) == 3
        for e in events:
            assert "contact_id" in e
            assert "contact_name" in e
            assert "birthday" in e
            assert "next_occurrence" in e
            assert "days_until" in e
        next_occurrences = [e["next_occurrence"] for e in events]
        assert next_occurrences == sorted(next_occurrences)
        assert events[0]["contact_name"] == "Bob"
        assert events[0]["next_occurrence"] == "2025-06-10"
        assert events[0]["days_until"] == 9
        assert data["message"] == ""

    def test_calendar_no_birthdays_returns_200_empty_events(self, mock_user):
        """When no contacts have birthdays, calendar returns 200 with empty events."""
        mock_db = Mock()
        exec_mock = Mock()
        exec_mock.all.return_value = []
        mock_db.exec.return_value = exec_mock

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user):
            response = client.get("/api/v1/calendar")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["events"] == []
        assert data["message"] == ""

    def test_calendar_mixed_contacts_only_includes_birthdays(self, mock_user):
        """Contacts without birthday are excluded from events (query filters by birthday not null)."""
        today = date(2025, 1, 15)
        contact_with_bday = Contact(
            id=uuid.uuid4(),
            name="WithBirthday",
            relationship_type="Friend",
            birthday=date(1990, 3, 10),
            user_id=mock_user.id,
            created_at=datetime.now(),
        )
        contact_no_bday = Contact(
            id=uuid.uuid4(),
            name="NoBirthday",
            relationship_type="Friend",
            birthday=None,
            user_id=mock_user.id,
            created_at=datetime.now(),
        )
        mock_db = Mock()
        exec_mock = Mock()
        exec_mock.all.return_value = [contact_with_bday, contact_no_bday]
        mock_db.exec.return_value = exec_mock

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user, today=today):
            response = client.get("/api/v1/calendar")

        assert response.status_code == 200
        events = response.json()["data"]["events"]
        assert len(events) == 1
        assert events[0]["contact_name"] == "WithBirthday"
        assert events[0]["birthday"] == "1990-03-10"
        assert events[0]["next_occurrence"] == "2025-03-10"

    def test_calendar_feb29_non_leap_year_uses_march_first(self, mock_user):
        """Feb 29 birthday in non-leap year has next_occurrence on March 1."""
        today = date(2025, 1, 15)
        contact = Contact(
            id=uuid.uuid4(),
            name="LeapBaby",
            relationship_type="Friend",
            birthday=date(2000, 2, 29),
            user_id=mock_user.id,
            created_at=datetime.now(),
        )
        mock_db = Mock()
        exec_mock = Mock()
        exec_mock.all.return_value = [contact]
        mock_db.exec.return_value = exec_mock

        client = TestClient(app)
        with _override_deps(client, mock_db, mock_user, today=today):
            response = client.get("/api/v1/calendar")

        assert response.status_code == 200
        events = response.json()["data"]["events"]
        assert len(events) == 1
        assert events[0]["birthday"] == "2000-02-29"
        assert events[0]["next_occurrence"] == "2025-03-01"
        assert events[0]["days_until"] == (date(2025, 3, 1) - today).days


class TestCalendarRequiresAuth:
    """Calendar endpoint requires authentication."""

    def test_calendar_without_auth_returns_401(self):
        """GET /calendar without token returns 401."""
        client = TestClient(app)
        try:
            for dep in (get_session, get_current_user, get_today):
                if dep in app.dependency_overrides:
                    app.dependency_overrides.pop(dep, None)
            response = client.get("/api/v1/calendar")
            assert response.status_code == 401
            data = response.json()
            assert data.get("status") == "error"
            assert data.get("error_code") in ("MISSING_TOKEN", "INVALID_TOKEN", None) or "token" in data.get("message", "").lower()
        finally:
            app.dependency_overrides[get_session] = get_test_session
