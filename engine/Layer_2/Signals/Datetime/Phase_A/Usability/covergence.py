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
    """Measures whether the datetime column covers a reasonable, usable time range."""
    
    parsed = pd.to_datetime(col, errors="coerce")
    valid = parsed.dropna()
    
    if len(valid) < 2:
        return {"coverage_days": 0.0, "density": 0.0, "n_valid": 0}
    
    time_range = valid.max() - valid.min()
    coverage_days = time_range.total_seconds() / 86400
    
    # density: actual data points per day of coverage
    density = len(valid) / coverage_days if coverage_days > 0 else 0.0
    
    # temporal fill: unique dates vs total days in range
    n_unique_dates = valid.dt.date.nunique()
    total_days_in_range = int(coverage_days) + 1
    temporal_fill = n_unique_dates / total_days_in_range if total_days_in_range > 0 else 0.0
    
    return {
        "coverage_days": float(coverage_days),
        "density": float(density),
        "temporal_fill": float(min(1.0, temporal_fill)),
        "n_valid": len(valid)
    }

def infer_signals(signals: Dict) -> Result:
    tf = signals["temporal_fill"]
    cd = signals["coverage_days"]
    
    # score: 1 - temporal_fill (higher = worse = sparse coverage)
    score = 1.0 - tf
    
    # also flag if coverage is extremely narrow (< 7 days)
    if cd < 7 and cd > 0:
        score = max(score, 0.6)
    
    flag = score > 0.7
    
    if score > 0.7:
        label = "CRITICAL"
    elif score > 0.4:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_coverage",
        layer="usability",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "coverage_days": round(cd, 2),
            "temporal_fill": round(tf, 4),
            "density": round(signals["density"], 4)
        }
    )


def run_coverage_check():
    # sparse coverage: 30 data points over a year
    dates = pd.Series(pd.date_range("2023-01-01", periods=30, freq="12D"))
    combined_signals = get_signals(dates)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_coverage_check()
