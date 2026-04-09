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
    


def get_signals(col: pd.Series) -> dict:
    """Detects duplicate timestamps in a datetime column."""
    
    parsed = pd.to_datetime(col, errors="coerce")
    valid = parsed.dropna()
    
    if len(valid) == 0:
        return {"duplicate_ratio": 0.0, "n_duplicates": 0, "n_total": 0}
    
    n_total = len(valid)
    n_unique = valid.nunique()
    n_duplicates = n_total - n_unique
    duplicate_ratio = n_duplicates / n_total if n_total > 0 else 0.0
    
    # most repeated timestamp
    vc = valid.value_counts()
    max_repeat_count = int(vc.iloc[0]) if len(vc) > 0 else 0
    
    return {
        "duplicate_ratio": float(duplicate_ratio),
        "n_duplicates": int(n_duplicates),
        "n_total": n_total,
        "max_repeat_count": max_repeat_count
    }

def infer_signals(signals: Dict) -> Result:
    dr = signals["duplicate_ratio"]
    
    score = dr
    
    flag = score > 0.3
    
    if score > 0.3:
        label = "CRITICAL"
    elif score > 0.1:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_duplicates",
        layer="quality",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "duplicate_ratio": round(dr, 4),
            "n_duplicates": signals["n_duplicates"],
            "max_repeat_count": signals["max_repeat_count"]
        }
    )


def run_duplicates_check():
    dates = pd.Series(["2023-01-01"] * 10 + ["2023-01-02"] * 5 + 
                      [f"2023-01-{i:02d}" for i in range(3, 20)])
    combined_signals = get_signals(dates)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_duplicates_check()
