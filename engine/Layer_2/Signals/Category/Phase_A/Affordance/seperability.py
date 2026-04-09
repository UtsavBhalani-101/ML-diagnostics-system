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
        return {"entropy": 0.0, "n_effective": 0, "n_unique": 0}
    
    vc = clean.value_counts(normalize=True)
    n_unique = len(vc)
    
    # Shannon entropy (base-2)
    probs = vc.values
    entropy = -np.sum(probs * np.log2(probs + 1e-12))
    
    # effective categories: those above 1% frequency
    n_effective = int((vc > 0.01).sum())
    
    return {
        "entropy": float(entropy),
        "n_effective": n_effective,
        "n_unique": n_unique
    }

def infer_signals(signals: Dict) -> Result:
    ent = signals["entropy"]
    n_unique = signals["n_unique"]
    n_effective = signals["n_effective"]
    
    # normalized entropy: how spread is the distribution vs max possible
    max_entropy = np.log2(n_unique) if n_unique > 1 else 1.0
    norm_entropy = ent / max_entropy if max_entropy > 0 else 0.0
    
    # score: 1 - normalized_entropy → low spread = high score = bad separability
    score = 1.0 - norm_entropy
    
    flag = score > 0.7
    
    if score > 0.7:
        label = "CRITICAL"
    elif score > 0.4:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="categorical_separability",
        layer="affordance",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "entropy": round(ent, 4),
            "n_effective": n_effective,
            "normalized_entropy": round(norm_entropy, 4)
        }
    )


def run_separability_check():
    # well-spread series
    combined_signals = get_signals(pd.Series(["a", "b", "c", "d", "e"]))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_separability_check()
