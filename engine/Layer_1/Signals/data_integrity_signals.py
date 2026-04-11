import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ------------------ LOGGING SETUP ------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ml_diag")


# ------------------ STRUCTURE ------------------

@dataclass(frozen=True)
class Structure:
    dimension: str
    name: str
    label: str
    value: Any
    meta: Optional[Dict] = None


DIMENSION = "data_integrity"


# ------------------ VALIDATION ------------------

def validate_data(df: pd.DataFrame):
    if not isinstance(df, pd.DataFrame):
        logger.error("Invalid input type", extra={"type": str(type(df))})
        raise ValueError("Input must be a pandas DataFrame")

    if df.empty:
        logger.warning("Empty DataFrame detected")


# ------------------ SIGNALS ------------------

def dataset_shape(df: pd.DataFrame) -> Structure:
    rows, cols = df.shape

    result = Structure(
        dimension=DIMENSION,
        name="dataset_shape",
        label=None,
        value={"rows": int(rows), "cols": int(cols)},
        meta=None
    )

    logger.info("Computed dataset_shape")
    return result


def global_missing_ratio(df: pd.DataFrame) -> Structure:
    total_cells = df.shape[0] * df.shape[1]

    ratio = float(df.isna().sum().sum() / total_cells) if total_cells > 0 else 0.0
    
    if ratio < 0.05:
        label = "ACCEPTABLE"
    elif ratio < 0.2:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"

    result = Structure(
        dimension=DIMENSION,
        name="global_missing_ratio",
        label=label,
        value=ratio,
        meta={"total_cells": total_cells}
    )

    logger.info("Computed global_missing_ratio")
    return result


def col_missing_ratio(df: pd.DataFrame) -> Structure:
    ratio = df.isna().mean().to_dict()
    
    worst_ratio = max(ratio.values())

    if worst_ratio < 0.05:
        label = "ACCEPTABLE"
    elif worst_ratio < 0.2:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"
                

    result = Structure(
        dimension=DIMENSION,
        name="column_missing_ratio",
        label=label,
        value=ratio,
        meta={"num_columns": len(ratio)}
    )

    logger.info("Computed column_missing_ratio", extra={"num_columns": len(ratio)})
    return result


def duplicated_ratio(df: pd.DataFrame) -> Structure:
    
    df_copy = df.copy()
    
    df_copy = df_copy.fillna("__MISSING__")   
    
    
    ratio = float(df_copy.duplicated().mean()) if len(df) > 0 else 0.0
    
    if ratio < 0.02:
        label = "ACCEPTABLE"
    elif ratio < 0.15:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"

    result = Structure(
        dimension=DIMENSION,
        name="duplicate_ratio",
        label=label,
        value=ratio,
        meta={"num_rows": len(df_copy)}
    )

    logger.info("Computed duplicate_ratio")
    return result


def constant_columns(df: pd.DataFrame) -> Structure:
    constant_cols = df.columns[df.nunique(dropna=True) <= 1]
    
    ratio = float(len(constant_cols) / df.shape[1]) if df.shape[1] > 0 else 0.0
    
    if ratio == 0.0:
        label = "ACCEPTABLE"
    elif ratio < 0.2:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"
    

    result = Structure(
        dimension=DIMENSION,
        name="constant_columns",
        value={
            "columns": list(constant_cols),
            "ratio": ratio,
        },
        label=label,
        meta={"total_columns": df.shape[1]}
    )

    logger.info("Computed constant_columns", extra={"count": len(constant_cols)})
    return result


def hidden_missing_ratio(df: pd.DataFrame) -> Structure:
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
        
    if worst_ratio < 0.05:
        label = "ACCEPTABLE"
    elif worst_ratio < 0.2:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"

    result = Structure(
        dimension=DIMENSION,
        name="hidden_missing_ratio",
        value={"ratios": hidden_counts, "worst_ratio": worst_ratio},
        label=label,
        meta={"num_object_columns": len(obj_cols.columns)}
    )

    logger.info("Computed hidden_missing_ratio", extra={"columns_checked": len(hidden_counts)})
    return result


def mixed_type_columns(df: pd.DataFrame) -> Structure:
    mixed_cols = []
    obj_cols = df.select_dtypes(include="object")
    
    ignore_tokens = {"na", "n/a", "null", "none", "unknown", "?", "-", "", " "}

    for col in obj_cols:
        series = df[col].astype(str).str.strip().str.lower()

        # remove hidden missing BEFORE type check
        valid_series = series[~series.isin(ignore_tokens)]

        coerced = pd.to_numeric(valid_series, errors="coerce")

        has_numeric = coerced.notna().any()
        has_non_numeric = coerced.isna().any()

        if has_numeric and has_non_numeric:
            mixed_cols.append(col)

    ratio = len(mixed_cols) / df.shape[1] if df.shape[1] > 0 else 0.0

    if ratio == 0:
        label = "ACCEPTABLE"
    elif ratio < 0.05:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"

    result = Structure(
        dimension=DIMENSION,
        name="mixed_type_columns",
        value={"columns": mixed_cols, "ratio": ratio},
        label=label,
        meta={"num_object_columns": len(obj_cols.columns)}
    )
    
    if mixed_cols:
        logger.warning("Mixed type columns detected", extra={"columns": mixed_cols})
    else:
        logger.info("No mixed type columns detected")

    return result


# ------------------ ORCHESTRATOR ------------------

SIGNALS_REGISTRY = [
    dataset_shape,
    global_missing_ratio,
    col_missing_ratio,
    duplicated_ratio,
    constant_columns,
    hidden_missing_ratio,
    mixed_type_columns,
]


def run_signal_extraction(df: pd.DataFrame) -> List[Structure]:
    validate_data(df)

    results: List[Structure] = []

    for signal_fn in SIGNALS_REGISTRY:
        try:
            result = signal_fn(df)
            results.append(result)

        except Exception as e:
            logger.error(
                f"Signal failed: {signal_fn.__name__}",
                extra={"signal": signal_fn.__name__, "error": str(e)}
            )

            results.append(
                Structure(
                    dimension=DIMENSION,
                    name=signal_fn.__name__,
                    value=None,
                    label=None,
                    meta={"error": str(e)}
                )
            )

    return results


# ------------------ ENTRY ------------------

if __name__ == "__main__":
    
    # run_signal_extraction(df)
    
    # Example usage
    df = pd.DataFrame({
        "A": [1, 2, None, 4],
        "B": ["NA", "yes", "no", "unknown"]
    })

    results = run_signal_extraction(df)
    for r in results:
        print(r)
