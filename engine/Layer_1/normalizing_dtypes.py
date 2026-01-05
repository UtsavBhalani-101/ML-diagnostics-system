import os
import pandas as pd
import numpy as np

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def normalize_tabular_dtypes(df: pd.DataFrame, max_loss_ratio=0.05, cat_threshold=0.3):
    df = df.copy()
    report = {
        "upgraded_to_nullable": [],
        "converted_to_numeric": [],
        "converted_to_category": [],
        "dropped_high_sparsity": []
    }
    
    total_rows = len(df)
    if total_rows == 0:
        return df, report

    # 1. PRE-PROCESS: Global Nullable Upgrade
    # This turns int64 -> Int64 and float64 -> Float64 automatically.
    # It ensures 'NaN' doesn't force integers into floats.
    df = df.convert_dtypes()
    report["upgraded_to_nullable"] = list(df.columns)

    # 2. ITERATE: Object/String Columns
    object_cols = list(df.select_dtypes(include=['object', 'string']).columns)

    for col in object_cols:
        # Check Sparsity first (Production logic: don't process garbage)
        sparsity = df[col].isna().mean()
        if sparsity > 0.8:  # Example: 80% missing
            # In a real engine, you might drop this or flag it
            report["dropped_high_sparsity"].append(col)
            continue

        # --- Attempt 1: Numeric Conversion ---
        # We use the 'downcast' parameter to save memory (e.g., int64 -> int8)
        converted = pd.to_numeric(df[col], errors="coerce")
        
        original_nan = df[col].isna().sum()
        new_nan = converted.isna().sum()
        loss_ratio = (new_nan - original_nan) / total_rows

        if loss_ratio <= max_loss_ratio and new_nan < total_rows:
            # Force conversion back to Nullable Integer if it's whole numbers
            # This is the key "Production" fix you were looking for
            df[col] = converted.convert_dtypes() 
            report["converted_to_numeric"].append(f"{col} ({df[col].dtype})")
            continue

        # --- Attempt 2: Categorical Conversion ---
        n_unique = df[col].nunique()
        cardinality_ratio = n_unique / total_rows

        if cardinality_ratio < cat_threshold:
            df[col] = df[col].astype("category")
            report["converted_to_category"].append(col)

    return df, report


def test_normalize_dtypes():
    df = pd.read_csv(os.path.join(SCRIPT_DIR, 'train.csv'))
    out_df, report = normalize_tabular_dtypes(df)
    
    out_df.to_csv(os.path.join(SCRIPT_DIR, 'check.csv'))
    print(report)
    
    

if __name__ == "__main__":
    normalize_tabular_dtypes()
    # test_normalize_dtypes()