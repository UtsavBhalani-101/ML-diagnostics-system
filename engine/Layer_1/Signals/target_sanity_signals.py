import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

FAILURE_MODES = {
    "existence" : "target not present --> _____ (missing)",
    "consistency" : "same situation gives differnt answers --> _____ (noise, misalignment, encoding issue)",
    "informative" : "target not informative or useful to learn anything from -->  _____ (imbalance, degeneracy)"
}

# ------------------ LOGGING ------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ------------------ STRUCTURE ------------------

@dataclass(frozen=True)
class Structure:
    dimension: str
    name: str
    value: Any
    status: str  # "ok", "no_value", "error"
    meta: Optional[Dict] = None


DIMENSION = "target_viability"


# ------------------ ENFORCEMENT ------------------

def enforce(signal: Structure):
    if signal.status == "ok" and signal.value is None:
        raise ValueError(f"{signal.name}: status ok but value is None")

    if signal.status in ("no_value", "error") and signal.value is not None:
        raise ValueError(f"{signal.name}: has value but status={signal.status}")


# ------------------ CONSTANTS ------------------

HIDDEN_MISSING = {"na", "n/a", "null", "none", "", " ", "?", "unknown", "np.nan", "nan"}


# ------------------ UTILITIES ------------------

def clean_target(y) -> pd.Series:
    y = pd.Series(y)

    # Step 1: preserve true missing
    mask_missing = y.isna()

    # Step 2: process only non-missing
    y_clean = y.copy()
    y_clean[~mask_missing] = (
        y_clean[~mask_missing]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # Step 3: replace hidden missing
    y_clean = y_clean.replace(HIDDEN_MISSING, np.nan)

    return y_clean


def is_mixed_type(y: pd.Series) -> bool:
    types = set(type(v) for v in y.dropna())
    return len(types) > 1


# ------------------ VALIDATION ------------------

def validate_target(y: pd.Series) -> Dict:

    if len(y) == 0:
        return {"status": "fail", "reason": "Target is empty"}    
        
    if y.isna().all():
        return {"status": "fail", "reason": "Target is entirely filled with missing"}

    return {"status": "pass", "y": y}


# ------------------ SIGNALS ------------------

def target_missing_ratio(y: pd.Series) -> Structure:
    ratio = float(y.isna().mean())

    signal = Structure(
            DIMENSION,
            "target_missing_ratio",
            ratio,
            "ok",
            {"n_samples": len(y)}
        )

    enforce(signal)
    return signal

def target_degeneracy_flag(y: pd.Series) -> Structure:
    unique = int(y.dropna().nunique())
    is_degenerate = unique <= 1

    signal = Structure(
            DIMENSION,
            "target_degeneracy_flag",
            is_degenerate,
            "ok",
            {"unique_values": unique}
        )
    
    enforce(signal)
    return signal


def dominant_class_ratio(y: pd.Series) -> Structure:
    if y.dropna().empty:
        return Structure(DIMENSION, "dominant_class_ratio", None, "no_value")

    ratio = float(y.value_counts(normalize=True).iloc[0])

    signal =  Structure(
            DIMENSION,
            "dominant_class_ratio",
            ratio,
            "ok",
            {"n_samples": len(y)}
        )

    enforce(signal)
    return signal

def target_entropy(y: pd.Series) -> Structure:
    if y.dropna().empty:
        return Structure(DIMENSION, "target_entropy", None, "no_value")

    p = y.value_counts(normalize=True)
    entropy = float(-np.sum(p * np.log2(p + 1e-9)))

    signal =  Structure(
            DIMENSION,
            "target_entropy",
            entropy,
            "ok",
            {"num_classes": len(p)}
        )

    enforce(signal)
    return signal

def type_contamination_ratio(y: pd.Series) -> Structure:
    non_null = y.dropna()

    if len(non_null) == 0:
        return Structure(DIMENSION, "type_contamination_ratio", None, "no_value")

    types = non_null.map(type)
    majority_type = types.value_counts().idxmax()

    contamination = float((types != majority_type).mean())

    signal =  Structure(
            DIMENSION,
            "type_contamination_ratio",
            contamination,
            "ok",
            {"major_type": str(majority_type)}
        )

    enforce(signal)
    return signal

def dataset_shape(y: pd.Series) -> Structure:
    signal = Structure(
        dimension=DIMENSION,
        name="dataset_shape",
        value={"rows": len(y), "cols": 1},
        status="ok",
        meta={"n_samples": len(y)}
    )

    enforce(signal)
    return signal


# ------------------ REGISTRY ------------------

SIGNALS_REGISTRY = [
    target_missing_ratio,        # existence
    target_degeneracy_flag,      # informativeness (hard fail)
    dominant_class_ratio,        # informativeness (soft fail)
    target_entropy,              # consistency proxy
    type_contamination_ratio,     # consistency (representation)
    dataset_shape
]

REQUIRED_SIGNALS = {
    "target_missing_ratio": float,
    "target_degeneracy_flag": bool,
    "dominant_class_ratio": float,
    "target_entropy": (float, type(None)),
    "type_contamination_ratio": (float, type(None)),
    "dataset_shape" : dict
}


# ------------------ ORCHESTRATOR ------------------

def run_target_signals(y: pd.Series) -> List[Structure]:

    y_clean = clean_target(y)
    validation = validate_target(y_clean)

    if validation["status"] == "fail":
        return [
            Structure(
                dimension=DIMENSION,
                name="target_validation",
                value=None,
                status="error",
                meta={"reason": validation["reason"]}
            )
        ]

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
                    status="error",
                    meta={"error": str(e)}
                )
            )

    return results

if __name__ == "__main__":
    # Example target column
    # example_target_col = pd.Series([1, 0, 1, 1, "NA", np.nan, 0, 1, 1, 0, 0, 1, "", " ", None])
    example_target_col = pd.Series(["NY", "LA", "SF", "NY", "LA", "None", "  ", "NY", "LA", "SF", "NY", "LA", "np.nan"])
    # example_target_col = pd.Series([])
    print("--- Running Target Signals ---")
    results = run_target_signals(example_target_col)
    
    for res in results:
        # print(f"{res.name}:")
        # print(f"  Value: {res.value}")
        # print(f"  Meta: {res.meta}\n")
        
        print(res)

    print(dataset_shape(clean_target(example_target_col)))
    # print(clean_target(example_target_col))