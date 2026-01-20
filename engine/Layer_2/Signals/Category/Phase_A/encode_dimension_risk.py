def phasea_categorical_dimensionality_risk(
    col_name: str,
    stats,
    max_ohe_dim: int = 500,
    min_row_per_dim_ratio: float = 10.0
):
    """
    Phase A Assumption:
    Categorical encoding should not inflate dimensionality beyond data support.
    """

    n_unique = stats.n_unique
    n_rows = stats.n_rows

    # Projected dimensionality after OHE
    projected_dims = max(n_unique - 1, 1)
    row_to_dim_ratio = n_rows / projected_dims if projected_dims > 0 else 0

    evidence = {
        "n_unique": n_unique,
        "projected_ohe_dims": projected_dims,
        "row_to_dimension_ratio": round(row_to_dim_ratio, 2)
    }

    # Absolute explosion risk
    if n_unique >= max_ohe_dim:
        return {
            "assumption": "encoding_preserves_information",
            "type": "violated",
            "columns": [col_name],
            "evidence": evidence,
            "risk": (
                "One-hot encoding would massively expand feature space. "
                "High risk of sparse noise and degraded generalization."
            ),
            "severity": "high"
        }

    # Statistical sparsity risk
    if row_to_dim_ratio < min_row_per_dim_ratio:
        return {
            "assumption": "encoding_preserves_information",
            "type": "warning",
            "columns": [col_name],
            "evidence": evidence,
            "risk": (
                "Insufficient data per encoded dimension. "
                "Signal may be diluted by sparsity."
            ),
            "severity": "medium"
        }

    return None
