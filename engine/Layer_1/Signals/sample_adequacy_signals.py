import numpy as np
import pandas as pd
import logging
from typing import List
from engine.Layer_1.schema import Signal_Structure

FAILURE_MODES = [
    "Not having enough independent constraints (samples)",
    "not having enough coverage (variability or original diversity)",
]


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


DIMENSION = "sample_adequacy"

# & ------------------ ENFORCEMENT ------------------


def enforce(signal: Signal_Structure):
    if signal.status == "ok" and signal.value is None:
        raise ValueError(f"{signal.name}: ok but value is None")

    if signal.status in ("no_value", "error") and signal.value is not None:
        raise ValueError(f"{signal.name}: invalid state mismatch")


# & ------------------ VALIDATION ------------------


def validate_data(df: pd.DataFrame):
    if df is None or df.shape[0] == 0:
        return {"status": "fail", "reason": "Empty dataset"}

    if df.shape[1] == 0:
        return {"status": "fail", "reason": "No columns"}

    return {"status": "pass"}


# & ------------------ HELPERS ------------------


def _feature_matrix(df, cardinality_threshold=20):

    numeric = df.select_dtypes(include=[np.number])

    obj_cols = df.select_dtypes(include="object")

    # try to cast string columns to numeric first
    coerced = {}
    categorical = []

    for col in obj_cols.columns:
        attempted = pd.to_numeric(obj_cols[col], errors="coerce")
        if attempted.notna().mean() > 0.8:  # mostly numeric
            coerced[col] = attempted
        elif obj_cols[col].nunique() <= cardinality_threshold:
            categorical.append(col)
        # else drop — high cardinality string, useless for distance

    parts = [numeric]

    if coerced:
        parts.append(pd.DataFrame(coerced))

    if categorical:
        parts.append(pd.get_dummies(obj_cols[categorical], dummy_na=True))

    # return pd.concat(parts, axis=1)
    result = pd.concat(parts, axis=1)

    return result.astype(float)


def _nan_safe_distance(diff):
    mask = ~np.isnan(diff)
    valid_dims = mask.sum(axis=1)

    # avoid divide by zero
    valid_dims = np.maximum(valid_dims, 1)

    return np.sqrt(np.nansum(diff**2, axis=1) / valid_dims)


# & ------------------ FAILURE MODE A ------------------


# get actual duplicates without missing
def duplicated_ratio(
    df: pd.DataFrame,
) -> Signal_Structure:  #! should also detect hidden missing
    df_copy = df.fillna("__MISSING__")
    unique_rows = df_copy.drop_duplicates().shape[0]
    total_rows = df_copy.shape[0]
    ratio = 1 - (unique_rows / total_rows)

    signal = Signal_Structure(
        dimension=DIMENSION,
        name="duplicated_ratio",
        value=float(ratio),
        status="ok",
        meta={
            "total_rows": total_rows,
            "duplicate_rows": int(total_rows - unique_rows),
            "unique_rows": int(unique_rows),
        },
    )
    enforce(signal)
    return signal


def effective_sample_size(df: pd.DataFrame) -> Signal_Structure:
    """
    Proxy using average nearest neighbor distance.
    Lower distance → more clustering → models learns less unique → lower effective size
    """

    # 1. get the numeric df (distances must be in numbers)
    X = _feature_matrix(df)

    if X.shape[0] < 2:
        return Signal_Structure(
            dimension=DIMENSION,
            name="effective_sample_size",
            value=None,
            status="no_value",
            meta={"reason": "too insufficient samples"},
        )

    # 2. take 500 samples at random and find the nearest neighbor distances (finding all is computationally expensive)
    sample = X.sample(min(500, len(X)), random_state=42)

    # 3. get distances
    dists = []
    arr = sample.values

    for i in range(len(arr)):
        diff = arr - arr[i]  # difference from sample i to all others
        dist = _nan_safe_distance(diff)  # compute normalized distance
        dist[i] = np.inf  # ignore self-distance
        dists.append(dist.min())  # nearest neighbor distance

    # 4. get average nn distance
    avg_nn_dist = np.mean(dists)

    # 5. normalize (heuristic)
    score = float(avg_nn_dist)

    signal = Signal_Structure(
        dimension=DIMENSION,
        name="effective_sample_size",
        value=score,
        status="ok",
        meta={
            "avg_nn_distance": score,
            "sample_size_used": min(500, len(X)),
            "total_rows": len(df),
            "feature_count": X.shape[1],
        },
    )
    enforce(signal)
    return signal


def sample_dependency_score(df: pd.DataFrame) -> Signal_Structure:
    """
    Measures similarity between consecutive rows (order-sensitive proxy)
    """

    # 1. get a clean numbers only matrix / df
    X = _feature_matrix(df)

    if X.shape[0] < 2:
        return Signal_Structure(
            dimension=DIMENSION,
            name="sample_dependency_score",
            value=None,
            status="no_value",
            meta={"reason": "insufficient samples"},
        )

    # 2. convert df -> arr
    arr = X.values

    # 3. arr[i] - arr[i-1] for all
    diff = arr[1:] - arr[:-1]

    # 4. find euclidean distances for the differences
    dist = _nan_safe_distance(diff)

    # 5. average out
    score = float(np.mean(dist))

    signal = Signal_Structure(
        dimension=DIMENSION,
        name="sample_dependency_score",
        value=score,
        status="ok",
        meta={
            "avg_step_distance": score,
            "total_rows": len(df),
            "feature_count": X.shape[1],
        },
    )
    enforce(signal)
    return signal


# & ------------------ FAILURE MODE B ------------------


def feature_variance_score(df: pd.DataFrame) -> Signal_Structure:
    """ """
    # 1. get numeric df
    X = _feature_matrix(df)

    if X.shape[1] == 0:
        return Signal_Structure(
            dimension=DIMENSION,
            name="feature_variance_score",
            value=None,
            status="no_value",
            meta={
                "reason": "no usable numeric or low-cardinality categorical features"
            },
        )

    # 2. find it's variance
    variances = X.var(skipna=True)
    #
    threshold = np.nanmedian(variances) * 1e-3 if len(variances) > 0 else 0
    low_var_ratio = float((variances < threshold).mean())
    low_var_cols = list(variances[variances < threshold].index)

    signal = Signal_Structure(
        dimension=DIMENSION,
        name="feature_variance_score",
        value=low_var_ratio,
        status="ok",
        meta={
            "low_variance_ratio": low_var_ratio,
            "low_variance_columns": low_var_cols,
            "low_variance_count": len(low_var_cols),
            "total_features": len(variances),
            "threshold_used": float(threshold),
        },
    )
    enforce(signal)
    return signal


def marginal_coverage(df: pd.DataFrame, bins=10) -> Signal_Structure:
    X = _feature_matrix(df)

    coverage_scores = []

    for col in X.columns:
        try:
            binned = pd.qcut(X[col], q=bins, duplicates="drop")
            coverage = binned.nunique() / bins
            coverage_scores.append(coverage)
        except Exception:
            continue

    if not coverage_scores:
        return Signal_Structure(
            dimension=DIMENSION,
            name="marginal_coverage",
            value=None,
            status="no_value",
            meta={"reason": "failed to compute coverage"},
        )

    score = float(np.mean(coverage_scores))

    coverage_per_col = {}
    for col in X.columns:
        try:
            binned = pd.qcut(X[col], q=bins, duplicates="drop")
            coverage_per_col[col] = round(binned.nunique() / bins, 4)
        except Exception:
            continue

    score = float(np.mean(list(coverage_per_col.values())))

    signal = Signal_Structure(
        dimension=DIMENSION,
        name="marginal_coverage",
        value=score,
        status="ok",
        meta={
            "avg_bin_coverage": score,
            "per_column_coverage": coverage_per_col,
            "bins_used": bins,
            "columns_evaluated": len(coverage_per_col),
        },
    )
    enforce(signal)
    return signal


def joint_coverage(df: pd.DataFrame, bins=5) -> Signal_Structure:
    """
    Uses top 2 numeric features
    """
    X = _feature_matrix(df)

    if X.shape[1] < 2:
        return Signal_Structure(
            dimension=DIMENSION,
            name="joint_coverage",
            value=None,
            status="no_value",
            meta={"reason": "insufficient features"},
        )

    cols = X.var().sort_values(ascending=False).head(2).index
    sub = X[cols]

    try:
        b1 = pd.qcut(sub.iloc[:, 0], q=bins, duplicates="drop")
        b2 = pd.qcut(sub.iloc[:, 1], q=bins, duplicates="drop")

        grid = pd.crosstab(b1, b2)
        filled = (grid > 0).sum().sum()
        total = bins * bins

        score = float(filled / total)

    except Exception as e:
        return Signal_Structure(
            dimension=DIMENSION,
            name="joint_coverage",
            value=None,
            status="no_value",
            meta={"reason": f"calculation failed: {str(e)}"},
        )

    signal = Signal_Structure(
        dimension=DIMENSION,
        name="joint_coverage",
        value=score,
        status="ok",
        meta={
            "grid_fill": score,
            "columns_used": list(cols),
            "bins_used": bins,
            "filled_cells": int(filled),
            "total_cells": total,
        },
    )
    enforce(signal)
    return signal


# & ------------------ REGISTRY ------------------

SIGNALS_REGISTRY = [
    duplicated_ratio,
    effective_sample_size,
    sample_dependency_score,
    feature_variance_score,
    marginal_coverage,
    joint_coverage,
]

REQUIRED_SIGNALS = {
    "duplicated_ratio": float,
    "effective_sample_size": float,
    "sample_dependency_score": float,
    "feature_variance_score": float,
    "marginal_coverage": float,
    "joint_coverage": float,
}

# & ------------------ ORCHESTRATOR ------------------


def run_sample_adequacy_signals(df: pd.DataFrame) -> List[Signal_Structure]:

    # 1. validate data
    validation = validate_data(df)

    if validation["status"] == "fail":
        return [
            Signal_Structure(
                dimension=DIMENSION,
                name="data_validation",
                value=None,
                status="error",
                meta=validation,
            )
        ]

    # 2. a empty result list holder
    results = []

    # 3. run all the signals in registry, for each signal give input df
    for fn in SIGNALS_REGISTRY:
        try:
            results.append(fn(df))
        except Exception as e:
            results.append(
                Signal_Structure(
                    dimension=DIMENSION,
                    name=fn.__name__,
                    value=None,
                    status="error",
                    meta={"error": str(e)},
                )
            )

    return results


if __name__ == "__main__":
    import numpy as np

    df = pd.DataFrame(
        {
            "age": [25, 30, 30, 35, 40, 25, 30, 29, 35, 40],
            "city": ["NY", "LA", "SF", "NY", "LA", "NY", "LA", "SF", "NY", "LA"],
            "missing": [
                np.nan,
                np.nan,
                np.nan,
                np.nan,
                np.nan,
                np.nan,
                np.nan,
                np.nan,
                np.nan,
                np.nan,
            ],
        }
    )

    df = pd.read_csv(r"D:\ML diagnose v1\test_files\train.csv")

    results = run_sample_adequacy_signals(df)
    for r in results:
        print(r)

    # print(_feature_matrix(df))
