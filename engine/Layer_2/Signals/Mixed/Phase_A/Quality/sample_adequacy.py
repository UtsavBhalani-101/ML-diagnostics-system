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
    


def get_signals(numeric_col: pd.Series, cat_col: pd.Series, min_samples_per_group: int = 5) -> dict:
    """Checks if each categorical group has enough numeric samples for reliable statistics."""
    
    valid_mask = numeric_col.notna() & cat_col.notna()
    num_valid = numeric_col[valid_mask]
    cat_valid = cat_col[valid_mask].astype(str).str.strip().str.lower()
    
    if len(num_valid) == 0 or cat_valid.nunique() == 0:
        return {"inadequate_ratio": 1.0, "min_group_size": 0, "n_groups": 0}
    
    grouped_sizes = cat_valid.value_counts()
    n_groups = len(grouped_sizes)
    
    # groups below the minimum sample threshold
    inadequate_groups = int((grouped_sizes < min_samples_per_group).sum())
    inadequate_ratio = inadequate_groups / n_groups if n_groups > 0 else 0.0
    
    min_group_size = int(grouped_sizes.min())
    median_group_size = float(grouped_sizes.median())
    
    return {
        "inadequate_ratio": float(inadequate_ratio),
        "min_group_size": min_group_size,
        "median_group_size": median_group_size,
        "n_groups": n_groups,
        "inadequate_groups": inadequate_groups
    }

def infer_signals(signals: Dict) -> Result:
    ir = signals["inadequate_ratio"]
    mgs = signals["min_group_size"]
    
    score = ir
    
    flag = score > 0.5
    
    if score > 0.5:
        label = "CRITICAL"
    elif score > 0.2:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="mixed_sample_adequacy",
        layer="quality",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "inadequate_ratio": round(ir, 4),
            "min_group_size": mgs,
            "n_groups": signals["n_groups"]
        }
    )


def run_sample_adequacy_check():
    # some groups have very few samples
    cat = pd.Series(["big"] * 50 + ["medium"] * 20 + ["tiny_a"] * 3 + ["tiny_b"] * 2 + ["tiny_c"] * 1)
    num = pd.Series(np.random.normal(0, 1, len(cat)))
    combined_signals = get_signals(num, cat)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_sample_adequacy_check()
