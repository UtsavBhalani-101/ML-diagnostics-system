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
    
    

GARBAGE_TOKENS = {"nan", "null", "n/a", "na", "none", "missing", "", "?", "-", "unknown", "undefined"}

def get_signals(col: pd.Series) -> dict:
    non_null = col.dropna().astype(str).str.strip().str.lower()
    
    if len(non_null) == 0:
        return {"garbage_ratio": 0.0, "n_garbage_types": 0}
    
    garbage_mask = non_null.isin(GARBAGE_TOKENS)
    garbage_ratio = float(garbage_mask.mean())
    
    # which specific garbage tokens were found
    garbage_types_found = sorted(set(non_null[garbage_mask].unique()))
    n_garbage_types = len(garbage_types_found)
    
    return {
        "garbage_ratio": garbage_ratio,
        "n_garbage_types": n_garbage_types,
        "garbage_types_found": garbage_types_found
    }

def infer_signals(signals: Dict) -> Result:
    gr = signals["garbage_ratio"]
    ngt = signals["n_garbage_types"]
    
    score = gr
    
    flag = score > 0.2
    
    if score > 0.2:
        label = "CRITICAL"
    elif score > 0.05:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="categorical_invalid_categories",
        layer="quality",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "garbage_ratio": round(gr, 4),
            "n_garbage_types": ngt
        }
    )


def run_invalid_categories_check():
    combined_signals = get_signals(pd.Series(["cat", "dog", "?", "null", "none", "bird", "na"]))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_invalid_categories_check()
