import os
import shutil
from pathlib import Path
from engine.Layer_1.pipeline import run_pipeline

def start_engine(file_path):
    # Destination directory in engine/Layer_1
    destination_dir = os.path.join(os.path.dirname(__file__), "Layer_1")
    filename = os.path.basename(file_path)
    destination_path = os.path.join(destination_dir, filename)
    
    # Ensure directory exists
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    
    # Move/Copy file
    try:
        shutil.copy2(file_path, destination_path)
    except Exception as e:
        return {"error": f"Failed to move file to Layer 1: {str(e)}"}
    
    # Run Pipeline
    results = run_pipeline(destination_path)
    
    return results
