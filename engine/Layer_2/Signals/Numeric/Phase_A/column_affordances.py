import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis

def phase_a_column_affordances(col: pd.Series, col_name: str):
    """
    Phase A: Single-column diagnostic.
    Describes shape and structural affordances WITHOUT suggesting actions.
    """

    clean = pd.to_numeric(col, errors="coerce").dropna()

    if len(clean) < 20 or clean.nunique() < 2:
        return {
            "column": col_name,
            "signals": {},
            "tags": [],
            "notes": ["insufficient_variation"]
        }

    signals = {
        "min": float(clean.min()),
        "max": float(clean.max()),
        "mean": float(clean.mean()),
        "std": float(clean.std()),
        "skew": round(float(skew(clean)), 2),
        "kurtosis": round(float(kurtosis(clean)), 2),
        "unique_ratio": round(clean.nunique() / len(clean), 3)
    }

    tags = []
    notes = []

    # Integer-like check
    is_integer_like = np.allclose(clean % 1, 0, atol=1e-5)
    if is_integer_like:
        tags.append("integer_like")

    # Heavy tail (no judgment)
    if signals["min"] > 0 and signals["skew"] > 1.0:
        tags.append("heavy_right_tail")
        notes.append("multiplicative_or_regime_behavior_possible")

    # High dispersion relative to mean
    if signals["std"] > signals["mean"]:
        tags.append("high_dispersion")
        notes.append("aggregate_or_total_quantity_possible")

    # Low dispersion
    if signals["std"] < 0.1 * abs(signals["mean"]):
        tags.append("low_dispersion")
        notes.append("capacity_or_unit_quantity_possible")

    # Kurtosis extremes
    if signals["kurtosis"] > 3 or signals["kurtosis"] < -1:
        tags.append("non_gaussian_shape")

    # Monotonicity hint (diagnostic only)
    if clean.is_monotonic_increasing or clean.is_monotonic_decreasing:
        tags.append("monotonic_sequence")
        notes.append("ordering_or_difference_candidate")

    return {
        "column": col_name,
        "signals": signals,
        "tags": tags,
        "notes": notes
    }
