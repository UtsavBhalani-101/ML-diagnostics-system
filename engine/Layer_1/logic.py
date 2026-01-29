import pandas as pd
import numpy as np
from engine.Layer_1.risk_template import add_verdicts_to_tests


#^ key facts - dimensions
def extract_dataset_dimensions(signals: dict) -> dict:
    rows = signals["Metadata"]["Rows"]
    cols = signals["Metadata"]["Columns"]

    return {
        "rows": rows,
        "columns": cols,
        "shape": f"{rows} x {cols}",
        "scale_class": (
            "small" if rows < 1_000 else
            "medium" if rows < 100_000 else
            "large"
        )
    }


#^ key facts - memory 
def extract_memory_footprint(signals: dict) -> dict:
    memory_mb = signals["Metadata"]["Memory (MB)"]

    return {
        "memory_mb": round(memory_mb, 3),
        "memory_class": (
            "light" if memory_mb < 10 else
            "moderate" if memory_mb < 500 else
            "heavy"
        )
    }


#^ key facts - feature mix
def extract_feature_mix(df: pd.DataFrame):
    num_ratio = df['Metadata']['Numerical Columns Ratio']
    cat_ratio = df['Metadata']['Valid Categorical Columns Ratio'] #! fix this valid name thing from the signal
    mix_type = ""

    if cat_ratio >= 0.55:
        mix_type = "Categorical Dominant (High Complexity)"

    elif 0.40 <= cat_ratio < 0.55:
        mix_type = "Moderate Mix (Leaning Categorical)"

    elif abs(num_ratio - cat_ratio) <= 0.10:
        mix_type = "Balanced Mix"

    elif num_ratio >= 0.70:
        mix_type = "Numerical Dominant (Low Complexity)"

    elif 0.60 <= num_ratio < 0.70:
        mix_type = "Moderate Mix (Leaning Numerical)"

    else:
        mix_type = "Unclear Mix"

    return {
        "mix_type": mix_type,
        "num_ratio": round(num_ratio, 3),
        "cat_ratio": round(cat_ratio, 3)
    }

#^ checking missingness
def analyze_missingness(df: pd.DataFrame, signal_output: dict, critical_threshold=0.30):
    # Get the global ratio from signal_output
    global_missing = signal_output['Health Check']['missing_ratio']
    
    # Calculate per-column missingness using the raw DF passed by the runner
    col_missing_ratios = df.isnull().mean()
    critical_cols = col_missing_ratios[col_missing_ratios > critical_threshold].index.tolist()
    critical_count = len(critical_cols)
    
    tests = {}
    
    # Check 1: General volume
    if global_missing < 0.05:
        status_vol = "SAFE"
    elif global_missing < 0.15:
        status_vol = "WARNING"
    else:
        status_vol = "DANGER"

    tests["dataset_missing_ratio"] = {
        "check_id": "dataset_missing_ratio",
        "metric": round(global_missing, 4),
        "status": status_vol,
        "risk_code": "MISSINGNESS",
        "scope": "DATASET"
    }

    # Check 2: Structural holes
    tests["dataset_structural_missingness"] = {
        "check_id": "dataset_structural_missingness",
        "metric": critical_count,
        "status": "DANGER" if critical_count > 0 else "SAFE",
        "risk_code" : "STRUCTURAL_MISSINGNESS",
        "scope" : "DATASET"
    }
    
    # Check 3: Semantic Missing Values (Hidden Missing)
    # List of common placeholders
    semantic_placeholders = ["?", "NA", "na", "null", "NULL", "None", "none", "", " "]
    
    # Check object columns only for efficiency
    obj_cols = df.select_dtypes(include=['object', 'category'])
    semantic_missing_found = False
    total_semantic_missing = 0
    detected_placeholders = []
    
    if not obj_cols.empty:
        # Check which placeholders are actually present
        for placeholder in semantic_placeholders:
            mask = obj_cols.isin([placeholder])
            count = mask.sum().sum()
            if count > 0:
                detected_placeholders.append(placeholder if placeholder.strip() else repr(placeholder))
        
        # Get total count
        mask = obj_cols.isin(semantic_placeholders)
        total_semantic_missing = mask.sum().sum()
        
        if total_semantic_missing > 0:
            semantic_missing_found = True

    tests["dataset_hidden_missing_values"] = {
        "check_id": "dataset_hidden_missing_values",
        "status": "DANGER" if semantic_missing_found else "SAFE",
        "metric": total_semantic_missing,
        "info": {
            "semantic_missing_detected": semantic_missing_found, 
            "details": f"Found {total_semantic_missing} hidden missing values" if semantic_missing_found else "None"
        },
        "detected_placeholders": detected_placeholders if semantic_missing_found else [],
        "risk_code": "HIDDEN_MISSING",
        "scope": "DATASET"
    }

    constraints = []
    if critical_count > 0:
        constraints.append(f"Row-wise deletion unsafe; high missingness in: {critical_cols}")
        
    if semantic_missing_found:
        constraints.append(f"Hidden missing values detected (e.g. '?', 'NA'). Preprocessing required to handle them.")

    return tests, constraints
   
#^ checking duplicates  
def analyze_duplicates(signal_output:dict):
    duplicates_ratio = signal_output['Health Check']['duplicated_ratio']
    
    tests = {}
    
    if duplicates_ratio < 0.005:
        status = "SAFE"
    elif duplicates_ratio < 0.02:
        status = "WARNING"
    else:
        status = "DANGER"
    
    tests["dataset_duplicates_ratio"] = {
        "check_id": "dataset_duplicates_ratio",
        "metric" : duplicates_ratio,
        "status": status,
        "risk_code" : "DUPLICATION",
        "scope" : "DATASET"
    }
    
    constraints = []
    if status == "WARNING":
        constraints.append("Minor row-level bias detected; consider deduplication.")
    elif status == "DANGER":
        constraints.append("CRITICAL: Significant row-level bias. Statistics are unreliable.")
        

    return tests, constraints

#^ checking constant 
def analyze_constant_features(df: pd.DataFrame, signal_output: dict):
    max_constant = signal_output["Health Check"]["constant_ratio"]["max_ratio"]

    tests = {}
    
    # Find columns with near-constant values (threshold: 0.90)
    flagged_columns = []
    warning_threshold = 0.90
    danger_threshold = 0.95
    
    for col in df.columns:
        s = df[col].dropna()
        if s.empty:
            continue
        ratio = s.value_counts(normalize=True).iloc[0]
        if ratio >= warning_threshold:
            flagged_columns.append(col)

    # A4b: Presence of degenerate features
    if max_constant < 0.90:
        status_local = "SAFE"
    elif max_constant < 0.95:
        status_local = "WARNING"
    else:
        status_local = "DANGER"

    tests["column_max_constant_ratio"] = {
        "check_id": "column_max_constant_ratio",
        "metric": max_constant,
        "status": status_local,
        "risk_code": "DEGENERACY",
        "scope": "COLUMN",
        "column": flagged_columns
    }

    constraints = []

    if status_local in ["WARNING", "DANGER"]:
        constraints.append(
            "Some features may be non-informative and distort feature importance estimates"
        )

    return tests, constraints

#^ checking cardinality
def analyze_cardinality(signal_output: dict):
    cardinality_ratio = signal_output["Complexity profile"]["Cardinality"]
    
    tests = {}
    

    if cardinality_ratio <= 0.10:
        status = "SAFE"
    elif cardinality_ratio <= 0.50:
        status = "WARNING"
    else:
        status = "DANGER"
        
    
    tests["dataset_cardinality_ratio"] = {
        "check_id": "dataset_cardinality_ratio",
        "metric": cardinality_ratio,
        "status": status,
        "risk_code": "CARDINALITY_EXPLOSION",
        "scope": "DATASET"
    }
    
    constraints = []
    if status in ["WARNING", "DANGER"]:
        constraints.append("Naive categorical encoding may cause dimensions explosion")
    
    return tests, constraints

#^ checking multicollinearity
def analyze_multicollinearity(signal_output: dict):
    ratio = signal_output["Complexity profile"]["Multicollinearity"]
    
    if ratio <= 0.02:
        status = "SAFE"
    elif ratio <= 0.10:
        status = "WARNING"
    else:
        status = "DANGER"
    
    tests = {}
    tests["dataset_multicollinearity_density"] = {
        "check_id": "dataset_multicollinearity_density",
        "metric": ratio, 
        "status": status,
        "risk_code": "MULTICOLLINEARITY",
        "scope": "DATASET"
    }
    
    constraints = []
    if status in ["WARNING", "DANGER"]:
        constraints.append("Linear feature weights are unreliable")
        
    return tests, constraints

#^ detecting outliers
def analyze_outliers(signal_output: dict):
    ratio = signal_output["Complexity profile"]["Outliers"]
    
    if ratio <= 0.05:
        status = "SAFE"
    elif ratio <= 0.15:
        status = "WARNING"
    else:
        status = "DANGER"
    
    tests = {}
    tests["dataset_outlier_ratio"] = {
        "check_id": "dataset_outlier_ratio",
        "metric": ratio,
        "status": status,
        "risk_code": "OUTLIER_SENSITIVITY",
        "scope": "DATASET"
    }
    
    constraints = []
    if status in ["WARNING", "DANGER"]:
        constraints.append("Mean and scale-based statistics are unreliable")
        
    return tests, constraints

#^ checking mixed
def analyze_mixed(signal_output: dict):
    ratio = signal_output["Complexity profile"]["Mixed"]
    
    if ratio == 0.0:
        status = "SAFE"
    else:
        status = "DANGER"
    
    tests = {}
    tests["dataset_mixed_type_ratio"] = {
        "check_id": "dataset_mixed_type_ratio",
        "metric" : ratio,
        "status" : status,
        "risk_code": "TYPE_AMBIGUITY",
        "scope": "DATASET"
    }
    constraints = []
    if status == "DANGER":
        constraints.append("Column-level type assumptions are invalid")
        
    return tests, constraints

#~ combined function 
def run_logic_extraction(df: pd.DataFrame, signal_output: dict):
    result = {
        "facts": {},
        "tests": {},
        "constraints": []
    }

    # Facts
    result["facts"]["dimensions"] = extract_dataset_dimensions(signal_output)
    result["facts"]["memory"] = extract_memory_footprint(signal_output)
    result["facts"]["feature_mix"] = extract_feature_mix(signal_output)

    # Logic checks (NO KEYS)
    logic_functions = [
        lambda: analyze_missingness(df, signal_output),
        lambda: analyze_duplicates(signal_output),
        lambda: analyze_constant_features(df, signal_output),
        lambda: analyze_cardinality(signal_output),
        lambda: analyze_multicollinearity(signal_output),
        lambda: analyze_outliers(signal_output),
        lambda: analyze_mixed(signal_output),
    ]

    for fn in logic_functions:
        tests, cons = fn()

        # Merge tests (flat)
        for k, v in tests.items():
            if k in result["tests"]:
                raise ValueError(f"Duplicate test ID: {k}")
            result["tests"][k] = v

        # Merge constraints (list)
        result["constraints"].extend(cons)

    # Add verdicts to all tests based on risk_code and status
    result["tests"] = add_verdicts_to_tests(result["tests"])

    return result


if __name__ == "__main__":
    layer1_diagnostics()
