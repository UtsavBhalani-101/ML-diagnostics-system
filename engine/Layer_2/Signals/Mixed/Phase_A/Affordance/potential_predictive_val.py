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
    """Estimates whether the numeric-categorical pair could have predictive value via group mean spread."""
    
    valid_mask = numeric_col.notna() & cat_col.notna()
    num_valid = numeric_col[valid_mask]
    cat_valid = cat_col[valid_mask].astype(str).str.strip().str.lower()
    
    if len(num_valid) < 5 or cat_valid.nunique() < 2:
        return {"mean_spread_ratio": 0.0, "group_range": 0.0, "n_groups": 0}
    
    grouped = num_valid.groupby(cat_valid)
    group_means = grouped.mean()
    
    # spread of group means relative to overall range
    overall_range = float(num_valid.max() - num_valid.min())
    group_mean_range = float(group_means.max() - group_means.min())
    
    mean_spread_ratio = group_mean_range / overall_range if overall_range > 0 else 0.0
    
    # correlation ratio (eta): how much variance is explained by grouping
    grand_mean = num_valid.mean()
    group_sizes = grouped.size()
    ss_between = float(((group_means - grand_mean) ** 2 * group_sizes).sum())
    ss_total = float(((num_valid - grand_mean) ** 2).sum())
    
    eta_squared = ss_between / ss_total if ss_total > 0 else 0.0
    
    return {
        "mean_spread_ratio": float(mean_spread_ratio),
        "eta_squared": float(eta_squared),
        "group_range": group_mean_range,
        "n_groups": int(cat_valid.nunique())
    }

def infer_signals(signals: Dict) -> Result:
    eta = signals["eta_squared"]
    msr = signals["mean_spread_ratio"]
    
    # combine: both low → no predictive potential
    score = 1.0 - max(eta, msr)
    
    flag = score > 0.9
    
    if score > 0.9:
        label = "CRITICAL"
    elif score > 0.7:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="mixed_potential_predictive_value",
        layer="affordance",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "eta_squared": round(eta, 4),
            "mean_spread_ratio": round(msr, 4)
        }
    )


def run_predictive_value_check():
    cat = pd.Series(["low"] * 30 + ["mid"] * 30 + ["high"] * 30)
    num = pd.Series(
        np.concatenate([np.random.normal(20, 3, 30),
                        np.random.normal(50, 3, 30),
                        np.random.normal(80, 3, 30)])
    )
    combined_signals = get_signals(num, cat)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_predictive_value_check()
