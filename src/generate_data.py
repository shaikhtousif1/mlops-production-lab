import numpy as np
import pandas as pd


def main():
    np.random.seed(42)

    n_customers = 1000

    age = np.random.randint(18, 70, n_customers)

    tenure_months = np.random.randint(1, 73, n_customers)

    monthly_charges = np.random.normal(75, 20, n_customers)
    monthly_charges = np.clip(monthly_charges, 30, 150)

    support_tickets = np.random.poisson(2.5, n_customers)

    usage_hours = np.random.normal(150, 45, n_customers)
    usage_hours = np.clip(usage_hours, 20, 300)

    # Create a churn risk score.
    # Higher charges, more support tickets and lower usage/tenure
    # increase the probability of churn.
    risk_score = (
        -0.03 * tenure_months
        + 0.025 * monthly_charges
        + 0.30 * support_tickets
        - 0.012 * usage_hours
        + np.random.normal(0, 1.5, n_customers)
    )

    churn_probability = 1 / (1 + np.exp(-risk_score))

    churned = np.random.binomial(1, churn_probability)

    df = pd.DataFrame(
        {
            "age": age,
            "tenure_months": tenure_months,
            "monthly_charges": monthly_charges.round(2),
            "support_tickets": support_tickets,
            "usage_hours": usage_hours.round(2),
            "churned": churned,
        }
    )

    df.to_csv("data/customers.csv", index=False)

    print(f"Generated {len(df)} customer records.")
    print("\nClass distribution:")
    print(df["churned"].value_counts())
    print("\nChurn rate:")
    print(f"{df['churned'].mean():.2%}")


if __name__ == "__main__":
    main()