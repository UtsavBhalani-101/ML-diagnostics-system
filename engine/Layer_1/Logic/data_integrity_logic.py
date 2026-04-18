
# ------------------ ASSUMPTIONS ------------------

# * can I trust the data at all ?

ASSUMPTIONS = [
    "Data is supposed to be clean tabular data",
    "Missingness is random, not systematic",
    "Duplicates are accidental, not meaningful",
    "Columns represent independent features, not logs/events"
]


from dataclasses import dataclass
import logging
from typing import Dict, List, Optional

from engine.Layer_1.Signals.data_integrity_signals import Signal_Structure, REQUIRED_SIGNALS


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

def build_signal_map(signals: List[Signal_Structure]) -> Dict[str, Signal_Structure]:
    return {s.name: s for s in signals}


def get_value(signal_map, name):
    s = signal_map[name]
    if s.status != "ok":
        raise ValueError(f"{name} unusable")
    return s.value


def validate_signals_contract(signal_map: Dict[str, Signal_Structure]):
    for name, expected_type in REQUIRED_SIGNALS.items():
        s = signal_map[name]
        
        if s is None:
            raise ValueError(f"Missing signal: {name}")
        
        if s.status == "ok" and not isinstance(s.value, expected_type):
            raise TypeError(f"{name} invalid type")
        
        if s.status != "ok":
            raise ValueError(f"{name} is not ok: {s.status}")


# ------------------ LOGIC ------------------

def global_missing_risk(sm):
    ratio = get_value(sm, "global_missing_ratio")

    if ratio < 0.05:
        label = "ACCEPTABLE"
    elif ratio < 0.2:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"

    return TestResult(DIMENSION, "global_missing_risk", label,
                      f"ratio={ratio}", ratio)


def column_missing_risk(sm):
    data = get_value(sm, "column_missing_ratio")
    worst = data["worst_ratio"]

    if worst < 0.05:
        label = "ACCEPTABLE"
    elif worst < 0.2:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"

    return TestResult(DIMENSION, "column_missing_risk", label,
                      f"worst={worst}", worst)


def duplicate_risk(sm):
    ratio = get_value(sm, "duplicated_ratio")

    if ratio < 0.02:
        label = "ACCEPTABLE"
    elif ratio < 0.15:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"

    return TestResult(DIMENSION, "duplicate_risk", label,
                      f"ratio={ratio}", ratio)


def constant_risk(sm):
    data = get_value(sm, "constant_columns_ratio")
    ratio = data["ratio"]

    if ratio == 0:
        label = "ACCEPTABLE"
    elif ratio < 0.2:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"

    return TestResult(DIMENSION, "constant_risk", label,
                      f"ratio={ratio}", ratio)


def hidden_missing_risk(sm):
    data = get_value(sm, "hidden_missing_ratio")
    worst = data["worst_ratio"]

    if worst < 0.05:
        label = "ACCEPTABLE"
    elif worst < 0.15:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"

    return TestResult(DIMENSION, "hidden_missing_risk", label,
                      f"worst={worst}", worst)


def mixed_type_risk(sm):
    data = get_value(sm, "mixed_type_columns_ratio")
    ratio = data["ratio"]

    if ratio == 0:
        label = "ACCEPTABLE"
    elif ratio < 0.05:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"

    return TestResult(DIMENSION, "mixed_type_risk", label,
                      f"ratio={ratio}", ratio)


LOGIC_REGISTRY = [
    global_missing_risk,
    column_missing_risk,
    duplicate_risk,
    constant_risk,
    hidden_missing_risk,
    mixed_type_risk
]


def aggregate(results):
    status = "PROCEED"

    for r in results:
        if r.label == "UNACCEPTABLE":
            return OverallResult(DIMENSION, "STOP", "Unacceptable issue")
        elif r.label == "CONCERN":
            status = "REVIEW"

    return OverallResult(DIMENSION, status, "Aggregated")


def run_data_integrity(signals: List[Signal_Structure]):
    sm = build_signal_map(signals)
    validate_contract(sm)

    results = []

    for fn in LOGIC_REGISTRY:
        try:
            results.append(fn(sm))
        except Exception as e:
            results.append(TestResult(DIMENSION, fn.__name__,
                                     "ERROR", str(e), 1.0))

    return results, aggregate(results)

if __name__ == "__main__":
    run_data_integrity()