
def print_layer1_report(result: dict) -> None:
    print("\n=== DATASET TRIAGE (LAYER 1) ===\n")

    d = result["dimensions"]
    print(f"Rows: {d['rows']}")
    print(f"Columns: {d['columns']}")
    print(f"Memory: {d['memory_mb']} MB\n")

    print("Feature Breakdown:")
    for k, v in result["feature_breakdown"].items():
        print(f"  - {k}: {v}")

    print("\nVitals:")
    for k, v in result["vitals"].items():
        print(f"  - {k}: {v}")

    print("\nOverall Health:", result["health_status"])
    print("Summary:", result["summary"])

if __name__ == "__main__":
    print_layer1_report()