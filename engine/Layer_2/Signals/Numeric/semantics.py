import numpy as np
import pandas as pd
from scipy.signal import find_peaks


class NumericScaleInconsistencyDiagnostic:
    """
    Layer-2 diagnostic.
    Detects multi-regime numeric scales and extreme repeated sentinels
    without inferring semantics or units.
    """

    def diagnose(self, col: pd.Series):
        data = pd.to_numeric(col, errors="coerce").dropna()

        if len(data) < 20:
            return {
                "scale_inconsistency": {
                    "status": "insufficient_data",
                    "signals": {},
                    "ambiguity": {},
                    "notes": []
                }
            }

        # -------------------------
        # EXTREME REPEATED VALUES
        # -------------------------
        counts = data.value_counts()
        q1, q3 = data.quantile([0.25, 0.75])
        iqr = q3 - q1

        repeated_extremes = []
        for val, count in counts.items():
            if (
                count > 1
                and abs(val) > q3 + 5 * iqr
                and float(val).is_integer()
            ):
                repeated_extremes.append(val)

        # -------------------------
        # MULTI-SCALE DENSITY MODES
        # -------------------------
        densities, bin_edges = np.histogram(data, bins="auto", density=True)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        peaks, props = find_peaks(densities, height=densities.mean())
        peak_centers = bin_centers[peaks]

        scale_separation_ratio = None
        if len(peak_centers) >= 2 and peak_centers[0] != 0:
            peak_centers = sorted(peak_centers)
            scale_separation_ratio = round(
                peak_centers[-1] / peak_centers[0], 3
            )

        # -------------------------
        # STATUS AGGREGATION
        # -------------------------
        status = "valid"
        notes = []
        ambiguity = {}

        if repeated_extremes:
            status = "weak"
            notes.append(
                "Repeated extreme values detected far outside bulk distribution"
            )

        if scale_separation_ratio and scale_separation_ratio > 5:
            status = "weak"
            notes.append(
                "Multiple dense numeric regimes detected with large scale separation"
            )

        if scale_separation_ratio and 4 <= scale_separation_ratio <= 6:
            ambiguity["scale_separation_confidence"] = "borderline"
            notes.append(
                "Scale separation near threshold; interpretation uncertain"
            )

        return {
            "scale_inconsistency": {
                "status": status,
                "signals": {
                    "repeated_extreme_values": repeated_extremes,
                    "scale_separation_ratio": scale_separation_ratio
                },
                "ambiguity": ambiguity,
                "notes": notes
            }
        }
