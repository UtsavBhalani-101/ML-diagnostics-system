import pandas as pd
import numpy as np
from difflib import SequenceMatcher

def phasea_categorical_finite_set(
    col: pd.Series,
    col_name: str,
    high_cardinality_ratio: float = 0.9,
    rare_frequency_threshold: float = 0.01,
    fuzzy_similarity_threshold: float = 0.85
):
    """
    Phase A: Finite & Closed Categorical Set Diagnostic.

    Assumption:
        Column represents a clean, finite, stable category label space.
    """

    if col.empty:
        return None

    # -------------------------------
    # Basic preparation
    # -------------------------------
    clean_col = col.dropna().astype(str)
    n_rows = len(clean_col)

    if n_rows == 0:
        return None

    value_counts = clean_col.value_counts()
    n_unique = len(value_counts)
    unique_ratio = n_unique / n_rows

    evidence = {}

    # =====================================================
    # 1. TEXT / ID LIKENESS (structure-breaking)
    # =====================================================
    avg_len = clean_col.str.len().mean()
    unique_len_ratio = clean_col.str.len().nunique() / max(n_unique, 1)

    text_likeness_score = min(
        1.0,
        0.5 * unique_ratio +
        0.3 * (avg_len > 15) +
        0.2 * unique_len_ratio
    )

    if unique_ratio > high_cardinality_ratio or text_likeness_score > 0.8:
        evidence["text_likeness_score"] = round(text_likeness_score, 3)
        evidence["unique_ratio"] = round(unique_ratio, 3)

    # =====================================================
    # 2. LONG-TAIL DISTRIBUTION (instability)
    # =====================================================
    freq_ratio = value_counts / n_rows
    rare_ratio = (freq_ratio < rare_frequency_threshold).mean()

    if rare_ratio > 0.5:
        evidence["rare_category_ratio"] = round(rare_ratio, 3)

    # =====================================================
    # 3. SEMANTIC FRAGMENTATION (fuzzy duplicates)
    # =====================================================
    labels = value_counts.index.tolist()
    fuzzy_hits = 0

    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            if SequenceMatcher(None, labels[i], labels[j]).ratio() >= fuzzy_similarity_threshold:
                fuzzy_hits += 1
                break

    fragmentation_score = fuzzy_hits / n_unique if n_unique > 0 else 0

    if fragmentation_score > 0.1:
        evidence["semantic_fragmentation_score"] = round(fragmentation_score, 3)

    # =====================================================
    # 4. IMPLICIT NULLS (garbage categories)
    # =====================================================
    garbage_tokens = {
        "?", "nan", "null", "none", "n/a", "-", "unknown", "missing", ""
    }

    observed_tokens = set(clean_col.str.lower().unique())
    garbage_hits = garbage_tokens.intersection(observed_tokens)

    if garbage_hits:
        evidence["implicit_null_ratio"] = round(
            clean_col.str.lower().isin(garbage_hits).mean(), 3
        )

    # =====================================================
    # 5. MIXED TYPES (consistency)
    # =====================================================
    python_types = col.dropna().map(type).unique()

    if len(python_types) > 1:
        evidence["mixed_type_detected"] = True

    # -------------------------------
    # Emit ONE diagnostic if needed
    # -------------------------------
    if evidence:
        return {
            "assumption": "finite_categorical_set",
            "type": "violated",
            "columns": [col_name],
            "evidence": evidence,
            "risk": (
                "Column does not behave like a clean, finite categorical label set. "
                "Observed patterns suggest unstable semantics, unconstrained growth, "
                "or label fragmentation."
            ),
            "severity": (
                "high" if (
                    unique_ratio > high_cardinality_ratio or
                    text_likeness_score > 0.8
                ) else "medium"
            )
        }

    return None
