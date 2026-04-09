import numpy as np 
import pandas as pd 
from dataclasses import dataclass
from typing import List, Optional, Dict


# * states (immutable)
@dataclass(frozen=True)
class Signals:
    numeric_ratio: float = 0.0
    cardinality_ratio: float = 0.0
    unique_count: int = 0
    dominance_ratio: float = 0.0
    missing_ratio: Optional[float] = 0.0
    
   
# ^ validating data   
def validate_data(col: pd.Series):
    if not isinstance(col, pd.Series):
        return ValueError("provided Data is not series")


# ^ validating signals -- used as guards
def get_validity_signals(col: pd.Series) -> dict:
    if len(col) == 0:
        return {
            "numeric_ratio": 0.0,
            "missing_ratio": 1.0
        }

    # normalize for hidden missing
    col_str = col.astype(str).str.strip().str.lower()
    missing_tokens = {"na", "n/a", "null", "none", "unknown", "?", "-", ""}

    hidden_missing = col_str.isin(missing_tokens)
    total_missing = col.isna() | hidden_missing

    # numeric consistency
    numeric = pd.to_numeric(col, errors='coerce')
    numeric_ratio = numeric.notna().mean()

    # missing
    missing_ratio = total_missing.mean()

    return {
        "numeric_ratio": float(numeric_ratio),
        "missing_ratio": float(missing_ratio)
    }



# ^ capability signals -- used for affordance 
def get_capability_signals(col: pd.Series) -> dict:
    if len(col) == 0:
        return {
            "cardinality_ratio": 0.0,
            "dominance_ratio": 0.0,
            "unique_count": 0
        }

    # normalize for missing
    col_str = col.astype(str).str.strip().str.lower()
    missing_tokens = {"na", "n/a", "null", "none", "unknown", "?", "-", ""}

    hidden_missing = col_str.isin(missing_tokens)
    total_missing = col.isna() | hidden_missing

    valid_mask = ~total_missing
    clean_col = col[valid_mask]

    valid_count = len(clean_col)

    if valid_count == 0:
        return {
            "cardinality_ratio": 0.0,
            "dominance_ratio": 0.0,
            "unique_count": 0
        }

    unique_count = clean_col.nunique()
    cardinality_ratio = unique_count / valid_count

    vc = clean_col.value_counts(normalize=True)
    dominance_ratio = vc.iloc[0]

    return {
        "cardinality_ratio": float(cardinality_ratio),
        "dominance_ratio": float(dominance_ratio),
        "unique_count": int(unique_count)
    }    

# ^ gating logic to block or allow cols
def gate_numeric_column(validity: dict) -> dict:
    nr = validity["numeric_ratio"]
    mr = validity["missing_ratio"]

    issues = []
    proceed = True

    # ---- Hard gate: not numeric enough ----
    if nr < 0.8:
        proceed = False
        issues.append("not_numeric")

    # ---- Extreme case: almost entirely missing ----
    if mr > 0.95:
        proceed = False
        issues.append("almost_all_missing")

    return {
        "proceed": proceed,
        "issues": issues
    }


SIGNAL_REGISTRY = [
    get_validity_signals,
    get_capability_signals
]

# * aggregating all the signals
def build_signals(col: pd.Series) -> Signals:
    combined = {}
    
    for fn in SIGNAL_REGISTRY:
        result = fn(col)
        if result:
            combined.update(result)
            
    return Signals(**combined)



def main():
    validate_data(col)
    validity = get_validity_signals(col)

    gate = gate_numeric_column(validity)

    if not gate["proceed"]:
        return {
            "affordance": None,
            "issues": gate["issues"]
        }

    signals = build_signals(col)
    

if __name__ == "__main__":
    main()
