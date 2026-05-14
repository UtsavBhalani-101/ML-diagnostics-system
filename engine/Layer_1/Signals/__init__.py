"""
Signal orchestrator for Layer 1.

Aggregates all signal modules and produces a flat dict
that the pipeline and logic layers can consume.
"""
import pandas as pd
import logging

from engine.Layer_1.Signals.data_integrity_signals import run_data_integrity_signals
from engine.Layer_1.Signals.sample_adequacy_signals import run_sample_adequacy_signals
from engine.Layer_1.Signals.target_validity_signals import run_target_validity_signals
from engine.Layer_1.schema import SignalExtractionResult

logger = logging.getLogger(__name__)


def run_signal_extraction(df: pd.DataFrame, target_column: str | None = None) -> SignalExtractionResult:
    logger.info("Starting Layer 1 signal extraction")
    dimensions = {}
    
    logger.info("Extracting Data Integrity signals")
    dimensions["data_integrity"] = run_data_integrity_signals(df)
    
    logger.info("Extracting Sample Adequacy signals")
    dimensions["sample_adequacy"] = run_sample_adequacy_signals(df)
    
    if target_column and target_column in df.columns:
        logger.info(f"Extracting Target Validity signals for: {target_column}")
        y = df[target_column]
        if isinstance(y, pd.Series):
            dimensions["target_validity"] = run_target_validity_signals(y, target_column)
    
    logger.info("Signal extraction complete")
    return SignalExtractionResult(dimensions=dimensions)
    
    

if __name__ == "__main__":
    df = pd.read_csv(r"D:\ML diagnose v1\test_files\train.csv")
    target = "Survived"
    
    results = run_signal_extraction(df, target)
    
    print(results)
    # print(results.get("data_integrity", "global_missing_ratio"))