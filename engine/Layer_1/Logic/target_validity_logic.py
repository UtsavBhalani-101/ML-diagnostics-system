import numpy as np
import logging
from typing import List, Dict

from engine.Layer_1.schema import Signal_Structure, Logic_Structure, Logic_OverallResult
from engine.Layer_1.Signals.target_validity_signals import REQUIRED_SIGNALS


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

DIMENSION = "target_validity"



# ------------------ SIGNAL ACCESS LAYER ------------------


# convert the list of signals to dict (easy to access)
def build_signal_map(signals: List[Signal_Structure]) -> Dict[str, Signal_Structure]:
    signal_map = {}

    for s in signals:
        if s.name in signal_map:
            raise ValueError(f"Duplicate signal detected: {s.name}")
        signal_map[s.name] = s

    return signal_map


# a shortcut helper func to get the value of the signal
def get_value(signal_map: Dict[str, Signal_Structure], name: str):
    s = signal_map[name]

    if s.status != "ok":
        raise ValueError(f"{name} unusable: {s.status}")

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


def missing_risk(signal_map: Dict[str, Signal_Structure]) -> Logic_Structure:
    signal = signal_map["target_missing_ratio"]
    ratio = signal.value
    samples = signal.meta["n_samples"]

    if ratio >= 0.4:
        label = "CRITICAL"
    elif ratio > 0.1:
        label = "WARNING"
    else:
        label = "SAFE"

    impact = "BLOCKER"

    return Logic_Structure(
        dimension=DIMENSION,
        name="missing_risk",
        label=label,
        risk=round(ratio, 4),
        metrics={
            "observed": round(ratio, 4),
            "threshold": "<=0.10 safe / <=0.40 warning / >0.40 critical (target missing ratio)",
            "impact": impact,
            "missing_ratio": round(ratio, 4),
            "total_samples": samples,
            "missing_count": signal.meta["missing_count"]
        }
    )


def target_degeneracy_risk(signal_map: Dict[str, Signal_Structure]) -> Logic_Structure:
    signal = signal_map["target_degeneracy_flag"]
    flag = signal.value
    value_count = signal.meta["unique_values"]

    if flag is True:
        label = "CRITICAL"
    else:
        label = "SAFE"

    impact = "BLOCKER"

    return Logic_Structure(
        dimension=DIMENSION,
        name="target_degeneracy_risk",
        label=label,
        risk=float(flag),
        metrics={
            "observed": float(flag),
            "threshold": "False (0) = safe; True (1) = critical (is target degenerate)",
            "impact": impact,
            "is_degenerate": flag,
            "unique_value": value_count
        }
    )


def dominant_class_risk(signal_map: Dict[str, Signal_Structure]) -> Logic_Structure:
    signal = signal_map["dominant_class_ratio"]
    ratio = signal.value

    if ratio > 0.95:
        label = "CRITICAL"
    elif ratio > 0.8:
        label = "WARNING"
    else:
        label = "SAFE"

    impact = "DEGRADING"

    return Logic_Structure(
        dimension=DIMENSION,
        name="dominance_class_risk",
        label=label,
        risk=round(ratio, 4),
        metrics={
            "observed": round(ratio, 4),
            "threshold": "<=0.80 safe / <=0.95 warning / >0.95 critical (dominant class ratio)",
            "impact": impact,
            "dominant_class": signal.meta["dominant_class"],
            "dominant_ratio": ratio,
            "dominant_count": signal.meta["dominant_count"],
            "class_distribution": signal.meta["class_distribution"]
        }
    )


def target_entropy_risk(signal_map: Dict[str, Signal_Structure]) -> Logic_Structure:
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

    impact = "DEGRADING"

    return Logic_Structure(
        dimension=DIMENSION,
        name="target_entropy_risk",
        label=label,
        risk=round((1 - normalized_entropy), 4),
        metrics={
            "observed": round(normalized_entropy, 4),
            "threshold": ">=0.80 safe / >=0.50 warning / <0.50 critical (normalised entropy)",
            "impact": impact,
            "raw_entropy": round(entropy, 4),
            "normalized_entropy": round(normalized_entropy, 4),
            "num_classes": num_classes,
            "max_possible_entropy": signal.meta["max_entropy"]
        }
    )


def type_contamination_risk(signal_map: Dict[str, Signal_Structure]) -> Logic_Structure:
    signal = signal_map["type_contamination_ratio"]
    ratio = signal.value

    if ratio > 0.1:
        label = "CRITICAL"
    elif ratio > 0.05:
        label = "WARNING"
    else:
        label = "SAFE"

    impact = "BLOCKER"

    return Logic_Structure(
        dimension=DIMENSION,
        name="type_contamination_risk",
        label=label,
        risk=round(ratio, 4),
        metrics={
            "observed": round(ratio, 4),
            "threshold": "<=0.05 safe / <=0.10 warning / >0.10 critical (type contamination ratio)",
            "impact": impact,
            "contamination_ratio": round(ratio, 4),
            "contaminated_count": signal.meta["contaminated_count"],
            "major_type": signal.meta["major_type"],
            "type_breakdown": signal.meta["type_breakdown"]
        }
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


def run_target_validity_logic(signals: List[Signal_Structure]):
    logger.info(f"Executing {DIMENSION} logic suite")
    # 1. build signals map
    signal_map = build_signal_map(signals)

    # 2. verify status of signals 
    if "target_validation" in signal_map and signal_map["target_validation"].status == "error":
        logger.warning(f"{DIMENSION} logic halted: target_validation error")
        err_res = Logic_Structure(
            dimension=DIMENSION,
            name="target_validation",
            label="ERROR",
            risk=1.0,
            metrics=signal_map["target_validation"].meta
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
        Signal_Structure(dimension='target_validity', name='target_column_name', value='Ticket', status='ok', meta={'dtype': 'object'}),
        Signal_Structure(dimension='target_validity', name='target_shape', value={'rows': 891, 'cols': 1}, status='ok', meta={'n_samples': 891}),
        Signal_Structure(dimension='target_validity', name='target_missing_ratio', value=0.0, status='ok', meta={'n_samples': 891, 'missing_count': 0}),
        Signal_Structure(dimension='target_validity', name='target_degeneracy_flag', value=False, status='ok', meta={'unique_values': 681}),
        Signal_Structure(dimension='target_validity', name='dominant_class_ratio', value=0.007856341189674524, status='ok', meta={'n_samples': 891, 'dominant_class': '347082', 'dominant_count': 7, 'total_unique': 681, 'class_distribution': {'347082': 0.0079, '1601': 0.0079, 'ca. 2343': 0.0079, '3101295': 0.0067, 'ca 2144': 0.0067, '347088': 0.0067, '382652': 0.0056, 's.o.c. 14879': 0.0056, '113760': 0.0045, '19950': 0.0045, '_other': 0.936}}),
        Signal_Structure(dimension='target_validity', name='target_entropy', value=9.23300039564576, status='ok', meta={'num_classes': 681, 'max_entropy': 9.4115}),
        Signal_Structure(dimension='target_validity', name='type_contamination_ratio', value=0.0, status='ok', meta={'major_type': 'str', 'contaminated_count': 0, 'total_non_null': 891, 'type_breakdown': {'str': 891}})
    ]

    results, overall = run_target_validity_logic(mock_signals)

    for r in results:
        print(r)
    print(overall)
