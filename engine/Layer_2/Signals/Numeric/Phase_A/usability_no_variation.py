import numpy as np 
import pandas as pd 
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass(frozen=True)
class Signals:
    unique_ratio: float
    dominance_ratio: float
    spread: float

class Result:
    pass

def validate_data():
    pass

def get_signals(col: pd.Series):

    if col.nunique() == 1:
        return Signals (0.0, 1.0, 0.0)
    
    
    

    range_ = max(col) - min(col)
    n = col.shape[0]

    unique_ratio = col.nunique() / n
    
    dominance_ratio = col.value_counts().max() / n
    
    q75 = np.percentile(col, 75)
    q25 = np.percentile(col, 25)
    iqr = q75 - q25

    spread = iqr / (range_ + 1e-8)
        
    return Signals(
        unique_ratio=unique_ratio,
        dominance_ratio=dominance_ratio,
        spread=spread
    )

def infer_signals(signals: Signals):
    ur = signals.unique_ratio
    dr = signals.dominance_ratio
    sp = signals.spread

    reasons = []

    variation_score = (ur + (1 - dr) + sp) / 3

    if ur < 0.1:
        reasons.append(f"low unique ratio ({ur:.2f})")

    if dr > 0.9:
        reasons.append(f"high dominance ({dr:.2f})")

    if sp < 0.1:
        reasons.append(f"low spread ({sp:.2f})")

    # Label
    if variation_score < 0.2:
        label = "CRITICAL"
    elif variation_score < 0.4:
        label = "WARNING"
    else:
        label = "SAFE"

    return {
        "variation_score": variation_score,
        "label": label,
        "reasons": reasons,
        "signals": signals
    }
    