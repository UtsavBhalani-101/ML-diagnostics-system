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
    """Validates whether a column is actually a valid datetime column by measuring parse success rate."""
    
    n_total = len(col)
    
    if n_total == 0:
        return {"parse_ratio": 0.0, "n_total": 0}
    
    n_null = int(col.isna().sum())
    non_null = col.dropna()
    
    if len(non_null) == 0:
        return {"parse_ratio": 0.0, "n_total": n_total}
    
    parsed = pd.to_datetime(non_null, errors="coerce")
    n_parsed = int(parsed.notna().sum())
    n_non_null = len(non_null)
    
    parse_ratio = n_parsed / n_non_null if n_non_null > 0 else 0.0
    
    # check for reasonable date range (not year 0001 or 9999)
    valid_dates = parsed.dropna()
    reasonable_dates = 0
    if len(valid_dates) > 0:
        min_year = valid_dates.dt.year.min()
        max_year = valid_dates.dt.year.max()
        reasonable_mask = (valid_dates.dt.year >= 1900) & (valid_dates.dt.year <= 2100)
        reasonable_dates = int(reasonable_mask.sum())
    
    reasonable_ratio = reasonable_dates / n_non_null if n_non_null > 0 else 0.0
    
    return {
        "parse_ratio": float(parse_ratio),
        "reasonable_ratio": float(reasonable_ratio),
        "n_total": n_total,
        "n_null": n_null
    }

def infer_signals(signals: Dict) -> Result:
    pr = signals["parse_ratio"]
    rr = signals["reasonable_ratio"]
    
    # combined validity: both parseable AND reasonable
    validity = min(pr, rr)
    
    # score: 1 - validity (higher = worse = not a valid datetime column)
    score = 1.0 - validity
    
    flag = score > 0.5
    
    if score > 0.5:
        label = "CRITICAL"
    elif score > 0.2:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_is_valid",
        layer="semantics",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "parse_ratio": round(pr, 4),
            "reasonable_ratio": round(rr, 4)
        }
    )


def run_is_valid_datetime_check():
    data = pd.Series(["2023-01-01", "2023-06-15", "not_a_date", "2023-12-31", "abc123"])
    combined_signals = get_signals(data)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_is_valid_datetime_check()
