import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List


FAILURE_MODES = [
    "Not having enough independent constraints (samples)",
    "not having enough coverage (variability or original diversity)"
]



logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ------------------ STRUCTURE ------------------

@dataclass(frozen=True)
class Structure:
    dimension: str
    name: str
    value: Any
    status: str
    meta: Optional[Dict] = None

DIMENSION = "sample_adequacy"

# ------------------ ENFORCEMENT ------------------

def enforce(signal: Structure):
    if signal.status == "ok" and signal.value is None:
        raise ValueError(f"{signal.name}: ok but value is None")

    if signal.status in ("no_value", "error") and signal.value is not None:
        raise ValueError(f"{signal.name}: invalid state mismatch")

# ------------------ VALIDATION ------------------

def validate_data(df: pd.DataFrame):
    if df is None or df.shape[0] == 0:
        return {"status": "fail", "reason": "Empty dataset"}
    
    if df.shape[1] == 0:
        return {"status": "fail", "reason": "No columns"}

    return {"status": "pass"}

# ------------------ HELPERS ------------------

def _feature_matrix(df):
    return pd.get_dummies(df, dummy_na=True)

def _nan_safe_distance(diff):
    mask = ~np.isnan(diff)
    valid_dims = mask.sum(axis=1)

    # avoid divide by zero
    valid_dims = np.maximum(valid_dims, 1)

    return np.sqrt(np.nansum(diff ** 2, axis=1) / valid_dims)

# ------------------ FAILURE MODE A ------------------

def duplicated_ratio(df: pd.DataFrame) -> Structure:
    df_copy = df.fillna("__MISSING__")
    unique_rows = df_copy.drop_duplicates().shape[0]
    total_rows = df_copy.shape[0]
    ratio = 1 - (unique_rows / total_rows)

    signal = Structure(
        DIMENSION,
        "duplicated_ratio",
        float(ratio),
        "ok",
        {"n": total_rows}
    )
    enforce(signal)
    return signal


def effective_sample_size(df: pd.DataFrame) -> Structure:
    """
    Proxy using average nearest neighbor distance.
    Lower distance → more clustering → lower effective size
    """
    X = _feature_matrix(df)

    if X.shape[0] < 2 or X.shape[1] == 0:
        return Structure(DIMENSION, "effective_sample_size", None, "no_value")

    # sample subset for efficiency
    sample = X.sample(min(500, len(X)), random_state=42)

    dists = []
    arr = sample.values

    for i in range(len(arr)):
        diff = arr - arr[i]
        dist = _nan_safe_distance(diff)
        dist[i] = np.inf
        dists.append(dist.min())

    avg_nn_dist = np.mean(dists)

    # normalize (heuristic)
    score = float(avg_nn_dist)

    signal = Structure(
        DIMENSION,
        "effective_sample_size",
        score,
        "ok",
        {"avg_nn_distance": score}
    )
    enforce(signal)
    return signal


def sample_dependency_score(df: pd.DataFrame) -> Structure:
    """
    Measures similarity between consecutive rows (order-sensitive proxy)
    """
    X = _feature_matrix(df)

    if X.shape[0] < 2:
        return Structure(DIMENSION, "sample_dependency_score", None, "no_value")

    arr = X.values
    diff = arr[1:] - arr[:-1]
    dist = _nan_safe_distance(diff)

    score = float(np.mean(dist))

    signal = Structure(
        DIMENSION,
        "sample_dependency_score",
        score,
        "ok",
        {"avg_step_distance": score}
    )
    enforce(signal)
    return signal

def label_noise_proxy(df: pd.DataFrame, y: Optional[pd.Series] = None, k: int = 5) -> Structure:
    """
    Measures local label inconsistency.
    For each point, checks if neighbors have same label.
    """

    if y is None or len(y) != len(df):
        return Structure(DIMENSION, "label_noise_proxy", None, "no_value")

    X = _feature_matrix(df)

    if X.shape[0] < k + 1 or X.shape[1] == 0:
        return Structure(DIMENSION, "label_noise_proxy", None, "no_value")

    arr = X.values
    labels = y.values

    inconsistencies = []

    for i in range(len(arr)):
        diff = arr - arr[i]
        dist = _nan_safe_distance(diff)
        dist[i] = np.inf

        nn_idx = np.argsort(dist)[:k]
        nn_labels = labels[nn_idx]

        mismatch = np.mean(nn_labels != labels[i])
        inconsistencies.append(mismatch)

    score = float(np.mean(inconsistencies))

    signal = Structure(
        DIMENSION,
        "label_noise_proxy",
        score,
        "ok",
        {"avg_local_mismatch": score, "k": k}
    )
    enforce(signal)
    return signal


# ------------------ FAILURE MODE B ------------------

def feature_variance_score(df: pd.DataFrame) -> Structure:
    X = _feature_matrix(df)

    if X.shape[1] == 0:
        return Structure(DIMENSION, "feature_variance_score", None, "no_value")

    variances = X.var(skipna=True)
    threshold = np.nanmedian(variances) * 1e-3 if len(variances) > 0 else 0
    low_var_ratio = float((variances < threshold).mean())

    signal = Structure(
        DIMENSION,
        "feature_variance_score",
        low_var_ratio,
        "ok",
        {"low_variance_ratio": low_var_ratio}
    )
    enforce(signal)
    return signal


def marginal_coverage(df: pd.DataFrame, bins=10) -> Structure:
    X = _feature_matrix(df)

    if X.shape[1] == 0:
        return Structure(DIMENSION, "marginal_coverage", None, "no_value")

    coverage_scores = []

    for col in X.columns:
        try:
            binned = pd.qcut(X[col], q=bins, duplicates="drop")
            coverage = binned.nunique() / bins
            coverage_scores.append(coverage)
        except Exception:
            continue

    if not coverage_scores:
        return Structure(DIMENSION, "marginal_coverage", None, "no_value")

    score = float(np.mean(coverage_scores))

    signal = Structure(
        DIMENSION,
        "marginal_coverage",
        score,
        "ok",
        {"avg_bin_coverage": score}
    )
    enforce(signal)
    return signal


def joint_coverage(df: pd.DataFrame, bins=5) -> Structure:
    """
    Uses top 2 numeric features
    """
    X = _feature_matrix(df)

    if X.shape[1] < 2:
        return Structure(DIMENSION, "joint_coverage", None, "no_value")

    cols = X.var().sort_values(ascending=False).head(2).index
    sub = X[cols]

    try:
        b1 = pd.qcut(sub.iloc[:, 0], q=bins, duplicates="drop")
        b2 = pd.qcut(sub.iloc[:, 1], q=bins, duplicates="drop")

        grid = pd.crosstab(b1, b2)
        filled = (grid > 0).sum().sum()
        total = bins * bins

        score = float(filled / total)

    except Exception:
        return Structure(DIMENSION, "joint_coverage", None, "no_value")

    signal = Structure(
        DIMENSION,
        "joint_coverage",
        score,
        "ok",
        {"grid_fill": score}
    )
    enforce(signal)
    return signal


# ------------------ REGISTRY ------------------

SIGNALS_REGISTRY = [
    duplicated_ratio,
    effective_sample_size,
    sample_dependency_score,
    label_noise_proxy,
    feature_variance_score,
    marginal_coverage,
    joint_coverage
]

REQUIRED_SIGNALS = {
    "duplicated_ratio": float,
    "effective_sample_size": float,
    "sample_dependency_score": float,
    "label_noise_proxy" : float,
    "feature_variance_score": float,
    "marginal_coverage": float,
    "joint_coverage": float
}

# ------------------ ORCHESTRATOR ------------------

def run_sample_adequacy(df: pd.DataFrame) -> List[Structure]:

    validation = validate_data(df)

    if validation["status"] == "fail":
        return [
            Structure(DIMENSION, "data_validation", None, "error", validation)
        ]

    results = []

    for fn in SIGNALS_REGISTRY:
        try:
            results.append(fn(df))
        except Exception as e:
            results.append(
                Structure(DIMENSION, fn.__name__, None, "error", {"error": str(e)})
            )

    return results

if __name__ == "__main__":
    import numpy as np

    df = pd.DataFrame({
        "age": [25, 30, np.nan, 35, 40, 25, 30, np.nan, 35, 40],
        "city": ["NY", "LA", "SF", "NY", "LA", "NY", "LA", "SF", "NY", "LA"],
        'missing' : [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
    })

    results = run_sample_adequacy(df)
    for r in results:
        print(r)
    
    print(_feature_matrix(df))