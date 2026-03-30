import pandas as pd
import numpy as np
import sys
import traceback
from dataclasses import asdict
from engine.Layer_1 import signals
from engine.Layer_1 import logic
from engine.Layer_1.formatter import format_final_output
from Backend.file_support_check import load_dataframe_from_file


def convert_numpy_types(obj):
    """
    Recursively convert numpy types to Python native types for JSON serialization.
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj


def compute_facts(df: pd.DataFrame, signal_output: dict) -> dict:
    """
    Compute key facts about the dataset for the frontend key_facts section.
    Uses signals + DataFrame to produce dimensions, memory, and feature_mix.
    """
    rows = signal_output["rows"]
    cols = signal_output["cols"]

    # Scale classification
    total_cells = rows * cols
    if total_cells < 10_000:
        scale_class = "small"
    elif total_cells < 1_000_000:
        scale_class = "medium"
    else:
        scale_class = "large"

    # Memory usage
    memory_bytes = df.memory_usage(deep=True).sum()
    memory_mb = round(memory_bytes / (1024 * 1024), 2)

    if memory_mb < 10:
        memory_class = "light"
    elif memory_mb < 100:
        memory_class = "moderate"
    else:
        memory_class = "heavy"

    # Feature mix
    num_cols = len(df.select_dtypes(include="number").columns)
    cat_cols = cols - num_cols
    num_ratio = round(num_cols / cols, 2) if cols > 0 else 0
    cat_ratio = round(cat_cols / cols, 2) if cols > 0 else 0

    if num_ratio > 0.8:
        mix_type = "Mostly Numeric"
    elif cat_ratio > 0.8:
        mix_type = "Mostly Categorical"
    elif abs(num_ratio - cat_ratio) < 0.2:
        mix_type = "Balanced Mix"
    else:
        mix_type = "Mixed"

    return {
        "dimensions": {
            "rows": rows,
            "columns": cols,
            "shape": f"{rows} x {cols}",
            "scale_class": scale_class,
        },
        "memory": {
            "memory_mb": memory_mb,
            "memory_class": memory_class,
        },
        "feature_mix": {
            "mix_type": mix_type,
            "num_ratio": num_ratio,
            "cat_ratio": cat_ratio,
        },
    }


def run_logic_tests(signal_output: dict) -> list:
    """
    Run all logic tests and collect results as a list of dicts.
    Handles edge cases where certain tests may fail (e.g., empty hidden_missing_ratio).
    """
    logic.validate_data(signal_output)

    # (function, test_name) — test_name matches logic.py's TestResult.test field
    test_functions = [
        (logic.test_dataset_size, "dataset_size"),
        (logic.test_global_missing, "global_missing"),
        (logic.test_column_missing, "column_missing"),
        (logic.test_duplicates, "duplicates"),
        (logic.test_constant_columns, "constant_columns"),
        (logic.test_mixed_columns, "mixed_column"),
        (logic.test_hidden_missing, "hidden_missing"),
    ]

    results = []
    for test_fn, test_name in test_functions:
        try:
            result = test_fn(signal_output)
            results.append(asdict(result))
        except Exception as e:
            # If a test fails (e.g., empty data / no mixed cols), record gracefully
            results.append({
                "test": test_name,
                "status": "SAFE",
                "message": f"Test skipped: {str(e)}",
                "affected_columns": None,
                "metrics": None,
            })

    return results


def run_pipeline(file_path):
    """
    Run the full Layer 1 diagnostic pipeline.

    Layer 1 always analyzes the ENTIRE DataFrame (all columns).
    Target column specification has no effect on Layer 1 output.

    Args:
        file_path: Path to the dataset file

    Returns:
        Dictionary with pipeline results (JSON-serializable)
    """
    results = {}

    try:
        # 1. Load the data using universal loader (supports all formats)
        df = load_dataframe_from_file(file_path)
        results['data_loaded'] = True
        results['shape'] = df.shape

        # 2. Execute Signal Extraction
        signal_output = signals.run_signal_extraction(df)
        results['signals'] = signal_output

        # 3. Compute key facts from signals + DataFrame
        facts = compute_facts(df, signal_output)

        # 4. Execute Logic Tests
        test_results = run_logic_tests(signal_output)

        # Bundle logic output in the format formatter expects
        results['logic'] = {
            "facts": facts,
            "tests": test_results,
        }

        # Convert numpy types to native Python types for JSON serialization
        results = convert_numpy_types(results)

        # 5. Format final output for frontend
        final_output = format_final_output(results)
        results['final_output'] = final_output

        results['status'] = 'success'

        return results

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Test with a sample path if run directly
    if len(sys.argv) > 1:
        result = run_pipeline(sys.argv[1])
        print(f"\nPipeline result: {result.get('status')}")
    else:
        print("Usage: python pipeline.py <path_to_csv>")