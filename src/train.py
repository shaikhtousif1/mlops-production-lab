import argparse
import os
import pandas as pd
import mlflow
import joblib

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--c", type=float, default=0.5)

    args = parser.parse_args()

    C = args.c

    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "customer-churn-ci")
    mlflow.set_experiment(experiment_name)
    print(f"MLflow experiment: {experiment_name}")

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
    model = LogisticRegression(C=C, max_iter=1000)
    cv_scores = cross_val_score(
        model,
        X,
        y,
        cv=5,
        scoring="accuracy",
    )
    mean_accuracy = cv_scores.mean()
    std_accuracy = cv_scores.std()

    cv_f1_scores = cross_val_score(
        model,
        X,
        y,
        cv=5,
        scoring="f1",
    )

    mean_f1 = cv_f1_scores.mean()
    std_f1 = cv_f1_scores.std()

    print(f"Cross-validation accuracy: {mean_accuracy:.2f}")
    print(f"Cross-validation std: {std_accuracy:.2f}")
    print(f"Cross-validation F1: {mean_f1:.2f}")
    print(f"Cross-validation F1 std: {std_f1:.2f}")

    # 5. Start an MLflow experiment run
    with mlflow.start_run():

        # Record model parameters
        mlflow.log_param("model_type", "LogisticRegression")
        mlflow.log_param("C", C)
        mlflow.log_param("max_iter", 1000)
        mlflow.log_param("test_size", 0.2)
        mlflow.log_param("random_state", 42)
        mlflow.log_metric("mean_accuracy", mean_accuracy)
        mlflow.log_metric("std_accuracy", std_accuracy)

        # Dataset version for lineage
        mlflow.set_tag("dataset_version", "v2")

        mlflow.log_metric("mean_f1", mean_f1)
        mlflow.log_metric("std_f1", std_f1)

        # 6. Train the model
        model.fit(X_train, y_train)
        joblib.dump(model, "model.pkl")
        print("y_test shape:", y_test.shape)

        # 7. Make predictions
        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)[:, 1]

        print("predictions shape:", predictions.shape)
        print("probabilities shape:", probabilities.shape)

        precision = precision_score(y_test, predictions)
        recall = recall_score(y_test, predictions)
        f1 = f1_score(y_test, predictions)
        cm = confusion_matrix(y_test, predictions)
        roc_auc = roc_auc_score(y_test, probabilities)

        print(f"\nprecision: {precision:.2f}")
        print(f"\nrecall: {recall:.2f}")
        print(f"\nf1: {f1:.2f}")
        print(f"\ncm: {cm}")
        print(f"\nroc_auc: {roc_auc:.2f}")

        # 8. Evaluate the model
        accuracy = accuracy_score(y_test, predictions)

        print(f"\nModel accuracy: {accuracy:.2f}")

        # Record metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1", f1)
        mlflow.log_metric("roc_auc", roc_auc)

        # Store the trained model
        mlflow.sklearn.log_model(
            model,
            name="model"
        )


if __name__ == "__main__":
    main()
