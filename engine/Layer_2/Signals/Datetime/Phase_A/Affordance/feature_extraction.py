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
    """Checks how many useful temporal features can be extracted from this datetime column."""
    
    parsed = pd.to_datetime(col, errors="coerce")
    valid = parsed.dropna()
    
    if len(valid) < 3:
        return {"extractable_components": 0, "component_variation": {}}
    
    components = {}
    
    # check which components have variation (>1 unique value)
    for name, accessor in [("year", valid.dt.year), ("month", valid.dt.month),
                           ("day", valid.dt.day), ("hour", valid.dt.hour),
                           ("minute", valid.dt.minute), ("dayofweek", valid.dt.dayofweek)]:
        n_unique = accessor.nunique()
        components[name] = int(n_unique)
    
    # components with actual variation (>1 unique)
    varying = {k: v for k, v in components.items() if v > 1}
    extractable = len(varying)
    
    return {
        "extractable_components": extractable,
        "component_variation": components,
        "total_components": len(components)
    }

def infer_signals(signals: Dict) -> Result:
    ec = signals["extractable_components"]
    tc = signals["total_components"]
    
    # score: fraction of components that DON'T vary (higher = worse)
    score = 1.0 - (ec / tc) if tc > 0 else 1.0
    
    flag = score > 0.7
    
    if score > 0.7:
        label = "CRITICAL"
    elif score > 0.4:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_feature_extraction",
        layer="affordance",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "extractable_components": ec,
            "total_components": tc
        }
    )


def run_feature_extraction_check():
    dates = pd.date_range("2023-01-01", periods=100, freq="h")
    combined_signals = get_signals(pd.Series(dates))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_feature_extraction_check()
