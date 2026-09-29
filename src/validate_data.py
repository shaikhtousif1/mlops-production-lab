import sys
import pandas as pd


EXPECTED_COLUMNS = [
    "age",
    "tenure_months",
    "monthly_charges",
    "support_tickets",
    "usage_hours",
    "churned",
]

NUMERIC_COLUMNS = [
    "age",
    "tenure_months",
    "monthly_charges",
    "support_tickets",
    "usage_hours",
    "churned",
]


def validate_data(path="data/customers.csv"):
    errors = []

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return [f"Unable to read dataset: {exc}"]

    # Schema
    missing_columns = [
        column for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]

    unexpected_columns = [
        column for column in df.columns
        if column not in EXPECTED_COLUMNS
    ]

    if missing_columns:
        errors.append(f"Missing columns: {missing_columns}")

    if unexpected_columns:
        errors.append(f"Unexpected columns: {unexpected_columns}")

    # Stop here if the schema is incomplete because subsequent
    # column-level checks cannot be performed reliably.
    if missing_columns:
        return errors

    # Null checks
    null_counts = df[EXPECTED_COLUMNS].isnull().sum()

    for column, count in null_counts.items():
        if count > 0:
            errors.append(
                f"Column '{column}' contains {count} null values"
            )

    # Numeric type checks
    for column in NUMERIC_COLUMNS:
        if not pd.api.types.is_numeric_dtype(df[column]):
            errors.append(
                f"Column '{column}' must be numeric"
            )

    # Range checks
    if pd.api.types.is_numeric_dtype(df["age"]):
        if ((df["age"] < 0) | (df["age"] > 120)).any():
            errors.append("Column 'age' contains values outside 0-120")

    if pd.api.types.is_numeric_dtype(df["tenure_months"]):
        if (df["tenure_months"] < 0).any():
            errors.append(
                "Column 'tenure_months' contains negative values"
            )

    if pd.api.types.is_numeric_dtype(df["monthly_charges"]):
        if (df["monthly_charges"] < 0).any():
            errors.append(
                "Column 'monthly_charges' contains negative values"
            )

    if pd.api.types.is_numeric_dtype(df["support_tickets"]):
        if (df["support_tickets"] < 0).any():
            errors.append(
                "Column 'support_tickets' contains negative values"
            )

    if pd.api.types.is_numeric_dtype(df["usage_hours"]):
        if (df["usage_hours"] < 0).any():
            errors.append(
                "Column 'usage_hours' contains negative values"
            )

    # Target validation
    if pd.api.types.is_numeric_dtype(df["churned"]):
        invalid_targets = set(df["churned"].dropna().unique()) - {0, 1}

        if invalid_targets:
            errors.append(
                f"Column 'churned' contains invalid values: "
                f"{sorted(invalid_targets)}"
            )

    return errors


def main():
    errors = validate_data()

    if errors:
        print("Data validation FAILED:")
        for error in errors:
            print(f" - {error}")
        sys.exit(1)

    print("Data validation PASSED")


if __name__ == "__main__":
    main()
