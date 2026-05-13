
import numpy as np
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

from engine.Layer_1.Signals.sample_adequacy_signals import Structure, REQUIRED_SIGNALS

# ------------------ ASSUMPTIONS ------------------

# * ?

ASSUMPTIONS = [

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
    risk: float
    metrics: Optional[Dict]


@dataclass(frozen=True)
class OverallResult:
    dimension: str
    status: str
    peak_risk : float | None
    severity_score : float | None
    composite : float | None
    critical: List[str]    # names of CRITICAL signals
    warnings: List[str]    # names of WARNING signals
    safe: List[str]        # names of SAFE signals
    errors: List[str]      # names of ERROR signals

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
        reason = s.meta.get("reason") or s.meta.get("error") or s.status
        raise ValueError(f"{name} unusable: {reason}")

    return s.value


# ------------------ CONTRACT VALIDATION ------------------

def strength():
    pass

def stability_across_slices():
    pass


def directional_consistency():
    # monotonicity
    pass
    
def leakage_detection():
    pass


def proxy_relationship():
    pass


def perturbation():
    pass

# ------------------ REGISTRY ------------------

LOGIC_REGISTRY = [

]

# ------------------ AGGREGATION ------------------

LABEL_SCORE = {"CRITICAL": 1.0, "WARNING": 0.5, "SAFE": 0.0}

def aggregate_risk(results: List[TestResult]) -> OverallResult:
    valid = [r for r in results if r.label in LABEL_SCORE]
    errors = [r.name for r in results if r.label not in LABEL_SCORE]

    if not valid:
        return OverallResult(
            dimension=DIMENSION,
            status="REVIEW",
            peak_risk=None,
            severity_score=None,
            composite=None,
            critical=[],
            warnings=[],
            safe=[],
            errors=errors
        )

    criticals = [r.name for r in valid if r.label == "CRITICAL"]
    warnings = [r.name for r in valid if r.label == "WARNING"]
    safe = [r.name for r in valid if r.label == "SAFE"]

    if criticals:
        status = "STOP"
    elif warnings:
        status = "REVIEW"
    else:
        status = "PROCEED"

    # worst case — drives the status decision
    peak_risk = round(max(r.risk for r in valid), 4)
    
    # breadth — what fraction of signals are problematic
    severity_score = round(sum(LABEL_SCORE[r.label] for r in valid) / len(valid), 4)
    
    # combined — peak tells you how bad the worst is,
    # severity tells you how widespread it is
    composite = round((0.6 * peak_risk + 0.4 * severity_score) , 4)
    
    return OverallResult(
        dimension=DIMENSION,
        status=status,
        peak_risk=peak_risk,
        severity_score=severity_score,
        composite=composite,
        critical=criticals,
        warnings=warnings,
        safe=safe,
        errors=errors
    )

# ------------------ ORCHESTRATOR ------------------

def run_sample_adequacy(signals: List[Structure]):
    
    pass


if __name__ == "__main__":
    pass
