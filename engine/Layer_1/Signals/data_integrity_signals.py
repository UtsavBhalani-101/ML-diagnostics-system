import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ------------------ LOGGING SETUP ------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ------------------ STRUCTURE ------------------

@dataclass(frozen=True)
class Signal_Structure:
    dimension: str
    name: str
    value: Any
    meta: Optional[Dict] = None


DIMENSION = "data_integrity"


# ------------------ VALIDATION ------------------

def validate_data(df: pd.DataFrame):
    pass


# ------------------ SIGNALS ------------------

def dataset_shape(df: pd.DataFrame) -> Signal_Structure:
    rows, cols = df.shape
    
    if rows is None:
        return Signal_Structure(
            dimension=DIMENSION,
            name="dataset_shape",
            value={"rows": None, "cols" : int(cols)},
            meta={"status" : "undefined" , "reason" : "no rows"}
        )
        
    if cols is None:
        return Signal_Structure(
            dimension=DIMENSION,
            name="dataset_shape",
            value={"rows": int(rows), "cols" : None},
            meta={"status" : "undefined" , "reason" : "no columns"}
        )
    
    if rows is None and cols is None:
        return Signal_Structure(
            dimension=DIMENSION,
            name="dataset_shape",
            value=None,
            meta={"status" : "undefined" , "reason" : "no rows and columns"}
        )

    result = Signal_Structure(
        dimension=DIMENSION,
        name="dataset_shape",
        value={"rows": int(rows), "cols": int(cols)},
        meta=None
    )

    return result


def global_missing_ratio(df: pd.DataFrame) -> Signal_Structure:
    total_cells = df.shape[0] * df.shape[1]
    
    if total_cells == 0.0:
        return Signal_Structure(
            dimension=DIMENSION,
            name="global_missing_ratio",
            value=None,
            meta={"status" : "undefined", "reason" : "no cells"}
        )

    ratio = float(df.isna().sum().sum() / total_cells)

    result = Signal_Structure(
        dimension=DIMENSION,
        name="global_missing_ratio",
        value=ratio,
        meta={"total_cells": total_cells}
    )

    return result


def column_missing_ratio(df: pd.DataFrame) -> Signal_Structure:
    
    if df.columns == 0:
        return Signal_Structure(
            dimension=DIMENSION,
            name="column_missing_ratio",
            value=None,
            meta={"status" : "valid", "error" : "no columns"}
        )
    
    ratio = df.isna().mean().to_dict()
    
    worst_ratio = max(ratio.values())                

    result = Signal_Structure(
        dimension=DIMENSION,
        name="column_missing_ratio",
        value={
            "per_column": ratio,
            "worst_ratio": worst_ratio
        },
        meta={"num_columns": len(ratio)}
    )

    return result


def duplicated_ratio(df: pd.DataFrame) -> Signal_Structure:
    
    df_copy = df.copy()
    
    df_copy = df_copy.fillna("__MISSING__")   
    
    if len(df) == 0:
        return Signal_Structure(
            dimension=DIMENSION,
            name="duplicated_ratio",
            value=None,
            meta={"status" : "undefined" , "reason" : "dataframe length is 0"}
        )     
    
    ratio = float(df_copy.duplicated().mean())

    result = Signal_Structure(
        dimension=DIMENSION,
        name="duplicated_ratio",
        value=ratio,
        meta={"num_rows": len(df_copy)}
    )

    return result


def constant_columns_ratio(df: pd.DataFrame) -> Signal_Structure:
    constant_cols = df.columns[df.nunique(dropna=True) <= 1]
    
    if df.shape[1] == 0:
        return Signal_Structure(
            dimension=DIMENSION,
            name="constant_columns_ratio",
            value=None,
            meta={"status":"undefined" , "reason" : "no columns"}
        )
    
    ratio = float(len(constant_cols) / df.shape[1])
            
    result = Signal_Structure(
        dimension=DIMENSION,
        name="constant_columns_ratio",
        value={
            "columns": list(constant_cols),
            "ratio": ratio,
        },
        meta={"total_columns": df.shape[1]}
    )

    return result


def hidden_missing_ratio(df: pd.DataFrame) -> Signal_Structure:
    tokens = {"na", "n/a", "null", "none", "unknown", "?", "-", "", " "}
    hidden_counts = {}

    obj_cols = df.select_dtypes(include="object")
    worst_ratio = 0.0

    for col in obj_cols:
        series = df[col].astype(str).str.strip().str.lower()
        ratio = float(series.isin(tokens).mean())
        hidden_counts[col] = ratio
        if ratio > worst_ratio:
            worst_ratio = ratio
        

    result = Signal_Structure(
        dimension=DIMENSION,
        name="hidden_missing_ratio",
        value={"ratios": hidden_counts, "worst_ratio": worst_ratio},
        meta={"num_object_columns": len(obj_cols.columns)}
    )

    return result


def mixed_type_columns_ratio(df: pd.DataFrame) -> Signal_Structure:
    mixed_cols = []
    obj_cols = df.select_dtypes(include="object")
    
    ignore_tokens = {"na", "n/a", "null", "none", "unknown", "?", "-", "", " "}
    
    if df.shape[1] == 0:
        return Signal_Structure(
            dimension=DIMENSION,
            name="mixed_type_columns_ratio",
            value=None,
            meta={"status" : "undefined", "reason" : "no columns"}
        )

    for col in obj_cols:
        series = df[col].astype(str).str.strip().str.lower()

        # remove hidden missing BEFORE type check
        valid_series = series[~series.isin(ignore_tokens)]

        coerced = pd.to_numeric(valid_series, errors="coerce")

        has_numeric = coerced.notna().any()
        has_non_numeric = coerced.isna().any()

        if has_numeric and has_non_numeric:
            mixed_cols.append(col)

    ratio = len(mixed_cols) / df.shape[1]


    result = Signal_Structure(
        dimension=DIMENSION,
        name="mixed_type_columns_ratio",
        value={"columns": mixed_cols, "ratio": ratio},
        meta={"num_object_columns": len(obj_cols.columns)}
    )

    return result


# ------------------ ORCHESTRATOR ------------------

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
    "dataset_shape" : (dict, type(None)),
    "global_missing_ratio" : (float, type(None)),   
    "column_missing_ratio" : (dict, type(None)),
    "duplicated_ratio" : (float, type(None)),
    "constant_columns_ratio" : (float, type(None)),
    "hidden_missing_ratio" : dict,
    "mixed_type_columns_ratio" : (dict, type(None))
}

def run_signal_extraction(df: pd.DataFrame) -> List[Signal_Structure]:
    validation = validate_data(df)
    
    if validation["status"] == "fail":
        logger.error("Data integrity validation failed: ", extra={"reason" : validation["reason"]})
        
        return Signal_Structure(
            dimension=DIMENSION,
            name="data_integrity",
            value=None,
            meta={"status" : "error" , "reason" : validation["reason"]}
        )
        

    results: List[Signal_Structure] = []

    for signal_fn in SIGNALS_REGISTRY:
        try:
            result = signal_fn(df)
            logger.debug(f"{signal_fn.__name__} success")
            results.append(result)

        except Exception as e:
            logger.error(
                f"Signal failed: {signal_fn.__name__}",
                extra={"signal": signal_fn.__name__, "error": str(e)}
            )

            results.append(
                Signal_Structure(
                    dimension=DIMENSION,
                    name=signal_fn.__name__,
                    value=None,
                    meta={"error": str(e)}
                )
            )

    return results


# ------------------ ENTRY ------------------

if __name__ == "__main__":
    
    # run_signal_extraction(df)
    N_SAMPLES = 10000
    
    def build_categorical_clean() -> pd.DataFrame:
        np.random.seed(42)
        df = pd.DataFrame({
            "cat_1": np.random.choice(["A", "B", "C"], size=N_SAMPLES),
            "cat_2": np.random.choice(["X", "Y"], size=N_SAMPLES),
            "cat_3": np.random.choice(["low", "medium", "high"], size=N_SAMPLES),
        })
        return df
    
    def build_categorical_hidden_missing() -> pd.DataFrame:
        df = build_categorical_clean().astype(object)
        np.random.seed(42)
        mask = np.random.rand(N_SAMPLES) < 0.15
        df.loc[mask, "cat_1"] = "NA"
        return df
    
    
    df = build_categorical_hidden_missing()

    results = run_signal_extraction(df)
    for r in results:
        print(r)

