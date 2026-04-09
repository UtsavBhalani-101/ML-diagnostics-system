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
    """Identifies whether the numeric-categorical pair forms a meaningful grouping relationship."""
    
    valid_mask = numeric_col.notna() & cat_col.notna()
    num_valid = numeric_col[valid_mask]
    cat_valid = cat_col[valid_mask].astype(str).str.strip().str.lower()
    
    n_valid = len(num_valid)
    n_groups = cat_valid.nunique()
    
    if n_valid < 5 or n_groups < 2:
        return {"pair_type": "insufficient", "group_ratio": 0.0, "mean_group_size": 0.0}
    
    group_ratio = n_groups / n_valid
    mean_group_size = n_valid / n_groups
    
    # classify the pair type
    if group_ratio > 0.5:
        pair_type = "id_like"         # too many groups, likely an ID
    elif n_groups == 2:
        pair_type = "binary_split"    # binary grouping
    elif n_groups <= 10:
        pair_type = "categorical_group"  # clean grouping
    elif n_groups <= 50:
        pair_type = "high_cardinality_group"
    else:
        pair_type = "fragmented"      # too fragmented to be useful
    
    return {
        "pair_type": pair_type,
        "group_ratio": float(group_ratio),
        "mean_group_size": float(mean_group_size),
        "n_groups": n_groups
    }

def infer_signals(signals: Dict) -> Result:
    pt = signals["pair_type"]
    gr = signals["group_ratio"]
    
    # map pair types to risk scores
    type_scores = {
        "insufficient": 1.0,
        "id_like": 0.9,
        "fragmented": 0.7,
        "high_cardinality_group": 0.4,
        "categorical_group": 0.1,
        "binary_split": 0.0
    }
    
    score = type_scores.get(pt, 0.5)
    
    flag = score > 0.7
    
    if score > 0.7:
        label = "CRITICAL"
    elif score > 0.4:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="mixed_identify_pair",
        layer="semantics",
        score=score,
        label=label,
        flag=flag,
        meta={
            "pair_type": pt,
            "group_ratio": round(gr, 4),
            "n_groups": signals["n_groups"]
        }
    )


def run_identify_pair_check():
    cat = pd.Series(["group_a"] * 40 + ["group_b"] * 35 + ["group_c"] * 25)
    num = pd.Series(np.random.normal(0, 1, 100))
    combined_signals = get_signals(num, cat)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_identify_pair_check()
