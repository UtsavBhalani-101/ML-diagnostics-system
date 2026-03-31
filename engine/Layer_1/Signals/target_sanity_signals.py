import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass(frozen=True)
class Structure:
    dimension: str = "Target_viability"
    name: str = None
    value: any = None
    meta: dict = None

HIDDEN_MISSING = {"na", "n/a", "null", "none", "", "?", "unknown"}

def clean_target(y):
    y = pd.Series(y)

    # Convert to string for uniform processing
    y_clean = y.astype(str).str.lower().str.strip()

    # Replace hidden missing with NaN
    y_clean = y_clean.replace(HIDDEN_MISSING, np.nan)

    return y_clean

def validate_target(y):
    y_clean = clean_target(y)

    if is_mixed_type(y_clean):
        return {
            "status": "fail",
            "reason": "Target column has mixed types"
        }

    return {
        "status": "pass",
        "y_clean": y_clean
    }


def target_missing_ratio(target: pd.Series):
    HIDDEN_MISSING = {"na", "n/a", "null", "none", "", "?", "unknown"}
    col_str = target.astype(str).str.strip().str.lower()

    y_clean = col_str.replace(HIDDEN_MISSING, np.nan)

    target_missing_ratio = y_clean.isna().mean()
    
    return{
        "target_missing_ratio" : target_missing_ratio
    }
    
    

def target_variance_or_unique(y, task_type=None):
    """
    Computes target variability depending on task type.

    Returns:
        {
            "task_type": inferred or given,
            "value": variance or unique_count,
            "status": pass/warn/fail,
            "reason": explanation
        }
    """

    y = pd.Series(y)

    # --- Step 1: Drop true NaNs ---
    y_clean = y.dropna()

    if len(y_clean) == 0:
        return {
            "task_type": task_type,
            "value": None,
            "status": "fail",
            "reason": "All target values are missing"
        }

    # --- Step 2: Infer task if not given ---
    if task_type is None:
        n_unique = y_clean.nunique()
        unique_ratio = n_unique / len(y_clean)

        if n_unique <= 10 and unique_ratio < 0.1:
            task_type = "classification"
        else:
            task_type = "regression"

    # --- Step 3: Compute metric ---
    if task_type == "regression":

        variance = float(np.var(y_clean))

        # --- Decision ---
        if variance == 0:
            status = "fail"
            reason = "Target has zero variance; prediction is meaningless"
        elif variance < 1e-5:
            status = "warn"
            reason = "Target has very low variance; weak learning signal"
        else:
            status = "pass"
            reason = "Target has sufficient variability"

        value = variance

    elif task_type == "classification":

        unique_count = int(y_clean.nunique())

        # --- Decision ---
        if unique_count <= 1:
            status = "fail"
            reason = "Target has only one class; classification impossible"
        elif unique_count == 2:
            status = "pass"
            reason = "Binary classification detected"
        elif unique_count <= 20:
            status = "pass"
            reason = "Multi-class classification detected"
        else:
            status = "warn"
            reason = "High number of classes; may be noisy or misclassified as regression"

        value = unique_count

    else:
        return {
            "task_type": task_type,
            "value": None,
            "status": "fail",
            "reason": f"Unknown task type: {task_type}"
        }

    return {
        "task_type": task_type,
        "value": value,
        "status": status,
        "reason": reason
    }