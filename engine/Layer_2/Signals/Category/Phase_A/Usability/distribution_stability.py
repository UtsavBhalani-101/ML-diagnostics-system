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
        return {"gini": 0.0, "top3_concentration": 0.0}
    
    vc = clean.value_counts(normalize=True)
    
    if len(vc) <= 1:
        return {"gini": 1.0, "top3_concentration": 1.0}
    
    # gini coefficient: measures inequality of distribution
    freqs = np.sort(vc.values)
    n = len(freqs)
    index = np.arange(1, n + 1)
    gini = (2 * np.sum(index * freqs) - (n + 1) * np.sum(freqs)) / (n * np.sum(freqs))
    
    # top-3 concentration: share held by top 3 categories
    top3_concentration = float(vc.iloc[:3].sum())
    
    return {
        "gini": float(gini),
        "top3_concentration": top3_concentration
    }

def infer_signals(signals: Dict) -> Result:
    gini = signals["gini"]
    t3c = signals["top3_concentration"]
    
    score = gini
    
    flag = score > 0.8
    
    if score > 0.8:
        label = "CRITICAL"
    elif score > 0.5:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="categorical_distribution_stability",
        layer="usability",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "gini": round(gini, 4),
            "top3_concentration": round(t3c, 4)
        }
    )


def run_distribution_stability_check():
    # highly unequal distribution
    data = ["dominant"] * 90 + ["minor_a"] * 7 + ["minor_b"] * 2 + ["minor_c"] * 1
    combined_signals = get_signals(pd.Series(data))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_distribution_stability_check()
