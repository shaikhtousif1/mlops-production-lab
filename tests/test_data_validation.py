import pandas as pd

from src.validate_data import validate_data


EXPECTED_COLUMNS = [
    "age",
    "tenure_months",
    "monthly_charges",
    "support_tickets",
    "usage_hours",
    "churned",
]


def write_dataset(tmp_path, data):
    path = tmp_path / "customers.csv"
    pd.DataFrame(data).to_csv(path, index=False)
    return path


def valid_row():
    return {
        "age": 45,
        "tenure_months": 24,
        "monthly_charges": 80.0,
        "support_tickets": 2,
        "usage_hours": 150.0,
        "churned": 1,
    }


def test_valid_dataset(tmp_path):
    path = write_dataset(tmp_path, [valid_row()])

    errors = validate_data(path)

    assert errors == []


def test_missing_column(tmp_path):
    row = valid_row()
    del row["age"]

    path = write_dataset(tmp_path, [row])

    errors = validate_data(path)

    assert any("Missing columns" in error for error in errors)


def test_unexpected_column(tmp_path):
    row = valid_row()
    row["customer_id"] = 123

    path = write_dataset(tmp_path, [row])

    errors = validate_data(path)

    assert any("Unexpected columns" in error for error in errors)


def test_null_value(tmp_path):
    row = valid_row()
    row["monthly_charges"] = None

    path = write_dataset(tmp_path, [row])

    errors = validate_data(path)

    assert any("null values" in error for error in errors)


def test_invalid_age(tmp_path):
    row = valid_row()
    row["age"] = 150

    path = write_dataset(tmp_path, [row])

    errors = validate_data(path)

    assert any("age" in error.lower() for error in errors)


def test_negative_monthly_charges(tmp_path):
    row = valid_row()
    row["monthly_charges"] = -10

    path = write_dataset(tmp_path, [row])

    errors = validate_data(path)

    assert any("monthly_charges" in error for error in errors)


def test_invalid_churn_target(tmp_path):
    row = valid_row()
    row["churned"] = 2

    path = write_dataset(tmp_path, [row])

    errors = validate_data(path)

    assert any("invalid values" in error for error in errors)
