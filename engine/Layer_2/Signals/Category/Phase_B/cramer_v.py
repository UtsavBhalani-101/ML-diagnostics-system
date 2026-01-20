import pandas as pd
import numpy as np
import scipy.stats as ss

def cramers_v(col_a, col_b):
    contingency = pd.crosstab(col_a, col_b)
    if contingency.size == 0:
        return 0.0

    chi2 = ss.chi2_contingency(contingency)[0]
    n = contingency.values.sum()
    phi2 = chi2 / n
    r, k = contingency.shape

    phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
    rcorr = r - ((r - 1) ** 2) / (n - 1)
    kcorr = k - ((k - 1) ** 2) / (n - 1)

    denom = min((kcorr - 1), (rcorr - 1))
    return np.sqrt(phi2corr / denom) if denom > 0 else 0.0


def phaseb_categorical_redundancy(
    df: pd.DataFrame,
    categorical_cols: list,
    cardinality_cap: int = 50,
    threshold: float = 0.95
):
    """
    Phase B: Categorical ↔ Categorical Redundancy Audit.

    Assumption:
        Categorical features encode independent information.
    """

    findings = []

    for i in range(len(categorical_cols)):
        for j in range(i + 1, len(categorical_cols)):
            col_a = categorical_cols[i]
            col_b = categorical_cols[j]

            # Safety guard
            if (
                df[col_a].nunique() > cardinality_cap or
                df[col_b].nunique() > cardinality_cap
            ):
                continue

            score = cramers_v(df[col_a], df[col_b])

            if score >= threshold:
                findings.append({
                    "assumption": "categorical_independence",
                    "type": "redundant_categories",
                    "columns": [col_a, col_b],
                    "evidence": {
                        "metric": "cramers_v",
                        "value": round(score, 3)
                    },
                    "risk": (
                        "Two categorical features encode nearly identical information. "
                        "This may inflate feature importance and reduce model stability."
                    ),
                    "severity": "medium"
                })

    return findings if findings else None
