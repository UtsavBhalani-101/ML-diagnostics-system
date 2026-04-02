import logging
from typing import Dict, Any

from engine.Layer_1.risk_template import worst_status

logger = logging.getLogger(__name__)


# -------------------------
# VALIDATION
# -------------------------
def _validate_dimension(name: str, dim: Dict[str, Any]):
    required = ["signals", "dominant_risks", "additive_risks", "total_risk", "status"]

    for key in required:
        if key not in dim:
            logger.error(f"Dimension '{name}' missing key: {key}")
            raise ValueError(f"Invalid dimension structure: {name}.{key}")


# -------------------------
# FORMAT ONE DIMENSION
# -------------------------
def _format_dimension(name: str, dim: Dict[str, Any]) -> Dict[str, Any]:
    _validate_dimension(name, dim)

    logger.debug(f"Formatting dimension: {name}")

    return {
        "status": dim["status"],
        "risk": dim["total_risk"],

        # WHY layer
        "breakdown": {
            "dominant": dim["dominant_risks"],
            "additive": dim["additive_risks"],
        },

        # WHAT layer
        "signals": dim["signals"],
    }


# -------------------------
# OVERALL AGGREGATION
# -------------------------
def _compute_overall(dimensions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    risks = [d["risk"] for d in dimensions.values()]
    statuses = [d["status"] for d in dimensions.values()]

    overall = {
        "risk": max(risks) if risks else 0.0,
        "status": worst_status(statuses),
    }

    logger.info(f"Overall computed: {overall}")

    return overall


# -------------------------
# FINAL FORMATTER
# -------------------------
def format_final_output(raw_pipeline: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("Starting Layer 1 formatting (risk-based)")

    logic = raw_pipeline.get("logic", {})
    dims = logic.get("dimensions", {})

    if not dims:
        logger.error("No dimensions found in pipeline output")
        raise ValueError("Invalid pipeline output: missing dimensions")

    formatted_dims = {}

    for name, dim_data in dims.items():
        formatted_dims[name] = _format_dimension(name, dim_data)

    overall = _compute_overall(formatted_dims)

    result = {
        "overall": overall,
        "dimensions": formatted_dims,
    }

    logger.info(f"Formatting complete. Status: {overall['status']}")

    return result