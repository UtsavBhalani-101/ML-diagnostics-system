"""
Phase A Pipeline Orchestrator
=============================
Runs all Phase A diagnostic modules on numeric columns.

Flow:
1. Data → Signals folder
2. divide_dtype.py groups columns by dtype
3. Numeric columns → Phase_A diagnostics (this pipeline)
"""

import pandas as pd
from typing import Dict, Any, List, Optional

# Import all Phase A diagnostics
from concentration import ConcentrationDiagnostic
from outlier_geometry import NumericOutlierGeometryDiagnostic
from validity import NumericValidityDiagnostic
from categorical_disguise import analyze_numeric_category_pathology
from redundancy import NumericRedundancyDiagnostic
from scale_inconsistency import NumericScaleInconsistencyDiagnostic
from placeholder_detection import NumericPlaceholderDiagnostic
from column_affordances import phase_a_column_affordances
from numeric_geometry import NumericGeometryDiagnostic
from id_structure import NumericIDStructureDiagnostic


def run_phase_a_single_column(col: pd.Series, col_name: str) -> Dict[str, Any]:
    """
    Run all Phase A diagnostics on a single numeric column.
    
    Args:
        col: Pandas Series containing numeric data
        col_name: Name of the column
        
    Returns:
        Dict containing results from all diagnostics
    """
    results = {
        "column": col_name,
        "diagnostics": {}
    }
    
    # 1. Concentration (constant/near-constant detection)
    try:
        conc_diag = ConcentrationDiagnostic()
        results["diagnostics"]["concentration"] = conc_diag.diagnose(col)
    except Exception as e:
        results["diagnostics"]["concentration"] = {"error": str(e)}
    
    # 2. Outlier Geometry (extreme structure)
    try:
        outlier_diag = NumericOutlierGeometryDiagnostic()
        results["diagnostics"]["outlier_geometry"] = outlier_diag.diagnose(col)
    except Exception as e:
        results["diagnostics"]["outlier_geometry"] = {"error": str(e)}
    
    # 3. Validity (sign consistency, scale spikes)
    try:
        validity_diag = NumericValidityDiagnostic()
        results["diagnostics"]["validity"] = validity_diag.diagnose(col)
    except Exception as e:
        results["diagnostics"]["validity"] = {"error": str(e)}
    
    # 4. Categorical Disguise (mixed semantics detection)
    try:
        results["diagnostics"]["categorical_disguise"] = analyze_numeric_category_pathology(col)
    except Exception as e:
        results["diagnostics"]["categorical_disguise"] = {"error": str(e)}
    
    # 5. Redundancy (intra-column redundancy)
    try:
        redundancy_diag = NumericRedundancyDiagnostic()
        results["diagnostics"]["redundancy"] = redundancy_diag.diagnose(col)
    except Exception as e:
        results["diagnostics"]["redundancy"] = {"error": str(e)}
    
    # 6. Scale Inconsistency (multi-regime scales)
    try:
        scale_diag = NumericScaleInconsistencyDiagnostic()
        results["diagnostics"]["scale_inconsistency"] = scale_diag.diagnose(col)
    except Exception as e:
        results["diagnostics"]["scale_inconsistency"] = {"error": str(e)}
    
    # 7. Placeholder Detection (sentinel values)
    try:
        placeholder_diag = NumericPlaceholderDiagnostic()
        results["diagnostics"]["placeholder_detection"] = placeholder_diag.diagnose(col)
    except Exception as e:
        results["diagnostics"]["placeholder_detection"] = {"error": str(e)}
    
    # 8. Column Affordances (shape and structural signals)
    try:
        results["diagnostics"]["column_affordances"] = phase_a_column_affordances(col, col_name)
    except Exception as e:
        results["diagnostics"]["column_affordances"] = {"error": str(e)}
    
    # 9. Numeric Geometry (scale + shape risks)
    try:
        geometry_diag = NumericGeometryDiagnostic()
        results["diagnostics"]["numeric_geometry"] = geometry_diag.diagnose(col)
    except Exception as e:
        results["diagnostics"]["numeric_geometry"] = {"error": str(e)}
    
    # 10. ID Structure (ID-like detection)
    try:
        id_diag = NumericIDStructureDiagnostic()
        results["diagnostics"]["id_structure"] = id_diag.diagnose(col)
    except Exception as e:
        results["diagnostics"]["id_structure"] = {"error": str(e)}
    
    return results


def run_phase_a_all_columns(df: pd.DataFrame, numeric_cols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run Phase A diagnostics on all numeric columns in a DataFrame.
    
    Args:
        df: Input DataFrame
        numeric_cols: Optional list of numeric column names. 
                      If None, will auto-detect numeric columns.
        
    Returns:
        Dict with results for each column
    """
    if numeric_cols is None:
        numeric_cols = list(df.select_dtypes(include='number').columns)
    
    results = {
        "total_columns": len(numeric_cols),
        "columns": {}
    }
    
    for col_name in numeric_cols:
        results["columns"][col_name] = run_phase_a_single_column(df[col_name], col_name)
    
    return results


def run_full_layer2_pipeline(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run the complete Layer 2 pipeline:
    1. Divide columns by dtype
    2. Run Phase A diagnostics on numeric columns
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dict with dtype grouping and Phase A results for numeric columns
    """
    import sys
    import os
    
    # Add Signals directory to import divide_dtype
    # Path: Phase_A -> Numeric -> Signals
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Phase_A
    numeric_dir = os.path.dirname(current_dir)                 # Numeric
    signals_dir = os.path.dirname(numeric_dir)                 # Signals
    if signals_dir not in sys.path:
        sys.path.insert(0, signals_dir)
    
    from divide_dtype import find_dtype
    
    # Step 1: Divide by dtype
    numeric_cols, categorical_cols, mixed_cols, identifier_cols, text_cols, datetime_cols = find_dtype(df)
    
    results = {
        "dtype_groups": {
            "numeric": numeric_cols,
            "categorical": categorical_cols,
            "mixed": mixed_cols,
            "identifier": identifier_cols,
            "text": text_cols,
            "datetime": datetime_cols
        },
        "phase_a_results": None
    }
    
    # Step 2: Run Phase A on numeric columns
    if numeric_cols:
        results["phase_a_results"] = run_phase_a_all_columns(df, numeric_cols)
    
    return results


if __name__ == "__main__":
    import json
    
    # Test with sample data
    test_data = pd.read_csv(r'D:\ML diagnose v1\tests\snapshot_normalized.csv')
    
    print("=" * 60)
    print("LAYER 2 - PHASE A PIPELINE TEST")
    print("=" * 60)
    
    # Run full pipeline
    results = run_full_layer2_pipeline(test_data)
    
    print(f"\nDtype Groups:")
    for dtype, cols in results["dtype_groups"].items():
        print(f"  {dtype.upper()}: {len(cols)} columns")
    
    if results["phase_a_results"]:
        print(f"\nPhase A Results: {results['phase_a_results']['total_columns']} numeric columns analyzed")
        
        # Show sample result for first column
        first_col = list(results["phase_a_results"]["columns"].keys())[0]
        print(f"\nSample output for '{first_col}':")
        print(json.dumps(results["phase_a_results"]["columns"][first_col], indent=2, default=str))
