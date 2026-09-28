import joblib
import pandas as pd


def test_model_prediction():
    model = joblib.load("model.pkl")

    customer = pd.DataFrame([
        {
            "age": 45,
            "tenure_months": 24,
            "monthly_charges": 80,
            "support_tickets": 2,
            "usage_hours": 150,
        }
    ])

    prediction = model.predict(customer)

    assert prediction[0] in [0, 1]