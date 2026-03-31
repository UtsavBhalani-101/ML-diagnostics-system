import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List


# ------------------ LOGGING ------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ml_diag")


# ------------------ STRUCTURE ------------------

@dataclass(frozen=True)
class Structure:
    dimension: str
    name: str
    value: Any
    meta: Optional[Dict] = None


DIMENSION = "target_viability"


# ------------------ CONSTANTS ------------------

HIDDEN_MISSING = {"na", "n/a", "null", "none", "", "?", "unknown"}


# ------------------ UTILITIES ------------------

def clean_target(y) -> pd.Series:
    y = pd.Series(y)

    y_clean = y.astype(str).str.strip().str.lower()
    y_clean = y_clean.replace(HIDDEN_MISSING, np.nan)

    return y_clean


def is_mixed_type(y: pd.Series) -> bool:
    types = set(type(v) for v in y.dropna())
    return len(types) > 1


def infer_task_type(y: pd.Series) -> Dict:
    n = len(y)
    n_unique = y.nunique()
    unique_ratio = n_unique / n if n > 0 else 0

    most_common_ratio = y.value_counts(normalize=True).iloc[0] if n > 0 else 0

    classification_score = 0
    regression_score = 0

    if n_unique <= 10:
        classification_score += 2
    if unique_ratio > 0.1:
        regression_score += 2
    if most_common_ratio > 0.5:
        classification_score += 2
    if most_common_ratio < 0.1:
        regression_score += 2

    task = "classification" if classification_score > regression_score else "regression"

    confidence = abs(classification_score - regression_score) / 4

    return {
        "task_type": task,
        "confidence": confidence,
        "meta": {
            "n_unique": n_unique,
            "unique_ratio": unique_ratio,
            "most_common_ratio": most_common_ratio
        }
    }


# ------------------ VALIDATION ------------------

def validate_target(y: pd.Series) -> Dict:
    y_clean = clean_target(y)

    if y_clean.isna().all():
        return {
            "status": "fail",
            "reason": "Target is entirely missing"
        }

    if is_mixed_type(y_clean):
        return {
            "status": "fail",
            "reason": "Target column has mixed data types"
        }

    return {
        "status": "pass",
        "y_clean": y_clean
    }


# ------------------ SIGNALS ------------------

def target_missing_ratio(y: pd.Series) -> Structure:
    y_clean = clean_target(y)

    ratio = float(y_clean.isna().mean())

    result = Structure(
        dimension=DIMENSION,
        name="target_missing_ratio",
        value=ratio,
        meta={"n_samples": len(y)}
    )

    logger.info("Computed target_missing_ratio", extra={
        "dimension": DIMENSION,
        "value": ratio
    })

    return result


def target_variance(y: pd.Series) -> Structure:
    y_clean = clean_target(y)
    y_numeric = pd.to_numeric(y_clean, errors="coerce").dropna()

    variance = float(np.var(y_numeric)) if len(y_numeric) > 0 else None

    result = Structure(
        dimension=DIMENSION,
        name="target_variance",
        value=variance,
        meta={"valid_numeric_samples": len(y_numeric)}
    )

    logger.info("Computed target_variance", extra={
        "value": variance
    })

    return result


def target_unique_count(y: pd.Series) -> Structure:
    y_clean = clean_target(y)

    unique_count = int(y_clean.nunique())

    result = Structure(
        dimension=DIMENSION,
        name="target_unique_count",
        value=unique_count,
        meta={"n_samples": len(y_clean)}
    )

    logger.info("Computed target_unique_count", extra={
        "value": unique_count
    })

    return result


def class_imbalance_score(y: pd.Series) -> Structure:
    y_clean = clean_target(y).dropna()

    if len(y_clean) == 0:
        score = None
    else:
        score = float(y_clean.value_counts(normalize=True).iloc[0])

    result = Structure(
        dimension=DIMENSION,
        name="class_imbalance_score",
        value=score,
        meta={"n_samples": len(y_clean)}
    )

    logger.info("Computed class_imbalance_score", extra={
        "value": score
    })

    return result


def task_type_signal(y: pd.Series) -> Structure:
    y_clean = clean_target(y).dropna()

    result_data = infer_task_type(y_clean)

    result = Structure(
        dimension=DIMENSION,
        name="task_type",
        value=result_data["task_type"],
        meta={
            "confidence": result_data["confidence"],
            **result_data["meta"]
        }
    )

    logger.info("Inferred task_type", extra={
        "task_type": result.value,
        "confidence": result.meta["confidence"]
    })

    return result


# ------------------ ORCHESTRATOR ------------------

SIGNALS_REGISTRY = [
    target_missing_ratio,
    target_variance,
    target_unique_count,
    class_imbalance_score,
    task_type_signal
]


def run_target_signals(y: pd.Series) -> List[Structure]:

    validation = validate_target(y)

    if validation["status"] == "fail":
        logger.error("Target validation failed", extra={"reason": validation["reason"]})

        return [
            Structure(
                dimension=DIMENSION,
                name="target_validation",
                value=None,
                meta={"status": "fail", "reason": validation["reason"]}
            )
        ]

    results = []

    for signal_fn in SIGNALS_REGISTRY:
        try:
            res = signal_fn(y)
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
                    meta={"error": str(e)}
                )
            )

    return results

if __name__ == "__main__":
    run_target_signals(target_col)
    
    