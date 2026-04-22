"""
Signal orchestrator for Layer 1.

Aggregates all signal modules and produces a flat dict
that the pipeline and logic layers can consume.
"""
import pandas as pd
import logging

from engine.Layer_1.Signals.data_integrity_signals import run_signal_extraction as _run_integrity_signals
from engine.Layer_1.Signals.sample_adequacy_signals import run_sample_adequacy as _run_sample_signals
from engine.Layer_1.Signals.target_sanity_signals import run_target_sanity as _run_target_signals

logger = logging.getLogger(__name__)


def run_signal_extraction(df: pd.DataFrame, target_column: str | None = None) -> tuple[dict, list]:
    """
    Run all signal modules and merge into a single flat dict and list of structures.
    This is what pipeline.py calls as `signals.run_signal_extraction(df)`.
    """
    flat = {}
    structures = []

    # ── Data integrity signals ──
    integrity_results = _run_integrity_signals(df)
    structures.extend(integrity_results)
    for struct in integrity_results:
        name = struct.name
        value = struct.value

        # Flatten compound signals
        if name == "dataset_shape" and isinstance(value, dict):
            flat["rows"] = value.get("rows", 0)
            flat["cols"] = value.get("cols", 0)
        elif name == "column_missing_ratio" and isinstance(value, dict):
            flat["column_missing_ratio"] = value
        elif name == "constant_columns_ratio" and isinstance(value, dict):
            flat["constant_columns"] = value.get("columns", [])
            flat["constant_ratio"] = value.get("ratio", 0.0)
        elif name == "hidden_missing_ratio" and isinstance(value, dict):
            flat["hidden_missing_ratio"] = value
        elif name == "mixed_type_columns_ratio" and isinstance(value, dict):
            flat["mixed_type_columns"] = value.get("columns", [])
            flat["mixed_ratio"] = value.get("ratio", 0.0)
        else:
            flat[name] = value

    # ── Sample adequacy signals ──
    sample_results = _run_sample_signals(df)
    structures.extend(sample_results)
    for struct in sample_results:
        name = struct.name
        value = struct.value
        if value is not None:
            flat.setdefault(name, value)

    # Target viability signals
    if target_column and target_column in df.columns:
        target_results = _run_target_signals(df[target_column])
        structures.extend(target_results)
        for struct in target_results:
            name = struct.name
            value = struct.value
            meta = struct.meta or {}

            if name == "target_validation":
                reason = str(meta.get("reason", "")).lower()
                if "entirely missing" in reason or "empty" in reason:
                    flat["target_missing_ratio"] = 1.0
                    flat["target_degeneracy_flag"] = True
                continue

            if name == "dataset_shape":
                continue

            if value is not None:
                flat[name] = value

    logger.info(f"Signal extraction complete: {len(flat)} keys")
    return flat, structures
