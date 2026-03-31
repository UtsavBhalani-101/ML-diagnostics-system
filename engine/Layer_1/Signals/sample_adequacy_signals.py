import pandas as pd
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, List


# ------------------ LOGGING ------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger('ml_diag')


# ------------------ STRUCTURE ------------------

@dataclass(frozen=True)
class Structure:
    dimension: str
    name: str
    value: Any
    meta: Optional[Dict] = None


DIMENSION = "sample_adequacy"


# ------------------ SIGNALS ------------------

def dataset_size(df: pd.DataFrame) -> Structure:
    size = int(df.shape[0])

    result = Structure(
        dimension=DIMENSION,
        name="dataset_size",
        value=size,
        meta={"n_rows": size}
    )

    logger.info(f"Computed dataset_size: {size}")
    return result


def feature_count(df: pd.DataFrame) -> Structure:
    count = int(df.shape[1])

    result = Structure(
        dimension=DIMENSION,
        name="feature_count",
        value=count,
        meta={"n_features": count}
    )

    logger.info(f"Computed feature_count: {count}")
    return result


def n_to_d_ratio(df: pd.DataFrame) -> Structure:
    n = df.shape[0]
    d = df.shape[1]

    ratio = float(n / d) if d > 0 else None

    result = Structure(
        dimension=DIMENSION,
        name="n_to_d_ratio",
        value=ratio,
        meta={
            "n_rows": n,
            "n_features": d
        }
    )

    logger.info(f"Computed n_to_d_ratio: {ratio}")
    return result


# ------------------ ORCHESTRATOR ------------------

SIGNALS_REGISTRY = [
    dataset_size,
    feature_count,
    n_to_d_ratio
]


def run_sample_adequacy(df: pd.DataFrame) -> List[Structure]:

    if not isinstance(df, pd.DataFrame):
        logger.error("Invalid input type for sample adequacy")
        return [
            Structure(
                dimension=DIMENSION,
                name="validation",
                value=None,
                meta={"status": "fail", "reason": "Input is not DataFrame"}
            )
        ]

    results = []

    for signal_fn in SIGNALS_REGISTRY:
        try:
            res = signal_fn(df)
            results.append(res)

        except Exception as e:
            logger.error(f"Signal failed: {signal_fn.__name__} | {str(e)}")

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
    run_sample_adequacy(df)
