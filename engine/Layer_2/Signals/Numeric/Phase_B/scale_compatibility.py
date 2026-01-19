import pandas as pd
import numpy as np

class PhaseB_ScaleCompatibilityAudit:
    """
    Phase B: Numeric scale compatibility diagnostics.
    Flags magnitude and variance dominance that can distort model behavior.
    """

    def __init__(self, df: pd.DataFrame, thresholds=None):
        self.df = df.select_dtypes(include=[np.number]).dropna()
        self.thresholds = thresholds or {
            "magnitude_gap": 3.0,     # log10 orders of magnitude
            "variance_dominance": 0.9
        }
        self.findings = []

    def run(self):
        if self.df.empty or self.df.shape[1] < 2:
            return []

        self._check_magnitude_gap()
        self._check_variance_dominance()

        return self.findings

    # -------------------------------------------------- #
    # 1. ORDER-OF-MAGNITUDE GAP
    # -------------------------------------------------- #
    def _check_magnitude_gap(self):
        magnitudes = np.log10(self.df.abs().median() + 1e-9)

        min_mag = magnitudes.min()
        max_mag = magnitudes.max()
        gap = max_mag - min_mag

        if gap >= self.thresholds["magnitude_gap"]:
            large_scale = magnitudes[magnitudes >= max_mag - 1].index.tolist()
            small_scale = magnitudes[magnitudes <= min_mag + 1].index.tolist()

            self.findings.append({
                "assumption": "scale_compatibility",
                "type": "order_of_magnitude_gap",
                "columns": {
                    "large_scale": large_scale,
                    "small_scale": small_scale
                },
                "evidence": {
                    "metric": "log10_median_gap",
                    "value": round(gap, 2)
                },
                "risk": (
                    "Large differences in numeric scale may dominate distance- or "
                    "variance-sensitive models and distort relative feature influence."
                ),
                "severity": "high"
            })

    # -------------------------------------------------- #
    # 2. VARIANCE DOMINANCE
    # -------------------------------------------------- #
    def _check_variance_dominance(self):
        variances = self.df.var()
        total_variance = variances.sum()

        if total_variance == 0:
            return

        relative_var = variances / total_variance

        dominant = relative_var[relative_var >= self.thresholds["variance_dominance"]]

        for col, score in dominant.items():
            self.findings.append({
                "assumption": "scale_compatibility",
                "type": "variance_dominance",
                "columns": [col],
                "evidence": {
                    "metric": "relative_variance",
                    "value": round(score, 4)
                },
                "risk": (
                    "Single feature accounts for most dataset variance. "
                    "Variance-based methods (e.g., PCA, clustering) may be driven "
                    "primarily by this feature."
                ),
                "severity": "medium"
            })
