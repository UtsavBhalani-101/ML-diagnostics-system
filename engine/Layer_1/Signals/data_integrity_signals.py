import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ------------------ STRUCTURE ------------------

@dataclass(frozen=True)
class Signal_Structure:
    dimension: str
    name: str
    value: Any
    status: str  # "ok", "no_value", "error"
    meta: Optional[Dict] = None


DIMENSION = "data_integrity"


# ------------------ ENFORCEMENT ------------------

def enforce(signal: Signal_Structure):
    if signal.status == "ok" and signal.value is None:
        raise ValueError(f"{signal.name}: ok but value is None")

    if signal.status in ("no_value", "error") and signal.value is not None:
        raise ValueError(f"{signal.name}: invalid state mismatch")


# ------------------ VALIDATION ------------------

def validate_data(df: pd.DataFrame):
    if df is None or df.shape[0] == 0:
        return {"status": "fail", "reason": "Empty dataframe"}

    return {"status": "pass"}


# ------------------ SIGNALS ------------------

def dataset_shape(df: pd.DataFrame) -> Signal_Structure:
    rows, cols = df.shape

    signal = Signal_Structure(
        DIMENSION,
        "dataset_shape",
        {"rows": int(rows), "cols": int(cols)},
        "ok",
        None
    )
    enforce(signal)
    return signal


def global_missing_ratio(df: pd.DataFrame) -> Signal_Structure:
    total = df.shape[0] * df.shape[1]

    if total == 0:
        signal = Signal_Structure(DIMENSION, "global_missing_ratio", None, "no_value")
        enforce(signal)
        return signal

    ratio = float(df.isna().sum().sum() / total)

    signal = Signal_Structure(
        DIMENSION,
        "global_missing_ratio",
        ratio,
        "ok",
        {"total_cells": total}
    )
    enforce(signal)
    return signal


def column_missing_ratio(df: pd.DataFrame) -> Signal_Structure:
    if df.shape[1] == 0:
        signal = Signal_Structure(DIMENSION, "column_missing_ratio", None, "no_value")
        enforce(signal)
        return signal

    ratios = df.isna().mean().to_dict()
    worst = max(ratios.values())

    signal = Signal_Structure(
        DIMENSION,
        "column_missing_ratio",
        {"per_column": ratios, "worst_ratio": worst},
        "ok",
        {"num_columns": len(ratios)}
    )
    enforce(signal)
    return signal


def duplicated_ratio(df: pd.DataFrame) -> Signal_Structure:
    if len(df) == 0:
        signal = Signal_Structure(DIMENSION, "duplicated_ratio", None, "error")
        enforce(signal)
        return signal

    df_copy = df.fillna("__MISSING__")
    ratio = float(df_copy.duplicated().mean())

    signal = Signal_Structure(
        DIMENSION,
        "duplicated_ratio",
        ratio,
        "ok",
        {"num_rows": len(df)}
    )
    enforce(signal)
    return signal


def constant_columns_ratio(df: pd.DataFrame) -> Signal_Structure:
    if df.shape[1] == 0:
        signal = Signal_Structure(DIMENSION, "constant_columns_ratio", None, "no_value")
        enforce(signal)
        return signal

    const_cols = df.columns[df.nunique(dropna=True) <= 1]
    ratio = float(len(const_cols) / df.shape[1])

    signal = Signal_Structure(
        DIMENSION,
        "constant_columns_ratio",
        {"columns": list(const_cols), "ratio": ratio},
        "ok",
        {"total_columns": df.shape[1]}
    )
    enforce(signal)
    return signal


def hidden_missing_ratio(df: pd.DataFrame) -> Signal_Structure:
    tokens = {"na", "n/a", "null", "none", "unknown", "?", "-", "", " "}
    obj_cols = df.select_dtypes(include="object")

    worst = 0.0
    ratios = {}

    for col in obj_cols:
        series = df[col].astype(str).str.strip().str.lower()
        r = float(series.isin(tokens).mean())
        ratios[col] = r
        worst = max(worst, r)

    signal = Signal_Structure(
        DIMENSION,
        "hidden_missing_ratio",
        {"ratios": ratios, "worst_ratio": worst},
        "ok",
        {"num_object_columns": len(obj_cols.columns)}
    )
    enforce(signal)
    return signal


def mixed_type_columns_ratio(df: pd.DataFrame) -> Signal_Structure:
    if df.shape[1] == 0:
        signal = Signal_Structure(DIMENSION, "mixed_type_columns_ratio", None, "no_value")
        enforce(signal)
        return signal

    ignore = {"na", "n/a", "null", "none", "unknown", "?", "-", "", " "}
    obj_cols = df.select_dtypes(include="object")

    mixed = []

    for col in obj_cols:
        s = df[col].astype(str).str.strip().str.lower()
        valid = s[~s.isin(ignore)]

        coerced = pd.to_numeric(valid, errors="coerce")

        if coerced.notna().any() and coerced.isna().any():
            mixed.append(col)

    ratio = len(mixed) / df.shape[1]

    signal = Signal_Structure(
        DIMENSION,
        "mixed_type_columns_ratio",
        {"columns": mixed, "ratio": ratio},
        "ok",
        {"num_object_columns": len(obj_cols.columns)}
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
    "hidden_missing_ratio": dict,
    "mixed_type_columns_ratio": dict,
}


def run_signal_extraction(df: pd.DataFrame) -> List[Signal_Structure]:

    validation = validate_data(df)

    if validation["status"] == "fail":
        return [
            Signal_Structure(DIMENSION, "data_validation", None, "error",
                             {"reason": validation["reason"]})
        ]

    results = []

    for fn in SIGNALS_REGISTRY:
        try:
            results.append(fn(df))
        except Exception as e:
            results.append(
                Signal_Structure(DIMENSION, fn.__name__, None, "error",
                                 {"error": str(e)})
            )

    return results

if __name__ == "__main__":
    run_signal_extraction(df)