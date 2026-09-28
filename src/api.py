import pandas as pd
import joblib
from fastapi import FastAPI

app = FastAPI(title="Customer Churn Prediction API")

model = joblib.load("model.pkl")


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/predict")
def predict(
    age: int,
    tenure_months: int,
    monthly_charges: float,
    support_tickets: int,
    usage_hours: float,
):
    customer = pd.DataFrame([
        {
            "age": age,
            "tenure_months": tenure_months,
            "monthly_charges": monthly_charges,
            "support_tickets": support_tickets,
            "usage_hours": usage_hours,
        }
    ])

    prediction = model.predict(customer)

    return {
        "prediction": int(prediction[0])
    }