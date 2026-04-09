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
    
    

def get_signals(col: pd.Series, rare_threshold: float = 0.01) -> dict:
    clean = col.dropna().astype(str).str.strip().str.lower()
    
    if len(clean) == 0:
        return {"rare_to_total_ratio": 0.0, "n_rare": 0, "projected_sparse_dims": 0}
    
    vc = clean.value_counts()
    n_unique = len(vc)
    n_rows = len(clean)
    
    if n_unique == 0:
        return {"rare_to_total_ratio": 0.0, "n_rare": 0, "projected_sparse_dims": 0}
    
    freq = vc / n_rows
    
    # rare categories below threshold
    n_rare = int((freq < rare_threshold).sum())
    rare_to_total_ratio = n_rare / n_unique
    
    # projected sparse dims: OHE columns that would be near-zero for most rows
    projected_sparse_dims = n_rare  # each rare category = one near-empty OHE column
    
    return {
        "rare_to_total_ratio": float(rare_to_total_ratio),
        "n_rare": n_rare,
        "projected_sparse_dims": projected_sparse_dims
    }

def infer_signals(signals: Dict) -> Result:
    rtr = signals["rare_to_total_ratio"]
    n_rare = signals["n_rare"]
    psd = signals["projected_sparse_dims"]
    
    score = rtr
    
    flag = score > 0.7
    
    if score > 0.7:
        label = "CRITICAL"
    elif score > 0.4:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="categorical_rare_explosion",
        layer="usability",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "rare_to_total_ratio": round(rtr, 4),
            "n_rare": n_rare,
            "projected_sparse_dims": psd
        }
    )


def run_rare_explosion_check():
    # many rare categories → sparse encoding risk
    data = ["common_a"] * 50 + ["common_b"] * 30 + [f"rare_{i}" for i in range(80)]
    combined_signals = get_signals(pd.Series(data))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_rare_explosion_check()
