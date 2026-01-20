import pandas as pd
import numpy as np

def phasea_categorical_integrity(
    col: pd.Series,
    col_name: str,
    high_cardinality_cap: int = 50,
    near_unique_ratio: float = 0.9
):
    """
    Phase A: Categorical Integrity & Cardinality Diagnostic.

    Assumption:
        Column represents a clean, finite categorical label set.
    """

    if col.empty:
        return None

    raw_col = col
    clean_col = col.dropna().astype(str)
    n_rows = len(clean_col)

    if n_rows == 0:
        return None

    # -----------------------------
    # Hygiene simulation (internal)
    # -----------------------------
    n_raw = clean_col.nunique()
    n_lower = clean_col.str.lower().nunique()
    n_strip = clean_col.str.strip().nunique()

    hygiene_noise = (
        n_lower < n_raw or
        n_strip < n_raw
    )

    garbage_tokens = {'?', 'nan', 'null', 'none', 'missing', 'n/a', '-', ''}
    garbage_ratio = clean_col.str.lower().isin(garbage_tokens).mean()

    mixed_types = raw_col.dropna().map(type).nunique() > 1

    # -----------------------------
    # Cardinality logic (exposed)
    # -----------------------------
    n_unique = n_lower
    unique_ratio = n_unique / n_rows

    evidence = {}

    if unique_ratio > near_unique_ratio:
        evidence["unique_ratio"] = round(unique_ratio, 3)

    if n_unique > high_cardinality_cap:
        evidence["unique_count"] = n_unique

    if garbage_ratio > 0.05:
        evidence["implicit_null_ratio"] = round(garbage_ratio, 3)

    if mixed_types:
        evidence["mixed_type_detected"] = True

    # Hygiene only raises severity if something else is wrong
    severity = "medium"
    if unique_ratio > near_unique_ratio:
        severity = "high"

    if evidence:
        return {
            "assumption": "finite_categorical_set",
            "type": "violated",
            "columns": [col_name],
            "evidence": evidence,
            "risk": (
                "Column does not behave like a clean finite categorical label set. "
                "Observed cardinality, uniqueness, or consistency patterns "
                "suggest unstable or unconstrained categories."
            ),
            "severity": severity
        }

    return None
