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


def test_list_agents():
    r = client.get("/v1/agents")
    assert r.status_code == 200
    agents = r.json()
    assert isinstance(agents, list)
    assert any(a["name"] == "data_loader" for a in agents)
