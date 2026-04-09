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
    
    

IMPLICIT_MISSING_TOKENS = {
    "nan", "null", "n/a", "na", "none", "missing", "", "?", "unknown", "-", "undefined"
}

def get_signals(col: pd.Series) -> dict:
    n_total = len(col)
    
    if n_total == 0:
        return {"missing_ratio": 0.0, "real_null_count": 0, "implicit_null_count": 0}
    
    # real nulls (NaN, None)
    real_null_count = int(col.isna().sum())
    
    # implicit nulls (garbage tokens hiding as valid values)
    non_null = col.dropna().astype(str).str.strip().str.lower()
    implicit_mask = non_null.isin(IMPLICIT_MISSING_TOKENS)
    implicit_null_count = int(implicit_mask.sum())
    
    total_missing = real_null_count + implicit_null_count
    missing_ratio = total_missing / n_total
    
    return {
        "missing_ratio": float(missing_ratio),
        "real_null_count": real_null_count,
        "implicit_null_count": implicit_null_count,
        "total_missing": total_missing
    }

def infer_signals(signals: Dict) -> Result:
    mr = signals["missing_ratio"]
    rnc = signals["real_null_count"]
    inc = signals["implicit_null_count"]
    
    score = mr
    
    flag = mr > 0.5
    
    if mr > 0.5:
        label = "CRITICAL"
    elif mr > 0.1:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="categorical_measure_missing",
        layer="quality",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "missing_ratio": round(mr, 4),
            "real_null_count": rnc,
            "implicit_null_count": inc
        }
    )


def run_measure_missing_check():
    combined_signals = get_signals(pd.Series(["cat", None, "dog", "null", "?", "bird", None, "na"]))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_measure_missing_check()
