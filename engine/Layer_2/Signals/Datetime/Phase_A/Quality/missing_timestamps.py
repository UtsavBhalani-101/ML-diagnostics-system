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
    """Detects missing timestamps in a datetime column by comparing actual vs expected count."""
    
    parsed = pd.to_datetime(col, errors="coerce")
    
    n_total = len(col)
    n_null = int(col.isna().sum())
    n_parse_fail = int(parsed.isna().sum()) - n_null
    
    valid = parsed.dropna().sort_values()
    
    if len(valid) < 3:
        return {"missing_ratio": 1.0, "gap_count": 0, "n_total": n_total}
    
    # infer expected frequency from median delta
    deltas = valid.diff().dropna()
    median_delta = deltas.median()
    
    if median_delta.total_seconds() <= 0:
        return {"missing_ratio": 0.0, "gap_count": 0, "n_total": n_total}
    
    # expected number of timestamps given the time range and median frequency
    time_range = valid.max() - valid.min()
    expected_count = int(time_range / median_delta) + 1
    actual_count = len(valid)
    
    # gaps: points where delta > 2x median (missing timestamps inferred)
    gap_mask = deltas > (median_delta * 2)
    gap_count = int(gap_mask.sum())
    
    missing_count = max(0, expected_count - actual_count)
    missing_ratio = missing_count / expected_count if expected_count > 0 else 0.0
    
    return {
        "missing_ratio": float(min(1.0, missing_ratio)),
        "gap_count": gap_count,
        "expected_count": expected_count,
        "actual_count": actual_count,
        "n_total": n_total
    }

def infer_signals(signals: Dict) -> Result:
    mr = signals["missing_ratio"]
    gc = signals["gap_count"]
    
    score = mr
    
    flag = score > 0.3
    
    if score > 0.3:
        label = "CRITICAL"
    elif score > 0.1:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_missing_timestamps",
        layer="quality",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "missing_ratio": round(mr, 4),
            "gap_count": gc,
            "expected_count": signals.get("expected_count", 0)
        }
    )


def run_missing_timestamps_check():
    # daily series with gaps
    dates = list(pd.date_range("2023-01-01", periods=30, freq="D"))
    # remove some to create gaps
    del dates[10:15]
    del dates[20:23]
    combined_signals = get_signals(pd.Series(dates))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_missing_timestamps_check()
