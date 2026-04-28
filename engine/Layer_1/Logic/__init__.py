"""
Logic orchestrator for Layer 1.

Exposes evaluate_* functions that the pipeline calls.
Each function takes a flat signal dict and returns a dimension dict
matching the formatter's expected structure:
  {
    "signals": { ... },
    "dominant_risks": { ... },
    "additive_risks": { ... },
    "total_risk": float,
    "status": str,
    "primary_issues": [{ "name": str, "risk": float, "action": str }],
    "interpretation": str
  }
"""
import logging

from engine.Layer_1.Logic.data_integrity_logic import run_data_integrity
from engine.Layer_1.Logic.target_sanity_logic import run_target_viability
from engine.Layer_1.Logic.sample_adequacy_logic import run_sample_adequacy
from engine.Layer_1.primary_issues import generate_primary_issues

logger = logging.getLogger(__name__)


def _build_dimension_dict(
    *,
    dimension_signals: dict,
    dominant_risks: dict,
    additive_risks: dict,
    total_risk: float,
    status: str,
    interpretation: str,
) -> dict:
    dimension = {
        "signals": dimension_signals,
        "dominant_risks": dominant_risks,
        "additive_risks": additive_risks,
        "total_risk": round(float(total_risk), 4),
        "status": status,
        "primary_issues": generate_primary_issues(dominant_risks),
        "interpretation": interpretation,
    }

    required = {
        "signals",
        "dominant_risks",
        "additive_risks",
        "total_risk",
        "status",
        "primary_issues",
        "interpretation",
    }
    missing = required.difference(dimension)
    if missing:
        raise ValueError(
            f"Incomplete Layer 1 dimension output: missing {sorted(missing)}"
        )

    return dimension


def _overall_risk(overall) -> float:
    """Use the new Layer 1 aggregate score, falling back to peak risk for errors."""
    risk = getattr(overall, "composite", None)
    if risk is None:
        risk = getattr(overall, "peak_risk", None)
    return round(float(risk or 0.0), 4)


def _interpretation(dimension_name: str, overall) -> str:
    status = getattr(overall, "status", "REVIEW")
    critical = getattr(overall, "critical", []) or []
    warnings = getattr(overall, "warnings", []) or []
    errors = getattr(overall, "errors", []) or []

    if errors:
        return f"{dimension_name} could not be fully evaluated because {', '.join(map(str, errors))} failed."
    if critical:
        return f"{dimension_name} has critical structural risk from {', '.join(critical)}."
    if warnings:
        return f"{dimension_name} needs review because {', '.join(warnings)} raised warning-level risk."
    if status == "PROCEED":
        return f"{dimension_name} checks did not raise material structural risk."
    return f"{dimension_name} completed with status {status}."


def _build_breakdown(results: list) -> tuple:
    dominant = {r.name: r.risk for r in results if r.risk >= 0.5 and r.label != "ERROR"}
    additive = {r.name: r.risk for r in results if 0.0 < r.risk < 0.5 and r.label != "ERROR"}
    
    # ensure any ERROR states are marked somehow, or just excluded from breakdown
    # If they failed, their risk is 1.0 but they are not 'dominant' structural risks, they are errors.
    errors = {r.name: 1.0 for r in results if r.label == "ERROR"}
    if errors:
        dominant.update(errors)
        
    return dominant, additive


def evaluate_data_integrity(structures: list, flat_signals: dict) -> dict:
    """Evaluate data integrity dimension."""
    logger.info("Evaluating data_integrity dimension")

    dim_signals = {
        k: flat_signals[k] for k in [
            "rows", "cols",
            "global_missing_ratio", "column_missing_ratio",
            "duplicated_ratio", "duplicate_ratio", "constant_columns", "constant_ratio",
            "hidden_missing_ratio", "mixed_type_columns", "mixed_ratio"
        ] if k in flat_signals
    }

    dim_structs = [s for s in structures if s.dimension == "data_integrity"]
    results, overall = run_data_integrity(dim_structs)
    dominant_risks, additive_risks = _build_breakdown(results)

    return _build_dimension_dict(
        dimension_signals=dim_signals,
        dominant_risks=dominant_risks,
        additive_risks=additive_risks,
        total_risk=_overall_risk(overall),
        status=overall.status,
        interpretation=_interpretation("Data integrity", overall),
    )


def evaluate_target_viability(structures: list, flat_signals: dict) -> dict:
    """Evaluate target viability dimension."""
    logger.info("Evaluating target_viability dimension")

    dim_signals = {
        k: flat_signals.get(k) for k in [
            "target_column_name", "target_rows",
            "target_missing_ratio", "target_degeneracy_flag",
            "dominant_class_ratio", "target_entropy",
            "type_contamination_ratio", "dataset_shape", "task_confidence"
        ] if k in flat_signals
    }

    dim_structs = [s for s in structures if s.dimension == "target_viability"]
    if not dim_structs:
        return _build_dimension_dict(
            dimension_signals=dim_signals,
            dominant_risks={},
            additive_risks={},
            total_risk=0.0,
            status="PROCEED",
            interpretation="Target viability checks were skipped because no target column was provided.",
        )

    try:
        results, overall, _signal_map = run_target_viability(dim_structs)
        dominant_risks, additive_risks = _build_breakdown(results)

        return _build_dimension_dict(
            dimension_signals=dim_signals,
            dominant_risks=dominant_risks,
            additive_risks=additive_risks,
            total_risk=_overall_risk(overall),
            status=overall.status,
            interpretation=_interpretation("Target viability", overall),
        )
    except Exception as e:
        logger.warning(f"Target viability evaluation failed: {e}, defaulting to SAFE")
        return _build_dimension_dict(
            dimension_signals=dim_signals,
            dominant_risks={},
            additive_risks={},
            total_risk=0.0,
            status="SAFE",
            interpretation="Target checks were unavailable, so no structural target risk was raised.",
        )


def evaluate_sample_adequacy(structures: list, flat_signals: dict) -> dict:
    """Evaluate sample adequacy dimension."""
    logger.info("Evaluating sample_adequacy dimension")

    dim_signals = {
        k: flat_signals.get(k) for k in [
            "duplicated_ratio", "effective_sample_size", "effective_sample_score",
            "sample_dependency_score","feature_variance_score", 
            "marginal_coverage", "joint_coverage"
        ] if k in flat_signals
    }

    dim_structs = [s for s in structures if s.dimension == "sample_adequacy"]
    results, overall = run_sample_adequacy(dim_structs)
    dominant_risks, additive_risks = _build_breakdown(results)

    return _build_dimension_dict(
        dimension_signals=dim_signals,
        dominant_risks=dominant_risks,
        additive_risks=additive_risks,
        total_risk=_overall_risk(overall),
        status=overall.status,
        interpretation=_interpretation("Sample adequacy", overall),
    )
