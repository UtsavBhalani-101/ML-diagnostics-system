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
    


def get_signals(numeric_col: pd.Series, cat_col: pd.Series) -> dict:
    """Checks whether combining a numeric and categorical column yields useful interaction signal."""
    
    valid_mask = numeric_col.notna() & cat_col.notna()
    num_valid = numeric_col[valid_mask]
    cat_valid = cat_col[valid_mask].astype(str).str.strip().str.lower()
    
    if len(num_valid) < 5 or cat_valid.nunique() < 2:
        return {"interaction_strength": 0.0, "variance_ratio": 0.0, "n_groups": 0}
    
    # per-group coefficient of variation spread
    grouped = num_valid.groupby(cat_valid)
    group_stds = grouped.std().dropna()
    group_means = grouped.mean()
    
    # coefficient of variation per group
    cv_per_group = (group_stds / group_means.abs().replace(0, np.nan)).dropna()
    
    if len(cv_per_group) < 2:
        return {"interaction_strength": 0.0, "variance_ratio": 0.0, "n_groups": int(cat_valid.nunique())}
    
    # if groups have very different CVs, the interaction is meaningful
    cv_spread = float(cv_per_group.std())
    
    # variance ratio: within-group variance vs overall
    overall_var = float(num_valid.var())
    within_var = float(grouped.var().mean()) if overall_var > 0 else 0.0
    variance_ratio = within_var / overall_var if overall_var > 0 else 1.0
    
    # interaction strength: categories modulate the numeric distribution differently
    interaction_strength = 1.0 - variance_ratio
    
    return {
        "interaction_strength": float(max(0, interaction_strength)),
        "variance_ratio": float(variance_ratio),
        "cv_spread": round(cv_spread, 4),
        "n_groups": int(cat_valid.nunique())
    }

def infer_signals(signals: Dict) -> Result:
    ist = signals["interaction_strength"]
    
    # low interaction → combining these columns adds nothing
    score = 1.0 - ist
    
    flag = score > 0.9
    
    if score > 0.9:
        label = "CRITICAL"
    elif score > 0.7:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="mixed_interaction_usefulness",
        layer="affordance",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "interaction_strength": round(ist, 4),
            "variance_ratio": round(signals["variance_ratio"], 4)
        }
    )


def run_interaction_usefulness_check():
    cat = pd.Series(["A"] * 40 + ["B"] * 40)
    num = pd.Series(
        np.concatenate([np.random.normal(100, 5, 40),
                        np.random.normal(100, 50, 40)])
    )
    combined_signals = get_signals(num, cat)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_interaction_usefulness_check()
