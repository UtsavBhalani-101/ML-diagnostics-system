import pandas as pd
import numpy as np
from sklearn.metrics import mutual_info_score

def phaseb_categorical_target_leakage(
    df: pd.DataFrame,
    col_name: str,
    target_col: str,
    task_type: str = "classification",
    leak_threshold: float = 0.95
):
    """
    Phase B: Category ↔ Target Leakage Check.

    Assumption:
        A categorical feature should not deterministically encode the target.
    """

    # ----------------------------
    # 1. Prepare data
    # ----------------------------
    data = df[[col_name, target_col]].dropna()

    if data.empty or data[col_name].nunique() <= 1:
        return None

    x = data[col_name].astype(str)
    y = data[target_col]

    evidence = {}
    score = None
    metric = None

    # ----------------------------
    # 2. Association measurement
    # ----------------------------
    if task_type == "classification":
        # Mutual Information (normalized)
        mi = mutual_info_score(x, y)

        # Entropies for normalization
        hx = mutual_info_score(x, x)
        hy = mutual_info_score(y, y)

        if hx + hy > 0:
            score = 2 * mi / (hx + hy)
            metric = "normalized_mutual_information"

    elif task_type == "regression":
        # Correlation Ratio (η²)
        # Measures variance explained by category
        groups = y.groupby(x)
        overall_mean = y.mean()

        ss_between = sum(len(g) * (g.mean() - overall_mean) ** 2 for _, g in groups)
        ss_total = sum((y - overall_mean) ** 2)

        if ss_total > 0:
            score = ss_between / ss_total
            metric = "correlation_ratio"

    if score is None:
        return None

    evidence = {
        "metric": metric,
        "value": round(score, 4)
    }

    # ----------------------------
    # 3. Violation logic
    # ----------------------------
    if score >= leak_threshold:
        return {
            "assumption": "non_leaky_feature_target_relationship",
            "type": "violated",
            "columns": [col_name],
            "evidence": evidence,
            "risk": (
                "Categorical feature shows near-deterministic association "
                "with the target. Likely acts as a proxy or leaks outcome information."
            ),
            "severity": "high"
        }

    # Mild warning zone (strong but not perfect)
    if score >= 0.8:
        return {
            "assumption": "non_leaky_feature_target_relationship",
            "type": "warning",
            "columns": [col_name],
            "evidence": evidence,
            "risk": (
                "Categorical feature has unusually strong association with the target. "
                "May cause shortcut learning or instability."
            ),
            "severity": "medium"
        }

    return None
