import logging
from typing import Dict, Any

from engine.Layer_1.risk_template import STATUS_RANK, worst_status

logger = logging.getLogger(__name__)


# -------------------------
# FORMAT ONE DIMENSION
# -------------------------
def _format_dimension(name: str, dim: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats a single dimension into the new 'checks' based structure.
    """
    logger.debug(f"Formatting dimension: {name}")

    # Map raw logic results to the new 'checks' format
    # Note: We expect 'raw_results' to be added to the logic output in the next stage
    raw_results = dim.get("raw_results", [])
    
    checks = []
    for r in raw_results:
        # If r is a dict (serialized Logic_Structure)
        checks.append({
            "name": r.get("name"),
            "label": r.get("label"),
            "risk": r.get("risk"),
            "threshold": r.get("metrics", {}).get("threshold"),
            "observed": r.get("metrics", {}).get("observed"),
            "impact": r.get("metrics", {}).get("impact"),
            "detail": r.get("metrics", {})
        })

    return {
        "status": dim.get("status"),
        "composite_risk": dim.get("total_risk"), # Mapping old total_risk to new name for now
        "peak_risk": dim.get("peak_risk", dim.get("total_risk")),
        "critical": dim.get("critical", []),
        "warnings": dim.get("warnings", []),
        "checks": checks,
        "interpretation": dim.get("interpretation")
    }


# -------------------------
# OVERALL AGGREGATION
# -------------------------
def _compute_overall(dimensions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    risks = [d["composite_risk"] for d in dimensions.values() if d["composite_risk"] is not None]
    statuses = [d["status"] for d in dimensions.values()]
    
    ranked_dimensions = sorted(
        dimensions.items(),
        key=lambda item: item[1]["composite_risk"] or 0,
        reverse=True,
    )
    
    top_dimension_name = ranked_dimensions[0][0] if ranked_dimensions else None
    top_dimension_risk = ranked_dimensions[0][1]["composite_risk"] if ranked_dimensions else 0.0

    overall = {
        "risk": max(risks) if risks else 0.0,
        "status": worst_status(statuses),
        "primary_failure_source": top_dimension_name if top_dimension_risk > 0 else None,
        "total_dimensions": len(dimensions),
    }

    logger.info(f"Overall computed: {overall}")
    return overall


# -------------------------
# FINAL FORMATTER
# -------------------------
def format_final_output(raw_pipeline: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("Starting Layer 1 formatting")

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


if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)

    # 1. New "Expert Mode" Mock Data
    mock_raw_data = {
        "logic": {
            "dimensions": {
                "data_integrity": {
                    "status": "STOP",
                    "total_risk": 0.65, # composite
                    "peak_risk": 0.85,
                    "critical": ["missing_values"],
                    "warnings": ["mixed_types"],
                    "interpretation": "Critical integrity issues found.",
                    "raw_results": [
                        {
                            "name": "missing_values",
                            "label": "CRITICAL",
                            "risk": 0.85,
                            "metrics": {"threshold": 0.2, "observed": 0.45, "impact": "blocker"}
                        },
                        {
                            "name": "mixed_types",
                            "label": "WARNING",
                            "risk": 0.3,
                            "metrics": {"threshold": 0.05, "observed": 0.08, "impact": "degrading"}
                        }
                    ]
                }
            }
        }
    }

    print("\n--- Testing Formatter (Expert Mode) ---")
    try:
        final_result = format_final_output(mock_raw_data)
        import json
        print(json.dumps(final_result, indent=4))
    except Exception as e:
        print(f"Formatter failed: {e}")
