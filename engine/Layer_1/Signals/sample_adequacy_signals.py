import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List


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


DIMENSION = "sample_adequacy"


# ------------------ ENFORCEMENT ------------------

def enforce(signal: Structure):
    if signal.status == "ok" and signal.value is None:
        raise ValueError(f"{signal.name}: ok but value is None")

    if signal.status in ("no_value", "error") and signal.value is not None:
        raise ValueError(f"{signal.name}: invalid state mismatch")


# ------------------ VALIDATION ------------------

def validate_data(df: pd.DataFrame):
    if df is None or df.shape[0] == 0:
        return {"status": "fail", "reason": "Empty dataset"}
    
    if df.shape[1] == 0:
        return {"status" : "fail", "reason" : "No columns"}
        

    return {"status": "pass"}


# ------------------ SIGNALS ------------------

def dataset_size(df: pd.DataFrame) -> Structure:
    n = int(df.shape[0])

    signal = Structure(
        dimension=DIMENSION,
        name="dataset_size",
        value=n,
        status="ok",
        meta={"n_rows": n}
    )
    enforce(signal)
    return signal


def feature_count(df: pd.DataFrame) -> Structure:
    d = int(df.shape[1])

    signal = Structure(
        dimension=DIMENSION,
        name="feature_count",
        value=d,
        status="ok",
        meta={"n_features": d}
    )
    enforce(signal)
    return signal


def n_to_d_ratio(df: pd.DataFrame) -> Structure:
    n = df.shape[0]
    d = df.shape[1]

    ratio = float(n / d)

    signal = Structure(
        dimension=DIMENSION,
        name="n_to_d_ratio",
        value=ratio,
        status="ok",
        meta={"n_rows": n, "n_features": d}
    )
    enforce(signal)
    return signal


# ------------------ REGISTRY ------------------

SIGNALS_REGISTRY = [
    dataset_size,
    feature_count,
    n_to_d_ratio
]


REQUIRED_SIGNALS = {
    "dataset_size": int,
    "feature_count": int,
    "n_to_d_ratio": float,
}


# ------------------ ORCHESTRATOR ------------------

def run_sample_adequacy(df: pd.DataFrame) -> List[Structure]:

    validation = validate_data(df)

    if validation["status"] == "fail":
        return [
            Structure(
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
                Structure(
                    dimension=DIMENSION,
                    name=fn.__name__,
                    value=None,
                    status="error",
                    meta={"error": str(e)}
                )
            )

    return results

if __name__ == "__main__":
        
    results = run_sample_adequacy(df)
    print(results)