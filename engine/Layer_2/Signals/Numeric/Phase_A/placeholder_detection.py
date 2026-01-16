import pandas as pd
import numpy as np

class NumericPlaceholderDiagnostic:
    def __init__(self, score_threshold=60):
        self.score_threshold = score_threshold

    def _digit_entropy(self, val):
        s = str(abs(int(round(val))))
        return len(set(s))

    def diagnose(self, col: pd.Series):
        total_rows = len(col)
        numeric = pd.to_numeric(col, errors="coerce")

        actual_nan_count = numeric.isna().sum()
        non_null = numeric.dropna()

        placeholder_mask = pd.Series(False, index=col.index)
        violations = []

        if non_null.nunique() >= 3:
            vals = non_null.unique()

            candidates = {non_null.min(), non_null.max()}

            # MODE DOMINANCE CHECK
            mode_val = non_null.mode().iloc[0]
            mode_freq = (non_null == mode_val).mean()
            avg_freq = 1 / non_null.nunique()

            if mode_freq > 5 * avg_freq:
                candidates.add(mode_val)

            sorted_vals = np.sort(vals)
            diffs = np.diff(sorted_vals)
            med_diff = np.median(diffs) if np.median(diffs) > 0 else 1

            for val in candidates:
                score = 0
                evidence = {}

                # GAP ANALYSIS
                if val == sorted_vals[-1]:
                    gap = abs(val - sorted_vals[-2])
                elif val == sorted_vals[0]:
                    gap = abs(sorted_vals[1] - val)
                else:
                    gap = 0

                gap_ratio = gap / med_diff
                if gap_ratio > 50:
                    score += 30
                    evidence["gap_ratio"] = round(gap_ratio, 2)

                # DIGIT ENTROPY
                entropy = self._digit_entropy(val)
                if entropy <= 2:
                    score += 20
                    evidence["digit_entropy"] = entropy

                # ROUND NUMBER (FLOAT SAFE)
                if np.isclose(val % 10, 0, atol=1e-6):
                    score += 10
                    evidence["round_number"] = True

                if score >= self.score_threshold:
                    mask = numeric == val
                    placeholder_mask |= mask

                    violations.append({
                        "type": "SENTINEL_VALUE_PATTERN",
                        "confidence": round(min(score / 100, 1.0), 2),
                        "evidence": {
                            "value": val,
                            **evidence
                        }
                    })

        placeholder_count = int(placeholder_mask.sum())
        missing_ratio = round(
            (actual_nan_count + placeholder_count) / total_rows, 4
        )

        status = "valid"
        if missing_ratio > 0.8:
            status = "broken"
        elif missing_ratio > 0:
            status = "weak"

        return {
            "missing_component": {
                "actual_nan": actual_nan_count,
                "placeholder": placeholder_count
            },
            "violations": violations
        }

if __name__ == "__main__":
    NumericPlaceholderDiagnostic()