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
    
    

BUCKET_SCORES = {
    "binary": 0.0,
    "low": 0.2,
    "medium": 0.5,
    "high": 0.8,
    "id_like": 1.0
}

def get_signals(col: pd.Series) -> dict:
    clean = col.dropna().astype(str).str.strip().str.lower()
    
    if len(clean) == 0:
        return {"n_unique": 0, "unique_ratio": 0.0, "cardinality_bucket": "binary"}
    
    n_unique = clean.nunique()
    n_rows = len(clean)
    unique_ratio = n_unique / n_rows if n_rows > 0 else 0.0
    
    # classify cardinality bucket
    if n_unique <= 2:
        bucket = "binary"
    elif n_unique <= 10:
        bucket = "low"
    elif n_unique <= 50:
        bucket = "medium"
    elif unique_ratio < 0.5:
        bucket = "high"
    else:
        bucket = "id_like"
    
    return {
        "n_unique": int(n_unique),
        "unique_ratio": float(unique_ratio),
        "cardinality_bucket": bucket
    }

def infer_signals(signals: Dict) -> Result:
    nu = signals["n_unique"]
    ur = signals["unique_ratio"]
    bucket = signals["cardinality_bucket"]
    
    score = BUCKET_SCORES[bucket]
    
    flag = score > 0.8
    
    if score > 0.8:
        label = "CRITICAL"
    elif score > 0.5:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="categorical_cardinality_type",
        layer="semantics",
        score=score,
        label=label,
        flag=flag,
        meta={
            "n_unique": nu,
            "unique_ratio": round(ur, 4),
            "cardinality_bucket": bucket
        }
    )


def run_cardinality_type_check():
    # ID-like column
    combined_signals = get_signals(pd.Series([f"user_{i}" for i in range(100)]))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_cardinality_type_check()
