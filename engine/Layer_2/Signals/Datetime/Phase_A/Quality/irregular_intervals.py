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
    """Measures how irregular the time intervals are between consecutive timestamps."""
    
    parsed = pd.to_datetime(col, errors="coerce")
    valid = parsed.dropna().sort_values().reset_index(drop=True)
    
    if len(valid) < 3:
        return {"cv_intervals": 0.0, "median_interval_seconds": 0.0, "n_intervals": 0}
    
    # compute time deltas in seconds
    deltas = valid.diff().dropna().dt.total_seconds()
    
    if len(deltas) == 0 or deltas.mean() == 0:
        return {"cv_intervals": 0.0, "median_interval_seconds": 0.0, "n_intervals": 0}
    
    mean_delta = float(deltas.mean())
    std_delta = float(deltas.std())
    median_delta = float(deltas.median())
    
    # coefficient of variation: how irregular
    cv_intervals = std_delta / abs(mean_delta) if mean_delta != 0 else 0.0
    
    # ratio of max gap to median gap
    max_gap = float(deltas.max())
    max_to_median_ratio = max_gap / median_delta if median_delta > 0 else 0.0
    
    return {
        "cv_intervals": float(cv_intervals),
        "median_interval_seconds": median_delta,
        "max_to_median_ratio": float(max_to_median_ratio),
        "n_intervals": len(deltas)
    }

def infer_signals(signals: Dict) -> Result:
    cv = signals["cv_intervals"]
    
    # normalize CV to [0, 1]: cap at CV=3 as extreme irregularity
    score = min(1.0, cv / 3.0)
    
    flag = score > 0.6
    
    if score > 0.6:
        label = "CRITICAL"
    elif score > 0.3:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_irregular_intervals",
        layer="quality",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "cv_intervals": round(cv, 4),
            "max_to_median_ratio": round(signals["max_to_median_ratio"], 4),
            "median_interval_seconds": signals["median_interval_seconds"]
        }
    )


def run_irregular_intervals_check():
    # mostly regular with one big gap
    dates = list(pd.date_range("2023-01-01", periods=50, freq="D"))
    dates += list(pd.date_range("2023-06-01", periods=50, freq="D"))  # 5-month gap
    combined_signals = get_signals(pd.Series(dates))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_irregular_intervals_check()
