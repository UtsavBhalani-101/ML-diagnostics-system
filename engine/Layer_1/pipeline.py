import pandas as pd
import numpy as np
import sys
import logging
from typing import Any, TypeVar

from engine.Layer_1.Signals.target_validity_signals import target_degeneracy_flag

T = TypeVar("T")

from engine.Layer_1 import Signals as signals
from engine.Layer_1 import Logic as logic
from engine.Layer_1.formatter import format_final_output
import engine.Layer_1.schema

logger = logging.getLogger(__name__)


# -------------------------
# UTILS
# -------------------------
def convert_numpy_types(obj: T) -> T:
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    return obj


# -------------------------
# FACTS
# -------------------------
def compute_facts(df: pd.DataFrame, signal_output: dict) -> dict:
    rows = signal_output["rows"]
    cols = signal_output["cols"]

    total_cells = rows * cols
    scale_class = (
        "small" if total_cells < 10_000
        else "medium" if total_cells < 1_000_000
        else "large"
    )

    memory_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
    memory_class = (
        "light" if memory_mb < 10
        else "moderate" if memory_mb < 100
        else "heavy"
    )

    num_cols = len(df.select_dtypes(include="number").columns)
    cat_cols = cols - num_cols

    num_ratio = round(num_cols / cols, 2) if cols else 0
    cat_ratio = round(cat_cols / cols, 2) if cols else 0

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



# -------------------------
# MAIN PIPELINE (WITHOUT FILEPATH)
# -------------------------

def run_pipeline_from_df(df: pd.DataFrame, target_column=None) -> dict[str, Any]:
    try:
        # 1. Signal Extraction
        extracted_signals = signals.run_signal_extraction(df, target_column=target_column)

        # 2. Compute Facts
        facts = compute_facts(df, {"rows": df.shape[0], "cols": df.shape[1]}) 

        # 3. Dimension Evaluations
        logger.info("Evaluating dimensions")
        extracted_logic = logic.run_logic_extraction(extracted_signals)

        result = {
            "data_loaded": True,
            "shape": list(df.shape),
            "signals": extracted_signals.dimensions,
            "logic": {
                "facts": facts,
                "dimensions": extracted_logic.dimensions,
            }
        }

        # Convert NumPy types for JSON serializability
        result = convert_numpy_types(result)

        # 4. Final Formatting
        final_output = format_final_output(result)
        result["final_output"] = final_output
        result["status"] = "success"

        logger.info("Pipeline complete")
        return result

    except Exception as e:
        logger.exception("Pipeline failed")
        return {"status": "error", "message": str(e)}
    
    
def test_run(df: pd.DataFrame, target_column: str | None = None):
    # This is a convenience wrapper for manual testing that mimics run_pipeline_from_df
    return run_pipeline_from_df(df, target_column=target_column)

    


if __name__ == "__main__":
    df = pd.read_csv(r"D:\ML diagnose v1\test_files\train.csv")
    target = "Survived"
    
    # 2. Get the result
    result = test_run(df, target)
    
    # 3. Print the polished report instead of the raw dict
    from engine.Layer_1.report import print_layer1_report
    print_layer1_report(result)