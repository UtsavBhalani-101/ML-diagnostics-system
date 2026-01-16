import numpy as np
import pandas as pd
from scipy.stats import entropy


class ConcentrationDiagnostic:
    """
    Layer-2 diagnostic.
    Detects constant, near-constant, and trigger-inflated columns
    without recommending actions.
    """

    def diagnose(self, col: pd.Series, near_constant_threshold=0.95):
        counts = col.value_counts(normalize=True, dropna=False)

        if counts.empty:
            return {
                "concentration": {
                    "status": "insufficient_data",
                    "profile": "empty",
                    "signals": {},
                    "ambiguity": {},
                    "notes": []
                }
            }

        top1_ratio = float(counts.iloc[0])
        spike_value = counts.index[0]

        residuals = col[col != spike_value].dropna()

        # Truly constant
        if residuals.empty:
            return {
                "concentration": {
                    "status": "degraded",
                    "profile": "constant",
                    "signals": {
                        "top1_ratio": 1.0
                    },
                    "ambiguity": {},
                    "notes": ["Column contains a single repeated value"]
                }
            }

        # Residual entropy
        res_counts = residuals.value_counts(normalize=True)
        res_entropy = entropy(res_counts)

        max_entropy = np.log(len(res_counts)) if len(res_counts) > 1 else 1
        norm_entropy = float(res_entropy / max_entropy)

        status = "valid"
        profile = "diverse_standard"
        notes = []
        ambiguity = {}

        # Near-constant (dead column)
        if top1_ratio > near_constant_threshold and norm_entropy < 0.1:
            status = "degraded"
            profile = "near_constant"
            notes.append(
                "Dominant value with minimal residual diversity"
            )

        # Trigger inflation (on/off behavior)
        elif top1_ratio > 0.5 and norm_entropy >= 0.3:
            status = "weak"
            profile = "trigger_inflation"
            notes.append(
                "Dominant spike with diverse residual values; conditional variation likely"
            )

        # Ambiguity near entropy boundary
        if 0.1 <= norm_entropy <= 0.2:
            ambiguity["residual_entropy_confidence"] = "borderline"
            notes.append(
                "Residual entropy near threshold; classification uncertain"
            )

        return {
            "concentration": {
                "status": status,
                "profile": profile,
                "signals": {
                    "top1_ratio": round(top1_ratio, 4),
                    "residual_entropy": round(norm_entropy, 4),
                    "residual_unique_ratio": round(len(res_counts) / len(residuals), 4)
                },
                "ambiguity": ambiguity,
                "notes": notes
            }
        }
