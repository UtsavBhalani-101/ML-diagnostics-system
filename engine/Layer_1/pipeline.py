import pandas as pd
import numpy as np
import traceback
from engine.Layer_1 import signals
from engine.Layer_1 import logic
from engine.Layer_1 import report


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


def run_pipeline(file_path, target_column=None):
    """
    Run the full Layer 1 diagnostic pipeline.
    
    Args:
        file_path: Path to the dataset file
        target_column: Name of the target column (optional). 
                      If not provided, the last column is used as the target.
    
    Returns:
        Dictionary with pipeline results
    """
    print("Starting Pipeline...")
    results = {}
    
    try:
        # 1. Load the data
        print("Loading data...")
        df = pd.read_csv(file_path)
        results['data_loaded'] = True
        results['shape'] = df.shape
        
        # 2. Prepare features and target
        if target_column and target_column in df.columns:
            # Use specified target column
            target = df[target_column]
            features = df.drop(columns=[target_column])
            print(f"Using specified target column: '{target_column}'")
        elif target_column and target_column not in df.columns:
            # Specified column not found, fall back to last column
            print(f"Warning: Target column '{target_column}' not found. Using last column as target.")
            target = df.iloc[:, -1]
            features = df.iloc[:, :-1]
        else:
            # No target specified, use last column as default
            last_col = df.columns[-1]
            target = df[last_col]
            features = df.drop(columns=[last_col])
            print(f"No target specified. Using last column as target: '{last_col}'")
        
        # 3. Execute Signal Extraction
        print("Executing Signal Extraction...")
        signal_output = signals.run_signals_extraction(features, target)
        results['signals'] = signal_output
        
        # 4. Execute Logic Analysis
        print("Executing Layer 1 Logic...")
        diagnostics = logic.run_logic_extraction(features, signal_output)
        results['logic'] = diagnostics
        
        # 5. Generate Report
        print("Generating Report...")
        try:
             results['report'] = report.get_report_string(diagnostics)
        except Exception as report_error:
             print(f"Report generation warning: {report_error}")
             results['report'] = f"Report generation failed: {report_error}"
        
        print("Pipeline Complete.")
        results['status'] = 'success'
        
        # Convert numpy types to native Python types for JSON serialization
        results = convert_numpy_types(results)
        
        return results
        
    except Exception as e:
        print(f"Pipeline Failed: {e}")
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