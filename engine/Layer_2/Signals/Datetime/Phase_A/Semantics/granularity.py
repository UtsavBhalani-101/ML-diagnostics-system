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
    


GRANULARITY_LEVELS = ["second", "minute", "hour", "day", "month", "year"]
GRANULARITY_SCORES = {
    "second": 0.0,  # finest = best
    "minute": 0.1,
    "hour": 0.2,
    "day": 0.3,
    "month": 0.5,
    "year": 0.8
}

def get_signals(col: pd.Series) -> dict:
    """Determines the effective granularity of a datetime column."""
    
    parsed = pd.to_datetime(col, errors="coerce")
    valid = parsed.dropna().sort_values()
    
    if len(valid) < 3:
        return {"granularity": "unknown", "median_interval_seconds": 0.0}
    
    deltas = valid.diff().dropna().dt.total_seconds()
    median_seconds = float(deltas.median())
    
    # classify granularity based on median interval
    if median_seconds < 60:
        granularity = "second"
    elif median_seconds < 3600:
        granularity = "minute"
    elif median_seconds < 86400:
        granularity = "hour"
    elif median_seconds < 86400 * 28:
        granularity = "day"
    elif median_seconds < 86400 * 365:
        granularity = "month"
    else:
        granularity = "year"
    
    # check sub-granularity variation (do sub-components have any variation?)
    has_time_component = valid.dt.hour.nunique() > 1 or valid.dt.minute.nunique() > 1
    
    return {
        "granularity": granularity,
        "median_interval_seconds": median_seconds,
        "has_time_component": has_time_component,
        "n_unique_dates": int(valid.dt.date.nunique())
    }

def infer_signals(signals: Dict) -> Result:
    gran = signals["granularity"]
    
    score = GRANULARITY_SCORES.get(gran, 0.5)
    
    flag = score > 0.5
    
    if score > 0.5:
        label = "CRITICAL"
    elif score > 0.3:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_granularity",
        layer="semantics",
        score=score,
        label=label,
        flag=flag,
        meta={
            "granularity": gran,
            "median_interval_seconds": signals["median_interval_seconds"],
            "has_time_component": signals["has_time_component"]
        }
    )


def run_granularity_check():
    # daily data
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    combined_signals = get_signals(pd.Series(dates))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_granularity_check()
