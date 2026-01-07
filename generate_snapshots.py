import pandas as pd
import os
import json
from engine.Layer_1 import normalizing_dtypes
from engine.Layer_1 import signals
from engine.Layer_1 import logic

def create_test_data():
    if not os.path.exists("tests"):
        os.makedirs("tests")
        print("Created /tests directory")
    # Load your raw data
    raw_df = pd.read_csv(r"D:\ML diagnose v1\uploads\train.csv")
    
    # Run Step 1 and Save
    df_norm, _ = normalizing_dtypes.normalize_tabular_dtypes(raw_df)
    df_norm.to_csv("tests/snapshot_normalized.csv", index=False)
    
    # Run Step 2 and Save
    df_signals = signals.run_signals_extraction(df_norm, df_norm['SalePrice'])
    with open('tests/snapshot_signal.json', 'w') as f:
        json.dump(df_signals, f, indent=4)
        
    df_logic = logic.run_logic_extraction(df_norm, df_signals)
    with open('tests/snapshot_logic.json', 'w') as f:
        json.dump(df_logic, f, indent=4)
        
    print("Snapshots created in /tests folder!")

if __name__ == "__main__":
    create_test_data()