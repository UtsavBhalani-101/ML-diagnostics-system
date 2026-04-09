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
    """Detects temporal trends (monotonic increase/decrease) in a datetime column."""
    
    parsed = pd.to_datetime(col, errors="coerce")
    valid = parsed.dropna().sort_index()
    
    if len(valid) < 5:
        return {"monotonic_ratio": 0.0, "trend_direction": "none", "reversal_ratio": 0.0}
    
    # compute differences between consecutive timestamps
    numeric_vals = valid.astype(np.int64)
    diffs = np.diff(numeric_vals)
    
    if len(diffs) == 0:
        return {"monotonic_ratio": 0.0, "trend_direction": "none", "reversal_ratio": 0.0}
    
    n_positive = int((diffs > 0).sum())
    n_negative = int((diffs < 0).sum())
    n_zero = int((diffs == 0).sum())
    n_total = len(diffs)
    
    # how monotonic is the sequence?
    monotonic_ratio = max(n_positive, n_negative) / n_total if n_total > 0 else 0.0
    
    # trend direction
    if n_positive > n_negative * 3:
        trend_direction = "increasing"
    elif n_negative > n_positive * 3:
        trend_direction = "decreasing"
    else:
        trend_direction = "mixed"
    
    # reversals: direction changes
    signs = np.sign(diffs)
    signs_nonzero = signs[signs != 0]
    reversals = int(np.sum(np.diff(signs_nonzero) != 0)) if len(signs_nonzero) > 1 else 0
    reversal_ratio = reversals / n_total if n_total > 0 else 0.0
    
    return {
        "monotonic_ratio": float(monotonic_ratio),
        "trend_direction": trend_direction,
        "reversal_ratio": float(reversal_ratio)
    }

def infer_signals(signals: Dict) -> Result:
    mr = signals["monotonic_ratio"]
    rr = signals["reversal_ratio"]
    td = signals["trend_direction"]
    
    # no clear temporal pattern → hard to use as time feature
    # score = 1 - monotonic_ratio (higher = worse = chaotic ordering)
    score = 1.0 - mr
    
    flag = score > 0.7
    
    if score > 0.7:
        label = "CRITICAL"
    elif score > 0.4:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_temporal_patterns",
        layer="affordance",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "monotonic_ratio": round(mr, 4),
            "trend_direction": td,
            "reversal_ratio": round(rr, 4)
        }
    )


def run_temporal_patterns_check():
    # mostly increasing timestamps with a few out-of-order
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    shuffled = dates.tolist()
    shuffled[50], shuffled[51] = shuffled[51], shuffled[50]  # one swap
    combined_signals = get_signals(pd.Series(shuffled))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_temporal_patterns_check()
