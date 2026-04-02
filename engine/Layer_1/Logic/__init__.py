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
    "status": str
  }
"""
import logging
from dataclasses import asdict

from engine.Layer_1.Logic.data_integrity_logic import run_data_integrity
from engine.Layer_1.Logic.target_sanity_logic import run_target_viability
from engine.Layer_1.Logic.sample_adequacy_logic import run_sample_adequacy

logger = logging.getLogger(__name__)


def _result_to_dimension_dict(result, signals: dict, dimension_signals: dict) -> dict:
    """
    Convert a TestResult dataclass to the dimension dict format
    that formatter.py expects.
    """
    # Extract breakdown from metrics if available
    breakdown = {}
    if result.metrics and "risk_breakdown" in result.metrics:
        breakdown = result.metrics["risk_breakdown"]

    dominant_risks = breakdown.get("dominant", {})
    additive_risks = breakdown.get("additive", {})

    return {
        "signals": dimension_signals,
        "dominant_risks": dominant_risks,
        "additive_risks": additive_risks,
        "total_risk": result.risk,
        "status": result.status,
    }


def evaluate_data_integrity(signals: dict) -> dict:
    """Evaluate data integrity dimension."""
    logger.info("Evaluating data_integrity dimension")

    # Signals relevant to this dimension
    dim_signals = {
        k: signals[k] for k in [
            "rows", "cols",
            "global_missing_ratio", "column_missing_ratio",
            "duplicate_ratio", "constant_columns", "constant_ratio",
            "hidden_missing_ratio", "mixed_type_columns", "mixed_ratio"
        ] if k in signals
    }

    result = run_data_integrity(signals)

    # Handle hard-fail case (TestResult without metrics.risk_breakdown)
    if result.metrics and "risk_breakdown" in result.metrics:
        return _result_to_dimension_dict(result, signals, dim_signals)

    # Hard failure — no breakdown computed, risk is 1.0
    return {
        "signals": dim_signals,
        "dominant_risks": {result.name: result.risk},
        "additive_risks": {},
        "total_risk": result.risk,
        "status": result.status,
    }


def evaluate_target_viability(signals: dict) -> dict:
    """Evaluate target viability dimension."""
    logger.info("Evaluating target_viability dimension")

    # Signals relevant to this dimension
    dim_signals = {
        k: signals.get(k) for k in [
            "target_missing_ratio", "target_unique_count",
            "class_imbalance_score", "target_variance",
            "task_type", "task_confidence"
        ] if k in signals
    }

    # Target signals need specific keys; provide defaults for missing ones
    target_signals = dict(signals)
    target_signals.setdefault("target_missing_ratio", 0.0)
    target_signals.setdefault("target_unique_count", 2)

    try:
        result = run_target_viability(target_signals)
        if result is None:
            return {
                "signals": dim_signals,
                "dominant_risks": {},
                "additive_risks": {},
                "total_risk": 0.0,
                "status": "SAFE",
            }

        if result.metrics and "risk_breakdown" in result.metrics:
            return _result_to_dimension_dict(result, signals, dim_signals)

        return {
            "signals": dim_signals,
            "dominant_risks": {result.name: result.risk},
            "additive_risks": {},
            "total_risk": result.risk,
            "status": result.status,
        }
    except Exception as e:
        logger.warning(f"Target viability evaluation failed: {e}, defaulting to SAFE")
        return {
            "signals": dim_signals,
            "dominant_risks": {},
            "additive_risks": {},
            "total_risk": 0.0,
            "status": "SAFE",
        }


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
        return {
            "signals": dim_signals,
            "dominant_risks": {},
            "additive_risks": {},
            "total_risk": 0.0,
            "status": "SAFE",
        }

    if result.metrics and "risk_breakdown" in result.metrics:
        return _result_to_dimension_dict(result, signals, dim_signals)

    return {
        "signals": dim_signals,
        "dominant_risks": {result.name: result.risk},
        "additive_risks": {},
        "total_risk": result.risk,
        "status": result.status,
    }
