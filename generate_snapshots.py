"""
Layer 1 Test Suite & Snapshot Generator
========================================
Tests each Layer 1 module individually and saves outputs to /tests folder.

Modules tested:
- signals.py: Signal extraction functions
- logic.py: Logic and diagnostic analysis
- report.py: Report generation
- pipeline.py: Full pipeline integration test
"""

import pandas as pd
import os
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from engine.Layer_1 import signals
from engine.Layer_1 import logic
from engine.Layer_1 import report
from engine.Layer_1.pipeline import run_pipeline


# ============================================================
# Configuration
# ============================================================

TEST_DATA_PATH = r"D:\ML diagnose v1\uploads\adult.csv"
TESTS_DIR = "tests"
LAYER1_TESTS_DIR = os.path.join(TESTS_DIR, "layer1")

# Target column (adjust based on your dataset)
TARGET_COLUMN = "income"


# ============================================================
# Utility Functions
# ============================================================

def setup_test_dirs():
    """Create test directories if they don't exist."""
    for dir_path in [TESTS_DIR, LAYER1_TESTS_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")


def save_json(data: dict, filename: str, subdir: str = None):
    """Save dictionary as JSON file."""
    if subdir:
        filepath = os.path.join(LAYER1_TESTS_DIR, subdir, filename)
        os.makedirs(os.path.join(LAYER1_TESTS_DIR, subdir), exist_ok=True)
    else:
        filepath = os.path.join(LAYER1_TESTS_DIR, filename)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4, default=str)
    print(f"  ✓ Saved: {filepath}")
    return filepath


def save_csv(df: pd.DataFrame, filename: str):
    """Save DataFrame as CSV file."""
    filepath = os.path.join(LAYER1_TESTS_DIR, filename)
    df.to_csv(filepath, index=False)
    print(f"  ✓ Saved: {filepath}")
    return filepath


def load_test_data():
    """Load the test dataset."""
    if not os.path.exists(TEST_DATA_PATH):
        raise FileNotFoundError(f"Test data not found: {TEST_DATA_PATH}")
    
    df = pd.read_csv(TEST_DATA_PATH)
    print(f"Loaded test data: {df.shape[0]} rows, {df.shape[1]} columns")
    return df


# ============================================================
# Individual Module Tests
# ============================================================

def test_signals_module(df: pd.DataFrame, target: pd.Series) -> dict:
    """
    Test all functions in signals.py individually.
    """
    print("\n" + "="*60)
    print("TESTING: signals.py")
    print("="*60)
    
    results = {
        "module": "signals.py",
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Test 1: classify_non_numeric
    print("\n[1/10] Testing classify_non_numeric...")
    try:
        valid_cats = signals.classify_non_numeric(df)
        results["tests"]["classify_non_numeric"] = {
            "status": "PASS",
            "output": valid_cats,
            "count": len(valid_cats)
        }
        print(f"  ✓ Found {len(valid_cats)} valid categorical columns")
    except Exception as e:
        results["tests"]["classify_non_numeric"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 2: get_memory_usage
    print("\n[2/10] Testing get_memory_usage...")
    try:
        memory = signals.get_memory_usage(df)
        results["tests"]["get_memory_usage"] = {
            "status": "PASS",
            "output": memory,
            "unit": "MB"
        }
        print(f"  ✓ Memory usage: {memory} MB")
    except Exception as e:
        results["tests"]["get_memory_usage"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 3: get_metadata
    print("\n[3/10] Testing get_metadata...")
    try:
        metadata = signals.get_metadata(df)
        results["tests"]["get_metadata"] = {
            "status": "PASS",
            "output": metadata
        }
        print(f"  ✓ Metadata extracted: {list(metadata.keys())}")
    except Exception as e:
        results["tests"]["get_metadata"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 4: get_global_constant_ratio
    print("\n[4/10] Testing get_global_constant_ratio...")
    try:
        constant_ratio = signals.get_global_constant_ratio(df)
        results["tests"]["get_global_constant_ratio"] = {
            "status": "PASS",
            "output": constant_ratio
        }
        print(f"  ✓ Constant ratio: {constant_ratio}")
    except Exception as e:
        results["tests"]["get_global_constant_ratio"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 5: get_health_signals
    print("\n[5/10] Testing get_health_signals...")
    try:
        health = signals.get_health_signals(df, target)
        results["tests"]["get_health_signals"] = {
            "status": "PASS",
            "output": health
        }
        print(f"  ✓ Health signals: {list(health.keys())}")
    except Exception as e:
        results["tests"]["get_health_signals"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 6: get_global_multicollinearity
    print("\n[6/10] Testing get_global_multicollinearity...")
    try:
        multicol = signals.get_global_multicollinearity(df)
        results["tests"]["get_global_multicollinearity"] = {
            "status": "PASS",
            "output": multicol
        }
        print(f"  ✓ Multicollinearity ratio: {multicol}")
    except Exception as e:
        results["tests"]["get_global_multicollinearity"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 7: get_global_cardinality
    print("\n[7/10] Testing get_global_cardinality...")
    try:
        cardinality = signals.get_global_cardinality(df)
        results["tests"]["get_global_cardinality"] = {
            "status": "PASS",
            "output": cardinality
        }
        print(f"  ✓ Cardinality ratio: {cardinality}")
    except Exception as e:
        results["tests"]["get_global_cardinality"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 8: get_global_outlier_ratio
    print("\n[8/10] Testing get_global_outlier_ratio...")
    try:
        outliers = signals.get_global_outlier_ratio(df)
        results["tests"]["get_global_outlier_ratio"] = {
            "status": "PASS",
            "output": outliers
        }
        print(f"  ✓ Outlier ratio: {outliers}")
    except Exception as e:
        results["tests"]["get_global_outlier_ratio"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 9: get_global_mixed_type_ratio
    print("\n[9/10] Testing get_global_mixed_type_ratio...")
    try:
        mixed = signals.get_global_mixed_type_ratio(df)
        results["tests"]["get_global_mixed_type_ratio"] = {
            "status": "PASS",
            "output": mixed
        }
        print(f"  ✓ Mixed type ratio: {mixed}")
    except Exception as e:
        results["tests"]["get_global_mixed_type_ratio"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 10: get_complexity_profile
    print("\n[10/10] Testing get_complexity_profile...")
    try:
        complexity = signals.get_complexity_profile(df)
        results["tests"]["get_complexity_profile"] = {
            "status": "PASS",
            "output": complexity
        }
        print(f"  ✓ Complexity profile: {list(complexity.keys())}")
    except Exception as e:
        results["tests"]["get_complexity_profile"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test: Full signal extraction
    print("\n[FULL] Testing run_signals_extraction...")
    try:
        full_signals = signals.run_signals_extraction(df, target)
        results["tests"]["run_signals_extraction"] = {
            "status": "PASS",
            "output": full_signals
        }
        print(f"  ✓ Full signal extraction complete")
        save_json(full_signals, "signals_output.json")
    except Exception as e:
        results["tests"]["run_signals_extraction"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Summary
    passed = sum(1 for t in results["tests"].values() if t.get("status") == "PASS")
    total = len(results["tests"])
    results["summary"] = {"passed": passed, "total": total, "success_rate": f"{passed/total*100:.1f}%"}
    
    print(f"\nSignals Module: {passed}/{total} tests passed")
    save_json(results, "signals_tests.json")
    
    return results


def test_logic_module(df: pd.DataFrame, signal_output: dict) -> dict:
    """
    Test all functions in logic.py individually.
    """
    print("\n" + "="*60)
    print("TESTING: logic.py")
    print("="*60)
    
    results = {
        "module": "logic.py",
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Test 1: extract_dataset_dimensions
    print("\n[1/8] Testing extract_dataset_dimensions...")
    try:
        dims = logic.extract_dataset_dimensions(signal_output)
        results["tests"]["extract_dataset_dimensions"] = {
            "status": "PASS",
            "output": dims
        }
        print(f"  ✓ Dimensions: {dims}")
    except Exception as e:
        results["tests"]["extract_dataset_dimensions"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 2: extract_memory_footprint
    print("\n[2/8] Testing extract_memory_footprint...")
    try:
        memory = logic.extract_memory_footprint(signal_output)
        results["tests"]["extract_memory_footprint"] = {
            "status": "PASS",
            "output": memory
        }
        print(f"  ✓ Memory footprint: {memory}")
    except Exception as e:
        results["tests"]["extract_memory_footprint"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 3: extract_feature_mix
    print("\n[3/8] Testing extract_feature_mix...")
    try:
        feature_mix = logic.extract_feature_mix(signal_output)
        results["tests"]["extract_feature_mix"] = {
            "status": "PASS",
            "output": feature_mix
        }
        print(f"  ✓ Feature mix: {feature_mix}")
    except Exception as e:
        results["tests"]["extract_feature_mix"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 4: analyze_missingness
    print("\n[4/8] Testing analyze_missingness...")
    try:
        missingness = logic.analyze_missingness(df, signal_output)
        results["tests"]["analyze_missingness"] = {
            "status": "PASS",
            "output": missingness
        }
        print(f"  ✓ Missingness analysis complete")
    except Exception as e:
        results["tests"]["analyze_missingness"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 5: analyze_duplicates
    print("\n[5/8] Testing analyze_duplicates...")
    try:
        duplicates = logic.analyze_duplicates(signal_output)
        results["tests"]["analyze_duplicates"] = {
            "status": "PASS",
            "output": duplicates
        }
        print(f"  ✓ Duplicates analysis complete")
    except Exception as e:
        results["tests"]["analyze_duplicates"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 6: analyze_constant_features
    print("\n[6/8] Testing analyze_constant_features...")
    try:
        constants = logic.analyze_constant_features(df, signal_output)
        results["tests"]["analyze_constant_features"] = {
            "status": "PASS",
            "output": constants
        }
        print(f"  ✓ Constant features analysis complete")
    except Exception as e:
        results["tests"]["analyze_constant_features"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 7: analyze_outliers
    print("\n[7/8] Testing analyze_outliers...")
    try:
        outliers = logic.analyze_outliers(signal_output)
        results["tests"]["analyze_outliers"] = {
            "status": "PASS",
            "output": outliers
        }
        print(f"  ✓ Outliers analysis complete")
    except Exception as e:
        results["tests"]["analyze_outliers"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test 8: analyze_mixed
    print("\n[8/8] Testing analyze_mixed...")
    try:
        mixed = logic.analyze_mixed(signal_output)
        results["tests"]["analyze_mixed"] = {
            "status": "PASS",
            "output": mixed
        }
        print(f"  ✓ Mixed types analysis complete")
    except Exception as e:
        results["tests"]["analyze_mixed"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Test: Full logic extraction
    print("\n[FULL] Testing run_logic_extraction...")
    try:
        full_logic = logic.run_logic_extraction(df, signal_output)
        results["tests"]["run_logic_extraction"] = {
            "status": "PASS",
            "output": full_logic
        }
        print(f"  ✓ Full logic extraction complete")
        save_json(full_logic, "logic_output.json")
    except Exception as e:
        results["tests"]["run_logic_extraction"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Summary
    passed = sum(1 for t in results["tests"].values() if t.get("status") == "PASS")
    total = len(results["tests"])
    results["summary"] = {"passed": passed, "total": total, "success_rate": f"{passed/total*100:.1f}%"}
    
    print(f"\nLogic Module: {passed}/{total} tests passed")
    save_json(results, "logic_tests.json")
    
    return results


def test_report_module(diagnostics: dict) -> dict:
    """
    Test report.py functions.
    """
    print("\n" + "="*60)
    print("TESTING: report.py")
    print("="*60)
    
    results = {
        "module": "report.py",
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Test: print_layer1_report
    print("\n[1/1] Testing print_layer1_report...")
    try:
        # Capture print output
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            report.print_layer1_report(diagnostics)
        
        output = f.getvalue()
        results["tests"]["print_layer1_report"] = {
            "status": "PASS",
            "output_preview": output[:500] + "..." if len(output) > 500 else output
        }
        print(f"  ✓ Report generated ({len(output)} characters)")
        
        # Save full report as text
        with open(os.path.join(LAYER1_TESTS_DIR, "report_output.txt"), 'w') as rf:
            rf.write(output)
        print(f"  ✓ Saved: tests/layer1/report_output.txt")
        
    except Exception as e:
        results["tests"]["print_layer1_report"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Summary
    passed = sum(1 for t in results["tests"].values() if t.get("status") == "PASS")
    total = len(results["tests"])
    results["summary"] = {"passed": passed, "total": total, "success_rate": f"{passed/total*100:.1f}%"}
    
    print(f"\nReport Module: {passed}/{total} tests passed")
    save_json(results, "report_tests.json")
    
    return results


def test_pipeline_integration(file_path: str) -> dict:
    """
    Test the full pipeline.py integration.
    """
    print("\n" + "="*60)
    print("TESTING: pipeline.py (Integration Test)")
    print("="*60)
    
    results = {
        "module": "pipeline.py",
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    print("\n[INTEGRATION] Testing run_pipeline...")
    try:
        pipeline_output = run_pipeline(file_path)
        
        results["tests"]["run_pipeline"] = {
            "status": "PASS" if pipeline_output.get("status") == "success" else "FAIL",
            "output": pipeline_output
        }
        
        if pipeline_output.get("status") == "success":
            print(f"  ✓ Pipeline completed successfully")
            print(f"    - Keys in output: {list(pipeline_output.keys())}")
        else:
            print(f"  ⚠ Pipeline returned error: {pipeline_output.get('message')}")
        
        save_json(pipeline_output, "pipeline_output.json")
        
    except Exception as e:
        results["tests"]["run_pipeline"] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Error: {e}")
    
    # Summary
    passed = sum(1 for t in results["tests"].values() if t.get("status") == "PASS")
    total = len(results["tests"])
    results["summary"] = {"passed": passed, "total": total, "success_rate": f"{passed/total*100:.1f}%"}
    
    print(f"\nPipeline Integration: {passed}/{total} tests passed")
    save_json(results, "pipeline_tests.json")
    
    return results


# ============================================================
# Main Test Runner
# ============================================================

def run_all_tests():
    """
    Run all Layer 1 tests and generate comprehensive report.
    """
    print("\n" + "#"*60)
    print("#" + " "*18 + "LAYER 1 TEST SUITE" + " "*18 + "#")
    print("#"*60)
    print(f"\nStarted at: {datetime.now().isoformat()}")
    
    # Setup
    setup_test_dirs()
    
    # Load test data
    try:
        df = load_test_data()
        target = df[TARGET_COLUMN]
        features = df.drop(columns=[TARGET_COLUMN])
    except Exception as e:
        print(f"\n✗ Failed to load test data: {e}")
        return
    
    all_results = {
        "test_suite": "Layer 1",
        "timestamp": datetime.now().isoformat(),
        "data_info": {
            "source": TEST_DATA_PATH,
            "rows": len(df),
            "columns": len(df.columns),
            "target_column": TARGET_COLUMN
        },
        "modules": {}
    }
    
    # Test 1: Signals Module
    signals_results = test_signals_module(features, target)
    all_results["modules"]["signals"] = signals_results["summary"]
    
    # Get signal output for subsequent tests
    try:
        signal_output = signals.run_signals_extraction(features, target)
    except:
        signal_output = {}
    
    # Test 2: Logic Module
    logic_results = test_logic_module(features, signal_output)
    all_results["modules"]["logic"] = logic_results["summary"]
    
    # Get diagnostics for report test
    try:
        diagnostics = logic.run_logic_extraction(features, signal_output)
    except:
        diagnostics = {}
    
    # Test 3: Report Module
    report_results = test_report_module(diagnostics)
    all_results["modules"]["report"] = report_results["summary"]
    
    # Test 4: Pipeline Integration
    pipeline_results = test_pipeline_integration(TEST_DATA_PATH)
    all_results["modules"]["pipeline"] = pipeline_results["summary"]
    
    # Final Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    total_passed = 0
    total_tests = 0
    
    for module, summary in all_results["modules"].items():
        passed = summary.get("passed", 0)
        total = summary.get("total", 0)
        total_passed += passed
        total_tests += total
        status = "✓" if passed == total else "⚠"
        print(f"  {status} {module}: {passed}/{total} ({summary.get('success_rate', 'N/A')})")
    
    print(f"\n  TOTAL: {total_passed}/{total_tests} tests passed")
    all_results["final_summary"] = {
        "total_passed": total_passed,
        "total_tests": total_tests,
        "success_rate": f"{total_passed/total_tests*100:.1f}%" if total_tests > 0 else "N/A"
    }
    
    # Save comprehensive report
    save_json(all_results, "layer1_test_summary.json")
    
    print(f"\nCompleted at: {datetime.now().isoformat()}")
    print(f"Results saved to: {LAYER1_TESTS_DIR}/")
    print("#"*60)
    
    return all_results


if __name__ == "__main__":
    run_all_tests()