import pandas as pd

def infer_dtype_candidates(
    df: pd.DataFrame,
    max_loss_ratio=0.05,
    cat_threshold=0.3,
    sparsity_threshold=0.8,
):
    """
    Observes columns and proposes dtype conversions.
    DOES NOT modify data.
    """

    total_rows = len(df)
    plan = {}

    if total_rows == 0:
        return plan

    object_cols = df.select_dtypes(include=["object", "string"]).columns

    for col in object_cols:
        col_plan = {
            "action": None,
            "reason": None,
            "details": {}
        }

        sparsity = df[col].isna().mean()
        if sparsity > sparsity_threshold:
            col_plan["action"] = "skip"
            col_plan["reason"] = "high_sparsity"
            col_plan["details"]["sparsity"] = sparsity
            plan[col] = col_plan
            continue

        # --- numeric feasibility check ---
        converted = pd.to_numeric(df[col], errors="coerce")
        original_nan = df[col].isna().sum()
        new_nan = converted.isna().sum()
        loss_ratio = (new_nan - original_nan) / total_rows

        if loss_ratio <= max_loss_ratio and new_nan < total_rows:
            col_plan["action"] = "convert_to_numeric"
            col_plan["reason"] = "low_conversion_loss"
            col_plan["details"] = {
                "loss_ratio": loss_ratio,
                "result_dtype": str(converted.convert_dtypes().dtype)
            }
            plan[col] = col_plan
            continue

        # --- categorical feasibility check ---
        n_unique = df[col].nunique(dropna=True)
        cardinality_ratio = n_unique / total_rows

        if cardinality_ratio < cat_threshold:
            col_plan["action"] = "convert_to_category"
            col_plan["reason"] = "low_cardinality"
            col_plan["details"] = {
                "cardinality_ratio": cardinality_ratio
            }
            plan[col] = col_plan
            continue

        col_plan["action"] = "keep_object"
        col_plan["reason"] = "no_safe_conversion"
        plan[col] = col_plan

    return plan
