
# ------------------ ASSUMPTIONS ------------------

# * do I have enough data to even learn ?

ASSUMPTIONS = [
    "Model is classical tabular ML (not deep learning)", 
    "Features are moderately useful (not garbage, not perfect)",
    "Noise level is moderate",
    "Data is IID (no strong temporal dependence)",
]

import sys
import os

# Ensure the root directory is on the path so 'engine' can be imported when running standalone
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import numpy as np
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

from engine.Layer_1.Signals.sample_adequacy_signals import Structure, REQUIRED_SIGNALS


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DIMENSION = "sample_adequacy"


# ------------------ RESULT STRUCTURES ------------------

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


# ------------------ SIGNAL ACCESS ------------------

def build_signal_map(signals: List[Structure]) -> Dict[str, Structure]:
    signal_map = {}
    for s in signals:
        if s.name in signal_map:
            raise ValueError(f"Duplicate signal: {s.name}")
        signal_map[s.name] = s
    return signal_map


def get_value(signal_map: Dict[str, Structure], name: str):
    s = signal_map[name]

    if s.status != "ok":
        raise ValueError(f"{name} unusable: {s.status}")

    return s.value


def get_optional(signal_map: Dict[str, Structure], name: str):
    s = signal_map[name]

    if s.status == "ok":
        return s.value

    return None


# ------------------ CONTRACT VALIDATION ------------------

def validate_signals_contract(signal_map: Dict[str, Structure]):
    for name, expected_type in REQUIRED_SIGNALS.items():
        s = signal_map.get(name)

        if s is None:
            raise ValueError(f"Missing signal: {name}")

        if s.status == "ok" and not isinstance(s.value, expected_type):
            raise TypeError(f"{name} must be {expected_type}")
        
        if s.status != "ok":
            raise ValueError(f"{name} is not ok: {s.status}")
        
        n = signal_map["dataset_size"].value
        d = signal_map["feature_count"].value
        ratio = signal_map["n_to_d_ratio"].value

        if abs(ratio - n/d) > 1e-9:
            raise ValueError("n_to_d_ratio inconsistent with dataset_size and feature_count")


# ------------------ LOGIC ------------------

def n_to_d_risk(signal_map: Dict[str, Structure]) -> TestResult:

    ratio = get_value(signal_map, "n_to_d_ratio")

    # Thresholds (interpretable)
    if ratio < 2:
        label = "CRITICAL"
        risk = 1.0
    elif ratio < 5:
        label = "WARNING"
        risk = 0.7
    elif ratio < 10:
        label = "OK"
        risk = 0.4
    elif ratio < 20:
        label = "GOOD"
        risk = 0.2
    else:
        label = "SAFE"
        risk = 0.1

    return TestResult(
        DIMENSION,
        "n_to_d_risk",
        label,
        f"n/d ratio = {ratio:.2f}",
        risk,
        metrics={"n": n, "d": d}
    )


def sample_size_risk(signal_map: Dict[str, Structure]) -> TestResult:
    n = get_value(signal_map, "dataset_size")

    if n < 100:
        label = "CRITICAL"
        risk = 1.0
    elif n < 500:
        label = "WARNING"
        risk = 0.7
    elif n < 2000:
        label = "OK"
        risk = 0.4
    else:
        label = "SAFE"
        risk = 0.1

    return TestResult(
        DIMENSION,
        "sample_size_risk",
        label,
        f"n = {n}",
        risk
    )


def combined_sample_adequacy(signal_map: Dict[str, Structure]) -> TestResult:
    n = get_value(signal_map, "dataset_size")
    d = get_value(signal_map, "feature_count")

    ratio = get_value(signal_map, "n_to_d_ratio")

    # Combined logic (more realistic)
    if ratio < 2:
        label = "CRITICAL"
        reason = "Severely underdetermined (n/d < 2)"
        risk = 1.0

    elif n < 200 and d > 20:
        label = "CRITICAL"
        reason = "Too few samples for feature space"
        risk = 0.9

    elif ratio < 5:
        label = "WARNING"
        reason = "Low samples per feature"
        risk = 0.7

    elif n < 500:
        label = "WARNING"
        reason = "Small dataset size"
        risk = 0.6

    else:
        label = "SAFE"
        reason = "Sufficient samples and ratio"
        risk = 0.2

    return TestResult(
        DIMENSION,
        "combined_sample_adequacy",
        label,
        reason,
        risk,
        metrics={"n": n, "d": d, "ratio": round(ratio, 2)}
    )


# ------------------ REGISTRY ------------------

LOGIC_REGISTRY = [
    n_to_d_risk,
    sample_size_risk,
    combined_sample_adequacy
]


# ------------------ AGGREGATION ------------------

def aggregate(results: List[TestResult]) -> OverallResult:
    status = "PROCEED"

    for r in results:
        if r.label == "ERROR":
            return OverallResult(DIMENSION, "STOP", "Error occured when calculating")
        if r.label == "CRITICAL":
            return OverallResult(DIMENSION, "STOP", "Critical sample adequacy issue")
        elif r.label == "WARNING":
            status = "REVIEW"

    return OverallResult(DIMENSION, status, "Sample adequacy acceptable")


# ------------------ ORCHESTRATOR ------------------

def run_sample_adequacy_logic(signals: List[Structure]):

    signal_map = build_signal_map(signals)

    validate_signals_contract(signal_map)

    results = []

    for fn in LOGIC_REGISTRY:
        try:
            results.append(fn(signal_map))
        except Exception as e:
            results.append(
                TestResult(
                    DIMENSION,
                    fn.__name__,
                    "ERROR",
                    str(e),
                    1.0
                )
            )

    overall = aggregate(results)

    return results, overall


if __name__ == "__main__":
    result = run_sample_adequacy_logic([Structure(dimension='sample_adequacy', name='dataset_size', value=2, status='no_value', meta={'n_rows': 2}), Structure(dimension='sample_adequacy', name='feature_count', value=5, status='ok', meta={'n_features': 5}), Structure(dimension='sample_adequacy', name='n_to_d_ratio', value=0.4, status='ok', meta={'n_rows': 2, 'n_features': 5})])
    
    print(result)
    
    
