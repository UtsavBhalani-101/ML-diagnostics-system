from dataclasses import dataclass
import sys
import numpy as np
import os
import logging
from typing import Dict, List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from engine.Layer_1.Signals.data_integrity_signals import Structure, REQUIRED_SIGNALS


# ------------------ ASSUMPTIONS ------------------

# * can I trust the data at all ?

ASSUMPTIONS = [
    "Data is supposed to be clean tabular data",
    "Missingness is random, not systematic",
    "Duplicates are accidental, not meaningful",
    "Columns represent independent features, not logs/events",
]


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DIMENSION = "data_integrity"


@dataclass(frozen=True)
class TestResult:
    dimension: str
    name: str
    label: str
    reason: str
    risk: float
    metrics: Optional[Dict] = None


@dataclass(frozen=True)
class OverallResult:
    dimension: str
    status: str
    reason: str


# ------------------ ACCESS ------------------


def build_signal_map(signals: List[Structure]) -> Dict[str, Structure]:
    return {s.name: s for s in signals}


def get_value(signal_map, name):
    s = signal_map[name]
    if s.status != "ok":
        raise ValueError(f"{name} unusable")
    return s.value


def validate_signals_contract(signal_map: Dict[str, Structure]):
    for name, expected_type in REQUIRED_SIGNALS.items():
        s = signal_map.get(name)

        if s is None:
            raise ValueError(f"Missing signal: {name}")

        if s.status != "ok":
            raise ValueError(f"{name} is not ok: {s.status}")

        if s.status == "ok" and not isinstance(s.value, expected_type):
            raise TypeError(f"{name} invalid type")


# ------------------ LOGIC ------------------


def global_missing_risk(sm: Dict[str, Structure]) -> TestResult:
    ratio = get_value(sm, "global_missing_ratio")

    if ratio < 0.05:
        label = "SAFE"
    elif ratio < 0.2:
        label = "WARNING"
    else:
        label = "CRITICAL"

    return TestResult(DIMENSION, "global_missing_risk", label, f"ratio={ratio}", ratio)


def column_missing_risk(sm: Dict[str, Structure]) -> TestResult:
    data = get_value(sm, "column_missing_ratio")
    worst = data["worst_ratio"]

    if worst < 0.05:
        label = "SAFE"
    elif worst < 0.2:
        label = "WARNING"
    else:
        label = "CRITICAL"

    return TestResult(DIMENSION, "column_missing_risk", label, f"worst={worst}", worst)


def duplicate_risk(sm: Dict[str, Structure]) -> TestResult:
    ratio = get_value(sm, "duplicated_ratio")

    if ratio < 0.02:
        label = "SAFE"
    elif ratio < 0.15:
        label = "WARNING"
    else:
        label = "CRITICAL"

    return TestResult(DIMENSION, "duplicate_risk", label, f"ratio={ratio}", ratio)


def constant_risk(sm: Dict[str, Structure]) -> TestResult:
    data = get_value(sm, "constant_columns_ratio")
    ratio = data["ratio"]

    if ratio == 0:
        label = "SAFE"
    elif ratio < 0.2:
        label = "WARNING"
    else:
        label = "CRITICAL"

    return TestResult(DIMENSION, "constant_risk", label, f"ratio={ratio}", ratio)


def hidden_missing_risk(sm: Dict[str, Structure]) -> TestResult:
    data = get_value(sm, "hidden_missing_ratio")
    worst = data["worst_ratio"]

    if worst < 0.05:
        label = "SAFE"
    elif worst < 0.15:
        label = "WARNING"
    else:
        label = "CRITICAL"

    return TestResult(DIMENSION, "hidden_missing_risk", label, f"worst={worst}", worst)


def mixed_type_risk(sm: Dict[str, Structure]) -> TestResult:
    data = get_value(sm, "mixed_type_columns_ratio")
    ratio = data["ratio"]

    if ratio == 0:
        label = "SAFE"
    elif ratio < 0.05:
        label = "WARNING"
    else:
        label = "CRITICAL"

    return TestResult(DIMENSION, "mixed_type_risk", label, f"ratio={ratio}", ratio)


LOGIC_REGISTRY = [
    global_missing_risk,
    column_missing_risk,
    duplicate_risk,
    constant_risk,
    hidden_missing_risk,
    mixed_type_risk,
]


def aggregate_risk(results: List[TestResult]) -> OverallResult:

    risks = [r.risk for r in results if r.label == "ok"]

    if not risks:
        return OverallResult(DIMENSION, "REVIEW", "No valid signals")

    total_risk = 1 - np.prod([1 - r for r in risks])

    if total_risk >= 0.7:
        status = "STOP"
    elif total_risk >= 0.3:
        status = "REVIEW"
    else:
        status = "PROCEED"

    return OverallResult(
        DIMENSION,
        status,
        f"Aggregated risk={total_risk:.3f}"
    )

def run_data_integrity(signals: List[Structure]):
    sm = build_signal_map(signals)
    validate_signals_contract(sm)

    results = []

    for fn in LOGIC_REGISTRY:
        try:
            results.append(fn(sm))
        except Exception as e:
            results.append(TestResult(DIMENSION, fn.__name__, "ERROR", str(e), 1.0))

    return results, aggregate_risk(results)


if __name__ == "__main__":
    mock_signals = [
        Structure(
            dimension="data_integrity",
            name="dataset_shape",
            value={"rows": 10, "cols": 5},
            status="ok",
            meta=None,
        ),
        Structure(
            dimension="data_integrity",
            name="global_missing_ratio",
            value=0.04,
            status="ok",
            meta={"total_cells": 50},
        ),
        Structure(
            dimension="data_integrity",
            name="column_missing_ratio",
            value={
                "per_column": {
                    "age": 0.2,
                    "salary": 0.0,
                    "city": 0.0,
                    "score": 0.0,
                    "constant_col": 0.0,
                },
                "worst_ratio": 0.2,
            },
            status="ok",
            meta={"num_columns": 5},
        ),
        Structure(
            dimension="data_integrity",
            name="duplicated_ratio",
            value=0.3,
            status="ok",
            meta={"num_rows": 10},
        ),
        Structure(
            dimension="data_integrity",
            name="constant_columns_ratio",
            value={"columns": ["constant_col"], "ratio": 0.2},
            status="ok",
            meta={"total_columns": 5},
        ),
        Structure(
            dimension="data_integrity",
            name="hidden_missing_ratio",
            value={"ratios": {"city": 0.3, "score": 0.0}, "worst_ratio": 0.3},
            status="ok",
            meta={"num_object_columns": 2},
        ),
        Structure(
            dimension="data_integrity",
            name="mixed_type_columns_ratio",
            value={"columns": ["score"], "ratio": 0.2},
            status="ok",
            meta={"num_object_columns": 2},
        ),
    ]

    results, overall = run_data_integrity(mock_signals)

    for r in results:
        print(r)
    print(overall)
