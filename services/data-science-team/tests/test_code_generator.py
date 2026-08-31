import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_code_generator_in_pipeline():
    rows = ["age,income,churn"]
    for i in range(30):
        rows.append(f"{25 + i % 10},{4000 + i * 30},{i % 2}")
    csv_content = ("\n".join(rows)).encode()

    r = client.post(
        "/v1/pipelines",
        json={
            "name": "codegen",
            "steps": [
                "data_loader",
                "cleaner",
                "feature_engineer",
                "modeler",
                "interpretability",
                "code_generator",
            ],
        },
    )
    assert r.status_code == 200
    pid = r.json()["id"]

    r2 = client.post(
        f"/v1/pipelines/{pid}/run",
        files={"file": ("t.csv", io.BytesIO(csv_content), "text/csv")},
        data={"target_column": "churn"},
    )
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert data["status"] == "completed", data

    gen = data["results"][-1]
    assert gen["agent"] == "code_generator"
    assert gen["status"] == "ok"
    assert "import pandas" in gen["script"]
    assert "RandomForest" in gen["script"]

    r3 = client.get(f"/v1/pipelines/{pid}/script")
    assert r3.status_code == 200
    assert "ZYNTRA" in r3.text
