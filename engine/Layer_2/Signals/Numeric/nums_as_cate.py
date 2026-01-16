import pandas as pd
import numpy as np

def analyze_numeric_category_pathology(col: pd.Series):
    """
    Distinguishes between:
    1. Mixed Semantics: Continuous signal + sentinel spike
    2. Disguised Discrete: Categories encoded as numbers
    """

    # ---------- Fast Scan ----------
    clean_data = pd.to_numeric(col, errors="coerce").dropna()
    n_rows = len(clean_data)

    if n_rows < 20:
        return {"type": "insufficient_data", "action": "skip"}

    unique_vals = np.sort(clean_data.unique())
    n_unique = len(unique_vals)
    cardinality_ratio = n_unique / n_rows

    # Integer purity (with tolerance)
    is_integer_pure = np.all(np.isclose(clean_data % 1, 0, atol=1e-5))

    # Range size (prevents large-N false categoricals)
    value_range = unique_vals[-1] - unique_vals[0]

    # ---------- SCENARIO 2: DISGUISED DISCRETE ----------
    # Few options, integer-only, bounded range
    if (
        is_integer_pure
        and n_unique < 20
        and value_range < 50
    ):
        gaps = np.diff(unique_vals)
        is_uniform_ladder = (
            np.allclose(gaps, gaps[0], atol=1e-5) if len(gaps) > 0 else True
        )

        return {
            "type": "disguised_discrete",
            "subtype": "ordinal_ladder" if is_uniform_ladder else "nominal_codes",
            "metrics": {
                "unique_count": n_unique,
                "is_uniform": is_uniform_ladder
            },
            "action": "trigger_linearity_check"
        }

    # ---------- SCENARIO 1: MIXED SEMANTICS ----------
    counts = clean_data.value_counts(normalize=True)
    top_val = counts.index[0]
    top_freq = counts.iloc[0]

    # Common sentinel values (int or float)
    COMMON_SENTINELS = {0, -1, 999, 9999}

    is_spike_like = (
        np.isclose(top_val % 1, 0, atol=1e-5)
        and (
            top_val in COMMON_SENTINELS
            or top_val <= np.percentile(clean_data, 1)
            or top_val >= np.percentile(clean_data, 99)
        )
    )

    if (
        top_freq > 0.05
        and is_spike_like
        and n_unique > 20
    ):
        return {
            "type": "mixed_semantics",
            "spike_value": float(top_val),
            "spike_frequency": round(top_freq, 4),
            "action": "trigger_semantic_split"
        }

    # ---------- DEFAULT ----------
    return {
        "type": "pure_continuous",
        "action": "standard_scaling"
    }
