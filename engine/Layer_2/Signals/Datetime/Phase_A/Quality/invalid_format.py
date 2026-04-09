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
    """Measures what fraction of values fail to parse as valid datetimes."""
    
    n_total = len(col)
    
    if n_total == 0:
        return {"invalid_ratio": 1.0, "n_invalid": 0, "n_total": 0}
    
    # count real nulls
    n_null = int(col.isna().sum())
    
    # attempt to parse non-null values
    non_null = col.dropna()
    parsed = pd.to_datetime(non_null, errors="coerce")
    n_failed_parse = int(parsed.isna().sum())
    
    # total invalid = nulls + failed parses
    n_invalid = n_null + n_failed_parse
    invalid_ratio = n_invalid / n_total
    
    return {
        "invalid_ratio": float(invalid_ratio),
        "n_invalid": n_invalid,
        "n_null": n_null,
        "n_failed_parse": n_failed_parse,
        "n_total": n_total
    }

def infer_signals(signals: Dict) -> Result:
    ir = signals["invalid_ratio"]
    
    score = ir
    
    flag = score > 0.3
    
    if score > 0.3:
        label = "CRITICAL"
    elif score > 0.1:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_invalid_format",
        layer="quality",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "invalid_ratio": round(ir, 4),
            "n_null": signals["n_null"],
            "n_failed_parse": signals["n_failed_parse"]
        }
    )


def run_invalid_format_check():
    data = pd.Series(["2023-01-01", "2023-02-15", "not_a_date", None, "31/13/2023", "2023-06-01"])
    combined_signals = get_signals(data)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_invalid_format_check()
