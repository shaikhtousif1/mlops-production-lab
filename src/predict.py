import mlflow
import pandas as pd


MODEL_URI = "models:/customer-churn-model/1"


def main():

    print(f"Loading model: {MODEL_URI}")

    model = mlflow.pyfunc.load_model(MODEL_URI)

    customer = pd.DataFrame([
        {
            "age": 30,
            "tenure_months": 8,
            "monthly_charges": 105.0,
            "support_tickets": 5,
            "usage_hours": 90.0,
        }
    ])

    prediction = model.predict(customer)

    print("\nCustomer:")
    print(customer)

    print("\nPrediction:")
    print(prediction)


if __name__ == "__main__":
    main()