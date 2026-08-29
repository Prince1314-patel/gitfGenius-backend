from fastapi.testclient import TestClient

from app.main import app, parse_ai_ideas


def test_parse_ai_ideas_accepts_common_model_output():
    assert parse_ai_ideas('```json\n["Coffee kit", "Book"]\n```') == ["Coffee kit", "Book"]
    assert parse_ai_ideas('Here you go: ["Cafe card", "Notebook"]') == ["Cafe card", "Notebook"]


def test_contact_memory_and_recommendation_flow():
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/contacts",
            json={"name": "QA Friend", "relationship_type": "Friend", "birthday": "1995-05-10"},
        )
        assert created.status_code == 201
        contact = created.json()["data"]

        listed = client.get("/api/v1/contacts")
        assert listed.status_code == 200
        assert any(item["id"] == contact["id"] for item in listed.json()["data"]["contacts"])

        updated = client.put(
            f"/api/v1/contacts/{contact['id']}",
            json={"name": "QA Best Friend", "relationship_type": "Friend", "birthday": "1995-05-10"},
        )
        assert updated.status_code == 200
        assert updated.json()["data"]["name"] == "QA Best Friend"

        memory = client.post(
            f"/api/v1/contacts/{contact['id']}/memories",
            json={"content": "Loves coffee and books"},
        )
        assert memory.status_code == 201
        memory_id = memory.json()["data"]["id"]

        memories = client.get(f"/api/v1/contacts/{contact['id']}/memories")
        assert memories.status_code == 200
        assert memories.json()["data"]["memories"][0]["content"] == "Loves coffee and books"

        recs = client.get(f"/api/v1/contacts/{contact['id']}/recommendations")
        assert recs.status_code == 200
        assert recs.json()["data"]["recommendations"]

        removed_memory = client.delete(f"/api/v1/contacts/{contact['id']}/memories/{memory_id}")
        assert removed_memory.status_code == 200
        assert client.get(f"/api/v1/contacts/{contact['id']}/memories").json()["data"]["memories"] == []

        deleted = client.delete(f"/api/v1/contacts/{contact['id']}")
        assert deleted.status_code == 200


def test_dev_db_snapshot_hides_password_hashes():
    with TestClient(app) as client:
        snapshot = client.get("/api/v1/dev/db-snapshot")
        assert snapshot.status_code == 200
        data = snapshot.json()["data"]
        assert set(data["counts"]) == {"users", "contacts", "memories"}
        assert data["ai"] == {"provider": "local_fallback", "model": "local rules", "configured": False}
        assert "password_hash" not in str(data)
