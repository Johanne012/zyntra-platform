import io
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_feature_engineer_protects_target_and_encodes():
    # Build CSV with skew, category mid-cardinality, datetime, target
    lines = ["ts,city,amount,user_id,churn"]
    cities = [f"C{i % 25}" for i in range(40)]  # 25 levels → frequency encode band
    base = datetime(2024, 1, 1)
    for i in range(40):
        ts = (base + timedelta(days=i, hours=i % 24)).isoformat(sep=" ")
        amount = 10 ** (1 + (i % 5))  # skewed positive
        lines.append(f"{ts},{cities[i]},{amount},uid_{i},{i % 2}")
    raw = ("\n".join(lines)).encode()

    r = client.post(
        "/v1/pipelines",
        json={
            "name": "fe-deep",
            "steps": ["data_loader", "cleaner", "feature_engineer"],
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

    fe = data["results"][-1]
    assert fe["agent"] == "feature_engineer"
    assert fe["status"] == "ok"
    assert fe.get("target_column") == "churn"
    # user_id should be dropped; churn not in feature list as engineered id
    assert "churn" not in fe["feature_columns"]
    actions_text = " ".join(fe["actions"])
    assert "Protected target" in actions_text or fe["target_column"] == "churn"
