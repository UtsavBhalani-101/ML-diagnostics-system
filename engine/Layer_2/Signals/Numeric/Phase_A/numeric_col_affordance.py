import numpy as np 
import pandas as pd 
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class Signals:
    pass

def get_signals(col: pd.Series):
    
    col_str = col.astype(str).str.strip().str.lower()
    
    MISSING_TOKENS = {"na","n/a","null","none","unknown","?","-",""}
    hidden_missing = col_str.isin(MISSING_TOKENS)
    
    total_missing = col.isna() | hidden_missing
    
    numeric_ratio = pd.to_numeric(col, errors='coerce').notna().mean()
    cardinality_ratio = col.nunique() / len(col)
    unique_count = col.nunique()
    missing_ratio = total_missing.mean()
    
    vc = col.value_counts(normalize=True, dropna=True)
    dominance_ratio = vc.iloc[0] if len(vc) > 0 else 0
    
    return {
        "numeric_ratio": numeric_ratio,
        "cardinality_ratio": cardinality_ratio,
        "unique_count": unique_count,
        "missing_ratio": missing_ratio,
        "dominance_ratio": dominance_ratio
    }

def test_col_affordance(signals: dict):
    nr = signals['numeric_ratio']
    cr = signals['cardinality_ratio']
    dr = signals['dominance_ratio']
    mr = signals['missing_ratio']
    count = signals['unique_count']
    
    numeric = False
    binary = False
    id_like = False
    categorical_numeric = False
    datetime = False
    corrupted = False
    
    # binary
    if count == 2:
        binary = True
    
    # 1. Sparse column
    if mr > 0.8:
        corrupted = True
    
    # 2. Mostly numeric
    if nr > 0.9:
        
        if cr > 0.9:
            id_like = True
        
        if cr < 0.05:
            categorical_numeric = True
        
        if dr > 0.95:
            return "degenerate"
        
        numeric = True
    
    # 3. Mixed / corrupted numeric
    if 0.5 < nr <= 0.9:
        corrupted = True
    
    # 4. Categorical
    categorical_numeric = True
    
    return {
    'numeric' :numeric,
    'binary' : binary,
    'id_like' : id_like,
    'categorical_numeric' : categorical_numeric,
    'datetime' : datetime,
    'corrupted' : corrupted
    }
