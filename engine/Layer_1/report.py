"""
Layer 1 Report Generator
========================
Formats and prints the diagnostic results from the pipeline.
Works with the new TestResult-based data structure.
"""


def print_layer1_report(result: dict) -> None:
    """
    Print a formatted Layer 1 diagnostic report.

    Args:
        result: Dictionary from pipeline with structure:
            - logic.facts: {dimensions, memory, feature_mix}
            - logic.tests: list of {test, status, message, affected_columns, metrics}
    """
    logic_data = result.get("logic", result)
    facts = logic_data.get("facts", {})
    tests = logic_data.get("tests", [])

    print("\n" + "=" * 60)
    print("           DATASET TRIAGE (LAYER 1)")
    print("=" * 60)

    # ============================================================
    # Section 1: Key Facts
    # ============================================================

    # Dimensions
    dims = facts.get("dimensions", {})
    if dims:
        print("\n[DIMENSIONS]")
        print("-" * 40)

        rows = dims.get('rows', 'N/A')
        rows_str = f"{rows:,}" if isinstance(rows, (int, float)) else str(rows)
        print(f"  Rows:        {rows_str}")
        print(f"  Columns:     {dims.get('columns', 'N/A')}")
        print(f"  Shape:       {dims.get('shape', 'N/A')}")

        scale = dims.get('scale_class', 'N/A')
        print(f"  Scale:       {scale.upper() if isinstance(scale, str) else scale}")

    # Memory
    mem = facts.get("memory", {})
    if mem:
        print("\n[MEMORY]")
        print("-" * 40)
        print(f"  Usage:       {mem.get('memory_mb', 'N/A')} MB")

        mem_class = mem.get('memory_class', 'N/A')
        print(f"  Class:       {mem_class.upper() if isinstance(mem_class, str) else mem_class}")

    # Feature Mix
    mix = facts.get("feature_mix", {})
    if mix:
        print("\n[FEATURE MIX]")
        print("-" * 40)
        print(f"  Type:        {mix.get('mix_type', 'N/A')}")
        print(f"  Numeric:     {mix.get('num_ratio', 0) * 100:.1f}%")
        print(f"  Categorical: {mix.get('cat_ratio', 0) * 100:.1f}%")

    # ============================================================
    # Section 2: Diagnostic Tests
    # ============================================================
    print("\n" + "=" * 60)
    print("           DIAGNOSTIC TESTS")
    print("=" * 60)

    # Count statuses
    safe_count = sum(1 for t in tests if t.get("status") == "SAFE")
    warning_count = sum(1 for t in tests if t.get("status") == "WARNING")
    critical_count = sum(1 for t in tests if t.get("status") == "CRITICAL")

    # Status symbols (ASCII safe)
    status_symbols = {"SAFE": "[OK]", "WARNING": "[!]", "CRITICAL": "[X]"}

    for test_data in tests:
        test_name = test_data.get("test", "unknown")
        status = test_data.get("status", "unknown")
        symbol = status_symbols.get(status, "[?]")

        print(f"\n{symbol} {test_name}")
        print(f"   Status:     {status.upper()}")
        print(f"   Message:    {test_data.get('message', 'N/A')}")

        # Print metrics
        metrics = test_data.get("metrics")
        if metrics:
            for key, value in metrics.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.4f}")
                else:
                    print(f"   {key}: {value}")

        # Print affected columns if present
        affected = test_data.get("affected_columns")
        if affected:
            print(f"   Columns:    {affected}")

    # ============================================================
    # Section 3: Summary
    # ============================================================
    print("\n" + "=" * 60)
    print("           SUMMARY")
    print("=" * 60)

    # Calculate overall health
    if critical_count > 0:
        overall_health = "CRITICAL"
    elif warning_count > 0:
        overall_health = "WARNING"
    else:
        overall_health = "SAFE"

    print(f"\n  Overall Health: {overall_health}")
    print(f"  Tests:          {safe_count} SAFE, {warning_count} WARNING, {critical_count} CRITICAL")
    print("\n" + "=" * 60 + "\n")


def get_report_string(result: dict) -> str:
    """
    Returns the report as a string instead of printing.
    Useful for saving to file or API responses.
    """
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        print_layer1_report(result)

    return f.getvalue()


if __name__ == "__main__":
    # Test with sample data in new format
    sample_result = {
        "logic": {
            "facts": {
                "dimensions": {"rows": 1000, "columns": 50, "shape": "1000 x 50", "scale_class": "medium"},
                "memory": {"memory_mb": 5.5, "memory_class": "light"},
                "feature_mix": {"mix_type": "Balanced Mix", "num_ratio": 0.5, "cat_ratio": 0.5}
            },
            "tests": [
                {
                    "test": "dataset_size",
                    "status": "SAFE",
                    "message": "Dataset size appears structurally adequate.",
                    "affected_columns": None,
                    "metrics": {"rows": 1000}
                },
                {
                    "test": "global_missing",
                    "status": "WARNING",
                    "message": "Dataset's has moderate missingness, imputation may be unreliable",
                    "affected_columns": None,
                    "metrics": {"global_missing_ratio": 0.08}
                },
                {
                    "test": "constant_columns",
                    "status": "CRITICAL",
                    "message": "Constant cols exists, ",
                    "affected_columns": [["feature_1"]],
                    "metrics": {"constant_columns_ratio": 0.35}
                },
            ],
        }
    }
    print_layer1_report(sample_result)