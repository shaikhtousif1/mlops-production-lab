import json

import joblib
import pandas as pd
from fastapi import FastAPI

app = FastAPI(title="Customer Churn Prediction API")

model = joblib.load("model.pkl")

try:
    with open("model_metadata.json", "r", encoding="utf-8") as file:
        model_metadata = json.load(file)
except FileNotFoundError:
    # Local development can run against the checked-in model before the
    # CI packaging step has generated deployment metadata.
    model_metadata = {
        "model_name": "customer-churn-model",
        "model_version": "unknown",
        "run_id": "unknown",
        "dataset_version": "unknown",
    }


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/model-info")
def model_info():
    return model_metadata


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
