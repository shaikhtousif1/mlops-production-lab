import pandas as pd
import mlflow

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


def main():
    # 1. Load the dataset
    df = pd.read_csv("data/customers.csv")

    print("Dataset:")
    print(df)

    # 2. Separate features and target
    X = df.drop("churned", axis=1)
    y = df["churned"]

    # 3. Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    print(f"\nTraining samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")

    # 4. Create the model
    model = LogisticRegression(max_iter=1000)

    # 5. Start an MLflow experiment run
    with mlflow.start_run():

        # Record model parameters
        mlflow.log_param("model_type", "LogisticRegression")
        mlflow.log_param("max_iter", 1000)
        mlflow.log_param("test_size", 0.2)
        mlflow.log_param("random_state", 42)

        # 6. Train the model
        model.fit(X_train, y_train)

        # 7. Make predictions
        predictions = model.predict(X_test)

        # 8. Evaluate the model
        accuracy = accuracy_score(y_test, predictions)

        print(f"\nModel accuracy: {accuracy:.2f}")

        # Record metric
        mlflow.log_metric("accuracy", accuracy)

        # Store the trained model
        mlflow.sklearn.log_model(model, "model")


if __name__ == "__main__":
    main()
