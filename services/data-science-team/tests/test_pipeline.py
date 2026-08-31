import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_list_pipeline():
    r = client.post(
        "/v1/pipelines",
        json={"name": "demo", "steps": ["data_loader", "cleaner", "eda", "visualizer"]},
    )
    assert r.status_code == 200
    pipe = r.json()
    assert pipe["name"] == "demo"
    assert pipe["status"] == "created"
    assert "id" in pipe

    r2 = client.get("/v1/pipelines")
    assert r2.status_code == 200
    assert any(p["id"] == pipe["id"] for p in r2.json())


def test_run_full_pipeline_with_csv():
    r = client.post("/v1/pipelines", json={"name": "full-test"})
    assert r.status_code == 200
    pid = r.json()["id"]

    csv_content = (
        b"name,age,city,score\n"
        b"Alice,30,Riyadh,88\n"
        b"Bob,25,Jeddah,72\n"
        b"Carol,30,Riyadh,91\n"
        b"Dave,,Jeddah,65\n"
        b"Eve,28,Dammam,\n"
    )
    r2 = client.post(
        f"/v1/pipelines/{pid}/run",
        files={"file": ("sample.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["status"] == "completed"
    assert len(data["results"]) == 4

    agents = [r["agent"] for r in data["results"]]
    assert agents == ["data_loader", "cleaner", "eda", "visualizer"]

    # EDA should report numeric columns
    eda = data["results"][2]
    assert "age" in eda["numeric_columns"] or "score" in eda["numeric_columns"]

    # Visualizer should produce charts
    viz = data["results"][3]
    assert viz["chart_count"] >= 1
    assert isinstance(viz["charts"], list)


def test_unknown_agent_rejected():
    r = client.post(
        "/v1/pipelines",
        json={"name": "bad", "steps": ["data_loader", "not_real"]},
    )
    assert r.status_code == 400
