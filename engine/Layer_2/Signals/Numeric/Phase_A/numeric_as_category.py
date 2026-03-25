import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class TestResult:
    column_name: str
    inferred_type: str
  

def validate_data(col: pd.Series):
    if not isinstance(col, pd.Series):
        raise ValueError("Provided data is not a column")
    
    
def get_signals(col: pd.Series):
    
    col_str = col.astype(str).str.strip().str.lower()
    
    MISSING_TOKENS = {"na","n/a","null","none","unknown","?","-",""}
    hidden_missing = col_str.isin(MISSING_TOKENS)
    
    total_missing = col.isna() | hidden_missing
    
    cardinality_ratio = col.nunique() / len(col)
    missing_ratio = total_missing.mean()
    
    vc = col.value_counts(normalize=True, dropna=True)
    dominance_ratio = vc.iloc[0] if len(vc) > 0 else 0
    
    return {
        "cardinality_ratio": cardinality_ratio,
        "missing_ratio": missing_ratio,
        "dominance_ratio": dominance_ratio
    }

def infer_column_type(signals):
    
    cr = data['cardinality_ratio']
    mr = data['missing_ratio']
    dr = data['dominance_ratio']
    
    is_sparse = False
    is_continous = False
    is_categorical = False
    is_corrupted = False
    is_id_like = False
    is_degenerate = False
    
    is_sparse = mr > 0.8
    is_corrupted = mr > 0
    is_degenerate = dr > 0.9
    is_low_cardinality = cr < 0.2
    is_high_cardinality = cr > 0.95
    is_constant_gap = gap_var < 1e-6

    if is_sparse:
        return "sparse"
    
    if is_corrupted:
        return "corrupted"

    if is_degenerate:
        return "degenerate"

    if is_high_cardinality and is_constant_gap:
        return "id_like"

    if is_high_cardinality:
        return "continuous_numeric"

    if is_low_cardinality:
        return "categorical_numeric"

    return "continuous_numeric"
    

def main():
    pass

if __name__ == "__main__":
    main()