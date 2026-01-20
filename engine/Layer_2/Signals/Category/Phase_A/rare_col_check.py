import pandas as pd
import numpy as np
from scipy.stats import entropy

def compute_categorical_stats(col: pd.Series, rare_freq_threshold: float = 0.01):
    """
    CORE MEASUREMENT: Categorical Cardinality & Rarity Statistics.

    This function computes reusable statistics ONLY.
    No assumptions. No decisions. No recommendations.
    """

    col = col.dropna()

    if col.empty:
        return None

    vc = col.astype(str).value_counts()
    n_rows = len(col)

    # --- Cardinality ---
    n_unique = len(vc)  
    unique_ratio = n_unique / n_rows

    # --- Rare label structure ---
    freq_ratio = vc / n_rows
    rare_mask = freq_ratio < rare_freq_threshold
    n_rare = rare_mask.sum()
    rare_ratio = n_rare / n_unique if n_unique > 0 else 0

    # --- Dominance ---
    top_freq_ratio = freq_ratio.iloc[0]

    # --- Entropy (distribution health) ---
    dist_entropy = entropy(vc.values, base=2)

    return {
        "n_rows": n_rows,
        "n_unique": n_unique,
        "unique_ratio": round(unique_ratio, 4),
        "rare_category_count": int(n_rare),
        "rare_category_ratio": round(rare_ratio, 4),
        "top_category_ratio": round(top_freq_ratio, 4),
        "entropy": round(dist_entropy, 4)
    }
