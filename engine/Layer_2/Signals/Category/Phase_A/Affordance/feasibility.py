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
    
    

GARBAGE_TOKENS = {"nan", "null", "n/a", "na", "none", "missing", "", "?", "-", "unknown"}

def get_signals(col: pd.Series) -> dict:
    n_total = len(col)
    
    if n_total == 0:
        return {"valid_ratio": 0.0, "n_total": 0}
    
    # count real nulls
    n_null = col.isna().sum()
    
    # count implicit garbage tokens in non-null values
    non_null = col.dropna().astype(str).str.strip().str.lower()
    n_garbage = non_null.isin(GARBAGE_TOKENS).sum()
    
    n_valid = n_total - n_null - n_garbage
    valid_ratio = n_valid / n_total
    
    return {
        "valid_ratio": float(valid_ratio),
        "n_total": int(n_total)
    }

def infer_signals(signals: Dict) -> Result:
    vr = signals["valid_ratio"]
    
    # score: higher = worse feasibility (inverted)
    score = 1.0 - vr
    
    flag = score > 0.5
    
    if score > 0.5:
        label = "CRITICAL"
    elif score > 0.2:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="categorical_feasibility",
        layer="affordance",
        score=score,
        label=label,
        flag=flag,
        meta={"valid_ratio": vr}
    )


def run_feasibility_check():
    # mostly valid series
    combined_signals = get_signals(pd.Series(["cat", "dog", "bird", None, "?"]))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_feasibility_check()
