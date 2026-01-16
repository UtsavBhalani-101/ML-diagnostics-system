import pandas as pd
import numpy as np

class NumericValidityDiagnostic:
    def diagnose(self, col: pd.Series):
        numeric = pd.to_numeric(col, errors="coerce")
        total_rows = len(col)

        valid_series = numeric.dropna()
        invalid_mask = pd.Series(False, index=col.index)
        violations = []

        if valid_series.empty:
            return {
                "invalid_component": 0,
                "violations": []
            }

        # SIGN CONSISTENCY
        pos_ratio = (valid_series >= 0).mean()
        if 0.99 < pos_ratio < 1.0:
            mask = numeric < 0
            invalid_mask |= mask
            violations.append({
                "type": "SIGN_INCONSISTENCY",
                "confidence": round(mask.mean(), 3),
                "evidence": {"dominant_sign": "positive"}
            })
        elif 0 < pos_ratio < 0.01:
            mask = numeric >= 0
            invalid_mask |= mask
            violations.append({
                "type": "SIGN_INCONSISTENCY",
                "confidence": round(mask.mean(), 3),
                "evidence": {"dominant_sign": "negative"}
            })

        # SCALE SPIKE
        q99 = valid_series.quantile(0.99)
        max_val = valid_series.max()
        if q99 > 0 and (max_val / q99) > 10:
            mask = numeric == max_val
            invalid_mask |= mask
            violations.append({
                "type": "EXTREME_SCALE_SPIKE",
                "confidence": 0.9,
                "evidence": {
                    "max_value": max_val,
                    "q99": q99,
                    "ratio": round(max_val / q99, 2)
                }
            })

        invalid_count = int(invalid_mask.sum())

        return {
            "invalid_component": invalid_count,
            "violations": violations
        }

if __name__ == "__main__":
    NumericValidityDiagnostic()