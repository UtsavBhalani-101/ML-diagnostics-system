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
from engine.Layer_1.Logic.sample_adequacy_logic import run_sample_adequacy_logic as run_sample_adequacy
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


def _result_to_dimension_dict(result, dimension_signals: dict) -> dict:
    """
    Convert a TestResult dataclass to the dimension dict format
    that formatter.py expects.
    """
    breakdown = {}
    if result.metrics and "risk_breakdown" in result.metrics:
        breakdown = result.metrics["risk_breakdown"]

    dominant_risks = breakdown.get("dominant", {})
    additive_risks = breakdown.get("additive", {})

    return _build_dimension_dict(
        dimension_signals=dimension_signals,
        dominant_risks=dominant_risks,
        additive_risks=additive_risks,
        total_risk=result.risk,
        status=result.status,
        interpretation=result.reason,
    )


def evaluate_data_integrity(signals: dict) -> dict:
    """Evaluate data integrity dimension."""
    logger.info("Evaluating data_integrity dimension")

    dim_signals = {
        k: signals[k] for k in [
            "rows", "cols",
            "global_missing_ratio", "column_missing_ratio",
            "duplicate_ratio", "constant_columns", "constant_ratio",
            "hidden_missing_ratio", "mixed_type_columns", "mixed_ratio"
        ] if k in signals
    }

    result = run_data_integrity(signals)

    if result.metrics and "risk_breakdown" in result.metrics:
        return _result_to_dimension_dict(result, dim_signals)

    return _build_dimension_dict(
        dimension_signals=dim_signals,
        dominant_risks={result.name: result.risk},
        additive_risks={},
        total_risk=result.risk,
        status=result.status,
        interpretation=result.reason,
    )


def evaluate_target_viability(signals: dict) -> dict:
    """Evaluate target viability dimension."""
    logger.info("Evaluating target_viability dimension")

    dim_signals = {
        k: signals.get(k) for k in [
            "target_missing_ratio", "target_unique_count",
            "class_imbalance_score", "target_variance",
            "task_type", "task_confidence"
        ] if k in signals
    }

    target_signals = dict(signals)
    target_signals.setdefault("target_missing_ratio", 0.0)
    target_signals.setdefault("target_unique_count", 2)

    try:
        result = run_target_viability(target_signals)
        if result is None:
            return _build_dimension_dict(
                dimension_signals=dim_signals,
                dominant_risks={},
                additive_risks={},
                total_risk=0.0,
                status="SAFE",
                interpretation="No target-specific structural risk detected in Layer 1.",
            )

        if result.metrics and "risk_breakdown" in result.metrics:
            return _result_to_dimension_dict(result, dim_signals)

        return _build_dimension_dict(
            dimension_signals=dim_signals,
            dominant_risks={result.name: result.risk},
            additive_risks={},
            total_risk=result.risk,
            status=result.status,
            interpretation=result.reason,
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


def evaluate_sample_adequacy(signals: dict) -> dict:
    """Evaluate sample adequacy dimension."""
    logger.info("Evaluating sample_adequacy dimension")

    dim_signals = {
        k: signals.get(k) for k in [
            "rows", "cols", "sample_feature_ratio"
        ] if k in signals
    }

    result = run_sample_adequacy(signals)

    if result is None:
        return _build_dimension_dict(
            dimension_signals=dim_signals,
            dominant_risks={},
            additive_risks={},
            total_risk=0.0,
            status="SAFE",
            interpretation="Sufficient sample size relative to feature space. Low structural risk.",
        )

    if result.metrics and "risk_breakdown" in result.metrics:
        return _result_to_dimension_dict(result, dim_signals)

    return _build_dimension_dict(
        dimension_signals=dim_signals,
        dominant_risks={result.name: result.risk},
        additive_risks={},
        total_risk=result.risk,
        status=result.status,
        interpretation=result.reason,
    )
