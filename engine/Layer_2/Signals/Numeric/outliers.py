import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis


class NumericOutlierGeometryDiagnostic:
    """
    Layer-2 Phase-A diagnostic.
    Describes the geometric structure of extremes without recommending actions.
    """

    def __init__(self, bc_threshold=0.555, island_threshold=20.0):
        self.bc_threshold = bc_threshold
        self.island_threshold = island_threshold

    def diagnose(self, col: pd.Series):
        data = pd.to_numeric(col, errors="coerce").dropna()

        # --- Edge cases ---
        if len(data) < 10 or data.nunique() < 5:
            return {
                "outlier_geometry": {
                    "status": "insufficient_data",
                    "profile": "unknown",
                    "signals": {},
                    "ambiguity": {},
                    "notes": ["Not enough data to assess outlier structure"]
                }
            }

        # =====================
        # SIGNAL EXTRACTION
        # =====================

        # 1. Bimodality Coefficient
        s = skew(data)
        k = kurtosis(data, fisher=False)
        n = len(data)
        k_adj = 3 * ((n - 1) ** 2) / ((n - 2) * (n - 3))
        bc = (s**2 + 1) / (k + k_adj)

        # 2. Mean–Mode Hollow Test
        mean_val = data.mean()
        counts, bins = np.histogram(data, bins="auto")
        mode_val = bins[np.argmax(counts)]

        mean_density = data[(data >= mean_val * 0.95) & (data <= mean_val * 1.05)].count()
        mode_density = data[(data >= mode_val * 0.95) & (data <= mode_val * 1.05)].count()

        is_hollow_center = mean_density < (mode_density * 0.2)

        # 3. Island Index (gap isolation)
        sorted_vals = np.sort(data.unique())
        gaps = np.diff(sorted_vals)
        max_gap = gaps.max() if len(gaps) else 0
        med_gap = np.median(gaps) if len(gaps) else 1e-9
        island_index = max_gap / med_gap

        # 4. Quantile Staircase
        q40, q60 = data.quantile([0.4, 0.6])
        iqr = data.quantile(0.75) - data.quantile(0.25)
        staircase_ratio = (q60 - q40) / iqr if iqr > 0 else 0

        # 5. Extreme Density
        upper_fence = data.quantile(0.75) + (3 * iqr)
        extreme_density = (data > upper_fence).mean()

        # =====================
        # PROFILE CLASSIFICATION
        # =====================

        profile = "standard_unimodal"
        status = "valid"
        notes = []
        ambiguity = {}

        # Structural shift (mixture or regime change)
        if bc > self.bc_threshold or is_hollow_center or staircase_ratio > 2.0:
            profile = "structural_shift"
            status = "degraded"
            notes.append("Distribution shows evidence of multiple regimes or internal breaks")

        # Outlier geometry (only if not already structural)
        elif island_index > self.island_threshold:
            if extreme_density < 0.01:
                profile = "isolated_glitch"
                status = "weak"
                notes.append("Extremes are rare and disconnected from the bulk")
            else:
                profile = "continuous_tail"
                status = "weak"
                notes.append("Heavy tail is continuous with the bulk")

        # Ambiguity encoding (borderline bimodality)
        if 0.5 < bc < 0.6:
            ambiguity["bimodality_confidence"] = "borderline"
            notes.append("Bimodality signal is near threshold; interpretation uncertain")

        # =====================
        # FINAL OUTPUT
        # =====================

        return {
            "outlier_geometry": {
                "status": status,
                "profile": profile,
                "signals": {
                    "bimodality_coefficient": round(bc, 4),
                    "island_index": round(island_index, 2),
                    "staircase_ratio": round(staircase_ratio, 4),
                    "hollow_center": bool(is_hollow_center),
                    "extreme_density": round(extreme_density, 4)
                },
                "ambiguity": ambiguity,
                "notes": notes
            }
        }
