def print_layer1_report(result: dict) -> None:
    logic = result.get("logic", {})
    facts = logic.get("facts", {})
    dimensions = logic.get("dimensions", {})

    print("\n" + "=" * 60)
    print("        DATASET TRIAGE (LAYER 1 - RISK BASED)")
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

        print(f"Status: {dim['status']}")
        print(f"Risk:   {dim['total_risk']:.3f}")

        print("\n  Dominant Risks:")
        if dim["dominant_risks"]:
            for k, v in dim["dominant_risks"].items():
                print(f"    - {k}: {v:.3f}")
        else:
            print("    None")

        print("\n  Additive Risks:")
        if dim["additive_risks"]:
            for k, v in dim["additive_risks"].items():
                print(f"    - {k}: {v:.3f}")
        else:
            print("    None")

    # -------------------------
    # OVERALL
    # -------------------------
    print("\n" + "=" * 60)
    print("        OVERALL ASSESSMENT")
    print("=" * 60)

    overall = result.get("final_output", {}).get("overall", {})

    print(f"\nStatus: {overall.get('status')}")
    print(f"Risk:   {overall.get('risk'):.3f}")
    print("\n" + "=" * 60 + "\n")