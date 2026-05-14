
import numpy as np
import logging
from typing import List, Dict

from engine.Layer_1.schema import Signal_Structure, Logic_Structure, Logic_OverallResult
from engine.Layer_1.Signals.sample_adequacy_signals import REQUIRED_SIGNALS

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

# ------------------ SIGNAL ACCESS ------------------

def build_signal_map(signals: List[Signal_Structure]) -> Dict[str, Signal_Structure]:
    signal_map = {}
    for s in signals:
        if s.name in signal_map:
            raise ValueError(f"Duplicate signal: {s.name}")
        signal_map[s.name] = s
    return signal_map


def get_value(signal_map: Dict[str, Signal_Structure], name: str):
    s = signal_map[name]

    if s.status != "ok":
        reason = s.meta.get("reason") or s.meta.get("error") or s.status
        raise ValueError(f"{name} unusable: {reason}")

    return s.value


# ------------------ CONTRACT VALIDATION ------------------

def validate_signals_contract(signal_map: Dict[str, Signal_Structure]):
    for name, expected_type in REQUIRED_SIGNALS.items():
        s = signal_map.get(name)

        if s is None:
            raise ValueError(f"Missing signal: {name}")

        if s.status == "ok":
            if not isinstance(s.value, expected_type):
                raise TypeError(f"{name} must be {expected_type}")


# ------------------ LOGIC FUNCTIONS ------------------

def duplicated_risk(signal_map: Dict[str, Signal_Structure]) -> Logic_Structure:
    signal = signal_map["duplicated_ratio"]
    ratio = get_value(signal_map, "duplicated_ratio")
    
    if ratio >= 0.5:
        label = "CRITICAL"
    elif ratio >= 0.2:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return Logic_Structure(
        dimension=DIMENSION,
        name="duplicated_risk",
        label=label,
        risk=round(float(ratio), 4),
        metrics={
            "total_rows" : signal.meta["total_rows"],
            "duplicate_rows" : signal.meta["duplicate_rows"],
            "unique_rows" : signal.meta["unique_rows"]
        }
    )

def effective_sample_size_risk(signal_map: Dict[str, Signal_Structure]) -> Logic_Structure:
    signal = signal_map["effective_sample_size"]
    if signal.status == "no_value":
        return Logic_Structure(
            dimension=DIMENSION,
            name="effective_sample_size_risk",
            label="CRITICAL",
            risk=1.0,
            metrics=signal.meta
        )

    score = get_value(signal_map, "effective_sample_size")
    risk = float(np.exp(-score))
    
    if risk > 0.8:
        label = "CRITICAL"
    elif risk > 0.5:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return Logic_Structure(
        dimension=DIMENSION,
        name="effective_sample_size_risk",
        label=label,
        risk=round(risk, 4),
        metrics={
            "avg_nn_distance": signal.meta["avg_nn_distance"],
            "sample_size_used": signal.meta["sample_size_used"],
            "total_rows": signal.meta["total_rows"],
            "feature_count": signal.meta["feature_count"]
        }
    )

def sample_dependency_risk(signal_map: Dict[str, Signal_Structure]) -> Logic_Structure:
    signal = signal_map["sample_dependency_score"]
    if signal.status == "no_value":
        return Logic_Structure(
            dimension=DIMENSION,
            name="sample_dependency_risk",
            label="CRITICAL",
            risk=1.0,
            metrics=signal.meta
        )

    score = get_value(signal_map, "sample_dependency_score")
    risk = float(np.exp(-score))
    
    if risk > 0.8:
        label = "CRITICAL"
    elif risk > 0.5:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return Logic_Structure(
        dimension=DIMENSION,
        name="sample_dependency_risk",
        label=label,
        risk=round(risk, 4),
        metrics={
            "avg_step_distance": signal.meta["avg_step_distance"],
            "total_rows": signal.meta["total_rows"],
            "feature_count": signal.meta["feature_count"]
        }
    )


def feature_variance_risk(signal_map: Dict[str, Signal_Structure]) -> Logic_Structure:
    signal = signal_map["feature_variance_score"]
    if signal.status == "no_value":
        return Logic_Structure(
            dimension=DIMENSION,
            name="feature_variance_risk",
            label="SAFE",
            risk=0.0,
            metrics=signal.meta
        )

    ratio = get_value(signal_map, "feature_variance_score")
    risk = float(ratio)
    
    if risk >= 0.5:
        label = "CRITICAL"
    elif risk >= 0.2:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return Logic_Structure(
        dimension=DIMENSION,
        name="feature_variance_risk",
        label=label,
        risk=round(risk, 4),
        metrics={
            "low_variance_ratio": signal.meta["low_variance_ratio"],
            "low_variance_columns": signal.meta["low_variance_columns"],
            "low_variance_count": signal.meta["low_variance_count"],
            "total_features": signal.meta["total_features"],
            "threshold_used": signal.meta["threshold_used"]
        }
    )

def marginal_coverage_risk(signal_map: Dict[str, Signal_Structure]) -> Logic_Structure:
    signal = signal_map["marginal_coverage"]
    if signal.status == "no_value":
        return Logic_Structure(
            dimension=DIMENSION,
            name="marginal_coverage_risk",
            label="CRITICAL",
            risk=1.0,
            metrics=signal.meta
        )

    coverage = get_value(signal_map, "marginal_coverage")
    risk = float(1.0 - coverage)
    
    if risk >= 0.6:
        label = "CRITICAL"
    elif risk >= 0.3:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return Logic_Structure(
        dimension=DIMENSION,
        name="marginal_coverage_risk",
        label=label,
        risk=round(risk, 4),
        metrics={
            "avg_bin_coverage": signal.meta["avg_bin_coverage"],
            "per_column_coverage": signal.meta["per_column_coverage"],
            "bins_used": signal.meta["bins_used"],
            "columns_evaluated": signal.meta["columns_evaluated"]
        }
    )

def joint_coverage_risk(signal_map: Dict[str, Signal_Structure]) -> Logic_Structure:
    signal = signal_map["joint_coverage"]
    if signal.status == "no_value":
        reason = str(signal.meta.get("reason", ""))
        risk = 0.0 if "insufficient features" in reason else 0.5
        label = "SAFE" if risk == 0.0 else "WARNING"
        return Logic_Structure(
            dimension=DIMENSION,
            name="joint_coverage_risk",
            label=label,
            risk=risk,
            metrics=signal.meta
        )

    coverage = get_value(signal_map, "joint_coverage")
    risk = float(1.0 - coverage)
    
    if risk >= 0.7:
        label = "CRITICAL"
    elif risk >= 0.4:
        label = "WARNING"
    else:
        label = "SAFE"
        
    return Logic_Structure(
        dimension=DIMENSION,
        name="joint_coverage_risk",
        label=label,
        risk=round(risk, 4),
        metrics={
            "grid_fill": signal.meta["grid_fill"],
            "columns_used": signal.meta["columns_used"],
            "bins_used": signal.meta["bins_used"],
            "filled_cells": signal.meta["filled_cells"],
            "total_cells": signal.meta["total_cells"]
        }
    )

# ------------------ REGISTRY ------------------

LOGIC_REGISTRY = [
    duplicated_risk,
    effective_sample_size_risk,
    sample_dependency_risk,
    feature_variance_risk,
    marginal_coverage_risk,
    joint_coverage_risk
]

# ------------------ AGGREGATION ------------------

LABEL_SCORE = {"CRITICAL": 1.0, "WARNING": 0.5, "SAFE": 0.0}

def aggregate_risk(results: List[Logic_Structure]) -> Logic_OverallResult:
    valid = [r for r in results if r.label in LABEL_SCORE]
    errors = [r.name for r in results if r.label not in LABEL_SCORE]

    if not valid:
        return Logic_OverallResult(
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
    
    return Logic_OverallResult(
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

def run_sample_adequacy_logic(signals: List[Signal_Structure]):
    logger.info(f"Executing {DIMENSION} logic suite")
    # 1. build signals map
    signal_map = build_signal_map(signals)

    # 2. verify status of signals and allow only valid signals
    if "data_validation" in signal_map and signal_map["data_validation"].status == "error":
        logger.warning(f"{DIMENSION} logic halted: data_validation error")
        err_res = Logic_Structure(
            dimension=DIMENSION,
            name="data_validation",
            label="ERROR",
            risk=1.0,
            metrics=signal_map["data_validation"].meta
        )
        return [err_res], aggregate_risk([err_res])

    # 3. validate signal contract 
    try:
        validate_signals_contract(signal_map)
    except (ValueError, TypeError) as e:
        logger.error(f"{DIMENSION} contract validation failed: {str(e)}")
        err_res = Logic_Structure(
            dimension=DIMENSION,
            name="contract_validation",
            label="ERROR",
            risk=1.0,
            metrics={"error": str(e)}
        )
        return [err_res], aggregate_risk([err_res])

    # 4. run a loop on registry, for each func pass the signal_map,
    # if the signal don't have required valid data (like value), just store this in exception and the error
    results = []

    for fn in LOGIC_REGISTRY:
        try:
            logger.debug(f"Evaluating logic: {fn.__name__}")
            results.append(fn(signal_map))
        except Exception as e:
            logger.error(f"Logic function {fn.__name__} failed: {str(e)}")
            results.append(
                Logic_Structure(
                    dimension=DIMENSION,
                    name=fn.__name__,
                    label="ERROR",
                    risk=1.0,
                    metrics={"error": str(e)}
                )
            )
            
    # 5. pass the results list to aggregator 
    overall = aggregate_risk(results)

    return results, overall


if __name__ == "__main__":
    mock_signals = [
        Signal_Structure(dimension='sample_adequacy', name='duplicated_ratio', value=0.0, status='ok', meta={'n': 891}),
        Signal_Structure(dimension='sample_adequacy', name='effective_sample_size', value=2.8023705022704237, status='ok', meta={'avg_nn_distance': 2.8023705022704237}),
        Signal_Structure(dimension='sample_adequacy', name='sample_dependency_score', value=11.466907040283509, status='ok', meta={'avg_step_distance': 11.466907040283509}),
        Signal_Structure(dimension='sample_adequacy', name='feature_variance_score', value=0.07142857142857142, status='ok', meta={'low_variance_ratio': 0.07142857142857142}),
        Signal_Structure(dimension='sample_adequacy', name='marginal_coverage', value=0.31428571428571417, status='ok', meta={'avg_bin_coverage': 0.31428571428571417}),
        Signal_Structure(dimension='sample_adequacy', name='joint_coverage', value=1.0, status='ok', meta={'grid_fill': 1.0})
    ]

    results, overall = run_sample_adequacy_logic(mock_signals)

    for r in results:
        print(r)
    print(overall)
