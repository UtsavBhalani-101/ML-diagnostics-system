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
    risk: float


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
        },
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
        metrics=None,
    )


# ! evaluate task type is a global property, move it out


LOGIC_REGISTRY = [
    missing_risk,
    target_degeneracy_risk,
    dominant_class_risk,
    target_entropy_risk,
    type_contamination_risk,
]


# ------------------ AGGREGATION ------------------


LABEL_WEIGHTS = {"CRITICAL": 1.0, "WARNING": 0.5, "SAFE": 0.0, "ERROR": 1.0}


def aggregate_risk(results):
    valid = [r for r in results if r.label in LABEL_WEIGHTS]

    if not valid:
        return OverallResult(DIMENSION, "REVIEW", "No valid signals", 1.0)

    weighted = 0

    # severity-weighted average
    weighted = sum(LABEL_WEIGHTS[r.label] * r.risk for r in valid)
    print(weighted)
    total = sum(LABEL_WEIGHTS[r.label] for r in valid)
    score = weighted / total if total > 0 else 0.0

    # label still driven by worst case
    if any(r.label == "CRITICAL" for r in valid):
        status = "STOP"
    elif any(r.label == "WARNING" for r in valid):
        status = "REVIEW"
    else:
        status = "PROCEED"

    return OverallResult(
        dimension=DIMENSION, status=status, reason=f"score={score:.3f}", risk=score
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
        Structure(
            dimension="target_viability",
            name="target_missing_ratio",
            value=0.0,
            status="ok",
            meta={"n_samples": 891},
        ),
        Structure(
            dimension="target_viability",
            name="target_degeneracy_flag",
            value=False,
            status="ok",
            meta={"unique_values": 2},
        ),
        Structure(
            dimension="target_viability",
            name="dominant_class_ratio",
            value=0.6161616161616161,
            status="ok",
            meta={"n_samples": 891},
        ),
        Structure(
            dimension="target_viability",
            name="target_entropy",
            value=0.9607078989902569,
            status="ok",
            meta={"num_classes": 2},
        ),
        Structure(
            dimension="target_viability",
            name="type_contamination_ratio",
            value=0.0,
            status="ok",
            meta={"major_type": "<class 'str'>"},
        ),
        Structure(
            dimension="target_viability",
            name="dataset_shape",
            value={"rows": 891, "cols": 1},
            status="ok",
            meta={"n_samples": 891},
        ),
    ]

    results, overall = run_target_viability(mock_signals)

    # for r in results:
    # print(r)
    # print(overall)
