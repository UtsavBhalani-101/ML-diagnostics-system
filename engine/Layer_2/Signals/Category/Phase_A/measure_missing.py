import pandas as pd
import numpy as np

class CategoricalMissingStats:
    """
    PURE MEASUREMENT ENGINE
    Computes missingness structure for categorical columns.
    No decisions. No assumptions. No actions.
    """

    IMPLICIT_MISSING_TOKENS = {
        "nan", "null", "n/a", "na", "none", "missing", "", "?", "unknown"
    }

    def __init__(self, col: pd.Series):
        self.col = col
        self.n_rows = len(col)

        if self.n_rows == 0:
            self.valid = False
            return

        self.valid = True

        # --- REAL NULLS ---
        self.real_null_count = col.isna().sum()

        # --- STRING NORMALIZATION ---
        str_col = col.dropna().astype(str).str.lower().str.strip()

        # --- IMPLICIT NULLS ---
        self.implicit_null_mask = str_col.isin(self.IMPLICIT_MISSING_TOKENS)
        self.implicit_null_count = int(self.implicit_null_mask.sum())

        # --- TOTAL MISSING ---
        self.total_missing = int(self.real_null_count + self.implicit_null_count)
        self.missing_ratio = (
            self.total_missing / self.n_rows if self.n_rows > 0 else 0
        )

        # --- TYPES OF MISSING FOUND (DESCRIPTIVE) ---
        self.missing_types_found = set(
            str_col[self.implicit_null_mask].unique().tolist()
        )

        self.real_null_types = set()

        if col.isna().any():
            # Detect actual python-level nulls
            for v in col[col.isna()]:
                if v is None:
                    self.real_null_types.add("None")
                else:
                    self.real_null_types.add("np.nan")


    def as_evidence(self):
        if not self.valid or self.total_missing == 0:
            return None

        return {
            "missing_ratio": round(self.missing_ratio, 4),
            "total_missing": self.total_missing,
            "missing_breakdown": {
                "real_nulls": sorted(self.real_null_types),
                "implicit_nulls": sorted(self.missing_types_found)
            }
        }

