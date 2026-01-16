def detect_target_dependency_risk(df: pd.DataFrame, target_col: str, threshold=0.95):
    """
    Phase B: Target Dependency Risk Scan.
    Flags features whose association with the target is unusually strong
    and may invalidate standard evaluation assumptions.
    """

    if target_col not in df.columns:
        return {"error": "Target column not found"}

    numeric_df = df.select_dtypes(include=[np.number])

    clean_target = pd.to_numeric(df[target_col], errors="coerce")
    if clean_target.isna().all():
        return {"error": "Target column not numeric/binary"}

    findings = []

    correlations = numeric_df.corrwith(clean_target).abs()

    for feature, score in correlations.items():
        if feature == target_col:
            continue

        if score >= threshold:
            findings.append({
                "feature": feature,
                "association_strength": round(score, 4),
                "signal": "suspicious_target_dependency",
                "interpretation": (
                    "Association is unusually strong. "
                    "May indicate leakage, proxy variables, "
                    "or post-outcome features."
                ),
                "action": "review_feature_origin_and_availability"
            })

        elif score >= 0.8:
            findings.append({
                "feature": feature,
                "association_strength": round(score, 4),
                "signal": "strong_target_association",
                "interpretation": (
                    "Feature is a dominant predictor. "
                    "Ensure it is available at prediction time."
                ),
                "action": "monitor_and_validate"
            })

    return (
        pd.DataFrame(findings)
        .sort_values(by="association_strength", ascending=False)
        if findings else pd.DataFrame()
    )
