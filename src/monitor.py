"""Lightweight batch monitoring for feature and prediction drift.

This is intentionally infrastructure-free: it compares a reference dataset
with a current inference batch and produces an actionable monitoring report.
"""

import argparse
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "age",
    "tenure_months",
    "monthly_charges",
    "support_tickets",
    "usage_hours",
]


def psi(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    """Calculate Population Stability Index using reference quantile bins."""
    reference = pd.to_numeric(reference, errors="coerce").dropna()
    current = pd.to_numeric(current, errors="coerce").dropna()
    if reference.empty or current.empty:
        return 0.0

    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0] = -math.inf
    edges[-1] = math.inf

    ref_counts, _ = np.histogram(reference, bins=edges)
    cur_counts, _ = np.histogram(current, bins=edges)
    ref_pct = np.clip(ref_counts / len(reference), 1e-6, None)
    cur_pct = np.clip(cur_counts / len(current), 1e-6, None)

    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def prediction_rate(model, df: pd.DataFrame) -> float:
    predictions = model.predict(df[FEATURE_COLUMNS])
    return float(np.mean(predictions))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--model", default="model.pkl")
    parser.add_argument("--psi-threshold", type=float, default=0.20)
    parser.add_argument("--prediction-rate-threshold", type=float, default=0.10)
    parser.add_argument("--output", default="monitoring_report.json")
    args = parser.parse_args()

    reference = pd.read_csv(args.reference)
    current = pd.read_csv(args.current)

    required = set(FEATURE_COLUMNS)
    for name, df in [("reference", reference), ("current", current)]:
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"{name} dataset missing columns: {sorted(missing)}")

    feature_psi = {
        column: psi(reference[column], current[column])
        for column in FEATURE_COLUMNS
    }

    model = joblib.load(args.model)
    reference_prediction_rate = prediction_rate(model, reference)
    current_prediction_rate = prediction_rate(model, current)
    prediction_rate_delta = abs(current_prediction_rate - reference_prediction_rate)

    report = {
        "reference_rows": len(reference),
        "current_rows": len(current),
        "feature_psi": feature_psi,
        "prediction_rate": {
            "reference": reference_prediction_rate,
            "current": current_prediction_rate,
            "absolute_delta": prediction_rate_delta,
        },
        "thresholds": {
            "psi": args.psi_threshold,
            "prediction_rate_delta": args.prediction_rate_threshold,
        },
        "drift_detected": (
            any(value >= args.psi_threshold for value in feature_psi.values())
            or prediction_rate_delta >= args.prediction_rate_threshold
        ),
    }

    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("\nDRIFT DETECTED: investigate data/model performance before retraining or promotion."
          if report["drift_detected"]
          else "\nNo configured drift threshold was exceeded.")


if __name__ == "__main__":
    main()
