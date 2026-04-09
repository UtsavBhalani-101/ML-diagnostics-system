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
    """Measures aligned missingness between a numeric and categorical column pair."""
    
    n_total = len(numeric_col)
    
    if n_total == 0:
        return {"joint_missing_ratio": 0.0, "num_missing_ratio": 0.0, "cat_missing_ratio": 0.0}
    
    num_missing = numeric_col.isna()
    cat_missing = cat_col.isna()
    
    # individual missing
    num_missing_ratio = float(num_missing.mean())
    cat_missing_ratio = float(cat_missing.mean())
    
    # both missing at the same row
    both_missing = (num_missing & cat_missing).sum()
    joint_missing_ratio = float(both_missing / n_total)
    
    # any missing (union)
    either_missing = (num_missing | cat_missing).sum()
    either_missing_ratio = float(either_missing / n_total)
    
    # co-occurrence: how often missingness is aligned
    # if one is missing, is the other likely to be missing too?
    if either_missing > 0:
        cooccurrence = both_missing / either_missing
    else:
        cooccurrence = 0.0
    
    return {
        "joint_missing_ratio": joint_missing_ratio,
        "either_missing_ratio": either_missing_ratio,
        "num_missing_ratio": num_missing_ratio,
        "cat_missing_ratio": cat_missing_ratio,
        "cooccurrence": float(cooccurrence)
    }

def infer_signals(signals: Dict) -> Result:
    emr = signals["either_missing_ratio"]
    co = signals["cooccurrence"]
    
    # score: overall data loss from the pair
    score = emr
    
    flag = score > 0.3
    
    if score > 0.3:
        label = "CRITICAL"
    elif score > 0.1:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="mixed_missing_values",
        layer="quality",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "either_missing_ratio": round(emr, 4),
            "joint_missing_ratio": round(signals["joint_missing_ratio"], 4),
            "cooccurrence": round(co, 4)
        }
    )


def run_missing_vals_check():
    num = pd.Series([1, np.nan, 3, np.nan, 5, 6, np.nan, 8, 9, np.nan])
    cat = pd.Series(["a", None, "b", None, "c", None, "d", "e", None, None])
    combined_signals = get_signals(num, cat)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_missing_vals_check()
