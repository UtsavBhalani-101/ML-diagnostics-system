import math
import numpy as np
import pandas as pd
import logging
from scipy.stats import pearsonr
from typing import List
from engine.Layer_1.schema import Signal_Structure

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


DIMENSION = "feature_target_relationship"

# ------------------ HELPER ------------------


HIDDEN_TOKENS = {"na","n/a","null","none","unknown","?","-",""," ","np.nan","nan"}

def _normalize_hidden_missing(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    obj_cols = df2.select_dtypes(include="object").columns
    for c in obj_cols:
        s = df2[c].astype(str).str.strip().str.lower()
        df2[c] = s.replace(HIDDEN_TOKENS, np.nan)
    return df2


# ------------------ ENFORCEMENT ------------------

def _contains_nan_or_inf(value) -> bool:
    """Recursively check if value contains nan or inf anywhere."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    if isinstance(value, dict):
        return any(_contains_nan_or_inf(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_nan_or_inf(v) for v in value)
    return False


def enforce(signal: Signal_Structure):
    if signal.status == "ok" and signal.value is None:
        raise ValueError(f"{signal.name}: ok but value is None")

    if signal.status == "ok" and _contains_nan_or_inf(signal.value):
        raise ValueError(f"{signal.name}: ok but value contains nan or inf")

    if signal.status in ("no_value", "error") and signal.value is not None:
        raise ValueError(f"{signal.name}: invalid state mismatch")


# ------------------ VALIDATION ------------------

def validate_data(x: pd.DataFrame, y: pd.Series):
    if x is None or len(x) == 0 or x.size == 0:
        return {"status": "fail", "reason": "Empty input feature"}
    
    if x.shape[0] == 0:
        return {"status" : "fail", "reason" : "Feature empty"}
    
    if len(y) == 0:
        return {"status" : "fail", "reason" : "Target empty"}
         

    return {"status": "pass"}


# ------------------ SIGNALS ------------------

def strength(x: pd.DataFrame, y: pd.Series):
    
    corr, p_value = pearsonr(x, y)
    
    print(f"Correlation: {corr:.3f}, P-value: {p_value:.3f}")



def stability_across_slices(x: pd.DataFrame, y: pd.Series):
    pass



def directional_consistency(x: pd.DataFrame, y: pd.Series):
    # monotonicity
    pass
    
def leakage_detection(x: pd.DataFrame, y: pd.Series):
    pass


def proxy_relationship(x: pd.DataFrame, y: pd.Series):
    pass


def perturbation(x: pd.DataFrame, y: pd.Series):
    pass

# ------------------ REGISTRY ------------------

SIGNALS_REGISTRY = [

]


REQUIRED_SIGNALS = {

}


def run_feature_target_relationship_signals(df: pd.DataFrame) -> List[Signal_Structure]:

    return "Hello world"

if __name__ == "__main__":

    pass
    
    
    
