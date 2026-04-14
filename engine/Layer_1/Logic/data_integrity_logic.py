import sys
import os

# Add root project path to allow direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from dataclasses import dataclass
import logging
from typing import Dict, List, Optional
from engine.Layer_1.Signals.data_integrity_signals import Signal_Structure

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
    


DIMENSION = "data_integrity"


def validate_signals(signals: List[Signal_Structure]):
    pass


def global_missing_risk(signals: List[Signal_Structure]) -> TestResult:
    gm_signal = next(s for s in signals if s.name == "global_missing_ratio")
    ratio = gm_signal.value
    
    if ratio < 0.05:
        label = "ACCEPTABLE"
    elif ratio < 0.2:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"
        
    result = TestResult(
        dimension=DIMENSION,
        name="global_missing_risk",
        label=label,
        reason="None",
        risk=ratio,
        metrics=gm_signal.meta
    )
    
    logger.info(f"Compute missing_risk: {ratio}")
    return result

def column_missing_risk(signals: List[Signal_Structure]) -> TestResult:
    cm_signal = next(s for s in signals if s.name == "column_missing_ratio")
    worst_ratio = cm_signal.value['worst_ratio']

    if worst_ratio < 0.05:
        label = "ACCEPTABLE"
    elif worst_ratio < 0.2:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"
        
    result = TestResult(
        dimension=DIMENSION,
        name="column_missing_risk",
        label=label,
        reason="None",
        risk=worst_ratio,
        metrics=cm_signal.meta
    )
    return result

def duplicate_risk(signals: List[Signal_Structure]) -> TestResult:
    dup_signal = next(s for s in signals if s.name == "duplicate_ratio")
    ratio = dup_signal.value

    if ratio < 0.02:
        label = "ACCEPTABLE"
    elif ratio < 0.15:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"
    
    result = TestResult(
        dimension=DIMENSION,
        name="duplicate_risk",
        label=label,
        reason="None",
        risk=ratio,
        metrics=dup_signal.meta
    )
    
    logger.info(f"Compute duplicate_risk: {ratio}")
    return result

def constant_risk(signals: List[Signal_Structure]) -> TestResult:
    const_signal = next(s for s in signals if s.name == "constant_columns")
    ratio = const_signal.value["ratio"]
    
    if ratio == 0.0:
        label = "ACCEPTABLE"
    elif ratio < 0.2:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"
        
    result = TestResult(
        dimension=DIMENSION,
        name="constant_risk",
        label=label,
        reason="None",
        risk=ratio,
        metrics=const_signal.meta
    )
    
    logger.info(f"Compute constant_risk: {ratio}")
    return result

def hidden_missing_risk(signals: List[Signal_Structure]) -> TestResult:
    hidden_miss_signal = next(s for s in signals if s.name == "hidden_missing_ratio")
    worst_ratio = hidden_miss_signal.value['worst_ratio']
    
    if worst_ratio < 0.05:
        label = "ACCEPTABLE"
    elif worst_ratio < 0.15:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"
        
    result = TestResult(
        dimension=DIMENSION,
        name="hidden_missing_risk",
        label=label,
        reason="None",
        risk=worst_ratio,
        metrics=hidden_miss_signal.meta
    )
    
    logger.info(f"Compute hidden_missing_risk: {worst_ratio}")
    return result

def mixed_type_risk(signals: List[Signal_Structure]) -> TestResult:
    mixed_signal = next(s for s in signals if s.name == "mixed_type_columns")
    ratio = mixed_signal.value['ratio']
    
    if ratio == 0:
        label = "ACCEPTABLE"
    elif ratio < 0.05:
        label = "CONCERN"
    else:
        label = "UNACCEPTABLE"
        
    result = TestResult(
        dimension=DIMENSION,
        name="mixed_type_risk",
        label=label,
        reason="None",
        risk=ratio,
        metrics=mixed_signal.meta
    )    
    
    logger.info(f"Compute mixed_type_risk: {ratio}")
    return result

LOGIC_REGISTRY = [
    global_missing_risk,
    column_missing_risk,
    duplicate_risk,
    constant_risk,
    hidden_missing_risk,
    mixed_type_risk
]

def aggregate_risk(results: List[TestResult]) -> OverallResult:
    try:
        status = "PROCEED"
        
        for res in results:
            if res.label == "UNACCEPTABLE":
                status = "STOP"
            elif res.label == "CONCERN":
                status = "REVIEW"
        
        result =  OverallResult(
            dimension=DIMENSION,
            status=status,
            reason="None"
        )

    except Exception as e:
        logger.error(f"Overall result computation failed: {str(e)}")
        result = OverallResult(
            dimension=DIMENSION,
            status="STOP",
            reason="Some Internal failure occured"
        )
        
    return result

def run_data_integrity(signals: List[Signal_Structure]) -> tuple[List[TestResult], OverallResult]:
    results: List[TestResult] = []
    
    for logic_fn in LOGIC_REGISTRY:
        try: 
            result = logic_fn(signals)
            results.append(result)
        except Exception as e:
            logger.error(
                f"Logic computation failed: {logic_fn.__name__}",
                extra={"signal": logic_fn.__name__, "error": str(e)}
            )
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
    
    # Example signals provided by the user
    mocked_signals = [
        Signal_Structure(dimension='data_integrity', name='dataset_shape', value={'rows': 10000, 'cols': 3}, meta=None),
        Signal_Structure(dimension='data_integrity', name='global_missing_ratio', value=0.0, meta={'total_cells': 30000}),
        Signal_Structure(dimension='data_integrity', name='column_missing_ratio', value={'per_column': {'cat_1': 0.0, 'cat_2': 0.0, 'cat_3': 0.0}, 'worst_ratio': 0.0}, meta={'num_columns': 3}),
        Signal_Structure(dimension='data_integrity', name='duplicate_ratio', value=0.9976, meta={'num_rows': 10000}),
        Signal_Structure(dimension='data_integrity', name='constant_columns', value={'columns': [], 'ratio': 0.0}, meta={'total_columns': 3}),
        Signal_Structure(dimension='data_integrity', name='hidden_missing_ratio', value={'ratios': {'cat_1': 0.1534, 'cat_2': 0.0, 'cat_3': 0.0}, 'worst_ratio': 0.1534}, meta={'num_object_columns': 3}),
        Signal_Structure(dimension='data_integrity', name='mixed_type_columns', value={'columns': [], 'ratio': 0.0}, meta={'num_object_columns': 3})
    ]
    
    # Run the logic orchestrator
    test_results, overall_result = run_data_integrity(mocked_signals)
    
    print("=== TEST RESULTS ===")
    for res in test_results:
        print(res)
        
    print("\n=== OVERALL RESULT ===")
    print(f"Status: {overall_result}")
    
