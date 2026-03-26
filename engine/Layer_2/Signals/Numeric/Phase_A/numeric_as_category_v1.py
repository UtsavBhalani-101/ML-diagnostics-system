import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Dict



# * states (immutable)
@dataclass(frozen=True)
class Signals:
    cardinality_ratio: float = 0.0
    missing_ratio: float = 0.0
    dominance_ratio: float = 0.0
    gap_var: Optional[float] = None
    gap_mean: Optional[float] = None
    repeat_ratio: Optional[float] = None
    monotonicity: Optional[bool] = None
    


# ^ validate data
def validate_data(col: pd.Series):
    if not isinstance(col, pd.Series):
        raise ValueError("Provided data is not a column")
   
    
    
def get_monotonicity_signal(col: pd.Series):
    return {"monotonicity": col.is_monotonic_increasing}
    
    
    
def get_gap_signal(col: pd.Series) -> dict:
    numeric_col = pd.to_numeric(col, errors="coerce").dropna()
    if len(numeric_col) < 5:
        return None
    sorted_vals = np.sort(numeric_col.to_numpy())
    diffs = np.diff(sorted_vals)
    if len(diffs) == 0:
        return None
    return {"gap_var": float(np.var(diffs)), "gap_mean": float(np.mean(diffs))}



def get_repetation_signal(col)-> dict:
    col = pd.to_numeric(col, errors="coerce").dropna()
    
    if len(col) < 5:
        return None
    
    # measure how often consecutive values repeat
    repeats = (col.values[1:] == col.values[:-1]).mean()
    
    return {"repeat_ratio": repeats}  



def get_basic_signals(col: pd.Series)-> dict:
    col_str = col.astype(str).str.strip().str.lower()
    missing_tokens = {"na", "n/a", "null", "none", "unknown", "?", "-", ""}
    hidden_missing = col_str.isin(missing_tokens)
    total_missing = col.isna() | hidden_missing

    n = len(col)
    vc = col.value_counts(normalize=True, dropna=True) 

    return {
        "cardinality_ratio": float(col.nunique(dropna=True) / n) if n else 0.0,
        "missing_ratio": float(total_missing.mean()) if n else 1.0,
        "dominance_ratio": float(vc.iloc[0]) if len(vc) > 0 else 0.0,
    }



# * signal_registry
SIGNAL_REGISTRY = [
    get_basic_signals,
    get_gap_signal,
    get_repetation_signal,
    get_monotonicity_signal
]



# ^ aggregation function  
def build_signals(col: pd.Series) -> Signals:
    combined = {}

    for fn in SIGNAL_REGISTRY:
        result = fn(col)
        if result:
            combined.update(result)

    return Signals(**combined)



# ^ core logic
def infer_column_type(signals: Signals):
    # signals
    mr = signals.missing_ratio
    cr = signals.cardinality_ratio
    dr = signals.dominance_ratio
    gap_mean = signals.gap_mean
    gap_var = signals.gap_var
    rr = signals.repeat_ratio
    mono = signals.monotonicity

    # invariants - sparse, degenerate, continuous_numeric, categorical_numeric, id_like
    is_sparse = mr >= 0.6
    is_degenerate = dr >= 0.8
    is_low_cardinality = cr <= 0.2
    is_high_cardinality = cr >= 0.95
    is_constant_gap = gap_var is not None and gap_var <= 1e-6

    if is_sparse:
        return "sparse"
    if is_degenerate:
        return "degenerate"
    if is_low_cardinality:
        return "categorical_numeric"
    if cr > is_low_cardinality and cr < is_high_cardinality:
        if rr is not None and rr > 0.3:
            return "categorical_numeric"

    # Conservative ID rule: high cardinality + near-constant small step
    if is_high_cardinality and is_constant_gap and pd.notna(gap_mean) and gap_mean <= 2:
        return "id_like"

    return "continuous_numeric"
    


def main():
    validate_data(col)
    signal_info = build_signals(col)
    infer_column_type(signal_info)
    


if __name__ == "__main__":
    main()