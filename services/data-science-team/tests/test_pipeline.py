import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_list_pipeline():
    r = client.post("/v1/pipelines", json={"name": "demo", "steps": ["data_loader"]})
    assert r.status_code == 200
    pipe = r.json()
    assert pipe["name"] == "demo"
    assert pipe["status"] == "created"
    assert "id" in pipe

    r2 = client.get("/v1/pipelines")
    assert r2.status_code == 200
    assert any(p["id"] == pipe["id"] for p in r2.json())


def test_run_pipeline_with_csv():
    # Create pipeline
    r = client.post("/v1/pipelines", json={"name": "csv-test", "steps": ["data_loader"]})
    assert r.status_code == 200
    pid = r.json()["id"]

    csv_content = b"name,age\nAlice,30\nBob,25\n"
    r2 = client.post(
        f"/v1/pipelines/{pid}/run",
        files={"file": ("sample.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["status"] == "completed"
    assert len(data["results"]) == 1
    assert data["results"][0]["agent"] == "data_loader"
    assert data["results"][0]["shape"] == [2, 2]
