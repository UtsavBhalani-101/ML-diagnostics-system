import sys
import os

# Ensure the root directory is on the path so 'engine' can be imported when running standalone
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import numpy as np
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

from engine.Layer_1.Signals.target_sanity_signals import Structure, REQUIRED_SIGNALS


# ------------------ ASSUMPTIONS ------------------

# * Is the target even usable ?

ASSUMPTIONS = [
    "task : supervised",
    "target : stationary (distribution stable)",
    "Signal exists in data (not random noise)",
    "classes are expected to be reasonably balance",
]



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
        risk=missing_ratio,
        metrics=None
    )


def target_degeneracy_risk(signal_map: Dict[str, Structure]) -> TestResult:
    flag = get_value(signal_map, "target_degeneracy_flag")
    
    if flag is True:
        label = "CRITICAL"
    else:
        label = "SAFE"
        
    return TestResult(
        dimension=DIMENSION,
        name="target_degeneracy_risk",
        label=label,
        reason=f"Degeneracy flag: {flag}",
        risk=float(flag),
        metrics=None
    )


def dominant_class_risk(signal_map: Dict[str, Structure]) -> TestResult:
    ratio = get_value(signal_map, "dominant_class_ratio")
    
    if ratio > 0.95:
        label = "CRITICAL"
    elif ratio > 0.8:
        label = "WARNING"
    else:
        label = "SAFE"
        
    
    return TestResult(
        dimension=DIMENSION,
        name="dominance_class_risk",
        label=label,
        reason=f"dominance ratio: {ratio}",
        risk=ratio,
        metrics=None
    )


def target_entropy_risk(signal_map: Dict[str, Structure]) -> TestResult:
      signal = signal_map["target_entropy"]

      entropy = signal.value
      num_classes = signal.meta["num_classes"]

      if num_classes <= 1:
          normalized_entropy = 0.0
      else:
          max_entropy = float(np.log2(num_classes))
          normalized_entropy = entropy / max_entropy

      if normalized_entropy >= 0.8:
          label = "SAFE"
      elif normalized_entropy >= 0.5:
          label = "WARNING"
      else:
          label = "CRITICAL"

      return TestResult(
          dimension=DIMENSION,
          name="target_entropy_risk",
          label=label,
          reason=(
              f"target entropy: {entropy:.4f}, "
              f"normalized: {normalized_entropy:.4f}, "
              f"classes: {num_classes}"
          ),
          risk=1 - normalized_entropy,
          metrics={
              "entropy": entropy,
              "normalized_entropy": normalized_entropy,
              "num_classes": num_classes,
          }
      )

def type_contamination_risk(signal_map: Dict[str, Structure]) -> TestResult:
    ratio = get_value(signal_map, "type_contamination_ratio")
    
    if ratio > 0.1:
        label = "CRITICAL"
    elif ratio > 0.05:
        label = "WARNING"
    else:
        label = "SAFE"
        
    
    return TestResult(
        dimension=DIMENSION,
        name="type_contamination_risk",
        label=label,
        reason=f"type_contamination ratio: {ratio}",
        risk=ratio,
        metrics=None
    )



def evaluate_task_type(signal_map: Dict[str, Structure]) -> TestResult:
    degeneracy_signal = signal_map["target_degeneracy_flag"]
    if degeneracy_signal.status != "ok":
        raise ValueError("target_degeneracy_flag unusable")
    
    unique_count = degeneracy_signal.meta["unique_values"]
    shape = get_value(signal_map, "dataset_shape")
    total = shape["rows"]

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
        },
    )


LOGIC_REGISTRY = [
    missing_risk, 
    target_degeneracy_risk, 
    dominant_class_risk, 
    target_entropy_risk, 
    type_contamination_risk, 
    evaluate_task_type
]


# ------------------ AGGREGATION ------------------


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
                    risk=1.0,
                )
            )

    overall = aggregate_risk(results)

    return results, overall


if __name__ == "__main__":
    mock_signals = [
        Structure(dimension=DIMENSION, name='target_missing_ratio', value=0.05, status='ok'),
        Structure(dimension=DIMENSION, name='target_degeneracy_flag', value=False, status='ok', meta={'unique_values': 10}),
        Structure(dimension=DIMENSION, name='dominant_class_ratio', value=0.4, status='ok'),
        Structure(dimension=DIMENSION, name='target_entropy', value=0.9, status='ok'),
        Structure(dimension=DIMENSION, name='type_contamination_ratio', value=0.0, status='ok'),
        Structure(dimension=DIMENSION, name='dataset_shape', value={'rows': 1000}, status='ok')
    ]

    results, overall = run_target_viability(mock_signals)

    for r in results:
        print(r)
    print(overall)
