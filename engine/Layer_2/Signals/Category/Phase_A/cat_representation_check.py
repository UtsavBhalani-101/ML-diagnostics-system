import re
import pandas as pd

def phasea_categorical_representational_integrity(
    col: pd.Series,
    col_name: str,
    sample_size: int = 20
):
    """
    Phase A Assumption:
    Categorical columns truly represent discrete, unordered states.
    """

    if col.dropna().empty:
        return None

    # Sample top frequent categories (most impactful)
    unique_vals = col.dropna().astype(str).value_counts().index[:sample_size]

    findings = []

    # --- CHECK 1: Numeric Ranges masquerading as categories ---
    range_pattern = re.compile(r'^\s*\d+\s*[-_]\s*\d+\s*$')
    range_hits = [v for v in unique_vals if range_pattern.match(v)]

    if len(range_hits) >= max(3, len(unique_vals) * 0.6):
        findings.append({
            "assumption": "categorical_is_nominal",
            "type": "violated",
            "columns": [col_name],
            "evidence": {
                "pattern": "numeric_range_labels",
                "examples": range_hits[:5]
            },
            "risk": (
                "Column appears to be binned numeric data represented as labels. "
                "Treating it as nominal may destroy numeric signal."
            ),
            "severity": "high"
        })

    # --- CHECK 2: Ordinal labels disguised as categories ---
    digit_pattern = re.compile(r'(\d+)')
    extracted = []

    for v in unique_vals:
        m = digit_pattern.search(v)
        if m:
            extracted.append(int(m.group(1)))
        else:
            extracted = []
            break

    if extracted and len(set(extracted)) >= 3:
        findings.append({
            "assumption": "categorical_is_nominal",
            "type": "warning",
            "columns": [col_name],
            "evidence": {
                "pattern": "embedded_numeric_ordering",
                "examples": unique_vals[:5].tolist()
            },
            "risk": (
                "Column appears to have inherent ordering. "
                "Treating it as nominal may discard ordinal structure."
            ),
            "severity": "medium"
        })

    return findings or None
