import pandas as pd

from src.monitor import psi


def test_psi_is_zero_for_identical_data():
    data = pd.Series([1, 2, 3, 4, 5])
    assert psi(data, data) == 0.0


def test_psi_increases_when_distribution_shifts():
    reference = pd.Series(range(100))
    current = pd.Series(range(100, 200))
    assert psi(reference, current) > 0.20
