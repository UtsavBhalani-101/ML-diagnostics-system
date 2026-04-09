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
    clean = col.dropna().astype(str).str.strip().str.lower()
    
    if len(clean) == 0:
        return {"dominance_ratio": 1.0, "unique_ratio": 0.0}
    
    vc = clean.value_counts(normalize=True)
    n_unique = clean.nunique()
    n_rows = len(clean)
    
    dominance_ratio = float(vc.iloc[0])
    unique_ratio = n_unique / n_rows if n_rows > 0 else 0.0
    
    return {
        "dominance_ratio": dominance_ratio,
        "unique_ratio": float(unique_ratio)
    }

def infer_signals(signals: Dict) -> Result:
    dr = signals["dominance_ratio"]
    ur = signals["unique_ratio"]
    
    # score: dominance_ratio directly — a column dominated by one value has no signal
    score = dr
    
    flag = score > 0.95
    
    if score > 0.95:
        label = "CRITICAL"
    elif score > 0.8:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="categorical_signal_strength",
        layer="affordance",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "dominance_ratio": round(dr, 4),
            "unique_ratio": round(ur, 4)
        }
    )


def run_signal_strength_check():
    # near-constant column
    combined_signals = get_signals(pd.Series(["yes"] * 95 + ["no"] * 5))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_signal_strength_check()
