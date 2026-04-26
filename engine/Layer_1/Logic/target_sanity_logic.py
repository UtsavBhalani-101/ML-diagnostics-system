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
    signal = signal_map["target_missing_ratio"]
    ratio = signal.value
    samples = signal.meta["n_samples"]
    missing_count = int(ratio * samples)

    if ratio >= 0.4:
        label = "CRITICAL"
    elif ratio > 0.1:
        label = "WARNING"
    else:
        label = "SAFE"

    return TestResult(
        dimension=DIMENSION,
        name="missing_risk",
        label=label,
        risk=round(ratio, 4),
        metrics={
            "missing_ratio": round(ratio, 4),
            "total_samples": samples,
            "missing_count": missing_count
        }
    )


def target_degeneracy_risk(signal_map: Dict[str, Structure]) -> TestResult:
    signal = signal_map["target_degeneracy_flag"]
    flag = signal.value
    value_count = signal.meta["unique_values"]

    if flag is True:
        label = "CRITICAL"
    else:
        label = "SAFE"

    return TestResult(
        dimension=DIMENSION,
        name="target_degeneracy_risk",
        label=label,
        risk=float(flag),
        metrics={
            "is_degenerate": flag,
            "unique_value" : value_count
        }
    )


def dominant_class_risk(signal_map: Dict[str, Structure]) -> TestResult:
    signal = signal_map["dominant_class_ratio"]
    ratio = signal.value

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
        risk=round(ratio, 4),
        metrics={
            "dominant_class": signal.meta["dominant_class"],
            "dominant_ratio": ratio,
            "dominant_count": signal.meta["dominant_count"],
            "class_distribution": signal.meta["class_distribution"]
        }
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
        risk=round((1 - normalized_entropy) , 4),
        metrics={
            "raw_entropy": round(entropy, 4),
            "normalized_entropy": round(normalized_entropy, 4),
            "num_classes": num_classes,
            "max_possible_entropy": signal.meta["max_entropy"]
        }
    )


def type_contamination_risk(signal_map: Dict[str, Structure]) -> TestResult:
    signal = signal_map["type_contamination_ratio"]
    ratio = signal.value
    
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
        risk=round(ratio, 4),
        metrics={
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


def run_target_viability(signals: List[Structure]):

    # 1. build signals map
    signal_map = build_signal_map(signals)

    # 2. verify status of signals 
    if "data_validation" in signal_map and signal_map["data_validation"].status == "error":
        err_res = TestResult(
            dimension=DIMENSION,
            name="data_validation",
            label="ERROR",
            risk=1.0,
            metrics=signal_map["data_validation"].meta
        )
        return [err_res], aggregate_risk([err_res]), signal_map

    # 3. validate signal contract 
    try:
        validate_signals_contract(signal_map)
    except (ValueError, TypeError) as e:
        err_res = TestResult(
            dimension=DIMENSION,
            name="contract_validation",
            label="ERROR",
            risk=1.0,
            metrics={"error": str(e)}
        )
        return [err_res], aggregate_risk([err_res]), signal_map

    # 4. run a loop on registry, for each func pass the signal_map,
    # if the signal don't have required valid data (like value), just store this in exception and the error
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
                    risk=1.0,
                    metrics={"error": str(e)}
                )
            )

    # 5. pass the results list to aggregator 
    overall = aggregate_risk(results)

    return results, overall, signal_map  # ^ the formatter will extract the target name 


if __name__ == "__main__":
    mock_signals = [
        Structure(dimension='target_viability', name='target_column_name', value='Survived', status='ok', meta={'dtype': 'int64'}),
        Structure(dimension='target_viability', name='target_shape', value={'rows': 891, 'cols': 1}, status='ok', meta={'n_samples': 891}),
        Structure(dimension='target_viability', name='target_missing_ratio', value=0.0, status='ok', meta={'n_samples': 891, 'missing_count': 0}),
        Structure(dimension='target_viability', name='target_degeneracy_flag', value=False, status='ok', meta={'unique_values': 2}),
        Structure(dimension='target_viability', name='dominant_class_ratio', value=0.6161616161616161, status='ok', meta={'n_samples': 891, 'dominant_class': '1', 'dominant_count': 549, 'class_distribution': {'1': 0.6162, '0': 0.3838}}),
        Structure(dimension='target_viability', name='target_entropy', value=0.9607078989902569, status='ok', meta={'num_classes': 2, 'max_entropy': 1.0}),
        Structure(dimension='target_viability', name='type_contamination_ratio', value=0.0, status='ok', meta={'major_type': 'int', 'contaminated_count': 0, 'total_non_null': 891, 'type_breakdown': {'int': 891}})
    ]

    results, overall, mock_signals = run_target_viability(mock_signals)

    for r in results:
        print(r)
    print(overall)
