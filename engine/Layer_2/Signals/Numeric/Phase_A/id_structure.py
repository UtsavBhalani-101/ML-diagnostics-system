import numpy as np
import pandas as pd


class NumericIDStructureDiagnostic:
    """
    Layer-2 diagnostic.
    Detects numeric columns that structurally resemble IDs
    (sequential or random hash-like), without making decisions.
    """

    def diagnose(self, col: pd.Series, uniqueness_threshold=0.98):
        data = pd.to_numeric(col, errors="coerce").dropna()

        if len(data) < 10:
            return {
                "id_structure": {
                    "status": "insufficient_data",
                    "profile": "unknown",
                    "signals": {},
                    "ambiguity": {},
                    "notes": []
                }
            }

        n_rows = len(data)
        n_unique = data.nunique()
        uniqueness_ratio = n_unique / n_rows

        # Integer-likeness check
        is_integer_like = bool(np.all(np.isclose(data % 1, 0, atol=1e-5)))

        # Early non-ID signal
        if not is_integer_like or uniqueness_ratio < uniqueness_threshold:
            return {
                "id_structure": {
                    "status": "valid",
                    "profile": "non_id",
                    "signals": {
                        "uniqueness_ratio": round(uniqueness_ratio, 4),
                        "integer_like": is_integer_like
                    },
                    "ambiguity": {},
                    "notes": []
                }
            }

        # Sequential structure check
        sorted_vals = np.sort(data.unique())
        diffs = np.diff(sorted_vals)

        median_step = np.median(diffs) if len(diffs) else 0
        is_uniform_step = np.allclose(diffs, median_step, atol=1e-5)

        profile = "random_id_like"
        notes = [
            "High uniqueness and integer-only values detected"
        ]

        if is_uniform_step and median_step == 1:
            profile = "sequential_id_like"
            notes.append("Values increase with a near-uniform step of 1")

        status = "weak"

        ambiguity = {}
        if 0.95 <= uniqueness_ratio <= uniqueness_threshold:
            ambiguity["uniqueness_confidence"] = "borderline"
            notes.append("Uniqueness ratio near threshold")

        return {
            "id_structure": {
                "status": status,
                "profile": profile,
                "signals": {
                    "uniqueness_ratio": round(uniqueness_ratio, 4),
                    "integer_like": is_integer_like,
                    "median_step": round(float(median_step), 4),
                    "uniform_step": bool(is_uniform_step)
                },
                "ambiguity": ambiguity,
                "notes": notes
            }
        }
