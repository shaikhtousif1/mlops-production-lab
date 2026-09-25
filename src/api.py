import os

import mlflow
import pandas as pd
from fastapi import FastAPI

app = FastAPI(title="Customer Churn Prediction API")

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://mlflow:5000",
)

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

MODEL_URI = os.getenv(
    "MODEL_URI",
    "models:/customer-churn-model/1",
)

model = mlflow.pyfunc.load_model(MODEL_URI)


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