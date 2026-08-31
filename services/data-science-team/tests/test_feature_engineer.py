import io
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_feature_engineer_train_fit_and_modeler_reuses_split():
    lines = ["ts,city,amount,user_id,churn"]
    cities = [f"C{i % 25}" for i in range(40)]
    base = datetime(2024, 1, 1)
    for i in range(40):
        ts = (base + timedelta(days=i, hours=i % 24)).isoformat(sep=" ")
        amount = 10 ** (1 + (i % 5))
        lines.append(f"{ts},{cities[i]},{amount},uid_{i},{i % 2}")
    raw = ("\n".join(lines)).encode()

    r = client.post(
        "/v1/pipelines",
        json={
            "name": "fe-leakage",
            "steps": ["data_loader", "cleaner", "feature_engineer", "modeler"],
        },
    )
    assert r.status_code == 200
    pid = r.json()["id"]

    r2 = client.post(
        f"/v1/pipelines/{pid}/run",
        files={"file": ("fe.csv", io.BytesIO(raw), "text/csv")},
        data={"target_column": "churn"},
    )
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert data["status"] == "completed", data

    fe = data["results"][2]
    assert fe["agent"] == "feature_engineer"
    assert fe["train_fit"] is True
    assert any("train only" in a for a in fe["actions"])

    modeler = data["results"][3]
    assert modeler["agent"] == "modeler"
    assert modeler["split_source"] == "feature_engineer"
    assert modeler["n_train"] == fe["n_train"]
    assert modeler["n_test"] == fe["n_test"]
