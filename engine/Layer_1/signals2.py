import numpy as np
import pandas as pd


def validate_data(df: pd.DataFrame):
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")


def dataset_shape(df: pd.DataFrame):
    return {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1])
    }


def global_missing_ratio(df: pd.DataFrame):
    total_cells = df.shape[0] * df.shape[1]

    return {
        "global_missing_ratio": float(df.isna().sum().sum() / total_cells)
    }


def col_missing_ratio(df: pd.DataFrame):
    return {
        "column_missing_ratio": df.isna().mean().to_dict()
    }


def duplicated_ratio(df: pd.DataFrame):
    return {
        "duplicate_ratio": float(df.duplicated().mean())
    }


def constant_columns(df: pd.DataFrame):
    constant_cols = df.columns[df.nunique(dropna=False) <= 1]

    return {
        "constant_columns": list(constant_cols),
        "constant_ratio": float(len(constant_cols) / df.shape[1])
    }


def hidden_missing_ratio(df: pd.DataFrame):

    tokens = {"na", "n/a", "null", "none", "unknown", "?", "-", "", " "}

    hidden_counts = {}

    for col in df.select_dtypes(include="object"):
        ratio = (
            df[col]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(tokens)
            .mean()
        )
        hidden_counts[col] = float(ratio)

    return {"hidden_missing_ratio": hidden_counts}


def mixed_type_columns(df: pd.DataFrame):

    mixed_cols = []

    for col in df.select_dtypes(include="object"):

        numeric_ratio = pd.to_numeric(df[col], errors="coerce").notna().mean()

        if 0.7 < numeric_ratio < 1.0:
            mixed_cols.append(col)

    return {
        "mixed_type_columns": mixed_cols,
        "mixed_ratio": float(len(mixed_cols) / df.shape[1])
    }


def run_signal_extraction(df: pd.DataFrame):

    validate_data(df)

    signals = {}

    signals.update(dataset_shape(df))
    signals.update(global_missing_ratio(df))
    signals.update(col_missing_ratio(df))
    signals.update(duplicated_ratio(df))
    signals.update(constant_columns(df))
    signals.update(hidden_missing_ratio(df))
    signals.update(mixed_type_columns(df))

    return signals

if __name__ == "__main__":
    run_signal_extraction(df)