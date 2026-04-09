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
    clean = col.dropna().astype(str)
    
    if len(clean) == 0:
        return {"case_collision_ratio": 0.0, "whitespace_collision_ratio": 0.0, "duplicate_pair_count": 0}
    
    raw_unique = clean.nunique()
    
    if raw_unique <= 1:
        return {"case_collision_ratio": 0.0, "whitespace_collision_ratio": 0.0, "duplicate_pair_count": 0}
    
    # case collisions: categories that merge when lowercased
    lower_unique = clean.str.lower().nunique()
    case_collisions = raw_unique - lower_unique
    case_collision_ratio = case_collisions / raw_unique
    
    # whitespace collisions: categories that merge when stripped
    stripped_unique = clean.str.strip().nunique()
    whitespace_collisions = raw_unique - stripped_unique
    whitespace_collision_ratio = whitespace_collisions / raw_unique
    
    # total duplicate pairs (combined effect)
    fully_normalized_unique = clean.str.strip().str.lower().nunique()
    duplicate_pair_count = raw_unique - fully_normalized_unique
    
    return {
        "case_collision_ratio": float(case_collision_ratio),
        "whitespace_collision_ratio": float(whitespace_collision_ratio),
        "duplicate_pair_count": int(duplicate_pair_count)
    }

def infer_signals(signals: Dict) -> Result:
    ccr = signals["case_collision_ratio"]
    wcr = signals["whitespace_collision_ratio"]
    dpc = signals["duplicate_pair_count"]
    
    score = max(ccr, wcr)
    
    flag = score > 0.3
    
    if score > 0.3:
        label = "CRITICAL"
    elif score > 0.1:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="categorical_duplicated_categories",
        layer="quality",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "case_collision_ratio": round(ccr, 4),
            "whitespace_collision_ratio": round(wcr, 4),
            "duplicate_pair_count": dpc
        }
    )


def run_duplicated_categories_check():
    # series with case/whitespace duplicates
    combined_signals = get_signals(pd.Series(["Cat", "cat", "CAT", " dog", "dog", "bird"]))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_duplicated_categories_check()
