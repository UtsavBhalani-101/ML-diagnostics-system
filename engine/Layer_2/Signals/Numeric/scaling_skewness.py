import pandas as pd
import numpy as np

class NumericGeometryDiagnostic:
    """
    Layer-2 diagnostic.
    Describes numeric shape + scale risks without deciding transformations.
    """

    def diagnose(self, col: pd.Series):
        numeric = pd.to_numeric(col, errors="coerce")
        clean = numeric.dropna()

        # Edge cases
        if clean.empty or clean.nunique() < 2:
            return {
                "numeric_geometry": {
                    "status": "valid",
                    "signals": {},
                    "ambiguity": {},
                    "notes": []
                }
            }

        # ---------- SCALE SIGNALS ----------
        q75, q25 = clean.quantile([0.75, 0.25])
        iqr = q75 - q25
        data_range = clean.max() - clean.min()

        iqr_collapsed = bool(iqr == 0 and data_range > 0)

        if iqr > 0:
            range_ratio = round(data_range / iqr, 2)
        elif iqr_collapsed:
            range_ratio = 999999
        else:
            range_ratio = 0.0

        # ---------- SHAPE SIGNALS ----------
        skewness = round(clean.skew(), 4)
        sparsity_ratio = round((clean == 0).mean(), 4)

        # ---------- STATUS AGGREGATION ----------
        status = "valid"
        notes = []

        if abs(skewness) > 1.0 or range_ratio > 20 or sparsity_ratio > 0.8:
            status = "weak"

        # ---------- AMBIGUITY DECLARATION ----------
        ambiguity = {}

        if abs(skewness) > 1.0:
            ambiguity["skew_nature"] = "informational_or_mathematical"
            notes.append(
                "Skew detected; cannot determine if tail is signal or noise without target"
            )

        if range_ratio > 20 or iqr_collapsed:
            notes.append(
                "Scale distortion detected; scaling before shape correction may warp distribution"
            )
            ambiguity["ordering_constraint"] = "shape_before_scale"

        if sparsity_ratio > 0.8:
            notes.append(
                "High sparsity detected; centering may destroy zero identity"
            )

        return {
            "numeric_geometry": {
                "status": status,
                "signals": {
                    "skewness": skewness,
                    "range_ratio": range_ratio,
                    "iqr_collapsed": iqr_collapsed,
                    "sparsity_ratio": sparsity_ratio
                },
                "ambiguity": ambiguity,
                "notes": notes
            }
        }
