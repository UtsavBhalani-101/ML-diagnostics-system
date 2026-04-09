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
    vc = col.value_counts(normalize=True)
    
    max_ratio = vc.iloc[0]
    
    return {"max_ratio" : max_ratio}

def infer_signals(signals: Dict) -> Result:
    mr = signals["max_ratio"]
    score = mr
    
    flag = mr > 0.8
    
    if mr > 0.8:
        label = "CRITICAL"
    elif mr > 0.4:
        label = "WARNING"

    else: 
        label = "SAFE"    
    
    return Result(
        test_name="categorical_imbalance",
        layer="usability",
        score=score,
        label=label,
        flag=flag,
        meta={"max_ratio" : mr}
    )


def run_imbalance_check():
    combined_signals = get_signals(pd.Series([1,2,3,4,5]))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))
    
if __name__ == "__main__":
    run_imbalance_check()