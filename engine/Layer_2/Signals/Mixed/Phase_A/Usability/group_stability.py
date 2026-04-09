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
    """Measures whether group-level statistics are stable or if groups behave erratically."""
    
    valid_mask = numeric_col.notna() & cat_col.notna()
    num_valid = numeric_col[valid_mask]
    cat_valid = cat_col[valid_mask].astype(str).str.strip().str.lower()
    
    if len(num_valid) < 5 or cat_valid.nunique() < 2:
        return {"cv_of_means": 0.0, "cv_of_stds": 0.0, "n_groups": 0}
    
    grouped = num_valid.groupby(cat_valid)
    group_means = grouped.mean()
    group_stds = grouped.std().dropna()
    
    # coefficient of variation across group means
    mean_of_means = group_means.mean()
    cv_of_means = float(group_means.std() / abs(mean_of_means)) if mean_of_means != 0 else 0.0
    
    # coefficient of variation across group stds (heterogeneity of spread)
    mean_of_stds = group_stds.mean()
    cv_of_stds = float(group_stds.std() / mean_of_stds) if mean_of_stds > 0 else 0.0
    
    return {
        "cv_of_means": cv_of_means,
        "cv_of_stds": cv_of_stds,
        "n_groups": int(cat_valid.nunique())
    }

def infer_signals(signals: Dict) -> Result:
    cv_m = signals["cv_of_means"]
    cv_s = signals["cv_of_stds"]
    
    # high cv_of_stds → groups are very inconsistent in spread (unstable)
    score = min(1.0, cv_s)
    
    flag = score > 0.8
    
    if score > 0.8:
        label = "CRITICAL"
    elif score > 0.4:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="mixed_group_stability",
        layer="usability",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "cv_of_means": round(cv_m, 4),
            "cv_of_stds": round(cv_s, 4),
            "n_groups": signals["n_groups"]
        }
    )


def run_group_stability_check():
    # groups with wildly different spread
    cat = pd.Series(["tight"] * 40 + ["wild"] * 40 + ["moderate"] * 40)
    num = pd.Series(
        np.concatenate([np.random.normal(50, 1, 40),
                        np.random.normal(50, 50, 40),
                        np.random.normal(50, 10, 40)])
    )
    combined_signals = get_signals(num, cat)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_group_stability_check()
