from dataclasses import dataclass
import logging
from typing import Dict, Optional


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ml_diag")


@dataclass(frozen=True)
class TestResult:
    dimension: str
    name: str
    status: str
    reason: str
    risk: float
    metrics: Optional[Dict] = None


DIMENSION = "data_integrity"


def validate_signals(signals: dict):
    required = [
        "rows",
        "cols",
        "global_missing_ratio",
        "column_missing_ratio",
        "duplicate_ratio",
        "constant_columns",
        "constant_ratio",
        "hidden_missing_ratio",
        "mixed_type_columns",
        "mixed_ratio",
    ]

    for key in required:
        if key not in signals:
            raise ValueError(f"Missing signal: {key}")


def missing_risk(signals):
    ratio = signals["global_missing_ratio"]
    logger.info(f"Compute missing_risk: {ratio}")
    return min(ratio / 0.3, 1.0)


def duplicate_risk(signals):
    ratio = signals["duplicate_ratio"]
    logger.info(f"Compute duplicate_risk: {ratio}")
    return min(ratio / 0.2, 1.0)


def constant_risk(signals):
    ratio = signals["constant_ratio"]
    logger.info(f"Compute constant_risk: {ratio}")
    return min(ratio / 0.3, 1.0)


def hidden_missing_risk(signals):
    data = signals["hidden_missing_ratio"]
    if not data:
        return 0.0

    max_ratio = max(data.values())
    logger.info(f"Compute hidden_missing_risk: {max_ratio}")
    return min(max_ratio / 0.3, 1.0)


def mixed_type_risk(signals):
    ratio = signals["mixed_ratio"]
    logger.info(f"Compute mixed_type_risk: {ratio}")
    return min(ratio / 0.2, 1.0)


def check_hard_failures(signals):
    logger.info("Checking hard failures: Mixed type")
    if signals["mixed_ratio"] > 0:
        return TestResult(
            dimension=DIMENSION,
            name="mixed_types",
            status="CRITICAL",
            reason="Mixed data types detected; structure is ambiguous",
            risk=1.0,
            metrics={"mixed_ratio": signals["mixed_ratio"]},
        )

    logger.info("Checking hard failures: Hidden missing")
    if signals["hidden_missing_ratio"]:
        max_hidden = max(signals["hidden_missing_ratio"].values())
        if max_hidden > 0.5:
            return TestResult(
                dimension=DIMENSION,
                name="hidden_missing",
                status="CRITICAL",
                reason="Extreme hidden missing values detected",
                risk=1.0,
                metrics={"max_hidden_missing": max_hidden},
            )

    return None


def aggregate_risk(signals):
    """
    Hybrid aggregation:
    - dominant risks -> max()
    - additive risks -> average
    - final -> max(dominant, additive)
    """

    risks = {
        "missing_values": missing_risk(signals),
        "duplicates": duplicate_risk(signals),
        "constant_columns": constant_risk(signals),
        "hidden_missing": hidden_missing_risk(signals),
    }

    logger.info(f"Computed individual risks: {risks}")

    dominant_keys = ["hidden_missing"]
    additive_keys = ["missing_values", "duplicates", "constant_columns"]

    dominant_values = [risks[k] for k in dominant_keys if k in risks]
    dominant_max = max(dominant_values) if dominant_values else 0.0

    additive_values = [risks[k] for k in additive_keys if k in risks]
    additive_total = sum(additive_values) / len(additive_values) if additive_values else 0.0

    total_risk = max(dominant_max, additive_total)

    logger.info(
        f"Aggregation | dominant={dominant_max:.3f} "
        f"additive={additive_total:.3f} "
        f"total={total_risk:.3f}"
    )

    return total_risk, {
        "dominant": {k: risks[k] for k in dominant_keys},
        "additive": {k: risks[k] for k in additive_keys},
    }


def decision_from_risk(total_risk):
    logger.info("Taking a decision based on risk")

    if total_risk < 0.3:
        return "SAFE", "Missingness, duplication, and constants are currently low. Low structural risk."
    if total_risk < 0.7:
        return "WARNING", "Structural issues are present and should be investigated before modeling."
    return "CRITICAL", "Structural integrity is unreliable and likely to block dependable modeling."


def run_data_integrity(signals: dict) -> TestResult:
    validate_signals(signals)
    try:
        hard_fail = check_hard_failures(signals)
        if hard_fail:
            return hard_fail

        total_risk, individual_risks = aggregate_risk(signals)
        status, reason = decision_from_risk(total_risk)

        return TestResult(
            dimension=DIMENSION,
            name="data_integrity_overall",
            status=status,
            reason=reason,
            risk=round(total_risk, 3),
            metrics={
                "total_risk": total_risk,
                "risk_breakdown": individual_risks,
            },
        )
    except Exception as e:
        logger.error(
            "Signal evaluation failed for data integrity",
            extra={"error": str(e)},
        )
        raise
