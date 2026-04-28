import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass
from typing import Any, Dict, List

FAILURE_MODES = {
    "existence" : "target not present --> _____ (missing)",
    "consistency" : "same situation gives differnt answers --> _____ (noise, misalignment, encoding issue)",
    "informative" : "target not informative or useful to learn anything from -->  _____ (imbalance, degeneracy)"
}

# ------------------ LOGGING ------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ------------------ STRUCTURE ------------------

@dataclass(frozen=True)
class Structure:
    dimension: str
    name: str
    value: Any
    status: str  # "ok", "no_value", "error"
    meta: Dict[str, Any]


DIMENSION = "target_viability"


# ------------------ ENFORCEMENT ------------------

def enforce(signal: Structure):
    if signal.status == "ok" and signal.value is None:
        raise ValueError(f"{signal.name}: status ok but value is None")

    if signal.status in ("no_value", "error") and signal.value is not None:
        raise ValueError(f"{signal.name}: has value but status={signal.status}")


# ------------------ CONSTANTS ------------------

HIDDEN_MISSING = {"na", "n/a", "null", "none", "", " ", "?", "unknown", "np.nan", "nan"}


# ------------------ UTILITIES ------------------

def clean_target(y) -> pd.Series:
    y_clean = pd.Series(y).copy()

    # Step 1: process only string dtype or object dtypes 
    if y_clean.dtype == object or pd.api.types.is_string_dtype(y_clean):
        is_str = y_clean.map(lambda x: isinstance(x, str))
        if is_str.any():
            y_clean.loc[is_str] = (
                y_clean.loc[is_str]
                .astype(str)
                .str.strip()
                .str.lower()
            )

    # Step 2: replace hidden missing with np.nan
    y_clean = y_clean.replace(list(HIDDEN_MISSING), np.nan)

    return y_clean


# count the unique dtype of all the elements in y 
def is_mixed_type(y: pd.Series) -> bool:
    types = set(type(v) for v in y.dropna())
    return len(types) > 1


# ------------------ VALIDATION ------------------

# set of general guards that corrupt every signal, if found don't allow any further processing
def validate_target(y: pd.Series) -> Dict:

    if len(y) == 0:
        return {"status": "fail", "reason": "Target is empty"}    
        
    if y.isna().all():
        return {"status": "fail", "reason": "Target is entirely filled with np.nan missing"}

    if y.dropna().empty:
        return {"status" : "fail", "reason" : "no non-null values exists"}

    return {"status": "pass", "y": y}


# ------------------ SIGNALS ------------------

# get number of rows
def target_shape(y: pd.Series) -> Structure:
    signal = Structure(
        dimension=DIMENSION,
        name="target_shape",
        value={"rows": len(y), "cols": 1},
        status="ok",
        meta={"n_samples": len(y)}
    )

    enforce(signal)
    return signal


# get standard (np.nan) missing count
def target_missing_ratio(y: pd.Series) -> Structure:
    ratio = float(y.isna().mean())

    signal = Structure(
            dimension=DIMENSION,
            name="target_missing_ratio",
            value=ratio,
            status="ok",
            meta={
                "n_samples": len(y), 
                "missing_count": int(y.isna().sum())
            }
        )

    enforce(signal)
    return signal

# is target useless ? (does it only contain 1 unique value ?)
def target_degeneracy_flag(y: pd.Series) -> Structure:
    unique = int(y.dropna().nunique())
    is_degenerate = unique <= 1

    signal = Structure(
            dimension=DIMENSION,
            name="target_degeneracy_flag",
            value=is_degenerate,
            status="ok",
            meta={"unique_values": unique}
        )
    
    enforce(signal)
    return signal

# get the dominant class (index[0]) ratio
def dominant_class_ratio(y: pd.Series) -> Structure:
    counts = y.value_counts(normalize=True)

    ratio = float(counts.iloc[0])

    # cap distribution to top 10 classes to avoid flooding on regression targets
    TOP_N = 10
    total_unique = len(counts)

    if total_unique <= TOP_N:
        class_dist = {str(k): round(float(v), 4) for k, v in counts.items()}
    else:
        top = counts.head(TOP_N)
        class_dist = {str(k): round(float(v), 4) for k, v in top.items()}
        class_dist["_other"] = round(float(1.0 - top.sum()), 4)

    signal = Structure(
        dimension=DIMENSION,
        name="dominant_class_ratio",
        value=ratio,
        status="ok",
        meta={
            "n_samples": len(y),
            "dominant_class": str(counts.index[0]),
            "dominant_count": int(y.value_counts().iloc[0]),
            "total_unique": total_unique,
            "class_distribution": class_dist
        }
    )

    enforce(signal)
    return signal


# get how predictable the data points are
def target_entropy(y: pd.Series) -> Structure:
    if y.dropna().empty:
        return Structure(
            dimension=DIMENSION,
            name="target_entropy",
            value=None,
            status="no_value",
            meta={"reason": "empty target"}
        )

    p = y.value_counts(normalize=True)
    entropy = float(-np.sum(p * np.log2(p + 1e-9)))

    signal = Structure(
        dimension=DIMENSION,
        name="target_entropy",
        value=entropy,
        status="ok",
        meta={
            "num_classes": len(p),
            "max_entropy": round(float(np.log2(len(p))), 4) if len(p) > 1 else 0.0
        }
    )

    enforce(signal)
    return signal

# how badly the target is mixed with different dtypes 
def type_contamination_ratio(y: pd.Series) -> Structure:
    
    # 1. drop null values 
    non_null = y.dropna()

    if len(non_null) == 0:
        return Structure(
            dimension=DIMENSION,
            name="type_contamination_ratio",
            value=None,
            status="no_value",
            meta={"reason": "target only contains missing values"}
        )

    # 2. get the dtype of each 
    types = non_null.map(lambda x: type(x).__name__)
    
    # 3. from the value count, where is the max located 
    majority_type = types.value_counts().idxmax()

    # 4. what % of rows have type different from majority 
    contamination = float((types != majority_type).mean())
    
    type_counts = types.value_counts()

    signal = Structure(
        dimension=DIMENSION,
        name="type_contamination_ratio",
        value=contamination,
        status="ok",
        meta={
        "major_type": majority_type,
        "contaminated_count": int((types != majority_type).sum()),
        "total_non_null": len(non_null),
        "type_breakdown": {k: int(v) for k, v in type_counts.items()}
        }
    )

    enforce(signal)
    return signal




# ------------------ REGISTRY ------------------

SIGNALS_REGISTRY = [
    target_shape,
    target_missing_ratio,        # existence
    target_degeneracy_flag,      # informativeness (hard fail)
    dominant_class_ratio,        # informativeness (soft fail)
    target_entropy,              # consistency proxy
    type_contamination_ratio,     # consistency (representation)
]

REQUIRED_SIGNALS = {
    "target_shape" : dict,
    "target_missing_ratio": float,
    "target_degeneracy_flag": bool,
    "dominant_class_ratio": float,
    "target_entropy": (float, type(None)),
    "type_contamination_ratio": (float, type(None)),
}


# ------------------ ORCHESTRATOR ------------------

def run_target_sanity(y: pd.Series, col_name: str) -> List[Structure]:

    # 1. get clean y
    y_clean = clean_target(y)
    
    # 2. validate it
    validation = validate_target(y_clean)

    if validation["status"] == "fail":
        return [
            Structure(
                dimension=DIMENSION,
                name="target_validation",
                value=None,
                status="error",
                meta={"reason": validation["reason"]}
            )
        ]
        
    #3. get target col name before running the registry loop
    name_signal = Structure(
        dimension=DIMENSION,
        name="target_column_name",
        value=col_name,
        status="ok",
        meta={"dtype": str(y.dtype)}
    )

    # 4. save the target col name 
    results = [name_signal]
    
    # 5. registry loop to run all signals:
    #  take y_clean -> give to signal -> save the result and logger 

    for signal_fn in SIGNALS_REGISTRY:
        try:
            res = signal_fn(y_clean)
            logger.debug(f"{signal_fn.__name__} success")
            results.append(res)

    # if any error occured -> save that and logger 
        except Exception as e:
            logger.error("Signal failed", extra={
                "signal": signal_fn.__name__,
                "error": str(e)
            })

            results.append(
                Structure(
                    dimension=DIMENSION,
                    name=signal_fn.__name__,
                    value=None,
                    status="error",
                    meta={"error": str(e)}
                )
            )

    return results

if __name__ == "__main__":
    # example_target_col = pd.Series([1, 0, 1, 1, "NA", np.nan, 0, 1, 1, 0, 0, 1, "", " ", None])
    example_target_col = pd.Series(["NY", "LA", "SF", "NY", "LA", "None", "  ", "NY", "LA", "SF", "NY", "LA", "np.nan"])
    # example_target_col = pd.Series([])

    df = pd.read_csv(r"D:\ML diagnose v1\test_files\train.csv")
    target_col = df['Ticket']

    print("--- Running Target Signals ---")
    results = run_target_sanity(target_col, 'Ticket')
    
    for res in results:
        # print(f"{res.name}:")
        # print(f"  Value: {res.value}")
        # print(f"  Meta: {res.meta}\n")
        
        print(res)

    # print(clean_target(example_target_col))