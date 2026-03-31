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
        value={"rows": int(rows), "cols": int(cols)},
        meta=None
    )

    logger.info("Computed dataset_shape")
    return result


def global_missing_ratio(df: pd.DataFrame) -> Structure:
    total_cells = df.shape[0] * df.shape[1]

    ratio = float(df.isna().sum().sum() / total_cells) if total_cells > 0 else 0.0

    result = Structure(
        dimension=DIMENSION,
        name="global_missing_ratio",
        value=ratio,
        meta={"total_cells": total_cells}
    )

    logger.info("Computed global_missing_ratio")
    return result


def col_missing_ratio(df: pd.DataFrame) -> Structure:
    ratios = df.isna().mean().to_dict()

    result = Structure(
        dimension=DIMENSION,
        name="column_missing_ratio",
        value=ratios,
        meta={"num_columns": len(ratios)}
    )

    logger.info("Computed column_missing_ratio", extra={"num_columns": len(ratios)})
    return result


def duplicated_ratio(df: pd.DataFrame) -> Structure:
    ratio = float(df.duplicated().mean()) if len(df) > 0 else 0.0

    result = Structure(
        dimension=DIMENSION,
        name="duplicate_ratio",
        value=ratio,
        meta={"num_rows": len(df)}
    )

    logger.info("Computed duplicate_ratio")
    return result


def constant_columns(df: pd.DataFrame) -> Structure:
    constant_cols = df.columns[df.nunique(dropna=False) <= 1]

    result = Structure(
        dimension=DIMENSION,
        name="constant_columns",
        value={
            "columns": list(constant_cols),
            "ratio": float(len(constant_cols) / df.shape[1]) if df.shape[1] > 0 else 0.0
        },
        meta={"total_columns": df.shape[1]}
    )

    logger.info("Computed constant_columns", extra={"count": len(constant_cols)})
    return result


def hidden_missing_ratio(df: pd.DataFrame) -> Structure:
    tokens = {"na", "n/a", "null", "none", "unknown", "?", "-", "", " "}
    hidden_counts = {}

    obj_cols = df.select_dtypes(include="object")

    for col in obj_cols:
        series = df[col].astype(str).str.strip().str.lower()
        ratio = float(series.isin(tokens).mean())
        hidden_counts[col] = ratio

    result = Structure(
        dimension=DIMENSION,
        name="hidden_missing_ratio",
        value=hidden_counts,
        meta={"num_object_columns": len(obj_cols.columns)}
    )

    logger.info("Computed hidden_missing_ratio", extra={"columns_checked": len(hidden_counts)})
    return result


def mixed_type_columns(df: pd.DataFrame) -> Structure:
    mixed_cols = []
    obj_cols = df.select_dtypes(include="object")

    for col in obj_cols:
        numeric_ratio = pd.to_numeric(df[col], errors="coerce").notna().mean()

        if 0.7 < numeric_ratio < 1.0:
            mixed_cols.append(col)

    result = Structure(
        dimension=DIMENSION,
        name="mixed_type_columns",
        value={
            "columns": mixed_cols,
            "ratio": float(len(mixed_cols) / df.shape[1]) if df.shape[1] > 0 else 0.0
        },
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
                    meta={"error": str(e)}
                )
            )

    return results


# ------------------ ENTRY ------------------

if __name__ == "__main__":
    
    run_signal_extraction(df)
    
    # # Example usage
    # df = pd.DataFrame({
    #     "A": [1, 2, None, 4],
    #     "B": ["NA", "yes", "no", "unknown"]
    # })

    # results = run_signal_extraction(df)
    # for r in results:
    #     print(r)
