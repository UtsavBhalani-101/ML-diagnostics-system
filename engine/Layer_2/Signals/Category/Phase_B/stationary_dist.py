import numpy as np
import pandas as pd

def population_stability_index(expected: pd.Series, actual: pd.Series, eps=1e-6):
    """
    Computes PSI between two categorical distributions.
    expected: train distribution (value_counts normalized)
    actual: test distribution (value_counts normalized)
    """

    # Align categories
    all_cats = expected.index.union(actual.index)
    expected = expected.reindex(all_cats, fill_value=0)
    actual = actual.reindex(all_cats, fill_value=0)

    expected = expected.values + eps
    actual = actual.values + eps

    psi = np.sum((actual - expected) * np.log(actual / expected))
    return float(psi)


def phaseb_categorical_stationarity(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    col_name: str,
    psi_warning: float = 0.1,
    psi_violation: float = 0.25
):
    """
    Phase B Assumption:
    Category frequency distribution is stationary across splits.
    """

    if col_name not in train_df or col_name not in test_df:
        return None

    train_col = train_df[col_name].dropna().astype(str)
    test_col = test_df[col_name].dropna().astype(str)

    if train_col.empty or test_col.empty:
        return None

    train_dist = train_col.value_counts(normalize=True)
    test_dist = test_col.value_counts(normalize=True)

    psi = population_stability_index(train_dist, test_dist)

    evidence = {
        "psi": round(psi, 4),
        "train_unique": train_col.nunique(),
        "test_unique": test_col.nunique()
    }

    if psi >= psi_violation:
        return {
            "assumption": "categorical_distribution_stationarity",
            "type": "violated",
            "columns": [col_name],
            "evidence": evidence,
            "risk": (
                "Category distribution has shifted significantly between splits. "
                "Model behavior may be unstable or misleading."
            ),
            "severity": "high"
        }

    if psi >= psi_warning:
        return {
            "assumption": "categorical_distribution_stationarity",
            "type": "warning",
            "columns": [col_name],
            "evidence": evidence,
            "risk": (
                "Moderate distribution drift detected across splits. "
                "Monitor performance and consider time-aware validation."
            ),
            "severity": "medium"
        }

    return None
