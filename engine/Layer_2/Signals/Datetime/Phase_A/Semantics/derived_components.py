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
    """Identifies which datetime components carry meaningful variation for feature engineering."""
    
    parsed = pd.to_datetime(col, errors="coerce")
    valid = parsed.dropna()
    
    if len(valid) < 3:
        return {"n_useful_components": 0, "component_entropy": {}}
    
    component_entropy = {}
    
    for name, values in [("year", valid.dt.year), ("month", valid.dt.month),
                         ("day", valid.dt.day), ("hour", valid.dt.hour),
                         ("minute", valid.dt.minute), ("second", valid.dt.second),
                         ("dayofweek", valid.dt.dayofweek), ("quarter", valid.dt.quarter)]:
        vc = values.value_counts(normalize=True)
        # Shannon entropy normalized by max possible
        if len(vc) > 1:
            probs = vc.values
            ent = -np.sum(probs * np.log2(probs + 1e-12))
            max_ent = np.log2(len(vc))
            norm_ent = ent / max_ent if max_ent > 0 else 0.0
        else:
            norm_ent = 0.0
        component_entropy[name] = round(float(norm_ent), 4)
    
    # useful = components with normalized entropy > 0.3 (meaningful spread)
    n_useful = sum(1 for v in component_entropy.values() if v > 0.3)
    
    return {
        "n_useful_components": n_useful,
        "component_entropy": component_entropy,
        "total_components": len(component_entropy)
    }

def infer_signals(signals: Dict) -> Result:
    nuc = signals["n_useful_components"]
    tc = signals["total_components"]
    
    # score: fraction of components that are NOT useful
    score = 1.0 - (nuc / tc) if tc > 0 else 1.0
    
    flag = score > 0.8
    
    if score > 0.8:
        label = "CRITICAL"
    elif score > 0.5:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_derived_components",
        layer="semantics",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "n_useful_components": nuc,
            "total_components": tc
        }
    )


def run_derived_components_check():
    # data spanning multiple years, months, hours
    dates = pd.date_range("2020-01-01", periods=500, freq="7h")
    combined_signals = get_signals(pd.Series(dates))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_derived_components_check()
