import numpy as np 
import pandas as pd 
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass(frozen=True)
class Signals:
    # unique_ratio: float
    dominance_ratio: float
    resolution: float
    entropy: float
    low_sample: Optional[bool]



@dataclass(frozen=True)
class Result:
    label: str
    risk_score: float
    reason: str
    signals: Dict[str, float]

def validate_data(col: pd.Series):
    pass



# ^ get entropy
def get_entropy(col: pd.Series) -> dict:
    probs = col.value_counts(normalize=True)

    # Handle constant case explicitly
    if len(probs) <= 1:
        return {"entropy": 0.0}

    entropy = -(probs * np.log2(probs)).sum()

    max_entropy = np.log2(len(probs))
    normalized_entropy = entropy / max_entropy

    return {"entropy": float(normalized_entropy)}
    
    


# ^ get resolution
def get_resoluion(col: pd.Series) -> dict:
    col = col.dropna()

    if len(col) < 2:
        return {"resolution": 0.0}

    diffs = np.diff(np.sort(col))

    # ignore zero diffs
    diffs = diffs[diffs > 0]

    if len(diffs) == 0:
        return {"resolution": 0.0}

    min_diff = np.min(diffs)
    scale = np.abs(col.mean()) + 1e-8

    return {"resolution":  float(min_diff / scale) }



# ^ get basic signals 
def get_basic_signals(col: pd.Series) -> dict:

    col = col.dropna()
    n = col.shape[0]
    low_sample = False

    if n == 0:
        return {
            # "unique_ratio" : 0.0,
            "dominance_ratio": 0.0,
            "low_sample": False
        }
        
    if n < 5:
        low_sample = True
        
    #  Constant gate
    if col.nunique() == 1: 
        return {
            # "unique_ratio" : 0.0,
            "dominance_ratio": 1.0,
            "low_sample": False
        }

    range_ = col.max() - col.min()

    unique_ratio = col.nunique() / n
    dominance_ratio = col.value_counts().max() / n

    return {
        # "unique_ratio": unique_ratio,
        "dominance_ratio": dominance_ratio,
        "low_sample" : low_sample
    }



SIGNAL_REGISTRY = [
    get_basic_signals,
    get_entropy,
    get_resoluion
]



# * aggregation signals
def build_signals(col: pd.Series) -> Signals:
    combined = {}
    
    for fn in SIGNAL_REGISTRY:
        result = fn(col)
        if result:
            combined.update(result)
            
    return Signals(**combined)




# * logic    
def compute_naive_risk(signals):
    dr = signals.dominance_ratio            # already risk
    entropy_risk = 1 - signals.entropy
    resolution_risk = 1 - min(1, signals.resolution)

    return dr, entropy_risk, resolution_risk

def naive_risk_score(signals):
    
    dr, er, rr = compute_naive_risk(signals)

    risk = max(
        1.0*dr + 0.3*er,   # general risk
        0.6*rr             # resolution override
    )

    risk = min(1.0, risk)

    if signals.low_sample:
        label = "CRITICAL"
        risk = 1.0
    if risk >= 0.75:
        label = "CRITICAL"
    elif risk > 0.5:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return Result(
        label=label,
        risk_score=risk,
        reason="",
        signals={
            "dominance_ratio" : dr,
            "entropy" : signals.entropy,
            "resolution" : signals.resolution
        }
    )
    
    
def run_usability_no_variation():
    # Example
    col = pd.Series([5,5,5,5,7])

    combined_signals = build_signals(col)
    print(combined_signals)
    
    naive_risk_score(combined_signals)
    
    


if __name__ == "__main__":
    run_usability_no_variation()