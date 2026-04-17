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


DIMENSION = "target_viability"


# --------------------------- signal mapping ---------------------------

def build_signal_map(signals: List[Structure]) -> Dict[str, Structure]:
    signal_map = {}

    for s in signals:
        if s.name in signal_map:
            raise ValueError(f"Duplicate signal detected: {s.name}")
        signal_map[s.name] = s

    return signal_map

# --------------------------- validate signals contract and target col ---------------------------

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
            


def validate_target_signals(signals: List[Structure]):
    pass


# --------------------------- Signals ---------------------------



def missing_risk(signals: Dict[str, Structure]) -> TestResult:
    missing_ratio = signals["target_missing_ratio"].value
    
    if missing_ratio == 1.0:
        label = "CRITICAL"
    elif missing_ratio >= 0.4:
        label = "CRITICAL"
    elif missing_ratio > 0.1:
        label = "WARNING"
    else:
        label = "SAFE"
    
    result = TestResult(
        dimension= DIMENSION,
        name= "missing_risk",
        label=label,
        reason="None",
        risk=missing_ratio,
        metrics=None
    )
        
    return result


def class_imbalance_risk(signals: Dict[str, Structure]) -> TestResult:
    imbalance_score = signals["class_imbalance_score"].value
    
    if imbalance_score is None:
        return TestResult(
            dimension=DIMENSION,
            name="class_imbalance_risk",
            label="ERROR",
            reason="Missing imbalance score",
            risk=1.0,
            metrics={"status" : "undefined"}
        )
    
    if imbalance_score > 0.95:
        label = "CRITICAL"
    elif imbalance_score > 0.8:
        label = "WARNING"
    else:
        label = "SAFE"
        
    result = TestResult(
        dimension=DIMENSION,
        name="class_imbalace_risk",
        label=label,
        reason="None",
        risk=imbalance_score,
        metrics=None
    )
    
    return result


def variance_risk(signals: Dict[str, Structure]) -> TestResult:
    variance = signals["target_variance"].value["variance"]
    target_range = signals["target_variance"].value["target_range"]
    
    if variance is None:
        return TestResult(
            dimension=DIMENSION,
            name="varaince_risk",
            label="ERROR",
            reason="Missing variance",
            risk=1.0,
            metrics={"status" : "undefined"}
        )
    
    if target_range is None:
        return TestResult(
            dimension=DIMENSION,
            name="variance_risk",
            label="ERROR",
            reason="Missing target_range",
            risk=1.0,
            metrics={"status" : "undefined"}
        )

    normalized_variance = variance / (target_range ** 2)    
    
    if variance == 0.0 or target_range == 0:
        label = "CRITICAL"
                
    elif normalized_variance < 1e-4:
        label = "WARNING"
        
    else:
        label = "SAFE"
        
    result = TestResult(
        dimension=DIMENSION,
        name="variance_risk",
        label=label,
        reason="None",
        risk=normalized_variance,
        metrics=None
    )   

    return result


def evaluate_task_type(signals: Dict[str, Structure]) -> TestResult:
    unique_count = signals["target_unique_count"].value
    total = signals["dataset_shape"].value["rows"]
    
    if total == 0:
        return TestResult(
            dimension=DIMENSION,
            name="task_type_inference",
            label="ERROR",
            reason="total rows are 0",
            risk=1.0,
            metrics={"status" : "undefined"},
        )

    unique_ratio = unique_count / total if total > 0 else 0.0

    # -------------------------
    # HARD DECISION ZONES
    # -------------------------

    if unique_count <= 20:
        task = "classification"
        confidence = 1 - (unique_count / 20)

    elif unique_ratio > 0.05:
        task = "regression"
        confidence = min(1.0, unique_ratio / 0.05)

    else:
        task = "ambiguous"
        confidence = 0.5

    # -------------------------
    # FAILURE BOUNDARIES
    # -------------------------

    if confidence < 0.4:
        label = "UNACCEPTABLE"
        reason = "Unable to confidently determine task type"

    elif confidence < 0.7:
        label = "CONCERN"
        reason = "Task type is ambiguous"

    else:
        label = "ACCEPTABLE"
        reason = "Task type inferred with high confidence"

    result = TestResult(
        dimension=DIMENSION,
        name="task_type_inference",
        label=label,
        reason=reason,
        risk=1 - confidence,
        metrics={
            "task_type": task,
            "confidence": round(confidence, 3),
            "unique_count": unique_count,
            "unique_ratio": round(unique_ratio, 4),
        },
    )    
        
    return result


LOGIC_REGISTRY = [
    missing_risk,
    class_imbalance_risk,
    variance_risk,
    evaluate_task_type
]

# --------------------------- Aggregation ---------------------------


def aggregate_risk(results: List[TestResult]) -> OverallResult:
    
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


def run_target_viability(signals: List[Structure]) -> tuple[List[TestResult], OverallResult]:

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
            
    
    overall = aggregate_risk(results)
    
    return results, overall

if __name__ == "__main__":
    mock_Signals = [
            Structure(dimension='target_viability', name='target_missing_ratio', value=0.08333333333333333, meta={'n_samples': 12}),
            Structure(dimension='target_viability', name='target_variance', value={'variance': 0.24000000000000005, 'target_range': 1.0}, meta={'valid_numeric_samples': 10}),
            Structure(dimension='target_viability', name='target_unique_count', value=3, meta={'n_samples': 12}),
            Structure(dimension='target_viability', name='class_imbalance_score', value=0.5454545454545454, meta={'n_samples': 12}),
            Structure(dimension='target_viability', name='dataset_shape', value={'rows': 12, 'cols': 1}, meta={'n_samples': 12})
        ]
    
    validate_signals_contract(mock_Signals)
    
    validate_target_signals(mock_Signals)
    
    result, overall = run_target_viability(mock_Signals)
    
    print(result)
    print(overall)
    