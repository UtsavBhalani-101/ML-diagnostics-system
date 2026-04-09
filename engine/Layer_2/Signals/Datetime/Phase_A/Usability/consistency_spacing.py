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
    """Measures how consistent the time spacing is between consecutive timestamps."""
    
    parsed = pd.to_datetime(col, errors="coerce")
    valid = parsed.dropna().sort_values().reset_index(drop=True)
    
    if len(valid) < 3:
        return {"consistency_score": 0.0, "mode_coverage": 0.0, "n_distinct_intervals": 0}
    
    deltas = valid.diff().dropna()
    delta_seconds = deltas.dt.total_seconds()
    
    if len(delta_seconds) == 0:
        return {"consistency_score": 0.0, "mode_coverage": 0.0, "n_distinct_intervals": 0}
    
    # round to nearest second for grouping
    rounded = delta_seconds.round(0)
    vc = rounded.value_counts(normalize=True)
    
    # mode coverage: what fraction of intervals match the most common interval
    mode_coverage = float(vc.iloc[0]) if len(vc) > 0 else 0.0
    
    # number of distinct intervals
    n_distinct = len(vc)
    
    # consistency: high mode_coverage = consistent spacing
    consistency_score = mode_coverage
    
    return {
        "consistency_score": float(consistency_score),
        "mode_coverage": mode_coverage,
        "n_distinct_intervals": n_distinct,
        "mode_interval_seconds": float(vc.index[0]) if len(vc) > 0 else 0.0
    }

def infer_signals(signals: Dict) -> Result:
    cs = signals["consistency_score"]
    
    # score: 1 - consistency (higher = worse = inconsistent spacing)
    score = 1.0 - cs
    
    flag = score > 0.7
    
    if score > 0.7:
        label = "CRITICAL"
    elif score > 0.4:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_consistency_spacing",
        layer="usability",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "consistency_score": round(cs, 4),
            "mode_coverage": round(signals["mode_coverage"], 4),
            "n_distinct_intervals": signals["n_distinct_intervals"]
        }
    )


def run_consistency_spacing_check():
    # mostly consistent daily data with a few irregular entries
    dates = list(pd.date_range("2023-01-01", periods=95, freq="D"))
    dates += list(pd.date_range("2023-06-01 12:30:00", periods=5, freq="7h"))
    combined_signals = get_signals(pd.Series(dates))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_consistency_spacing_check()
