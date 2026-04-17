import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List


# ------------------ LOGGING ------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ------------------ STRUCTURE ------------------

@dataclass(frozen=True)
class Structure:
    dimension: str
    name: str
    value: Any
    meta: Optional[Dict] = None


DIMENSION = "sample_adequacy"


# ------------------ VALIDATION ------------------

def validate_data(df: pd.DataFrame):
    pass



# ------------------ SIGNALS ------------------

def dataset_size(df: pd.DataFrame) -> Structure:
    size = int(df.shape[0])

    result = Structure(
        dimension=DIMENSION,
        name="dataset_size",
        value=size,
        meta={"n_rows": size}
    )

    return result


def feature_count(df: pd.DataFrame) -> Structure:
    count = int(df.shape[1])

    result = Structure(
        dimension=DIMENSION,
        name="feature_count",
        value=count,
        meta={"n_features": count}
    )

    return result


def n_to_d_ratio(df: pd.DataFrame) -> Structure:
    n = df.shape[0]
    d = df.shape[1]
    
    if d == 0:
        return Structure(
            dimension=DIMENSION,
            name="n_to_d_ratio",
            value=ratio,
            meta={
                "n_rows": n,
                "n_features": d
            }
        )
        

    ratio = float(n / d)

    result = Structure(
        dimension=DIMENSION,
        name="n_to_d_ratio",
        value=ratio,
        meta={
            "n_rows": n,
            "n_features": d
        }
    )

    return result


# ------------------ ORCHESTRATOR ------------------

SIGNALS_REGISTRY = [
    dataset_size,
    feature_count,
    n_to_d_ratio
]

REQUIRED_SIGNALS = {
    "dataset_size" : int,
    "feature_count" : float,
    "n_to_d_ratio" : (float, type(None))
}


def run_sample_adequacy(df: pd.DataFrame) -> List[Structure]:
    
    validate = validate_data(df)
    
    if validate["status"] == "fail":
        logger.error("Data integrity validation failed: ", extra={"reason" : validate["reason"]})
        
        return Structure(
            dimension=DIMENSION,
            name="sample_adequacy",
            value=None,
            meta={"status" : "error" , "reason" : validate["reason"]}
        )

    results = []

    for signal_fn in SIGNALS_REGISTRY:
        try:
            res = signal_fn(df)
            logger.debug(f"{signal_fn.__name__} success")
            results.append(res)

        except Exception as e:
            logger.error(
                f"Signal failed: {signal_fn.__name__}",
                extra={"signal": signal_fn.__name__, "error": str(e)}
            )
            results.append(
                Structure(
                    dimension=DIMENSION,
                    name=signal_fn.__name__,
                    value=None,
                    meta={"error": str(e)}
                )
            )

    return results

if __name__ == "__main__":
    
    # run_sample_adequacy(df)
    N_SAMPLES = 10000
    
    def build_categorical_clean() -> pd.DataFrame:
        np.random.seed(42)
        df = pd.DataFrame({
            "cat_1": np.random.choice(["A", "B", "C"], size=N_SAMPLES),
            "cat_2": np.random.choice(["X", "Y"], size=N_SAMPLES),
            "cat_3": np.random.choice(["low", "medium", "high"], size=N_SAMPLES),
        })
        return df
    
    def build_categorical_hidden_missing() -> pd.DataFrame:
        df = build_categorical_clean().astype(object)
        np.random.seed(42)
        mask = np.random.rand(N_SAMPLES) < 0.15
        df.loc[mask, "cat_1"] = "NA"
        return df
    
    df = build_categorical_hidden_missing()
    
    results = run_sample_adequacy(df)
    for r in results:
        print(r)
