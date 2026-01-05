import pandas as pd
import traceback
from engine.Layer_1 import normalizing_dtypes
from engine.Layer_1 import signals
from engine.Layer_1 import logic
from engine.Layer_1 import report

def run_pipeline(file_path):
    print("Starting Pipeline...")
    results = {}
    
    try:
        # 1. Load the data (This is the start of the variable chain)
        # We use the path passed from main_engine.py
        df = pd.read_csv(file_path) # Or use a generic loader

        # 2. Execute Normalization
        print("Executing Normalization...")
        df_normalized, report_norm = normalizing_dtypes.normalize(df)
        results['normalization'] = report_norm
        
        # 3. Execute Signals (Passing the normalized DF)
        print("Executing Signal Extraction...")
        df_signals = signals.extract(df_normalized)
        results['signals'] = "Signals extracted"

        # 4. Execute Logic (Passing the signals DF)
        print("Executing Layer 1 Logic...")
        diagnostics = logic.layer1_diagnostics(df_signals)
        results['layer_1'] = diagnostics
        
        # 5. Generate Report
        print("Generating Report...")
        final_report = report.create_report(diagnostics)
        results['report'] = final_report
        
        print("Pipeline Complete.")
        results['status'] = 'success'
        return results
        
    except Exception as e:
        print(f"Pipeline Failed: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Test with a dummy path if run directly
    pass
    