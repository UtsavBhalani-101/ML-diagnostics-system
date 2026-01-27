import pandas as pd
import traceback
from engine.Layer_1 import signals
from engine.Layer_1 import logic
from engine.Layer_1 import report

# Default target column - adjust based on your dataset
DEFAULT_TARGET = "SalePrice"


def run_pipeline(file_path, target_column=None):
    """
    Run the full Layer 1 diagnostic pipeline.
    
    Args:
        file_path: Path to the dataset file
        target_column: Name of the target column (optional, defaults to DEFAULT_TARGET)
    
    Returns:
        Dictionary with pipeline results
    """
    print("Starting Pipeline...")
    results = {}
    target_col = target_column or DEFAULT_TARGET
    
    try:
        # 1. Load the data
        print("Loading data...")
        df = pd.read_csv(file_path)
        results['data_loaded'] = True
        results['shape'] = df.shape
        
        # 2. Prepare features and target
        if target_col in df.columns:
            target = df[target_col]
            features = df.drop(columns=[target_col])
        else:
            print(f"Warning: Target column '{target_col}' not found. Using full DataFrame.")
            target = df.iloc[:, -1]  # Use last column as target
            features = df.iloc[:, :-1]
        
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