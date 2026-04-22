import sys
import os

# Ensure the root directory is on the path so 'engine' can be imported when running standalone
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import numpy as np
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

from engine.Layer_1.Signals.sample_adequacy_signals import Structure, REQUIRED_SIGNALS

# ------------------ ASSUMPTIONS ------------------

# * do I have enough data to even learn ?

ASSUMPTIONS = [
    "Model is classical tabular ML (not deep learning)", 
    "Features are moderately useful (not garbage, not perfect)",
    "Noise level is moderate",
    "Data is IID (no strong temporal dependence)",
]



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
    risk: float


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

        if s.status == "ok":
            if not isinstance(s.value, expected_type):
                raise TypeError(f"{name} must be {expected_type}")


# ------------------ LOGIC FUNCTIONS ------------------

def duplicated_risk(signal_map: Dict[str, Structure]) -> TestResult:
    ratio = get_value(signal_map, "duplicated_ratio")
    
    if ratio >= 0.5:
        label = "CRITICAL"
    elif ratio >= 0.2:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return TestResult(
        dimension=DIMENSION,
        name="duplicated_risk",
        label=label,
        reason=f"Duplicated ratio = {ratio:.3f}",
        risk=float(ratio),
        metrics={"ratio": float(ratio)}
    )

def effective_sample_size_risk(signal_map: Dict[str, Structure]) -> TestResult:
    score = get_value(signal_map, "effective_sample_size")
    risk = float(np.exp(-score))
    
    if risk > 0.8:
        label = "CRITICAL"
    elif risk > 0.5:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return TestResult(
        dimension=DIMENSION,
        name="effective_sample_size_risk",
        label=label,
        reason=f"NN distance = {score:.3f}",
        risk=risk,
        metrics={"nn_distance": float(score)}
    )

def sample_dependency_risk(signal_map: Dict[str, Structure]) -> TestResult:
    score = get_value(signal_map, "sample_dependency_score")
    risk = float(np.exp(-score))
    
    if risk > 0.8:
        label = "CRITICAL"
    elif risk > 0.5:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return TestResult(
        dimension=DIMENSION,
        name="sample_dependency_risk",
        label=label,
        reason=f"Dependency score = {score:.3f}",
        risk=risk,
        metrics={"step_distance": float(score)}
    )

def label_noise_risk(signal_map: Dict[str, Structure]) -> TestResult:
    score = get_value(signal_map, "label_noise_proxy")
    risk = float(score)
    
    if risk > 0.4:
        label = "CRITICAL"
    elif risk > 0.2:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return TestResult(
        dimension=DIMENSION,
        name="label_noise_risk",
        label=label,
        reason=f"Label noise proxy = {score:.3f}",
        risk=risk,
        metrics={"noise_proxy": risk}
    )

def feature_variance_risk(signal_map: Dict[str, Structure]) -> TestResult:
    ratio = get_value(signal_map, "feature_variance_score")
    risk = float(ratio)
    
    if risk >= 0.5:
        label = "CRITICAL"
    elif risk >= 0.2:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return TestResult(
        dimension=DIMENSION,
        name="feature_variance_risk",
        label=label,
        reason=f"Low variance ratio = {ratio:.3f}",
        risk=risk,
        metrics={"low_variance_ratio": risk}
    )

def marginal_coverage_risk(signal_map: Dict[str, Structure]) -> TestResult:
    coverage = get_value(signal_map, "marginal_coverage")
    risk = float(1.0 - coverage)
    
    if risk >= 0.6:
        label = "CRITICAL"
    elif risk >= 0.3:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return TestResult(
        dimension=DIMENSION,
        name="marginal_coverage_risk",
        label=label,
        reason=f"Marginal coverage = {coverage:.3f}",
        risk=risk,
        metrics={"coverage": float(coverage)}
    )

def joint_coverage_risk(signal_map: Dict[str, Structure]) -> TestResult:
    coverage = get_value(signal_map, "joint_coverage")
    risk = float(1.0 - coverage)
    
    if risk >= 0.7:
        label = "CRITICAL"
    elif risk >= 0.4:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return TestResult(
        dimension=DIMENSION,
        name="joint_coverage_risk",
        label=label,
        reason=f"Joint coverage = {coverage:.3f}",
        risk=risk,
        metrics={"coverage": float(coverage)}
    )

# ------------------ REGISTRY ------------------

LOGIC_REGISTRY = [
    duplicated_risk,
    effective_sample_size_risk,
    sample_dependency_risk,
    label_noise_risk,
    feature_variance_risk,
    marginal_coverage_risk,
    joint_coverage_risk
]

# ------------------ AGGREGATION ------------------

def aggregate_risk(results: List[TestResult]) -> OverallResult:
    risks = [r.risk for r in results if r.label != "ERROR"]

    if not risks:
        return OverallResult(DIMENSION, "REVIEW", "No valid signals", 1.0)

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
        f"Aggregated risk={total_risk:.3f}",
        total_risk
    )

# ------------------ ORCHESTRATOR ------------------

def run_sample_adequacy(signals: List[Structure]):

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

    overall = aggregate_risk(results)

    return results, overall


if __name__ == "__main__":
    mock_signals = [
        Structure(dimension=DIMENSION, name='duplicated_ratio', value=0.1, status='ok'),
        Structure(dimension=DIMENSION, name='effective_sample_size', value=1.5, status='ok'),
        Structure(dimension=DIMENSION, name='sample_dependency_score', value=1.2, status='ok'),
        Structure(dimension=DIMENSION, name='label_noise_proxy', value=0.1, status='ok'),
        Structure(dimension=DIMENSION, name='feature_variance_score', value=0.1, status='ok'),
        Structure(dimension=DIMENSION, name='marginal_coverage', value=0.9, status='ok'),
        Structure(dimension=DIMENSION, name='joint_coverage', value=0.8, status='ok')
    ]

    results, overall = run_sample_adequacy(mock_signals)

    for r in results:
        print(r)
    print(overall)
