import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.feature_selection import mutual_info_regression
from scipy.stats import spearmanr, entropy

class PhaseB_NumericIndependenceAudit:
    """
    Phase B: Numeric ↔ Numeric independence diagnostics.
    Surfaces violations of independence & identifiability assumptions.
    """

    def __init__(self, df: pd.DataFrame, thresholds=None):
        self.df = df.select_dtypes(include=[np.number]).dropna()
        self.thresholds = thresholds or {
            "corr": 0.98,
            "vif": 10.0,
            "mi_ratio": 0.6,          # % of shared information
            "spearman_low": 0.5,
            "min_unique_ratio": 0.05
        }
        self.findings = []

    def run(self):
        if self.df.empty or self.df.shape[1] < 2:
            return []

        self._check_linear_redundancy()
        self._check_linear_dependence()
        self._check_nonlinear_redundancy()

        return self.findings

    # -------------------------------------------------- #
    # 1. LINEAR REDUNDANCY
    # -------------------------------------------------- #
    def _check_linear_redundancy(self):
        corr = self.df.corr().abs()
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))

        for col in upper.columns:
            for idx in upper.index:
                score = upper.loc[idx, col]
                if pd.notna(score) and score >= self.thresholds["corr"]:
                    self.findings.append({
                        "assumption": "numeric_independence",
                        "type": "linear_redundancy",
                        "columns": [idx, col],
                        "evidence": {
                            "metric": "pearson_correlation",
                            "value": round(score, 4)
                        },
                        "risk": (
                            "Features are nearly identical linearly. "
                            "May inflate importance and destabilize coefficients."
                        ),
                        "severity": "high"
                    })

    # -------------------------------------------------- #
    # 2. IDENTIFIABILITY (VIF)
    # -------------------------------------------------- #
    def _check_linear_dependence(self):
        X = self.df.values
        cols = self.df.columns

        for i, col in enumerate(cols):
            try:
                vif = variance_inflation_factor(X, i)
                if vif >= self.thresholds["vif"] and np.isfinite(vif):
                    self.findings.append({
                        "assumption": "feature_identifiability",
                        "type": "linear_dependence",
                        "columns": [col],
                        "evidence": {
                            "metric": "variance_inflation_factor",
                            "value": round(vif, 2)
                        },
                        "risk": (
                            "Feature appears to be a linear combination of others. "
                            "Coefficient estimates may be unstable or meaningless."
                        ),
                        "severity": "high"
                    })
            except Exception:
                continue

    # -------------------------------------------------- #
    # 3. NON-LINEAR REDUNDANCY (NORMALIZED MI)
    # -------------------------------------------------- #
    def _check_nonlinear_redundancy(self):
        cols = self.df.columns
        n = len(cols)

        sample_df = self.df if len(self.df) < 10000 else self.df.sample(
            10000, random_state=42
        )

        for i in range(n):
            for j in range(i + 1, n):
                a, b = cols[i], cols[j]

                # Skip if monotonic / linear already covered
                rho, _ = spearmanr(sample_df[a], sample_df[b])
                if abs(rho) >= self.thresholds["spearman_low"]:
                    continue

                # Skip low-entropy columns
                if (
                    sample_df[a].nunique() / len(sample_df) < self.thresholds["min_unique_ratio"]
                    or sample_df[b].nunique() / len(sample_df) < self.thresholds["min_unique_ratio"]
                ):
                    continue

                # Mutual Information (symmetric via min entropy normalization)
                mi_ab = mutual_info_regression(
                    sample_df[[a]], sample_df[b], random_state=42
                )[0]
                mi_ba = mutual_info_regression(
                    sample_df[[b]], sample_df[a], random_state=42
                )[0]

                mi = max(mi_ab, mi_ba)

                h_a = entropy(np.histogram(sample_df[a], bins=20)[0] + 1e-9)
                h_b = entropy(np.histogram(sample_df[b], bins=20)[0] + 1e-9)
                mi_ratio = mi / min(h_a, h_b)

                if mi_ratio >= self.thresholds["mi_ratio"]:
                    self.findings.append({
                        "assumption": "numeric_independence",
                        "type": "nonlinear_redundancy",
                        "columns": [a, b],
                        "evidence": {
                            "metric": "normalized_mutual_information",
                            "value": round(mi_ratio, 3),
                            "spearman_corr": round(rho, 3)
                        },
                        "risk": (
                            "Strong non-linear dependency detected. "
                            "Features may encode similar information "
                            "through a deterministic transformation."
                        ),
                        "severity": "medium"
                    })
