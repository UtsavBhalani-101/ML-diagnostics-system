
# ------------------ ASSUMPTIONS ------------------

# * Is the target even usable ?

ASSUMPTIONS = [
    "task : supervised",
    "target : stationary (distribution stable)",
    "Signal exists in data (not random noise)",
    "classes are expected to be reasonably balance"
]


import sys
import os

# Ensure the root directory is on the path so 'engine' can be imported when running standalone
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import numpy as np
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

from engine.Layer_1.Signals.target_sanity_signals import Structure, REQUIRED_SIGNALS

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DIMENSION = "target_viability"


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


# ------------------ SIGNAL ACCESS LAYER ------------------

def build_signal_map(signals: List[Structure]) -> Dict[str, Structure]:
    signal_map = {}

    for s in signals:
        if s.name in signal_map:
            raise ValueError(f"Duplicate signal detected: {s.name}")
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

        if s.status == "ok":
            if not isinstance(s.value, expected_type):
                raise TypeError(f"{name} must be {expected_type}")
            
        if s.status != "ok":
            raise ValueError(f"{name} is not ok: {s.status}")


# ------------------ LOGIC FUNCTIONS ------------------

def missing_risk(signal_map: Dict[str, Structure]) -> TestResult:
    missing_ratio = get_value(signal_map, "target_missing_ratio")

    if missing_ratio >= 0.4:
        label = "CRITICAL"
    elif missing_ratio > 0.1:
        label = "WARNING"
    else:
        label = "SAFE"

    return TestResult(
        dimension=DIMENSION,
        name="missing_risk",
        label=label,
        reason=f"Missing ratio = {missing_ratio}",
        risk=missing_ratio
    )


def class_imbalance_risk(signal_map: Dict[str, Structure]) -> TestResult:
    imbalance_score = get_optional(signal_map, "class_imbalance_score")

    if imbalance_score > 0.95:
        label = "CRITICAL"
    elif imbalance_score > 0.8:
        label = "WARNING"
    else:
        label = "SAFE"

    return TestResult(
        dimension=DIMENSION,
        name="class_imbalance_risk",
        label=label,
        reason=f"Imbalance score = {imbalance_score}",
        risk=imbalance_score
    )


def variance_risk(signal_map: Dict[str, Structure]) -> TestResult:
    variance_data = get_optional(signal_map, "target_variance")

    if variance_data is None:
        return TestResult(
            dimension=DIMENSION,
            name="variance_risk",
            label="ERROR",
            reason="Variance unavailable",
            risk=1.0
        )

    variance = variance_data["variance"]
    target_range = variance_data["target_range"]

    if variance == 0.0 or target_range == 0:
        label = "CRITICAL"
        risk = 1.0
        reason = "Zero variance or range"

    else:
        normalized_variance = variance / (target_range ** 2)

        if normalized_variance < 1e-4:
            label = "WARNING"
        else:
            label = "SAFE"

        risk = normalized_variance
        reason = f"Normalized variance = {normalized_variance:.6f}"

    return TestResult(
        dimension=DIMENSION,
        name="variance_risk",
        label=label,
        reason=reason,
        risk=risk
    )


def evaluate_task_type(signal_map: Dict[str, Structure]) -> TestResult:
    unique_count = get_value(signal_map, "target_unique_count")

    unique_ratio = unique_count / total

    if unique_count <= 20:
        task = "classification"
        confidence = 1 - (unique_count / 20)

    elif unique_ratio > 0.05:
        task = "regression"
        confidence = min(1.0, unique_ratio / 0.05)

    else:
        task = "ambiguous"
        confidence = 0.5

    if confidence < 0.4:
        label = "UNACCEPTABLE"
        reason = "Low confidence in task type"
    elif confidence < 0.7:
        label = "CONCERN"
        reason = "Ambiguous task type"
    else:
        label = "ACCEPTABLE"
        reason = "Clear task type"

    return TestResult(
        dimension=DIMENSION,
        name="task_type_inference",
        label=label,
        reason=reason,
        risk=1 - confidence,
        metrics={
            "task_type": task,
            "confidence": round(confidence, 3),
            "unique_ratio": round(unique_ratio, 4),
        }
    )


LOGIC_REGISTRY = [
    missing_risk,
    class_imbalance_risk,
    variance_risk,
    evaluate_task_type
]


# ------------------ AGGREGATION ------------------

def aggregate_risk(results: List[TestResult]) -> OverallResult:

    status = "PROCEED"

    for r in results:
        if r.label == "CRITICAL":
            return OverallResult(DIMENSION, "STOP", "Critical issue detected")
        elif r.label == "WARNING":
            status = "REVIEW"

    return OverallResult(DIMENSION, status, "Aggregated from tests")


# ------------------ ORCHESTRATOR ------------------

def run_target_viability(signals: List[Structure]):

    signal_map = build_signal_map(signals)

    validate_signals_contract(signal_map)

    results = []

    for fn in LOGIC_REGISTRY:
        try:
            results.append(fn(signal_map))
        except Exception as e:
            results.append(
                TestResult(
                    dimension=DIMENSION,
                    name=fn.__name__,
                    label="ERROR",
                    reason=str(e),
                    risk=1.0
                )
            )

    overall = aggregate_risk(results)

    return results, overall

if __name__ == "__main__":
    
    mock_Signals = [Structure(dimension='target_viability', name='target_missing_ratio', value=0.08333333333333333, status='ok', meta={'n_samples': 12}),
        Structure(dimension='target_viability', name='target_variance', value={'variance': 0.24000000000000005, 'target_range': 1.0}, status='ok', meta={'valid_numeric_samples': 10}),
        Structure(dimension='target_viability', name='target_unique_count', value=3, status='ok', meta={'n_samples': 12}),
        Structure(dimension='target_viability', name='class_imbalance_score', value=0.5454545454545454, status='ok', meta={'n_samples': 12}),
        Structure(dimension='target_viability', name='dataset_shape', value={'rows': 12, 'cols': 1}, status='ok', meta={'n_samples': 12})]

    signal_mapped = build_signal_map(mock_Signals)
    
    validate_signals_contract(signal_mapped)
        
    result, overall = run_target_viability(signal_mapped)
    
    print(result)
    print(overall)
    
    # print((mock_Signals))
    