import pandas as pd
import numpy as np
import traceback
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
        signal_output = signals.run_signals_extraction(df)
        results['signals'] = signal_output
        
        # 3. Execute Logic Analysis
        diagnostics = logic.run_logic_extraction(df, signal_output)
        results['logic'] = diagnostics
        
        # Convert numpy types to native Python types for JSON serialization
        results = convert_numpy_types(results)
        
        # 4. Format final output for frontend
        final_output = format_final_output(results)
        results['final_output'] = final_output
        
        results['status'] = 'success'
        
        return results
        
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Test with a sample path if run directly
    import sys
    if len(sys.argv) > 1:
        result = run_pipeline(sys.argv[1])
        print(f"\nPipeline result: {result.get('status')}")
    else:
        print("Usage: python pipeline.py <path_to_csv>")