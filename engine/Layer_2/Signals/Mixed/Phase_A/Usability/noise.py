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
    """Measures how much noise the categorical grouping injects into the numeric column."""
    
    valid_mask = numeric_col.notna() & cat_col.notna()
    num_valid = numeric_col[valid_mask]
    cat_valid = cat_col[valid_mask].astype(str).str.strip().str.lower()
    
    if len(num_valid) < 5 or cat_valid.nunique() < 2:
        return {"noise_ratio": 1.0, "within_var": 0.0, "total_var": 0.0}
    
    total_var = float(num_valid.var())
    
    if total_var == 0:
        return {"noise_ratio": 0.0, "within_var": 0.0, "total_var": 0.0}
    
    # within-group variance: variance not explained by the grouping
    grouped = num_valid.groupby(cat_valid)
    group_vars = grouped.var().dropna()
    group_sizes = grouped.size()
    
    # weighted average of within-group variances
    valid_groups = group_vars.index.intersection(group_sizes.index)
    within_var = float((group_vars[valid_groups] * group_sizes[valid_groups]).sum() / group_sizes[valid_groups].sum())
    
    # noise ratio: proportion of variance that remains unexplained
    noise_ratio = within_var / total_var
    
    return {
        "noise_ratio": float(min(1.0, noise_ratio)),
        "within_var": round(within_var, 4),
        "total_var": round(total_var, 4)
    }

def infer_signals(signals: Dict) -> Result:
    nr = signals["noise_ratio"]
    
    # high noise → grouping doesn't reduce variance, i.e., useless grouping
    score = nr
    
    flag = score > 0.9
    
    if score > 0.9:
        label = "CRITICAL"
    elif score > 0.7:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="mixed_noise",
        layer="usability",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "noise_ratio": round(nr, 4),
            "within_var": signals["within_var"],
            "total_var": signals["total_var"]
        }
    )


def run_noise_check():
    # grouping explains nothing — both groups same distribution
    cat = pd.Series(["x"] * 50 + ["y"] * 50)
    num = pd.Series(np.random.normal(50, 10, 100))
    combined_signals = get_signals(num, cat)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_noise_check()
