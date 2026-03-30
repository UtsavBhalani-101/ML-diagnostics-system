"""
Layer 1 Output Formatter
=========================
Transforms raw pipeline output into a clean, frontend-ready JSON structure.

Final output structure:
    - overall_status: highest severity across all tests
    - summary: test count breakdown
    - key_facts: size, memory, feature_mix
    - risks: critical and warning tests
    - no_issues: all SAFE tests
"""

from engine.Layer_1.risk_template import get_verdict, RISK_CODES


# Human-readable titles for each test name from logic.py
CHECK_TITLES = {
    "dataset_size": "Dataset Size",
    "global_missing": "Missing Values",
    "column_missing": "Structural Missingness",
    "duplicates": "Duplicate Rows",
    "constant_columns": "Near-Constant Features",
    "mixed_column": "Mixed Data Types",
    "hidden_missing": "Hidden Missing Values",
}

# Map test names to risk codes for verdict lookup
TEST_RISK_CODES = {
    "dataset_size": "DATASET_SIZE",
    "global_missing": "MISSINGNESS",
    "column_missing": "STRUCTURAL_MISSINGNESS",
    "duplicates": "DUPLICATION",
    "constant_columns": "DEGENERACY",
    "mixed_column": "TYPE_AMBIGUITY",
    "hidden_missing": "HIDDEN_MISSING",
}

# Map test names to scope
TEST_SCOPES = {
    "dataset_size": "DATASET",
    "global_missing": "DATASET",
    "column_missing": "COLUMN",
    "duplicates": "DATASET",
    "constant_columns": "COLUMN",
    "mixed_column": "COLUMN",
    "hidden_missing": "COLUMN",
}


def _format_test(test_data: dict) -> dict:
    """
    Format a single test result (from TestResult dataclass) into a frontend-friendly dict.
    
    Input test_data keys: test, status, message, affected_columns, metrics
    Output: id, title, check_name, metric, status, risk_code, scope, columns
    """
    test_name = test_data.get("test", "unknown")
    status = test_data.get("status", "SAFE")
    risk_code = TEST_RISK_CODES.get(test_name, test_name.upper())

    # Get the primary metric value from the metrics dict
    metrics = test_data.get("metrics") or {}
    metric_value = None
    if metrics:
        # Take the first metric value
        metric_value = next(iter(metrics.values()), None)

    # Get verdict from risk template
    verdict = get_verdict(risk_code, status)

    entry = {
        "id": test_name,
        "title": verdict,
        "check_name": CHECK_TITLES.get(test_name, test_name),
        "metric": metric_value,
        "status": status,
        "risk_code": risk_code,
        "scope": TEST_SCOPES.get(test_name, "DATASET"),
    }

    # Include affected columns if present
    affected = test_data.get("affected_columns")
    if affected:
        if isinstance(affected, list):
            # Flatten nested lists (e.g., [['col1', 'col2']])
            flat = []
            for item in affected:
                if isinstance(item, list):
                    flat.extend(item)
                else:
                    flat.append(item)
            entry["columns"] = flat
        elif isinstance(affected, str):
            entry["columns"] = [affected]

    # Include message as info.details
    message = test_data.get("message")
    if message:
        entry["info"] = {"details": message}

    return entry


def format_final_output(raw_pipeline: dict) -> dict:
    """
    Transform raw pipeline output into the final frontend-ready structure.

    Args:
        raw_pipeline: Dictionary from run_pipeline() with keys:
            data_loaded, shape, signals, logic (with facts + tests list), status

    Returns:
        Frontend-ready dictionary with:
            overall_status, summary, key_facts, risks, no_issues
    """
    logic_data = raw_pipeline.get("logic", {})
    facts = logic_data.get("facts", {})
    tests = logic_data.get("tests", [])  # Now a list of dicts

    # --- Overall Status ---
    statuses = [t.get("status", "SAFE") for t in tests]
    critical_count = statuses.count("CRITICAL")
    warning_count = statuses.count("WARNING")
    safe_count = statuses.count("SAFE")

    if critical_count > 0:
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

    for test_data in tests:
        entry = _format_test(test_data)
        status = test_data.get("status", "SAFE")

        if status == "CRITICAL":
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
            "critical": critical_count,
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
