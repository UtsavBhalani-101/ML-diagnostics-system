import pandas as pd
import numpy as np
from scipy import stats

class NumericPlaceholderDiagnostic:
    def __init__(self, threshold_score=70):
        self.threshold_score = threshold_score

    def _get_digit_entropy(self, val):
        s_val = str(abs(int(val))) if pd.notna(val) else ""
        return len(set(s_val)) if s_val else 10

    def _get_target_correlation(self, mask, target, target_type):
        if target is None: return 0
        valid = mask.notna() & target.notna()
        m, t = mask[valid], target[valid]
        
        if m.unique().size < 2 or t.unique().size < 2: return 0

        if target_type == 'regression':
            corr, p_val = stats.pointbiserialr(m, t)
        else:
            contingency = pd.crosstab(m, t)
            _, p_val, _, _ = stats.chi2_contingency(contingency)
            corr = 0 if p_val > 0.05 else 0.5
        return abs(corr)

    def diagnose_column(self, col, target=None, target_type='regression'):
        total_rows = len(col)
        # Handle standard NaNs first
        actual_nan_count = col.isna().sum()
        
        # Clean numeric conversion for placeholder analysis
        numeric_col = pd.to_numeric(col, errors='coerce')
        vals = numeric_col.dropna().unique()
        
        placeholder_rows = 0
        detected_values = []

        if len(vals) >= 3:
            candidates = [np.max(vals), np.min(vals)]
            # Add most frequent value if it's not the mean/median
            mode_val = numeric_col.mode()[0]
            if mode_val not in candidates:
                candidates.append(mode_val)

            for val in set(candidates):
                score = 0
                # 1. Gap Analysis
                sorted_vals = np.sort(vals)
                diffs = np.diff(sorted_vals)
                med_diff = np.median(diffs) if np.median(diffs) != 0 else 1
                gap = abs(val - sorted_vals[-2]) if val == sorted_vals[-1] else abs(val - sorted_vals[1])
                if (gap / med_diff) > 50: score += 30
                
                # 2. Entropy
                if self._get_digit_entropy(val) <= 2: score += 20
                if val % 10 == 0: score += 10
                
                # 3. Target Correlation
                mask = (numeric_col == val)
                corr = self._get_target_correlation(mask, target, target_type)
                if corr < 0.05: score += 40
                elif corr > 0.2: score -= 50

                if score >= self.threshold_score:
                    placeholder_rows += mask.sum()
                    detected_values.append(val)

        # Combine actual NaNs and identified placeholders
        total_missing = actual_nan_count + placeholder_rows
        missing_ratio = round(total_missing / total_rows, 4)
        
        # Determine status
        status = "valid"
        if missing_ratio > 0.8: status = "broken"
        elif missing_ratio > 0.0: status = "weak"

        return {
            "missingness": {
                "status": status,
                "value": missing_ratio,
                "evidence": {
                    "missing_ratio": missing_ratio,
                    "actual_nan_count": int(actual_nan_count),
                    # "detected_placeholders": detected_values,
                    # "placeholder_row_count": int(placeholder_rows)
                }
            }
        }

if __name__ == "__main__":
    
    # --- Example Usage for your Layer 2 system ---
    diagnostic = NumericPlaceholderDiagnostic()
    findings = diagnostic.diagnose_column(df['age'], target=df['income'], target_type='regression')