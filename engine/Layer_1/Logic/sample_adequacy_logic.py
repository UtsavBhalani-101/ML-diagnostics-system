import numpy as np
import logging
from dataclasses import dataclass
from typing import Dict, Optional
from engine.Layer_1.Signals.sample_adequacy_signals import Structure, REQUIRED_SIGNALS


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


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

DIMENSION = "sample_adequacy"

# --------------------------- signal mapping ---------------------------

def build_signal_map(signals: List[Structure]) -> Dict[str, Structure]:
    signal_map = {}

    for s in signals:
        if s.name in signal_map:
            raise ValueError(f"Duplicate signal detected: {s.name}")
        signal_map[s.name] = s

    return signal_map

# --------------------------- validate signals contract and sample signals ---------------------------

def validate_signals_contract(signals: List[Structure]):
    signal_map = {s.name: s for s in signals}

    missing = set(REQUIRED_SIGNALS.keys()) - set(signal_map.keys())
    if missing:
        raise ValueError(f"Missing signals: {missing}")

    for name, expected_type in REQUIRED_SIGNALS.items():
        value = signal_map[name].value

        if not isinstance(value, expected_type):
            raise TypeError(
                f"Signal '{name}' has invalid type. "
                f"Expected {expected_type}, got {type(value)}"
            )
            

def validate_sample_signals(signals: List[Structure]):
    required = ["rows", "cols"]

    for key in required:
        if key not in signals:
            raise ValueError(f"Missing required signal: {key}")

    rows = signals["rows"]
    cols = signals["cols"]

    if rows < 0 or cols < 0:
        logger.error("Invalid rows/cols values")
        raise ValueError("rows and cols must be non-negative")

    if cols == 0:
        logger.warning("Zero columns detected")


# --------------------------- Signals ---------------------------


def low_sample_risk(signals: Dict[str, Structure]) -> TestResult:
    n = signals["rows"]
    d = signals["cols"]

    if n is None or d is None:
        return TestResult(
            dimension=DIMENSION,
            name="low_sample_risk",
            label="ERROR",
            reason="rows or counts are 0",
            risk=1.0,
            metrics={"status" : "undefined"}
        )

    ratio = n / d
    risk = np.exp(-ratio / 5)
    
    if risk < 0.2:
        label = "SAFE"
    elif risk < 0.4:
        label = "WARNING"
    else:
        label = "CRITICAL"
        
    result = TestResult(
        dimension=DIMENSION,
        name="low_sample_risk",
        label=label,
        reason="None",
        risk=risk,
        metrics=None
    )

    return result


def sample_size_risk(signals: Dict[str, Structure]) -> TestResult:
    n = signals["rows"]
    risk = np.exp(-n / 300)

    if risk < 0.2:
        label = "SAFE"
    elif risk < 0.4:
        label = "WARNING"
    else:
        label = "CRITICAL"
        
    result = TestResult(
        dimension=DIMENSION,
        name="sample_size_risk",
        label=label,
        reason="None",
        risk=risk,
        metrics=None
    )

LOGIC_REGISTRY = [
    low_sample_risk,
    sample_size_risk
]

# --------------------------- Aggregate ---------------------------

def aggregate_sample_adequacy(signals: List[TestResult]) -> TestResult:
    try:
        status = "PROCEED"
        
        for res in results:
            if res.label == "CRITICAL":
                status = "STOP"
                break
            elif res.label == "WARNING" and status != "STOP":
                status = "REVIEW"
        
        result = OverallResult(
            dimension=DIMENSION,
            status=status,
            reason="None"
        )
        
    except Exception as e:
        result = OverallResult(
            dimension=DIMENSION,
            status="ERROR",
            reason="Some internal problem occured in calculating overall result"
        )

    return result


# --------------------------- Orchestrator ---------------------------


def run_sample_adequacy(signals: List[Structure]) -> tuple[List[TestResult], OverallResult]:
    
        # Step 1: build map

    signal_map = build_signal_map(signals)

    # Step 2: validate contract
    validate_signals_contract(signals)

    results: List[TestResult] = []
    
    for logic_fn in LOGIC_REGISTRY:
        try: 
            result = logic_fn(signal_map)
            results.append(result)
            
            logger.debug(f"{logic_fn.__name__} success")

        except Exception as e:
            logger.error("Signal failed", extra={
                "signal": logic_fn.__name__,
                "error": str(e)
            })
            
            results.append(
                TestResult(
                    dimension=DIMENSION,
                    name=logic_fn.__name__,
                    label="ERROR",
                    reason=str(e),
                    risk=1.0,
                    metrics={"error": str(e)}
                )
            )


if __name__ == "__main__":
    run_sample_adequacy()