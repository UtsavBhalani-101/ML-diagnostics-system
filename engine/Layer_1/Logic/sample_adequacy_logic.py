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


# ------------------ LOGIC ------------------

def low_sample_risk(signal_map: Dict[str, Structure]) -> TestResult:
    n = get_value(signal_map, "dataset_size")
    d = get_value(signal_map, "feature_count")

    if d == 0:
        return TestResult(
            dimension=DIMENSION,
            name="low_sample_risk",
            label="ERROR",
            reason="No features",
            risk=1.0
        )

    ratio = n / d
    risk = float(np.exp(-ratio / 5))

    if risk < 0.2:
        label = "SAFE"
    elif risk < 0.4:
        label = "WARNING"
    else:
        label = "CRITICAL"

    return TestResult(
        dimension=DIMENSION,
        name="low_sample_risk",
        label=label,
        reason=f"n/d ratio = {ratio:.3f}",
        risk=risk
    )


def sample_size_risk(signal_map: Dict[str, Structure]) -> TestResult:
    n = get_value(signal_map, "dataset_size")

    risk = float(np.exp(-n / 300))

    if risk < 0.2:
        label = "SAFE"
    elif risk < 0.4:
        label = "WARNING"
    else:
        label = "CRITICAL"

    return TestResult(
        dimension=DIMENSION,
        name="sample_size_risk",
        label=label,
        reason=f"n = {n}",
        risk=risk
    )


LOGIC_REGISTRY = [
    low_sample_risk,
    sample_size_risk
]


# ------------------ AGGREGATION ------------------

def aggregate(results: List[TestResult]) -> OverallResult:
    status = "PROCEED"

    for r in results:
        if r.label == "CRITICAL":
            return OverallResult(DIMENSION, "STOP", "Critical issue")
        elif r.label == "WARNING":
            status = "REVIEW"

    return OverallResult(DIMENSION, status, "Aggregated result")


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
                    dimension=DIMENSION,
                    name=fn.__name__,
                    label="ERROR",
                    reason=str(e),
                    risk=1.0
                )
            )

    overall = aggregate(results)

    return results, overall

if __name__ == "__main__":
    run_sample_adequacy_logic()