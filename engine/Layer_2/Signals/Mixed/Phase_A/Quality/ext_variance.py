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
    """Detects extreme variance differences across categorical groups in a numeric column."""
    
    valid_mask = numeric_col.notna() & cat_col.notna()
    num_valid = numeric_col[valid_mask]
    cat_valid = cat_col[valid_mask].astype(str).str.strip().str.lower()
    
    if len(num_valid) < 5 or cat_valid.nunique() < 2:
        return {"variance_ratio_max": 0.0, "n_groups": 0, "max_var_group": ""}
    
    grouped = num_valid.groupby(cat_valid)
    group_vars = grouped.var().dropna()
    
    if len(group_vars) < 2 or group_vars.min() == 0:
        return {"variance_ratio_max": 0.0, "n_groups": int(cat_valid.nunique()), "max_var_group": ""}
    
    # ratio of largest to smallest group variance
    variance_ratio_max = float(group_vars.max() / group_vars.min())
    max_var_group = str(group_vars.idxmax())
    min_var_group = str(group_vars.idxmin())
    
    return {
        "variance_ratio_max": variance_ratio_max,
        "n_groups": int(cat_valid.nunique()),
        "max_var_group": max_var_group,
        "min_var_group": min_var_group
    }

def infer_signals(signals: Dict) -> Result:
    vrm = signals["variance_ratio_max"]
    
    # normalize: log-scale since variance ratios can be huge
    # score in [0, 1]: log10(ratio) / log10(threshold_extreme)
    if vrm <= 1:
        score = 0.0
    else:
        score = min(1.0, np.log10(vrm) / np.log10(100))  # 100x ratio = score 1.0
    
    flag = score > 0.7
    
    if score > 0.7:
        label = "CRITICAL"
    elif score > 0.4:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="mixed_extreme_variance",
        layer="quality",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "variance_ratio_max": round(vrm, 4),
            "n_groups": signals["n_groups"]
        }
    )


def run_ext_variance_check():
    # group A: tight, group B: very spread out
    cat = pd.Series(["stable"] * 50 + ["volatile"] * 50)
    num = pd.Series(
        np.concatenate([np.random.normal(50, 1, 50),
                        np.random.normal(50, 30, 50)])
    )
    combined_signals = get_signals(num, cat)
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_ext_variance_check()
