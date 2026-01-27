def apply_dtype_normalization(
    df: pd.DataFrame,
    plan: dict,
):
    """
    Applies dtype changes based on an explicit plan.
    Mutates a COPY of the dataframe.
    """

    df = df.copy()
    report = {
        "converted_to_numeric": [],
        "converted_to_category": [],
        "skipped": [],
    }

    # Global nullable upgrade (intentional mutation)
    df = df.convert_dtypes()

    for col, decision in plan.items():
        action = decision["action"]

        if action == "convert_to_numeric":
            converted = pd.to_numeric(df[col], errors="coerce")
            df[col] = converted.convert_dtypes()
            report["converted_to_numeric"].append(col)

        elif action == "convert_to_category":
            df[col] = df[col].astype("category")
            report["converted_to_category"].append(col)

        else:
            report["skipped"].append(col)

    return df, report
