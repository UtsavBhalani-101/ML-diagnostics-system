import numpy as np 
import pandas as pd 
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class Signals:
    pass

def validate_data(col: pd.Series):
    if not isinstance(col, pd.Series):
        return ValueError("provided Data is not series")
    
def get_signals(col: pd.Series) -> dict:
    numeric_ratio = pd.to_numeric(col, errors='coerce').sum() / len(col)
    
    missing_tokens = {"na", "n/a", "null", "none", "unknown", "?", "-", ""}
    hidden_missing = col.isin(missing_tokens)
    total_missing = col.isna() | hidden_missing
    
    unique_count = col.nunique(dropna=True)
    cardinality_ratio = unique_count / len(col)
    dominance_ratio = col.value_counts().max() / len(col)
    
    missing_tokens = {"na", "n/a", "null", "none", "unknown", "?", "-", ""}
    
    missing_ratio = total_missing.mean()
    
    return {
        "missing_ratio" : missing_ratio,
        "cardinality_ratio" : cardinality_ratio,
        "dominance_ratio" : dominance_ratio,
        "unique_count" : unique_count
    }
    
def score_cardinality(cr):
    return {
        "id_numeric": cr * 3,
        "continuous_numeric": cr * 2,
        "categorical_numeric": (1 - cr) * 3,
        "binary_numeric": (1 - cr) * 2
    }

def score_dominance(dr):
    return {
        "categorical_numeric": dr * 4,
        "binary_numeric": dr * 2,
        "continuous_numeric": -dr * 2,
        "id_numeric": -dr * 3
    }
    
def generate_hypothesis(signals):
    cr = signals['cardinality_ratio']
    dr = signals['dominance_ratio']
    
    hypotheses = [
        "continuous_numeric",
        "categorical_numeric",
        "binary_numeric",
        "id_numeric"
    ]
    
    scores = {h: 0 for h in hypotheses}
    
    # apply cardinality
    cr_scores = score_cardinality(cr)
    for h in hypotheses:
        scores[h] += cr_scores[h]
    
    # apply dominance
    dr_scores = score_dominance(dr)
    for h in hypotheses:
        scores[h] += dr_scores[h]

        # shift scores to be positive
    min_score = min(scores.values())
    if min_score < 0:
        scores = {k: v - min_score for k, v in scores.items()}
    
    total = sum(scores.values()) or 1
    probs = {k: v / total for k, v in scores.items()}

    sorted_scores = sorted(probs.items(), key=lambda x: x[1], reverse=True)

    gap = sorted_scores[0][1] - sorted_scores[1][1]
    ambiguous = gap < 0.15
    
    return {
        "scores": scores,
        "probs": probs,
        "primary": sorted_scores[0][0],
        "ambiguous": ambiguous
    }

def score_hypothesis():
    pass

def normalize():
    pass

