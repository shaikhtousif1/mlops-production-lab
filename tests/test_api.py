from fastapi.testclient import TestClient

from src.api import app


client = TestClient(app)


def test_health_check():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict():
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
    assert response.json()["prediction"] in [0, 1]
