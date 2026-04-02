"""
Signal orchestrator for Layer 1.

Aggregates all signal modules and produces a flat dict
that the pipeline and logic layers can consume.
"""
import pandas as pd
import logging

from engine.Layer_1.Signals.data_integrity_signals import run_signal_extraction as _run_integrity_signals
from engine.Layer_1.Signals.sample_adequacy_signals import run_sample_adequacy as _run_sample_signals

logger = logging.getLogger(__name__)


def run_signal_extraction(df: pd.DataFrame) -> dict:
    """
    Run all signal modules and merge into a single flat dict.
    This is what pipeline.py calls as `signals.run_signal_extraction(df)`.
    """
    flat = {}

    # ── Data integrity signals ──
    integrity_results = _run_integrity_signals(df)
    for struct in integrity_results:
        name = struct.name
        value = struct.value

        # Flatten compound signals
        if name == "dataset_shape" and isinstance(value, dict):
            flat["rows"] = value.get("rows", 0)
            flat["cols"] = value.get("cols", 0)
        elif name == "column_missing_ratio" and isinstance(value, dict):
            flat["column_missing_ratio"] = value
        elif name == "constant_columns" and isinstance(value, dict):
            flat["constant_columns"] = value.get("columns", [])
            flat["constant_ratio"] = value.get("ratio", 0.0)
        elif name == "hidden_missing_ratio" and isinstance(value, dict):
            flat["hidden_missing_ratio"] = value
        elif name == "mixed_type_columns" and isinstance(value, dict):
            flat["mixed_type_columns"] = value.get("columns", [])
            flat["mixed_ratio"] = value.get("ratio", 0.0)
        else:
            flat[name] = value

    # ── Sample adequacy signals ──
    sample_results = _run_sample_signals(df)
    for struct in sample_results:
        name = struct.name
        value = struct.value
        # Only add if not already present (rows/cols from integrity)
        if name == "dataset_size":
            flat.setdefault("rows", value)
        elif name == "feature_count":
            flat.setdefault("cols", value)
        elif name == "n_to_d_ratio":
            flat["sample_feature_ratio"] = value
        else:
            flat.setdefault(name, value)

    logger.info(f"Signal extraction complete: {len(flat)} keys")
    return flat
