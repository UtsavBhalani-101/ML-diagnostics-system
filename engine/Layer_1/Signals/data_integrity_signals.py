import math
import numpy as np
import pandas as pd
import logging
from engine.Layer_1.schema import Signal_Structure
from typing import List


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)



DIMENSION = "data_integrity"

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

def validate_data(df: pd.DataFrame):
    if df is None or len(df) == 0 or df.size == 0:
        return {"status": "fail", "reason": "Empty dataframe"}
    
    if df.shape[0] == 0:
        return {"status" : "fail", "reason" : "No rows"}
    
    if df.shape[1] == 0:
        return {"status" : "fail", "reason" : "No columns"}
         

    return {"status": "pass"}


# ------------------ SIGNALS ------------------

def dataset_shape(df: pd.DataFrame) -> Signal_Structure:
    rows, cols = df.shape

    signal = Signal_Structure(
        dimension=DIMENSION,
        name="dataset_shape",
        value={"rows": int(rows), "cols": int(cols)},
        status="ok",
        meta={"total_cells": int(rows * cols)}
    )
    enforce(signal)
    return signal


def global_missing_ratio(df: pd.DataFrame) -> Signal_Structure:
    total = df.shape[0] * df.shape[1]

    ratio = float(df.isna().sum().sum() / total)

    signal = Signal_Structure(
        dimension=DIMENSION,
        name="global_missing_ratio",
        value=ratio,
        status="ok",
        meta={"total_cells": total}
    )
    enforce(signal)
    return signal


def column_missing_ratio(df: pd.DataFrame) -> Signal_Structure:

    ratios = df.isna().mean().to_dict()
    worst = max(ratios.values())

    signal = Signal_Structure(
        dimension=DIMENSION,
        name="column_missing_ratio",
        value={"per_column": ratios, "worst_ratio": worst},
        status="ok",
        meta={"num_columns": len(ratios)}
    )
    enforce(signal)
    return signal


def duplicated_ratio(df: pd.DataFrame) -> Signal_Structure:
    
    df_norm = _normalize_hidden_missing(df)
    df_copy = df_norm.fillna("__MISSING__")
    ratio = float(df_copy.duplicated().mean())
    
    signal = Signal_Structure(
        dimension=DIMENSION,
        name="duplicated_ratio",
        value=ratio,
        status="ok",
        meta={"num_rows": len(df)}
    )
    enforce(signal)
    return signal


def constant_columns_ratio(df: pd.DataFrame) -> Signal_Structure:
    
    df_norm = _normalize_hidden_missing(df)

    const_cols = df_norm.columns[df_norm.nunique(dropna=True) <= 1]
    ratio = float(len(const_cols) / df.shape[1])

    signal = Signal_Structure(
        dimension=DIMENSION,
        name="constant_columns_ratio",
        value={"columns": list(const_cols), "ratio": ratio},
        status="ok",
        meta={"total_columns": df.shape[1]}
    )
    enforce(signal)
    return signal


def hidden_missing_ratio(df: pd.DataFrame) -> Signal_Structure:
    obj_cols = df.select_dtypes(include="object")

    if len(obj_cols.columns) == 0:
        return Signal_Structure(
            dimension=DIMENSION,
            name="hidden_missing_ratio",
            value=None,
            status="no_value",
            meta={"reason": "no object columns"}
        )       
    
    worst = 0.0
    ratios = {}

    for col in obj_cols:
        series = df[col].astype(str).str.strip().str.lower()
        r = float(series.isin(HIDDEN_TOKENS).mean())
        ratios[col] = r
        worst = max(worst, r)

    signal = Signal_Structure(
        dimension=DIMENSION,
        name="hidden_missing_ratio",
        value={"ratios": ratios, "worst_ratio": worst},
        status="ok",
        meta={"num_object_columns": len(obj_cols.columns)}
    )
    
    enforce(signal)
    return signal


def mixed_type_columns_ratio(df: pd.DataFrame) -> Signal_Structure:

    ignore = {"na", "n/a", "null", "none", "unknown", "?", "-", "", " "}
    obj_cols = df.select_dtypes(include="object")

    if len(obj_cols.columns) == 0:
        return Signal_Structure(
            dimension=DIMENSION,
            name="mixed_type_columns_ratio",
            value=None,
            status="no_value",
            meta={"reason": "no object columns"}
        )

    mixed = []

    for col in obj_cols:
        s = df[col].astype(str).str.strip().str.lower()
        valid = s[~s.isin(ignore)]

        coerced = pd.to_numeric(valid, errors="coerce")

        if coerced.notna().any() and coerced.isna().any():
            mixed.append(col)

    ratio = len(mixed) / len(obj_cols.columns)

    signal = Signal_Structure(
        dimension=DIMENSION,
        name="mixed_type_columns_ratio",
        value={"columns": mixed, "ratio": ratio},
        status="ok",
        meta={"num_object_columns": len(obj_cols.columns)}
    )
    enforce(signal)
    return signal


# ------------------ REGISTRY ------------------

SIGNALS_REGISTRY = [
    dataset_shape,
    global_missing_ratio,
    column_missing_ratio,
    duplicated_ratio,
    constant_columns_ratio,
    hidden_missing_ratio,
    mixed_type_columns_ratio,
]


REQUIRED_SIGNALS = {
    "dataset_shape": dict,
    "global_missing_ratio": float,
    "column_missing_ratio": dict,
    "duplicated_ratio": float,
    "constant_columns_ratio": dict,
    "hidden_missing_ratio": (dict, type(None)),
    "mixed_type_columns_ratio": dict,
}


def run_data_integrity_signals(df: pd.DataFrame) -> List[Signal_Structure]:

    validation = validate_data(df)

    if validation["status"] == "fail":
        return [
            Signal_Structure(
                dimension=DIMENSION,
                name="data_validation",
                value=None,
                status="error",
                meta={"reason": validation["reason"]}
            )
        ]

    results = []

    for fn in SIGNALS_REGISTRY:
        try:
            results.append(fn(df))
        except Exception as e:
            results.append(
                Signal_Structure(
                    dimension=DIMENSION,
                    name=fn.__name__,
                    value=None,
                    status="error",
                    meta={"error": str(e)}
                )
            )

    return results

if __name__ == "__main__":

    df = pd.DataFrame({
        # "age": [25, 30, np.nan, 35, 40, 25, 30, np.nan, 35, 40],
        # "salary": [50000, 60000, 70000, 80000, 90000, 50000, 60000, 70000, 80000, 90000],
        "city": ["NY", "LA", "na", "NY", "unknown", "NY", "LA", "?", "NY", "LA"],
        # "score": ["10", "20", "abc", "30", "def", "10", "20", "abc", "30", "def"],
        "constant_col": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        # "missing" : [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
    })
    
    # df = pd.DataFrame([[]])
    
    # df = pd.DataFrame({"col1" : [], "col2" : []})

    df = pd.read_csv(r"D:\ML diagnose v1\test_files\train.csv")
    
    
    results = run_data_integrity_signals(df)
    for r in results:
        print(r)
    
    
    
