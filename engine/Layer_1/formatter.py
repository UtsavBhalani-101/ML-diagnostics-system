"""
Layer 1 Output Formatter
=========================
Transforms raw pipeline output into a clean, frontend-ready JSON structure.

Final output structure:
    - overall_status: highest severity across all tests
    - summary: test count breakdown
    - key_facts: size, memory, feature_mix
    - risks: critical (DANGER) and warning tests, ranked
    - no_issues: all SAFE tests
"""


# Human-readable titles for each check_id
CHECK_TITLES = {
    "dataset_missing_ratio": "Missing Values",
    "dataset_structural_missingness": "Structural Missingness",
    "dataset_hidden_missing_values": "Hidden Missing Values",
    "dataset_duplicates_ratio": "Duplicate Rows",
    "column_max_constant_ratio": "Near-Constant Features",
    "dataset_cardinality_ratio": "Cardinality Explosion",
    "dataset_multicollinearity_density": "Multicollinearity",
    "dataset_outlier_ratio": "Outlier Sensitivity",
    "dataset_mixed_type_ratio": "Mixed Data Types",
}


def _format_test(check_id: str, test_data: dict) -> dict:
    """
    Format a single test result into a frontend-friendly dict.
    """
    entry = {
        "id": check_id,
        "title": test_data.get("verdict"),
        "check_name": CHECK_TITLES.get(check_id, check_id),
        "metric": test_data.get("metric"),
        "status": test_data.get("status"),
        "risk_code": test_data.get("risk_code"),
        "scope": test_data.get("scope"),
    }

    # Include optional fields only if present
    if "column" in test_data and test_data["column"]:
        entry["columns"] = test_data["column"]

    if "info" in test_data:
        entry["info"] = test_data["info"]

    if "detected_placeholders" in test_data and test_data["detected_placeholders"]:
        entry["detected_placeholders"] = test_data["detected_placeholders"]

    return entry


def format_final_output(raw_pipeline: dict) -> dict:
    """
    Transform raw pipeline output into the final frontend-ready structure.

    Args:
        raw_pipeline: Dictionary from run_pipeline() with keys:
            data_loaded, shape, signals, logic, status

    Returns:
        Frontend-ready dictionary with:
            overall_status, summary, key_facts, risks, no_issues
    """
    logic = raw_pipeline.get("logic", {})
    facts = logic.get("facts", {})
    tests = logic.get("tests", {})

    # --- Overall Status ---
    statuses = [t.get("status") for t in tests.values()]
    danger_count = statuses.count("DANGER")
    warning_count = statuses.count("WARNING")
    safe_count = statuses.count("SAFE")

    if danger_count > 0:
        overall_status = "CRITICAL"
    elif warning_count > 0:
        overall_status = "WARNING"
    else:
        overall_status = "HEALTHY"

    # --- Key Facts ---
    dims = facts.get("dimensions", {})
    mem = facts.get("memory", {})
    mix = facts.get("feature_mix", {})

    key_facts = {
        "size": {
            "rows": dims.get("rows"),
            "columns": dims.get("columns"),
            "shape": dims.get("shape"),
            "scale": dims.get("scale_class"),
        },
        "memory": {
            "usage_mb": mem.get("memory_mb"),
            "class": mem.get("memory_class"),
        },
        "feature_mix": {
            "type": mix.get("mix_type"),
            "numeric_ratio": mix.get("num_ratio"),
            "categorical_ratio": mix.get("cat_ratio"),
        },
    }

    # --- Categorize Tests ---
    critical = []
    warnings = []
    no_issues = []

    for check_id, test_data in tests.items():
        entry = _format_test(check_id, test_data)
        status = test_data.get("status")

        if status == "DANGER":
            critical.append(entry)
        elif status == "WARNING":
            warnings.append(entry)
        else:
            no_issues.append(entry)

    # --- Build Final Output ---
    return {
        "overall_status": overall_status,
        "summary": {
            "total_tests": len(tests),
            "critical": danger_count,
            "warning": warning_count,
            "safe": safe_count,
        },
        "key_facts": key_facts,
        "risks": {
            "critical": critical,
            "warning": warnings,
        },
        "no_issues": no_issues,
    }
