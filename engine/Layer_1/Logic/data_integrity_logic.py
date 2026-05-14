import logging
from typing import Dict, List


from engine.Layer_1.schema import Logic_OverallResult, Signal_Structure, Logic_Structure
from engine.Layer_1.Signals.data_integrity_signals import REQUIRED_SIGNALS

# ------------------ ASSUMPTIONS ------------------

# * can I trust the data at all ?

ASSUMPTIONS = [
    "Data is supposed to be clean tabular data",
    "Missingness is random, not systematic",
    "Duplicates are accidental, not meaningful",
    "Columns represent independent features, not logs/events",
]


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DIMENSION = "data_integrity"


# ------------------ ACCESS ------------------


def build_signal_map(signals: List[Signal_Structure]) -> Dict[str, Signal_Structure]:
    return {s.name: s for s in signals}


def get_value(signal_map, name):
    s = signal_map[name]
    if s.status != "ok":
        raise ValueError(f"{name} unusable")
    return s.value

# ------------------ CONTRACT VALIDATION ------------------


def validate_signals_contract(signal_map: Dict[str, Signal_Structure]):
    for name, expected_type in REQUIRED_SIGNALS.items():
        s = signal_map.get(name)

        if s is None:
            raise ValueError(f"Missing signal: {name}")

        if s.status == "ok" and not isinstance(s.value, expected_type):
            raise TypeError(f"{name} invalid type")


# ------------------ LOGIC ------------------


def global_missing_risk(sm):
    ratio = get_value(sm, "global_missing_ratio")
    total_cells = sm["global_missing_ratio"].meta["total_cells"]
    missing_cells = round(ratio * total_cells)

    if ratio < 0.05:
        label = "SAFE"
    elif ratio < 0.2:
        label = "WARNING"
    else:
        label = "CRITICAL"

    return Logic_Structure(
        dimension=DIMENSION,
        name="global_missing_risk",
        label=label,
        risk=round(ratio, 4),
        metrics={
            "missing_ratio": round(ratio, 4),
            "missing_cells": missing_cells,
            "total_cells": total_cells
        }
    )


def column_missing_risk(sm):
    data = get_value(sm, "column_missing_ratio")
    worst = data["worst_ratio"]
    per_column = data["per_column"]

    if worst < 0.05:
        label = "SAFE"
    elif worst < 0.2:
        label = "WARNING"
    else:
        label = "CRITICAL"

    flagged = {col: round(r, 4) for col, r in per_column.items() if r > 0.05}
    worst_col = max(per_column, key=per_column.get)

    return Logic_Structure(
        dimension=DIMENSION,
        name="column_missing_risk",
        label=label,
        risk=round(worst, 4),
        metrics={
            "worst_column": worst_col,
            "worst_ratio": round(worst, 4),
            "flagged_columns": flagged,
            "total_columns": len(per_column)
        }
    )


def duplicate_risk(sm: Dict[str, Signal_Structure]) -> Logic_Structure:
    ratio = get_value(sm, "duplicated_ratio")

    if ratio < 0.02:
        label = "SAFE"
    elif ratio < 0.15:
        label = "WARNING"
    else:
        label = "CRITICAL"

    return Logic_Structure(
        dimension=DIMENSION,
        name="duplicate_risk",
        label=label,
        risk=round(ratio, 4),
        metrics={
            "duplicate_risk": round(ratio, 4),
            "duplicate_rows": round(ratio * sm["duplicated_ratio"].meta["num_rows"]),
            "total_rows": sm["duplicated_ratio"].meta["num_rows"]
        }
    )



def constant_risk(sm: Dict[str, Signal_Structure]) -> Logic_Structure:
    data = get_value(sm, "constant_columns_ratio")
    ratio = data["ratio"]

    if ratio == 0:
        label = "SAFE"
    elif ratio < 0.2:
        label = "WARNING"
    else:
        label = "CRITICAL"

    return Logic_Structure(
        dimension=DIMENSION,
        name="constant_risk",
        label=label,
        risk=round(ratio, 4),
        metrics={
            "constant_columns": data["columns"],  # actual names
            "ratio": round(data["ratio"], 4),
            "count": len(data["columns"])
        }
    )


def hidden_missing_risk(sm: Dict[str, Signal_Structure]) -> Logic_Structure:
    signal = sm["hidden_missing_ratio"]
    if signal.status == "no_value":
        return Logic_Structure(
            dimension=DIMENSION,
            name="hidden_missing_risk",
            label="SAFE",
            risk=0.0,
            metrics=signal.meta
        )

    data = get_value(sm, "hidden_missing_ratio")
    worst = data["worst_ratio"]
    per_column = data["ratios"]

    if worst < 0.05:
        label = "SAFE"
    elif worst < 0.15:
        label = "WARNING"
    else:
        label = "CRITICAL"
        
    flagged = {col: round(r, 4) for col, r in per_column.items() if r > 0.0}
    worst_col = max(per_column, key=per_column.get)

    return Logic_Structure(
        dimension=DIMENSION,
        name="hidden_missing_risk",
        label=label,
        risk=round(worst, 4),
        metrics = {"worst_columns" : worst_col,
                   "worst_ratio" : round(worst, 4),
                   "flagged_columns" : flagged,
                   "total_columns" : len(per_column)}
    )


def mixed_type_risk(sm: Dict[str, Signal_Structure]) -> Logic_Structure:
    signal = sm["mixed_type_columns_ratio"]
    if signal.status == "no_value":
        return Logic_Structure(
            dimension=DIMENSION,
            name="mixed_type_risk",
            label="SAFE",
            risk=0.0,
            metrics=signal.meta
        )

    data = get_value(sm, "mixed_type_columns_ratio")
    ratio = data["ratio"]

    if ratio == 0:
        label = "SAFE"
    elif ratio < 0.05:
        label = "WARNING"
    else:
        label = "CRITICAL"

    return Logic_Structure(
        dimension=DIMENSION,
        name="mixed_type_risk",
        label=label,
        risk=round(ratio, 4),
        metrics={
            "mixed_columns": data["columns"],
            "ratio": round(data["ratio"], 4),
            "number of columns": len(data["columns"])
        }
    )


LOGIC_REGISTRY = [
    global_missing_risk,
    column_missing_risk,
    duplicate_risk,
    constant_risk,
    hidden_missing_risk,
    mixed_type_risk,
]


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


def run_data_integrity_logic(signals: List[Signal_Structure]):
    logger.info(f"Executing {DIMENSION} logic suite")
    # 1. build signals map
    sm = build_signal_map(signals)

    # 2. verify status of signals 
    if "data_validation" in sm and sm["data_validation"].status == "error":
        logger.warning(f"{DIMENSION} logic halted: data_validation error")
        err_res = Logic_Structure(
            dimension=DIMENSION,
            name="data_validation",
            label="ERROR",
            risk=1.0,
            metrics=sm["data_validation"].meta
        )
        return [err_res], aggregate_risk([err_res])

    # 3. validate signal contract 
    try:
        validate_signals_contract(sm)
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
            results.append(fn(sm))
        except Exception as e:
            logger.error(f"Logic function {fn.__name__} failed: {str(e)}")
            results.append(
                Logic_Structure(
                    dimension=DIMENSION, 
                    name=fn.__name__, 
                    label="ERROR", 
                    risk=1.0, 
                    metrics={"error" : str(e)}))

    # 5. pass the results list to aggregator 
    overall = aggregate_risk(results)

    return results, overall


if __name__ == "__main__":
    mock_signals = [
        Signal_Structure(dimension='data_integrity', name='dataset_shape', value={'rows': 891, 'cols': 12}, status='ok', meta={"total_cells": 10692}),
        Signal_Structure(dimension='data_integrity', name='global_missing_ratio', value=0.08099513655069211, status='ok', meta={'total_cells': 10692}),
        Signal_Structure(dimension='data_integrity', name='column_missing_ratio', value={'per_column': {'PassengerId': 0.0, 'Survived': 0.0, 'Pclass': 0.0, 'Name': 0.0, 'Sex': 0.0, 'Age': 0.19865319865319866, 'SibSp': 0.0, 'Parch': 0.0, 'Ticket': 0.0, 'Fare': 0.0, 'Cabin': 0.7710437710437711, 'Embarked': 0.002244668911335578}, 'worst_ratio': 0.7710437710437711}, status='ok', meta={'num_columns': 12}),
        Signal_Structure(dimension='data_integrity', name='duplicated_ratio', value=0.0, status='ok', meta={'num_rows': 891}),
        Signal_Structure(dimension='data_integrity', name='constant_columns_ratio', value={'columns': [], 'ratio': 0.0}, status='ok', meta={'total_columns': 12}),
        Signal_Structure(dimension='data_integrity', name='hidden_missing_ratio', value={'ratios': {'Name': 0.0, 'Sex': 0.0, 'Ticket': 0.0, 'Cabin': 0.7710437710437711, 'Embarked': 0.002244668911335578}, 'worst_ratio': 0.7710437710437711}, status='ok', meta={'num_object_columns': 5}),
        Signal_Structure(dimension='data_integrity', name='mixed_type_columns_ratio', value={'columns': ['Ticket'], 'ratio': 0.2}, status='ok', meta={'num_object_columns': 5})
    ]

    results, overall = run_data_integrity_logic(mock_signals)

    for r in results:
        print(r)
    print(overall)
