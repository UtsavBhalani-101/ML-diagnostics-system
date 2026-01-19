import pandas as pd
import numpy as np

def phaseb_numeric_relationship_stability(
    df: pd.DataFrame,
    feature_col: str,
    target_col: str,
    n_splits: int = 5,
    std_threshold: float = 0.15,
    min_rows_per_split: int = 20,
    random_state: int = 42
):
    """
    Phase B: Numeric ↔ Target relationship stability diagnostic.

    Detects whether an observed association is unstable across
    random subsamples (sign flips or high volatility).

    Returns:
        - dict (diagnostic finding) OR
        - None (no instability detected / insufficient data)
    """

    # -------------------------------
    # 1. Prepare data
    # -------------------------------
    data = df[[feature_col, target_col]].dropna()

    if len(data) < n_splits * min_rows_per_split:
        return None

    # -------------------------------
    # 2. Shuffle & split
    # -------------------------------
    shuffled = data.sample(frac=1.0, random_state=random_state)
    chunks = np.array_split(shuffled, n_splits)

    correlations = []

    for chunk in chunks:
        corr = chunk[feature_col].corr(chunk[target_col])
        if not pd.isna(corr):
            correlations.append(corr)

    if len(correlations) < 2:
        return None

    # -------------------------------
    # 3. Analyze variability
    # -------------------------------
    mean_corr = float(np.mean(correlations))
    std_corr = float(np.std(correlations))
    min_corr = float(np.min(correlations))
    max_corr = float(np.max(correlations))

    sign_flip = (min_corr < -0.1) and (max_corr > 0.1)
    volatile = std_corr >= std_threshold

    # -------------------------------
    # 4. Emit diagnostic if unstable
    # -------------------------------
    if sign_flip or volatile:
        return {
            "assumption": "relationship_stability",
            "type": "subsample_instability",
            "columns": [feature_col, target_col],
            "evidence": {
                "metric": "subsample_correlation_variability",
                "mean_corr": round(mean_corr, 3),
                "min_corr": round(min_corr, 3),
                "max_corr": round(max_corr, 3),
                "std_corr": round(std_corr, 3),
                "sign_flip": sign_flip
            },
            "risk": (
                "Observed feature–target association varies substantially across "
                "random subsamples. The relationship may be driven by specific "
                "data segments and may not generalize reliably."
            ),
            "severity": "high" if sign_flip else "medium"
        }

    return None
