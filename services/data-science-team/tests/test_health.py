from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "zyntra-data-science-team"
    assert "version" in data


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "service" in r.json()
