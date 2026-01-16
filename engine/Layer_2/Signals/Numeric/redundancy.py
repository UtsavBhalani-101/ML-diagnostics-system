import numpy as np
import pandas as pd


class NumericRedundancyDiagnostic:
    """
    Layer-2 Phase-A diagnostic.
    Detects intra-column redundancy:
    - Logical overlap (numeric columns behaving like coded categories)
    - Sequential self-redundancy (ordering artifacts)
    """

    def diagnose(self, col: pd.Series, cardinality_thresh=0.05):
        data = pd.to_numeric(col, errors="coerce").dropna()

        if len(data) < 10:
            return {
                "redundancy": {
                    "status": "insufficient_data",
                    "signals": {},
                    "ambiguity": {},
                    "notes": []
                }
            }

        n_rows = len(data)
        unique_vals = np.sort(data.unique())
        n_unique = len(unique_vals)

        # -------------------------
        # LOGICAL OVERLAP SIGNALS
        # -------------------------

        is_uniform_gap = False
        if n_unique > 2:
            gaps = np.diff(unique_vals)
            is_uniform_gap = np.allclose(gaps, gaps[0], rtol=1e-5, atol=1e-8)

        cardinality_ratio = n_unique / n_rows
        is_integer_like = bool(np.all(unique_vals % 1 == 0))

        logical_overlap = (
            is_uniform_gap
            and is_integer_like
            and cardinality_ratio < cardinality_thresh
        )

        # -------------------------
        # SELF-REDUNDANCY SIGNALS
        # -------------------------

        autocorr = (
            data.autocorr(lag=1)
            if data.var() > 0
            else 1.0
        )

        high_sequential_redundancy = autocorr > 0.99

        # -------------------------
        # STATUS AGGREGATION
        # -------------------------

        status = "valid"
        notes = []
        ambiguity = {}

        if logical_overlap or high_sequential_redundancy:
            status = "weak"

        if logical_overlap:
            notes.append(
                "Values form a uniform integer ladder with low cardinality; "
                "column may represent encoded categories or ordinals"
            )

        if high_sequential_redundancy:
            notes.append(
                "High lag-1 autocorrelation detected; values may be ordered or duplicated sequentially"
            )

        if 0.03 <= cardinality_ratio <= 0.07:
            ambiguity["cardinality_confidence"] = "borderline"
            notes.append(
                "Cardinality ratio near threshold; numeric vs categorical behavior ambiguous"
            )

        return {
            "redundancy": {
                "status": status,
                "signals": {
                    "cardinality_ratio": round(cardinality_ratio, 4),
                    "uniform_gap": bool(is_uniform_gap),
                    "integer_like": bool(is_integer_like),
                    "lag1_autocorrelation": round(float(autocorr), 4)
                },
                "ambiguity": ambiguity,
                "notes": notes
            }
        }
