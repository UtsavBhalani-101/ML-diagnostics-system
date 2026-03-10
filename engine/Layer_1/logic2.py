import numpy as np
import pandas as pd

def validate_data(signals: dict):
    if not isinstance(signals, dict):
        raise ValueError("The data is not in Dict")
    
    items = ["rows", "cols", "global_missing_ratio", "column_missing_ratio", "duplicate_ratio", "constant_columns",
             "constant_ratio", "hidden_missing_ratio", "mixed_type_columns", "mixed_ratio"]

    if items not in signals:
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

    return {
        "test": "dataset_size",
        "status": status,
        "message": message,
        "affected_columns": None,
        "metrics": {
            "rows": rows,
            "cols": cols
        }
    }
        

def test_global_missing():
    pass


def test_column_missing():
    pass

def test_duplicates():
    pass

def test_constant_columns():
    pass


def test_mixed_columns():
    pass


def test_hidden_missing():
    pass

def main():
    
    validate_data(signals)
    
    test_dataset_size()
    test_global_missing()
    test_column_missing()
    test_duplicates()
    test_constant_columns()
    test_mixed_columns()
    test_hidden_missing()
    
    