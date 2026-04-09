import re
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
    
    

ORDINAL_KEYWORDS = {
    "low", "medium", "high", "med",
    "small", "large", "xl", "xs",
    "poor", "fair", "good", "excellent",
    "never", "rarely", "sometimes", "often", "always",
    "mild", "moderate", "severe",
    "beginner", "intermediate", "advanced", "expert"
}

def get_signals(col: pd.Series) -> dict:
    clean = col.dropna().astype(str).str.strip()
    
    if len(clean) == 0:
        return {"numeric_label_ratio": 0.0, "sequential_score": 0.0, "ordinal_keyword_ratio": 0.0}
    
    labels = clean.unique()
    labels_lower = [l.lower() for l in labels]
    n_labels = len(labels)
    
    if n_labels == 0:
        return {"numeric_label_ratio": 0.0, "sequential_score": 0.0, "ordinal_keyword_ratio": 0.0}
    
    # 1. numeric label ratio: fraction of categories containing digits
    digit_pattern = re.compile(r'\d+')
    numeric_labels = [l for l in labels if digit_pattern.search(l)]
    numeric_label_ratio = len(numeric_labels) / n_labels
    
    # 2. sequential score: if extracted numbers form a sequential pattern
    sequential_score = 0.0
    if len(numeric_labels) >= 3:
        extracted_nums = []
        for l in numeric_labels:
            m = digit_pattern.search(l)
            if m:
                extracted_nums.append(int(m.group()))
        
        if len(extracted_nums) >= 3:
            sorted_nums = sorted(extracted_nums)
            diffs = np.diff(sorted_nums)
            if len(diffs) > 0 and np.std(diffs) < np.mean(diffs) * 0.5:
                sequential_score = 1.0
            elif len(diffs) > 0:
                sequential_score = 0.5
    
    # 3. ordinal keyword match
    keyword_hits = sum(1 for l in labels_lower if l in ORDINAL_KEYWORDS)
    ordinal_keyword_ratio = keyword_hits / n_labels
    
    return {
        "numeric_label_ratio": float(numeric_label_ratio),
        "sequential_score": float(sequential_score),
        "ordinal_keyword_ratio": float(ordinal_keyword_ratio)
    }

def infer_signals(signals: Dict) -> Result:
    nlr = signals["numeric_label_ratio"]
    ss = signals["sequential_score"]
    okr = signals["ordinal_keyword_ratio"]
    
    # weighted combination
    score = 0.3 * nlr + 0.3 * ss + 0.4 * okr
    
    flag = score > 0.7
    
    if score > 0.7:
        label = "CRITICAL"
    elif score > 0.4:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="categorical_is_ordinal",
        layer="semantics",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "numeric_label_ratio": round(nlr, 4),
            "sequential_score": round(ss, 4),
            "ordinal_keyword_ratio": round(okr, 4)
        }
    )


def run_is_ordinal_check():
    # clearly ordinal series
    combined_signals = get_signals(pd.Series(["low", "medium", "high", "low", "high"]))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_is_ordinal_check()
