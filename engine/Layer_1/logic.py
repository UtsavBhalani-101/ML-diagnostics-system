import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Dict

# * the signals coming are raw data, can't be used directly for decision making
# * and some signals are column level, each col have different signal -- for layer 1 we detect structural issues
# * structural issues are global level 
# * so for multiple signals - aggregated (combined to one value) and then decided 
# * signal -> aggregate (if needed) -> decision -> result

@dataclass
class TestResult:
    test: str
    status: str
    message: str
    affected_columns: Optional[List[str]] = None
    metrics: Optional[Dict] = None

def validate_data(signals: dict):
    if not isinstance(signals, dict):
        raise ValueError("The data is not in Dict")
    
    items = ["rows", "cols", "global_missing_ratio", "column_missing_ratio", "duplicate_ratio", "constant_columns",
             "constant_ratio", "hidden_missing_ratio", "mixed_type_columns", "mixed_ratio"]

    for item in items:
        if item not in signals:
            raise ValueError("The data is corrupted")
        
    
def test_dataset_size(signals: dict):
    """Check whether dataset size is structurally adequate."""

    rows = signals["rows"]
    cols = signals["cols"]

    if rows < cols:
        status = "WARNING"
        message = "Dataset has fewer rows than columns; high dimensional structure may cause unstable analysis."

    elif rows < 50:
        status = "CRITICAL"
        message = "Dataset contains extremely few samples; structural reliability is very low."

    elif rows < 500:
        status = "WARNING"
        message = "Dataset has relatively few samples; statistical estimates may be unstable."

    else:
        status = "SAFE"
        message = "Dataset size appears structurally adequate."

    return TestResult(
        test="dataset_size",
        status=status,
        message=message,
        affected_columns=None,
        metrics={"rows": rows}
    )
        

def test_global_missing(signals: dict):
    ratio = signals['global_missing_ratio']
    percent = ratio * 100
    
    if percent <= 5:
        status = "SAFE"
        message = "Dataset's missingness can be fixed with imputation"
    elif percent <= 15:
        status = "WARNING"
        message = "Dataset's has moderate missingness, imputation may be unreliable"
    else:
        status = "CRITICAL"
        message = "Dataset missingness is extreme, statistical measurements are unreliable"
        
    return TestResult(
        test="global_missing",
        status=status,
        message=message,
        affected_columns=None,
        metrics={"global_missing_ratio" : ratio}
    )


def test_column_missing(signals : dict):
    data = signals['column_missing_ratio']
    
    if len(data) != 0:
    
        max_missing = max(data.values())
        col = next((k for k, v in data.items() if v == max_missing), None)
        
        percent = max_missing * 100
        
        if percent <= 5:
            status = "SAFE"
            message = "Column missingness is low, can be fixed with imputation"
                    
        elif percent <= 15:
            status = "WARNING"
            message = "Column missingness is moderate, only imputation would be unreliable"
            
        else:
            status = "CRITICAL"
            message = "Column missingness is high, statistical metrics are unreliable"
            
    return TestResult(
        test="column_missing",
        status=status,
        message=message,
        affected_columns=col,
        metrics={"column_missing_ratio" : max_missing}
    )

def test_duplicates(signals : dict):
    ratio = signals["duplicate_ratio"]
    percent = ratio * 100
    
    if percent <= 1:
        status = "SAFE"
        message = "Dataset's duplicates can be safely removed without too much data loss"
    elif percent <= 5:
        status = "WARNING"
        message = "Dataset's has moderate duplicates, removing may thin the data"
    else:
        status = "CRITICAL"
        message = "Dataset duplicates is extreme, removing will reduce significant portion of data"
        
    return TestResult(
        test="duplicates",
        status=status,
        message=message,
        affected_columns=None,
        metrics={"duplicates_ratio" : ratio}
    )
   
def test_constant_columns(signals : dict):
    cols = signals["constant_columns"]
    ratio = signals["constant_ratio"]
    
    if ratio != 0:
        percent = ratio * 100
        
        if percent > 30:
            status = "CRITICAL"
            message = "Constant cols exists, "
        elif percent > 0:
            status = "WARNING"
            message = "Constant cols exists, "
            
    else:
        status = "SAFE"
        message = "No constant columns detected"
    
    return TestResult(
        test="constant_columns",
        status=status,
        message=message,
        affected_columns=[cols],
        metrics={"constant_columns_ratio" : ratio}
    )

def test_mixed_columns(signals : dict):
    cols = signals["mixed_type_columns"]
    ratio = signals["mixed_ratio"]

    if ratio != 0:
        percent = ratio * 100
        
        if percent > 20:
            status = "CRITICAL"
            message = "Mixed cols exists, "
        elif percent > 0:
            status = "WARNING"
            message = "Mixed cols exists, "
    
    return TestResult(
        test="mixed_column",
        status=status,
        message=message,
        affected_columns=[cols],
        metrics={"mixed_column_ratio" : ratio}
    )
    
    
def test_hidden_missing(signals : dict):
    data = signals["hidden_missing_ratio"]
    
    max_missing = max(data.values())
    col = next((k for k, v in data.items() if v == max_missing), None)
    
    if max_missing != 0:
        percent = max_missing * 100
        
        if percent > 20:
            status = "CRITICAL"
            message = "hidden missing values exists, "
        elif percent > 0:
            status = "WARNING"
            message = "hidden missing values exists, "
            
    else:
        status = "SAFE"
        message = "No hidden missing values detected"
            
    return TestResult(
        test="hidden_missing",
        status=status,
        message=message,
        affected_columns=col,
        metrics={"hidden_missing_ratio" : max_missing}
    )

def main():
    
    validate_data(signals)
    
    print(test_dataset_size(signals))
    print(test_global_missing(signals))
    print(test_column_missing(signals))
    print(test_duplicates(signals))
    print(test_constant_columns(signals))
    print(test_mixed_columns(signals))
    print(test_hidden_missing(signals))
    
if __name__ == "__main__":
    main()