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
    """Checks if any categorical group has a meaningful structural pattern in the numeric column."""
    
    valid_mask = numeric_col.notna() & cat_col.notna()
    num_valid = numeric_col[valid_mask]
    cat_valid = cat_col[valid_mask].astype(str).str.strip().str.lower()
    
    if len(num_valid) < 5 or cat_valid.nunique() < 2:
        return {"structure_exists": False, "max_mean_diff": 0.0, "distinct_groups": 0}
    
    grand_mean = float(num_valid.mean())
    grand_std = float(num_valid.std())
    
    if grand_std == 0:
        return {"structure_exists": False, "max_mean_diff": 0.0, "distinct_groups": 0}
    
    grouped = num_valid.groupby(cat_valid)
    group_means = grouped.mean()
    
    # z-scores of group means relative to grand distribution
    z_scores = ((group_means - grand_mean) / grand_std).abs()
    
    # groups with mean > 1 std away from grand mean → structurally distinct
    distinct_groups = int((z_scores > 1.0).sum())
    max_mean_diff = float(z_scores.max())
    
    structure_exists = distinct_groups >= 1
    
    return {
        "structure_exists": structure_exists,
        "max_mean_diff": max_mean_diff,
        "distinct_groups": distinct_groups,
        "n_groups": int(cat_valid.nunique())
    }

def infer_signals(signals: Dict) -> Result:
    se = signals["structure_exists"]
    mmd = signals["max_mean_diff"]
    dg = signals["distinct_groups"]
    
    # no structure → the grouping is meaningless noise
    # score: 1 - normalized_max_diff (higher score = worse = no structure)
    normalized = min(1.0, mmd / 3.0)  # cap at 3 std deviations
    score = 1.0 - normalized
    
    flag = score > 0.8
    
    if score > 0.8:
        label = "CRITICAL"
    elif score > 0.5:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="mixed_group_structure_exists",
        layer="semantics",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "structure_exists": se,
            "max_mean_diff_z": round(mmd, 4),
            "distinct_groups": dg
        }
    )


def run_group_structure_check():
    # one group clearly different
    cat = pd.Series(["normal"] * 60 + ["outlier_group"] * 20 + ["control"] * 20)
    num = pd.Series(
        np.concatenate([np.random.normal(50, 5, 60),
                        np.random.normal(90, 5, 20),
                        np.random.normal(50, 5, 20)])
    )
    combined_signals = get_signals(num, cat)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_group_structure_check()
