def phasea_categorical_not_identity(
    col: pd.Series,
    col_name: str,
    unique_ratio_threshold: float = 0.9,
    median_freq_threshold: float = 1.0,
    reuse_ratio_threshold: float = 0.1
):
    """
    Phase A Assumption:
    Categories represent groups, not identities.
    """

    # --- Base stats ---
    base_stats = compute_categorical_stats(col)
    id_stats = compute_identity_signals(col)

    if base_stats is None or id_stats is None:
        return None

    evidence = {}

    # Signal 1: Near uniqueness
    if base_stats["unique_ratio"] >= unique_ratio_threshold:
        evidence["unique_ratio"] = base_stats["unique_ratio"]

    # Signal 2: No reuse
    if id_stats["median_frequency"] <= median_freq_threshold:
        evidence["median_frequency"] = id_stats["median_frequency"]

    # Signal 3: Most categories appear only once
    if id_stats["reuse_ratio"] <= reuse_ratio_threshold:
        evidence["reuse_ratio"] = id_stats["reuse_ratio"]

    if not evidence:
        return None

    severity = "high" if base_stats["unique_ratio"] > 0.95 else "medium"

    return {
        "assumption": "categorical_represents_groups",
        "type": "violated",
        "columns": [col_name],
        "evidence": evidence,
        "risk": (
            "Column behaves like an identity rather than a reusable group. "
            "Encoding may cause memorization and poor generalization."
        ),
        "severity": severity
    }
