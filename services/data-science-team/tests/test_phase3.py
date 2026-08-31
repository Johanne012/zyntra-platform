import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_all_phase3_agents():
    r = client.get("/v1/agents")
    assert r.status_code == 200
    names = {a["name"] for a in r.json()}
    assert {
        "data_loader",
        "cleaner",
        "eda",
        "visualizer",
        "feature_engineer",
        "modeler",
        "interpretability",
    }.issubset(names)


def test_full_phase3_pipeline_classification():
    # Synthetic classification-friendly CSV
    rows = ["age,income,city,churn"]
    for i in range(40):
        age = 20 + (i % 30)
        income = 3000 + i * 50
        city = ["Riyadh", "Jeddah", "Dammam"][i % 3]
        churn = 1 if income < 4500 else 0
        rows.append(f"{age},{income},{city},{churn}")
    csv_content = ("\n".join(rows)).encode()

    r = client.post(
        "/v1/pipelines",
        json={
            "name": "phase3-clf",
            "steps": [
                "data_loader",
                "cleaner",
                "feature_engineer",
                "modeler",
                "interpretability",
            ],
        },
    )
    assert r.status_code == 200
    pid = r.json()["id"]

    r2 = client.post(
        f"/v1/pipelines/{pid}/run",
        files={"file": ("churn.csv", io.BytesIO(csv_content), "text/csv")},
        data={"path": ""},  # file takes precedence
    )
    # path empty form may be sent; file is enough
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert data["status"] == "completed", data
    agents = [x["agent"] for x in data["results"]]
    assert agents == [
        "data_loader",
        "cleaner",
        "feature_engineer",
        "modeler",
        "interpretability",
    ]

    modeler = data["results"][3]
    assert modeler["status"] == "ok"
    assert modeler["task"] in {"classification", "regression"}
    assert "metrics" in modeler

    expl = data["results"][4]
    assert expl["status"] == "ok"
    assert len(expl["global_importance"]) >= 1
