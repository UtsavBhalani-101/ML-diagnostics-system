import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List


# ------------------ LOGGING ------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ------------------ STRUCTURE ------------------

@dataclass(frozen=True)
class Structure:
    dimension: str
    name: str
    value: Any
    meta: Optional[Dict] = None


DIMENSION = "target_viability"


# ------------------ CONSTANTS ------------------

HIDDEN_MISSING = {"na", "n/a", "null", "none", "", " ", "?", "unknown"}


# ------------------ UTILITIES ------------------

def clean_target(y) -> pd.Series:
    y = pd.Series(y)

    y_clean = y.astype(str).str.strip().str.lower()
    y_clean = y_clean.replace(HIDDEN_MISSING, np.nan)

    return y_clean


def is_mixed_type(y: pd.Series) -> bool:
    types = set(type(v) for v in y.dropna())
    return len(types) > 1



# ------------------ VALIDATION ------------------

def validate_target(y: pd.Series) -> Dict:

    if y.isna().all():
        return {
            "status": "fail",
            "reason": "Target is entirely missing"
        }

    if is_mixed_type(y):
        return {
            "status": "fail",
            "reason": "Target column has mixed data types"
        }

    return {
        "status": "pass",
        "y": y
    }


# ------------------ SIGNALS ------------------

def target_missing_ratio(y: pd.Series) -> Structure:

    ratio = float(y.isna().mean())

    result = Structure(
        dimension=DIMENSION,
        name="target_missing_ratio",
        value=ratio,
        meta={"n_samples": len(y)}
    )

    return result


def target_variance(y: pd.Series) -> Structure:
    y_numeric = pd.to_numeric(y, errors="coerce").dropna()
    
    if len(y_numeric) == 0:
        return Structure(
        dimension=DIMENSION,
        name="target_variance",
        value=None,
        meta={"status": "valid", "reason": "no numeric data"}
    )

    variance = float(np.var(y_numeric))
    
    target_range = float(np.max(y_numeric) - np.min(y_numeric))
        
    result = Structure(
        dimension=DIMENSION,
        name="target_variance",
        value={"variance" : variance, "target_range" : target_range},
        meta={"valid_numeric_samples": len(y_numeric)}
    )

    return result


def target_unique_count(y: pd.Series) -> Structure:
    
    unique_count = int(y.nunique())

    result = Structure(
        dimension=DIMENSION,
        name="target_unique_count",
        value=unique_count,
        meta={"n_samples": len(y)}
    )

    return result


def class_imbalance_score(y: pd.Series) -> Structure:

    if len(y) == 0:
        return Structure(
            dimension=DIMENSION,
            name="class_imbalance_score",
            value=None,
            meta={
                "status": "valid",
                "reason": "empty target"
            }
        )
    
    score = float(y.value_counts(normalize=True).iloc[0])

    result = Structure(
        dimension=DIMENSION,
        name="class_imbalance_score",
        value=score,
        meta={"n_samples": len(y)}
    )

    return result


def dataset_shape(y: pd.Series) -> Structure:

    result = Structure(
        dimension=DIMENSION,
        name="dataset_shape",
        value={"rows": len(y), "cols": 1},
        meta={"n_samples": len(y)}
    )

    return result



# ------------------ ORCHESTRATOR ------------------

SIGNALS_REGISTRY = [
    target_missing_ratio,
    target_variance,
    target_unique_count,
    class_imbalance_score,
    dataset_shape,
]

REQUIRED_SIGNALS = {
    "dataset_shape": dict,
    "target_missing_ratio": float,
    "target_variance": (dict, type(None)),
    "target_unique_count": int,
    "class_imbalance_score": (float, type(None)),
}


def run_target_signals(y: pd.Series) -> List[Structure]:
    
    y_clean = clean_target(y)

    validation = validate_target(y_clean)

    if validation["status"] == "fail":
        logger.error("Target validation failed", extra={"reason": validation["reason"]})

        return Structure(
                dimension=DIMENSION,
                name="target_validation",
                value=None,
                meta={"status": "error", "reason": validation["reason"]}
            )

    results = []

    for signal_fn in SIGNALS_REGISTRY:
        try:
            res = signal_fn(y_clean)
            logger.debug(f"{signal_fn.__name__} success")
            results.append(res)

        except Exception as e:
            logger.error("Signal failed", extra={
                "signal": signal_fn.__name__,
                "error": str(e)
            })

            results.append(
                Structure(
                    dimension=DIMENSION,
                    name=signal_fn.__name__,
                    value=None,
                    meta={"status" : "error" ,"error": str(e)}
                )
            )

    return results

if __name__ == "__main__":
    # Example target column
    example_target_col = pd.Series([1, 0, 1, 1, "NA", np.nan, 0, 1, 1, 0, 0, 1])
    print("--- Running Target Signals ---")
    results = run_target_signals(example_target_col)
    
    for res in results:
        # print(f"{res.name}:")
        # print(f"  Value: {res.value}")
        # print(f"  Meta: {res.meta}\n")
        
        print(res)
