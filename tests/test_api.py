from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)


def test_health_check():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_model_info():
    response = client.get("/model-info")

    assert response.status_code == 200
    result = response.json()

    assert result["model_name"] == "customer-churn-model"
    assert "model_release_version" in result
    assert "mlflow_model_version" in result
    assert "run_id" in result
    assert "dataset_version" in result


def test_prediction():
    response = client.post(
        "/predict",
        params={
            "age": 45,
            "tenure_months": 24,
            "monthly_charges": 80,
            "support_tickets": 2,
            "usage_hours": 150,
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert "prediction" in result
    assert result["prediction"] in [0, 1]
