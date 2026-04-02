from __future__ import annotations

from typing import Dict, List, Any


RISK_ACTION_MAP: Dict[str, str] = {
    "mixed_types": "Convert columns to consistent dtype",
    "mixed_type_columns": "Convert columns to consistent dtype",
    "target_mixed_type": "Convert target to a consistent dtype",
    "missing_values": "Apply imputation or remove columns",
    "missing": "Apply imputation or remove columns",
    "target_missing": "Apply imputation or remove rows with missing target values",
    "hidden_missing": "Standardize placeholder missing values before analysis",
    "hidden": "Standardize placeholder missing values before analysis",
    "duplicates": "Remove duplicate rows",
    "constant_columns": "Drop non-informative columns",
    "constant": "Drop non-informative columns",
    "low_sample": "Collect more data or reduce features",
    "sample_size": "Collect more data or reduce features",
    "task_uncertainty": "Clarify the target definition before modeling",
    "imbalance": "Rebalance classes or revisit the target distribution",
    "variance": "Verify the target has usable variability",
    "target_variance": "Verify the target has usable variability",
}


def generate_primary_issues(dominant_risks: Dict[str, float]) -> List[Dict[str, Any]]:
    ranked_risks = sorted(
        dominant_risks.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    primary_issues: List[Dict[str, Any]] = []
    for risk_name, risk_value in ranked_risks[:2]:
        if risk_value <= 0:
            continue

        primary_issues.append(
            {
                "name": risk_name,
                "risk": round(float(risk_value), 4),
                "action": RISK_ACTION_MAP.get(risk_name, "Inspect this structural risk"),
            }
        )

    return primary_issues
