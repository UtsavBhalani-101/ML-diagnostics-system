import numpy as np 
import pandas as pd 
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass(frozen=True)
class Signals:
    unique_ratio: float
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
    entropy =  -(probs * np.log2(probs + 1e-8)).sum()
    
    max_entropy = np.log2(len(col.unique()))
    normalized_entropy = entropy / (max_entropy + 1e-8)
    return {"entropy": normalized_entropy}
    
    


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
            "unique_ratio" : 0.0,
            "dominance_ratio": 0.0,
            "low_sample": False
        }
        
    if n < 5:
        low_sample = True
        
    #  Constant gate
    if col.nunique() == 1: 
        return {
            "unique_ratio" : 0.0,
            "dominance_ratio": 1.0,
            "low_sample": False
        }

    range_ = col.max() - col.min()

    unique_ratio = col.nunique() / n
    dominance_ratio = col.value_counts().max() / n

    return {
        "unique_ratio": unique_ratio,
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
def infer_signals(signals: Signals):
    ur = signals.unique_ratio
    dr = signals.dominance_ratio
    res = signals.resolution
    nr = signals.entropy
    low_sample = signals.low_sample

    risk = 0.0
    reasons = []

    high_dr = dr > 0.75
    moderate_dr = dr > 0.55

    low_ur = ur < 0.3

    low_entropy = nr < 0.3

    low_res = res < 0.1
    very_low_res = res < 0.01

    if low_sample:
        label = "CRITICAL"
        reasons.append("sample count is too low")

    if high_dr or very_low_res:
        label = "CRITICAL"
        if high_dr:
            reasons.append("high dominance")
        if very_low_res:
            reasons.append("very low spread")

    elif moderate_dr:
        label = "WARNING"
        reasons.append("moderate dominance")

    elif low_entropy:
        label = "WARNING"
        reasons.append("low entropy")

    elif low_res or low_ur or (low_ur and low_res):
        label = "WARNING"
        if low_res:
            reasons.append("low spread")
        if low_ur:
            reasons.append("low unique values")

    else:
        label = "SAFE"
        reasons.append("no problems")


    return Result(
        label=label,
        risk_score=risk,
        reason="; ".join(reasons),
        signals={
            "unique_ratio": ur,
            "dominance_ratio": dr,
            "resolution": res,
            "entropy": nr
        },
    )
    
    
def run_usability_no_variation():
    # Example
    # col = pd.Series([5,5,5,5,5,5])

    combined_signals = build_signals(col)
    infer_signals(combined_signals)
    


if __name__ == "__main__":
    run_usability_no_variation()