import pandas as pd
import numpy as np


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
    
    assumptions = {}
    
    # Check 1: General volume
    if global_missing < 0.05:
        status_vol = "SAFE"
    elif global_missing < 0.15:
        status_vol = "WARNING"
    else:
        status_vol = "DANGER"

    assumptions["Data is mostly complete"] = {
        "status": status_vol,
        "evidence": {"missing_ratio": round(global_missing, 4)}
    }

    # Check 2: Structural holes
    assumptions["Missingness is not structural"] = {
        "status": "DANGER" if critical_count > 0 else "SAFE",
        "evidence": {"critical_columns_found": critical_count}
    }
    
    # Check 3: Semantic Missing Values (Hidden Missing)
    # List of common placeholders
    semantic_placeholders = ["?", "NA", "na", "null", "NULL", "None", "none", "", " "]
    
    # Check object columns only for efficiency
    obj_cols = df.select_dtypes(include=['object', 'category'])
    semantic_missing_found = False
    semantic_evidence = []
    
    if not obj_cols.empty:
        # Check if any value in the entire object dataframe matches the placeholders
        # using isin matches exact strings
        mask = obj_cols.isin(semantic_placeholders)
        total_semantic_missing = mask.sum().sum()
        
        if total_semantic_missing > 0:
            semantic_missing_found = True
            semantic_evidence = f"Found {total_semantic_missing} hidden missing values"

    assumptions["No hidden missing values"] = {
        "status": "DANGER" if semantic_missing_found else "SAFE",
        "evidence": {"semantic_missing_detected": semantic_missing_found, "details": semantic_evidence if semantic_missing_found else "None"}
    }

    constraints = []
    if critical_count > 0:
        constraints.append(f"Row-wise deletion unsafe; high missingness in: {critical_cols}")
        
    if semantic_missing_found:
        constraints.append(f"Hidden missing values detected (e.g. '?', 'NA'). Preprocessing required to handle them.")

    return assumptions, constraints
   
#^ checking duplicates  
def analyze_duplicates(signal_output:dict):
    duplicates_ratio = signal_output['Health Check']['duplicated_ratio']
    
    assumptions = {}
    
    if duplicates_ratio < 0.005:
        status = "SAFE"
    elif duplicates_ratio < 0.02:
        status = "WARNING"
    else:
        status = "DANGER"
    
    assumptions['Duplicate rows are negligible'] = {
        "status": status,
        "evidence" : {"duplicated_ratio" : duplicates_ratio}
    }
    
    constraints = []
    if status == "WARNING":
        constraints.append("Minor row-level bias detected; consider deduplication.")
    elif status == "DANGER":
        constraints.append("CRITICAL: Significant row-level bias. Statistics are unreliable.")
        

    return assumptions, constraints

#^ checking constant 
def analyze_constant_features(signal_output: dict):
    mean_constant = signal_output["Health Check"]["constant_ratio"]["mean_ratio"]
    max_constant = signal_output["Health Check"]["constant_ratio"]["max_ratio"]

    assumptions = {}

    # A4: Global feature information density
    # A4: Global feature information density
    if mean_constant <= 0.50:
        status_global = "SAFE"
    elif mean_constant <= 0.80:
        status_global = "WARNING"
    else:
        status_global = "DANGER"

    assumptions["Most features carry information"] = {
        "status": status_global,
        "evidence": {
            "mean_constant_ratio": mean_constant
        }
    }

    # A4b: Presence of degenerate features
    if max_constant < 0.90:
        status_local = "SAFE"
    elif max_constant < 0.95:
        status_local = "WARNING"
    else:
        status_local = "DANGER"

    assumptions["No degenerate features exists"] = {
        "status": status_local,
        "evidence": {
            "max_constant_ratio": max_constant
        }
    }

    constraints = []

    if status_global in ["WARNING", "DANGER"]:
        constraints.append(
            "Global feature signal density is low; aggregate statistics may be diluted"
        )

    if status_local in ["WARNING", "DANGER"]:
        constraints.append(
            "Some features may be non-informative and distort feature importance estimates"
        )

    return assumptions, constraints

#^ checking cardinality
def analyze_cardinality(signal_output: dict):
    cardinality_ratio = signal_output["Complexity profile"]["Cardinality"]
    
    assumptions = {}
    

    if cardinality_ratio <= 0.10:
        status = "SAFE"
    elif cardinality_ratio <= 0.50:
        status = "WARNING"
    else:
        status = "DANGER"
        
    
    assumptions["Cardinality is manageable"] = {
        "status": status,
        "evidence": {"cardinality_ratio": cardinality_ratio}
    }
    
    constraints = []
    if status in ["WARNING", "DANGER"]:
        constraints.append("Naive categorical encoding may cause dimensions explosion")
    
    return assumptions, constraints

#^ checking multicollinearity
def analyze_multicollinearity(signal_output: dict):
    ratio = signal_output["Complexity profile"]["Multicollinearity"]
    
    if ratio <= 0.02:
        status = "SAFE"
    elif ratio <= 0.10:
        status = "WARNING"
    else:
        status = "DANGER"
    
    assumptions = {}
    assumptions["Strong multicollinearity is limited"] = {
        "status": status,
        "evidence": {"multicollinearity_density": ratio} 
    }
    
    constraints = []
    if status in ["WARNING", "DANGER"]:
        constraints.append("Linear feature weights are unreliable")
        
    return assumptions, constraints

#^ detecting outliers
def analyze_outliers(signal_output: dict):
    ratio = signal_output["Complexity profile"]["Outliers"]
    
    if ratio <= 0.05:
        status = "SAFE"
    elif ratio <= 0.15:
        status = "WARNING"
    else:
        status = "DANGER"
    
    assumptions = {}
    assumptions["Extreme outliers are rare"] = {
        "status": status,
        "evidence": {"outlier_ratio" : ratio}
    }
    
    constraints = []
    if status in ["WARNING", "DANGER"]:
        constraints.append("Mean and scale-based statistics are unreliable")
        
    return assumptions, constraints

#^ checking mixed
def analyze_mixed(signal_output: dict):
    ratio = signal_output["Complexity profile"]["Mixed"]
    
    if ratio == 0.0:
        status = "SAFE"
    else:
        status = "DANGER"
    
    assumptions = {}
    assumptions["Mixed columns are rare"] = {
        "status" : status,
        "evidence" : {"mixed_ratio" : ratio}
    }
    constraints = []
    if status == "DANGER":
        constraints.append("Column-level type assumptions are invalid")
        
    return assumptions, constraints

#~ combined function 
def run_logic_extraction(df: pd.DataFrame, signal_output: dict):
    result = {
        "facts": {},
        "assumptions": {},
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
        lambda: analyze_constant_features(signal_output),
        lambda: analyze_cardinality(signal_output),
        lambda: analyze_multicollinearity(signal_output),
        lambda: analyze_outliers(signal_output),
        lambda: analyze_mixed(signal_output),
    ]

    for fn in logic_functions:
        asm, cons = fn()

        # Merge assumptions (flat)
        for k, v in asm.items():
            if k in result["assumptions"]:
                raise ValueError(f"Duplicate assumption ID: {k}")
            result["assumptions"][k] = v

        # Merge constraints (list)
        result["constraints"].extend(cons)

    return result


if __name__ == "__main__":
    layer1_diagnostics()
