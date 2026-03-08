"""
Integration tests for Contacts and Memories API.

Uses test database (SQLite in-memory) to test full flow:
register -> create contact -> add memories -> list -> get -> delete,
and verify ownership (second user cannot access first user's data).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestContactsMemoriesIntegration:
    """Integration tests for contacts and memories flow."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def user_data(self):
        """Sample user for registration."""
        return {
            "email": "contacts_test@example.com",
            "password": "SecurePass123!",
            "full_name": "Contacts Test User",
        }

    def test_full_contact_and_memory_flow(
        self, client: TestClient, test_session, clean_database, user_data
    ):
        """Register -> create contact -> add memories -> list -> get -> delete."""
        # Register and get token
        reg = client.post("/api/v1/auth/register", json=user_data)
        assert reg.status_code == 200
        token = reg.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create contact
        create_body = {
            "name": "Amy Chen",
            "relationship_type": "Friend",
            "birthday": "1995-10-20",
        }
        create_resp = client.post("/api/v1/contacts", json=create_body, headers=headers)
        assert create_resp.status_code == 201
        create_data = create_resp.json()
        assert create_data["status"] == "success"
        assert create_data["data"]["name"] == "Amy Chen"
        contact_id = create_data["data"]["id"]

        # Add memories
        for content in ["Loves matcha tea", "Birthday in October"]:
            mem_resp = client.post(
                f"/api/v1/contacts/{contact_id}/memories",
                json={"content": content},
                headers=headers,
            )
            assert mem_resp.status_code == 201
            assert mem_resp.json()["data"]["content"] == content

        # List contacts (should have memory_count)
        list_resp = client.get("/api/v1/contacts", headers=headers)
        assert list_resp.status_code == 200
        contacts = list_resp.json()["data"]["contacts"]
        assert len(contacts) == 1
        assert contacts[0]["memory_count"] == 2

        # List memories (newest first)
        mem_list = client.get(
            f"/api/v1/contacts/{contact_id}/memories", headers=headers
        )
        assert mem_list.status_code == 200
        memories = mem_list.json()["data"]["memories"]
        assert len(memories) == 2
        assert memories[0]["content"] == "Birthday in October"
        assert memories[1]["content"] == "Loves matcha tea"

        # Get single contact
        get_resp = client.get(f"/api/v1/contacts/{contact_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["name"] == "Amy Chen"

        # Delete contact
        del_resp = client.delete(f"/api/v1/contacts/{contact_id}", headers=headers)
        assert del_resp.status_code == 200
        assert del_resp.json()["message"] == "Contact deleted successfully"

        # Contact and memories should be gone
        list_after = client.get("/api/v1/contacts", headers=headers)
        assert list_after.json()["data"]["contacts"] == []

    def test_ownership_second_user_cannot_access_contact(
        self, client: TestClient, test_session, clean_database, user_data
    ):
        """Second user gets 403 when accessing first user's contact."""
        # User 1: register and create contact
        reg1 = client.post("/api/v1/auth/register", json=user_data)
        assert reg1.status_code == 200
        token1 = reg1.json()["data"]["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        create1 = client.post(
            "/api/v1/contacts",
            json={"name": "User1 Contact", "relationship_type": "Friend"},
            headers=headers1,
        )
        assert create1.status_code == 201
        contact_id = create1.json()["data"]["id"]

        # User 2: register
        user2 = {
            "email": "user2_contacts@example.com",
            "password": "SecurePass123!",
            "full_name": "User Two",
        }
        reg2 = client.post("/api/v1/auth/register", json=user2)
        assert reg2.status_code == 200
        token2 = reg2.json()["data"]["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User 2 cannot get User 1's contact
        get_resp = client.get(f"/api/v1/contacts/{contact_id}", headers=headers2)
        assert get_resp.status_code == 403

        # User 2 cannot add memory to User 1's contact
        mem_resp = client.post(
            f"/api/v1/contacts/{contact_id}/memories",
            json={"content": "Should fail"},
            headers=headers2,
        )
        assert mem_resp.status_code == 403

        # User 2 cannot list memories for User 1's contact
        list_mem = client.get(
            f"/api/v1/contacts/{contact_id}/memories", headers=headers2
        )
        assert list_mem.status_code == 403

        # User 2 cannot delete User 1's contact
        del_resp = client.delete(f"/api/v1/contacts/{contact_id}", headers=headers2)
        assert del_resp.status_code == 403
