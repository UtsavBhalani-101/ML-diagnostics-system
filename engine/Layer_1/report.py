"""
Layer 1 Report Generator
========================
Formats and prints the diagnostic results from logic.py.
"""


def print_layer1_report(result: dict) -> None:
    """
    Print a formatted Layer 1 diagnostic report.
    
    Args:
        result: Dictionary from logic.run_logic_extraction() with structure:
            - facts: {dimensions, memory, feature_mix}
            - tests: {test_name: {check_id, metric, status, risk_code, scope, verdict}}
            - constraints: [list of constraint strings]
    """
    print("\n" + "="*60)
    print("           DATASET TRIAGE (LAYER 1)")
    print("="*60)
    
    # ============================================================
    # Section 1: Key Facts
    # ============================================================
    facts = result.get("facts", {})
    
    # Dimensions
    dims = facts.get("dimensions", {})
    print("\n[DIMENSIONS]")
    print("-" * 40)
    
    rows = dims.get('rows', 'N/A')
    rows_str = f"{rows:,}" if isinstance(rows, (int, float)) else str(rows)
    print(f"  Rows:        {rows_str}")
    
    print(f"  Columns:     {dims.get('columns', 'N/A')}")
    print(f"  Shape:       {dims.get('shape', 'N/A')}")
    print(f"  Scale:       {dims.get('scale_class', 'N/A').upper()}")
    
    # Memory
    mem = facts.get("memory", {})
    print("\n[MEMORY]")
    print("-" * 40)
    print(f"  Usage:       {mem.get('memory_mb', 'N/A')} MB")
    print(f"  Class:       {mem.get('memory_class', 'N/A').upper()}")
    
    # Feature Mix
    mix = facts.get("feature_mix", {})
    print("\n[FEATURE MIX]")
    print("-" * 40)
    print(f"  Type:        {mix.get('mix_type', 'N/A')}")
    print(f"  Numeric:     {mix.get('num_ratio', 0)*100:.1f}%")
    print(f"  Categorical: {mix.get('cat_ratio', 0)*100:.1f}%")
    
    # ============================================================
    # Section 2: Diagnostic Tests
    # ============================================================
    tests = result.get("tests", {})
    
    print("\n" + "="*60)
    print("           DIAGNOSTIC TESTS")
    print("="*60)
    
    # Count statuses
    safe_count = sum(1 for t in tests.values() if t.get("status") == "SAFE")
    warning_count = sum(1 for t in tests.values() if t.get("status") == "WARNING")
    danger_count = sum(1 for t in tests.values() if t.get("status") == "DANGER")
    total_count = len(tests)
    
    # Status symbols (ASCII safe)
    status_symbols = {"SAFE": "[OK]", "WARNING": "[!]", "DANGER": "[X]"}
    
    for test_name, details in tests.items():
        status = details.get("status", "unknown")
        symbol = status_symbols.get(status, "[?]")
        
        print(f"\n{symbol} {test_name}")
        print(f"   Check ID:   {details.get('check_id', 'N/A')}")
        
        metric = details.get("metric", "N/A")
        if isinstance(metric, float):
            print(f"   Metric:     {metric:.4f}")
        else:
            print(f"   Metric:     {metric}")
        
        print(f"   Status:     {status.upper()}")
        print(f"   Risk Code:  {details.get('risk_code', 'N/A')}")
        print(f"   Scope:      {details.get('scope', 'N/A')}")
        print(f"   Verdict:    {details.get('verdict', 'N/A')}")
        
        # Print additional info if present
        if "info" in details:
            info = details["info"]
            if isinstance(info, dict):
                for key, value in info.items():
                    print(f"   {key}: {value}")
        
        # Print column info if present (for column-scoped tests)
        if "column" in details and details["column"]:
            print(f"   Columns:    {details['column']}")
    
    # ============================================================
    # Section 3: Constraints
    # ============================================================
    constraints = result.get("constraints", [])
    
    print("\n" + "="*60)
    print("           CONSTRAINTS")
    print("="*60)
    
    if constraints:
        for i, constraint in enumerate(constraints, 1):
            print(f"\n  {i}. [!] {constraint}")
    else:
        print("\n  [OK] No constraints detected.")
    
    # ============================================================
    # Section 4: Summary
    # ============================================================
    print("\n" + "="*60)
    print("           SUMMARY")
    print("="*60)
    
    # Calculate overall health
    if danger_count > 0:
        health_status = "CRITICAL"
        health_symbol = "[!!!]"
    elif warning_count > 0:
        health_status = "WARNING"
        health_symbol = "[!]"
    else:
        health_status = "HEALTHY"
        health_symbol = "[OK]"
    
    print(f"\n  Overall Health: {health_symbol} {health_status}")
    print(f"  Tests:          {safe_count} SAFE, {warning_count} WARNING, {danger_count} DANGER")
    print(f"  Constraints:    {len(constraints)} identified")
    
    print("\n" + "="*60 + "\n")


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
        "facts": {
            "dimensions": {"rows": 1000, "columns": 50, "shape": "1000 x 50", "scale_class": "medium"},
            "memory": {"memory_mb": 5.5, "memory_class": "light"},
            "feature_mix": {"mix_type": "Balanced Mix", "num_ratio": 0.5, "cat_ratio": 0.5}
        },
        "tests": {
            "dataset_missing_ratio": {
                "check_id": "dataset_missing_ratio",
                "metric": 0.02,
                "status": "SAFE",
                "risk_code": "MISSINGNESS",
                "scope": "DATASET",
                "verdict": "Data completeness is acceptable. No imputation required."
            },
            "column_max_constant_ratio": {
                "check_id": "column_max_constant_ratio",
                "metric": 0.99,
                "status": "DANGER",
                "risk_code": "DEGENERACY",
                "scope": "COLUMN",
                "column": ["feature_1"],
                "verdict": "Near-constant features detected. These should be removed before modeling."
            }
        },
        "constraints": ["Row-wise deletion unsafe; high missingness in: ['col1', 'col2']"]
    }
    print_layer1_report(sample_result)