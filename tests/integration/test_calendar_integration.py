"""
Integration tests for Calendar API.

Uses test database (SQLite in-memory) to test GET /api/v1/calendar
with real auth and contacts: ordering, isolation, and empty state.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestCalendarIntegration:
    """Integration tests for calendar birthday events."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def user_data(self):
        """Sample user for registration."""
        return {
            "email": "calendar_test@example.com",
            "password": "SecurePass123!",
            "full_name": "Calendar Test User",
        }

    def test_calendar_returns_upcoming_birthdays_ordered(
        self, client: TestClient, test_session, clean_database, user_data
    ):
        """Create contacts with birthdays, GET calendar returns events ordered by next_occurrence."""
        reg = client.post("/api/v1/auth/register", json=user_data)
        assert reg.status_code == 200
        token = reg.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        contacts_with_birthdays = [
            {"name": "Alice", "relationship_type": "Friend", "birthday": "1990-08-15"},
            {"name": "Bob", "relationship_type": "Family", "birthday": "1985-03-10"},
            {"name": "Carol", "relationship_type": "Colleague", "birthday": "1992-12-01"},
        ]
        for body in contacts_with_birthdays:
            create = client.post("/api/v1/contacts", json=body, headers=headers)
            assert create.status_code == 201

        cal_resp = client.get("/api/v1/calendar", headers=headers)
        assert cal_resp.status_code == 200
        data = cal_resp.json()
        assert data["status"] == "success"
        assert "events" in data["data"]
        events = data["data"]["events"]
        assert len(events) == 3

        for e in events:
            assert "contact_id" in e
            assert "contact_name" in e
            assert "birthday" in e
            assert "next_occurrence" in e
            assert "days_until" in e
            assert isinstance(e["days_until"], int)
            assert e["days_until"] >= 0

        next_occurrences = [e["next_occurrence"] for e in events]
        assert next_occurrences == sorted(next_occurrences)
        assert data["message"] == ""

    def test_calendar_isolation_second_user_sees_only_own_contacts(
        self, client: TestClient, test_session, clean_database, user_data
    ):
        """First user's calendar does not include second user's contacts with birthdays."""
        reg1 = client.post("/api/v1/auth/register", json=user_data)
        assert reg1.status_code == 200
        token1 = reg1.json()["data"]["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        create1 = client.post(
            "/api/v1/contacts",
            json={"name": "User1 Contact", "relationship_type": "Friend", "birthday": "1990-05-20"},
            headers=headers1,
        )
        assert create1.status_code == 201

        user2 = {
            "email": "calendar_user2@example.com",
            "password": "SecurePass123!",
            "full_name": "User Two",
        }
        reg2 = client.post("/api/v1/auth/register", json=user2)
        assert reg2.status_code == 200
        token2 = reg2.json()["data"]["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        create2 = client.post(
            "/api/v1/contacts",
            json={"name": "User2 Contact", "relationship_type": "Friend", "birthday": "1988-11-11"},
            headers=headers2,
        )
        assert create2.status_code == 201

        cal1 = client.get("/api/v1/calendar", headers=headers1)
        assert cal1.status_code == 200
        events1 = cal1.json()["data"]["events"]
        names1 = {e["contact_name"] for e in events1}
        assert "User1 Contact" in names1
        assert "User2 Contact" not in names1

        cal2 = client.get("/api/v1/calendar", headers=headers2)
        assert cal2.status_code == 200
        events2 = cal2.json()["data"]["events"]
        names2 = {e["contact_name"] for e in events2}
        assert "User2 Contact" in names2
        assert "User1 Contact" not in names2

    def test_calendar_empty_when_no_contacts_or_no_birthdays(
        self, client: TestClient, test_session, clean_database, user_data
    ):
        """New user with no contacts or only contacts without birthday gets empty events."""
        reg = client.post("/api/v1/auth/register", json=user_data)
        assert reg.status_code == 200
        token = reg.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        cal_resp = client.get("/api/v1/calendar", headers=headers)
        assert cal_resp.status_code == 200
        assert cal_resp.json()["data"]["events"] == []

        client.post(
            "/api/v1/contacts",
            json={"name": "No Birthday", "relationship_type": "Friend"},
            headers=headers,
        )
        cal_resp2 = client.get("/api/v1/calendar", headers=headers)
        assert cal_resp2.status_code == 200
        assert cal_resp2.json()["data"]["events"] == []
