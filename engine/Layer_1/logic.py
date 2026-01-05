import pandas as pd
import numpy as np
from typing import Any, Optional


#^ key facts - dimensions
def key_facts_dimensions(df: dict):
    # Key facts

    # dimesions
    row = df['Metadata']['rows']
    col = df['Metadata']['cols']
    dimesions = f"{row} x {col}"
    return dimesions

#^ key facts - memory 
def key_facts_memory(df: dict):
    # deep=True is essential to get the actual memory of 'object' (string) types
    ...

#^ key facts - feature mix
def key_facts_feature_mix(df: dict):
    

    if cat_ratio >= 0.55:
        mix_type = "Categorical Dominant (High Complexity)"

    elif 0.40 <= cat_ratio < 0.55:
        mix_type = "Moderate Mix (Leaning Categorical)"

    elif abs(num_ratio - cat_ratio) <= 0.10:
        mix_type = "Balanced Mix"

    elif num_ratio >= 0.70:
        mix_type = "Numerical Dominant (Low Complexity)"

    elif 0.60 <= num_ratio < 0.70:
        mix_type = "Moderate Mix (Leaning Numerical)"

    else:
        mix_type = "Unclear Mix"

    return {
        "mix_type": mix_type,
        "num_ratio": round(num_ratio, 3),
        "cat_ratio": round(cat_ratio, 3)
    }

#! checking missingness
def analyze_missingness(df: pd.DataFrame, critical_threshold=0.30):
    # 1. Global Metrics
    total_cells = df.size
    total_missing = df.isna().sum().sum()
    global_pct = (total_missing / total_cells) * 100 if total_cells > 0 else 0

    # 2. Column-Level Metrics (The "Skew" Check)
    # Calculate missingness percentage for every column
    col_missing_pct = df.isna().mean()
    
    # Identify columns that cross the 'Critical' threshold (e.g., 30%)
    critical_cols = col_missing_pct[col_missing_pct > critical_threshold]
    critical_list = critical_cols.index.tolist()

    # 3. Risk Categorization
    if global_pct < 5 and len(critical_list) == 0:
        risk_status = "Low Risk: Dataset is clean."
    elif len(critical_list) > 0:
        risk_status = f"Medium-High Risk: {len(critical_list)} Critical Columns identified."
    else:
        risk_status = "Medium Risk: High global missingness but distributed evenly."

    # 4. Final Output Representation
    return {
        "global_missing_pct": f"{global_pct:.2f}%",
        "risk_level": risk_status,
        "critical_columns_detected": len(critical_list),
        "critical_column_details": {
            col: f"{col_missing_pct[col]:.1%}" for col in critical_list
        },
        "action_required": "Drop critical columns or use iterative imputation" if critical_list else "None"
    }




if __name__ == "__main__":
    layer1_diagnostics()
