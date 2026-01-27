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
            - assumptions: {assumption_name: {status, evidence}}
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
    print(f"  Rows:        {dims.get('rows', 'N/A'):,}")
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
    # Section 2: Assumptions & Health Status
    # ============================================================
    assumptions = result.get("assumptions", {})
    
    print("\n" + "="*60)
    print("           HEALTH ASSUMPTIONS")
    print("="*60)
    
    # Count statuses
    valid_count = sum(1 for a in assumptions.values() if a.get("status") == "valid")
    weak_count = sum(1 for a in assumptions.values() if a.get("status") == "weak")
    broken_count = sum(1 for a in assumptions.values() if a.get("status") == "broken")
    total_count = len(assumptions)
    
    # Status symbols (ASCII safe)
    status_symbols = {"valid": "[OK]", "weak": "[!]", "broken": "[X]"}
    
    for name, details in assumptions.items():
        status = details.get("status", "unknown")
        symbol = status_symbols.get(status, "[?]")
        evidence = details.get("evidence", {})
        
        print(f"\n{symbol} {name}")
        print(f"   Status: {status.upper()}")
        if evidence:
            for key, value in evidence.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.4f}")
                else:
                    print(f"   {key}: {value}")
    
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
    if broken_count > 2:
        health_status = "CRITICAL"
        health_symbol = "[!!!]"
    elif broken_count > 0 or weak_count > 2:
        health_status = "WARNING"
        health_symbol = "[!]"
    else:
        health_status = "HEALTHY"
        health_symbol = "[OK]"
    
    print(f"\n  Overall Health: {health_symbol} {health_status}")
    print(f"  Assumptions:    {valid_count} valid, {weak_count} weak, {broken_count} broken")
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
    # Test with sample data
    sample_result = {
        "facts": {
            "dimensions": {"rows": 1000, "columns": 50, "shape": "1000 x 50", "scale_class": "medium"},
            "memory": {"memory_mb": 5.5, "memory_class": "light"},
            "feature_mix": {"mix_type": "Balanced Mix", "num_ratio": 0.5, "cat_ratio": 0.5}
        },
        "assumptions": {
            "Data is mostly complete": {"status": "valid", "evidence": {"missing_ratio": 0.02}},
            "No degenerate features": {"status": "broken", "evidence": {"max_constant_ratio": 0.99}}
        },
        "constraints": ["Row-wise deletion unsafe; high missingness in: ['col1', 'col2']"]
    }
    print_layer1_report(sample_result)