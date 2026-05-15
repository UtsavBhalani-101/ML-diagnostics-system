def print_layer1_report(result: dict) -> None:
    logic = result.get("logic", {})
    facts = logic.get("facts", {})
    
    # Use the formatted dimensions from final_output
    final_output = result.get("final_output", {})
    dimensions = final_output.get("dimensions", {})

    print("\n" + "=" * 60)
    print("        DATASET TRIAGE (LAYER 1 - EXPERT MODE)")
    print("=" * 60)

    # -------------------------
    # FACTS
    # -------------------------
    dims = facts.get("dimensions", {})
    mem = facts.get("memory", {})
    mix = facts.get("feature_mix", {})

    print("\n[DATA OVERVIEW]")
    print("-" * 40)
    print(f"Rows:        {dims.get('rows')}")
    print(f"Columns:     {dims.get('columns')}")
    print(f"Scale:       {dims.get('scale_class')}")
    print(f"Memory:      {mem.get('memory_mb')} MB ({mem.get('memory_class')})")
    print(f"Feature Mix: {mix.get('mix_type')}")

    # -------------------------
    # DIMENSIONS
    # -------------------------
    print("\n" + "=" * 60)
    print("        DIMENSION ANALYSIS")
    print("=" * 60)

    for name, dim in dimensions.items():
        print(f"\n[{name.upper()}]")
        print("-" * 40)

        print(f"Status:         {dim.get('status')}")
        print(f"Composite Risk: {dim.get('composite_risk', 0.0):.3f}")
        print(f"Peak Risk:      {dim.get('peak_risk', 0.0):.3f}")

        checks = dim.get("checks", [])
        if checks:
            print("\n  Checks:")
            for check in checks:
                label = check.get('label', 'UNKNOWN')
                # Add color/indicator based on label
                indicator = "!" if label in ["CRITICAL", "STOP"] else "-"
                print(f"    {indicator} [{label}] {check.get('name')}: {check.get('risk', 0.0):.3f}")
        else:
            print("\n  No checks performed.")

        if dim.get("interpretation"):
            print(f"\n  Note: {dim.get('interpretation')}")

    # -------------------------
    # OVERALL
    # -------------------------
    print("\n" + "=" * 60)
    print("        OVERALL ASSESSMENT")
    print("=" * 60)

    overall = final_output.get("overall", {})

    print(f"\nStatus: {overall.get('status')}")
    print(f"Risk:   {overall.get('risk', 0.0):.3f}")
    print(f"Source: {overall.get('primary_failure_source', 'N/A')}")
    print("\n" + "=" * 60 + "\n")
    
    
if __name__ == "__main__":
    print_layer1_report()