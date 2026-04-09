import numpy as np 
import pandas as pd 
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass(frozen=True)
class Signals:
    pass

@dataclass()
class Result:
    test_name: str 
    layer: str 
    score: float
    label: str
    flag: bool
    meta: Dict[str, float]
    


def get_signals(numeric_col: pd.Series, cat_col: pd.Series) -> dict:
    """Checks whether a categorical column creates meaningful separation in a numeric column."""
    
    cat_clean = cat_col.dropna().astype(str).str.strip().str.lower()
    
    # align on shared valid indices
    valid_mask = cat_col.notna() & numeric_col.notna()
    num_valid = numeric_col[valid_mask]
    cat_valid = cat_clean[valid_mask]
    
    if len(num_valid) < 5 or cat_valid.nunique() < 2:
        return {"separation_score": 0.0, "n_groups": 0, "overall_std": 0.0}
    
    overall_std = float(num_valid.std())
    
    if overall_std == 0:
        return {"separation_score": 0.0, "n_groups": int(cat_valid.nunique()), "overall_std": 0.0}
    
    # between-group variance / total variance (eta-squared-like)
    grouped = num_valid.groupby(cat_valid)
    group_means = grouped.mean()
    group_sizes = grouped.size()
    grand_mean = num_valid.mean()
    
    ss_between = float(((group_means - grand_mean) ** 2 * group_sizes).sum())
    ss_total = float(((num_valid - grand_mean) ** 2).sum())
    
    separation_score = ss_between / ss_total if ss_total > 0 else 0.0
    
    return {
        "separation_score": float(separation_score),
        "n_groups": int(cat_valid.nunique()),
        "overall_std": round(overall_std, 4)
    }

def infer_signals(signals: Dict) -> Result:
    sep = signals["separation_score"]
    
    # low separation → categorical grouping doesn't explain numeric variance
    # invert: score = 1 - separation (higher = worse)
    score = 1.0 - sep
    
    flag = score > 0.9
    
    if score > 0.9:
        label = "CRITICAL"
    elif score > 0.7:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="mixed_group_separation",
        layer="affordance",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "separation_score": round(sep, 4),
            "n_groups": signals["n_groups"]
        }
    )


def run_group_separation_check():
    # clear separation: groups have distinct numeric ranges
    cat = pd.Series(["A"] * 30 + ["B"] * 30 + ["C"] * 30)
    num = pd.Series(
        np.concatenate([np.random.normal(10, 1, 30),
                        np.random.normal(50, 1, 30),
                        np.random.normal(90, 1, 30)])
    )
    combined_signals = get_signals(num, cat)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_group_separation_check()
