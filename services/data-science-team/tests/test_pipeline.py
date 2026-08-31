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
    assert pipe["steps"] == ["data_loader", "cleaner", "eda", "visualizer"]

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
        b"Carol,,Riyadh,91\n"
        b"Alice,30,Riyadh,88\n"  # duplicate
        b"Dave,40,,65\n"
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

    # Cleaner should have removed duplicate
    cleaner = data["results"][1]
    assert cleaner["status"] == "ok"
    assert cleaner["final_shape"][0] <= cleaner["original_shape"][0]

    # EDA should have describe / cardinality
    eda = data["results"][2]
    assert eda["status"] == "ok"
    assert "cardinality" in eda

    # Visualizer should produce charts
    viz = data["results"][3]
    assert viz["status"] == "ok"
    assert viz["chart_count"] >= 1


def test_unknown_agent_rejected():
    r = client.post(
        "/v1/pipelines",
        json={"name": "bad", "steps": ["data_loader", "nonexistent"]},
    )
    assert r.status_code == 400
