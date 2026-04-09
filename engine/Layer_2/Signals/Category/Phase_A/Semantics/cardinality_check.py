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
    clean = col.dropna().astype(str).str.strip()
    n_rows = len(clean)
    
    if n_rows == 0:
        return {"n_unique": 0, "unique_ratio": 0.0, "n_rows": 0}
    
    # normalize to lowercase for true cardinality
    n_raw = clean.nunique()
    n_normalized = clean.str.lower().nunique()
    
    unique_ratio = n_normalized / n_rows
    
    # how many categories collapse under normalization
    noise_ratio = (n_raw - n_normalized) / n_raw if n_raw > 0 else 0.0
    
    return {
        "n_unique": int(n_normalized),
        "unique_ratio": float(unique_ratio),
        "noise_ratio": float(noise_ratio),
        "n_rows": n_rows
    }

def infer_signals(signals: Dict) -> Result:
    ur = signals["unique_ratio"]
    nu = signals["n_unique"]
    nr = signals["noise_ratio"]
    
    # high unique_ratio → likely ID or free-text, not a real categorical
    score = ur
    
    flag = ur > 0.9
    
    if ur > 0.9:
        label = "CRITICAL"
    elif ur > 0.5:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="categorical_cardinality_check",
        layer="semantics",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "n_unique": nu,
            "unique_ratio": round(ur, 4),
            "noise_ratio": round(nr, 4)
        }
    )


def run_cardinality_check():
    # moderate cardinality column
    combined_signals = get_signals(pd.Series(["red", "blue", "green", "Red", "blue", "yellow", "red", "green"]))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_cardinality_check()
