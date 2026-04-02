import numpy as np
import logging
from dataclasses import dataclass
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


DIMENSION = "target_viability"


def validate_target_signals(signals: dict):
    required = ["target_missing_ratio", "target_unique_count"]

    for key in required:
        if key not in signals:
            raise ValueError(f"Missing target signal: {key}")

    missing_ratio = signals["target_missing_ratio"]
    if not (0.0 <= missing_ratio <= 1.0):
        raise ValueError("target_missing_ratio must be between 0 and 1")

    unique_count = signals["target_unique_count"]
    if unique_count < 0:
        raise ValueError("target_unique_count must be >= 0")

    if missing_ratio == 1.0 and unique_count > 0:
        raise ValueError("Inconsistent: all target missing but unique_count > 0")


def check_target_hard_fail(signals):
    logger.info("Checking target missing")
    if signals["target_missing_ratio"] == 1.0:
        return TestResult(
            dimension=DIMENSION,
            name="target_missing",
            status="CRITICAL",
            reason="Target is completely missing",
            risk=1.0,
        )

    logger.info("Checking target variance")
    if signals["target_unique_count"] <= 1:
        return TestResult(
            dimension=DIMENSION,
            name="target_variance",
            status="CRITICAL",
            reason="Target has no variability; nothing can be learned",
            risk=1.0,
        )

    logger.info("Checking target mixed types")
    if signals.get("target_mixed_type", False):
        return TestResult(
            dimension=DIMENSION,
            name="target_mixed_type",
            status="CRITICAL",
            reason="Target has mixed types; label semantics are ambiguous",
            risk=1.0,
        )

    return None


def missing_risk(signals):
    missing_ratio = signals["target_missing_ratio"]
    logger.info(f"Computing target missing risk: {missing_ratio}")
    return min(missing_ratio / 0.3, 1.0)


def imbalance_risk(signals):
    imbalance_score = signals.get("class_imbalance_score", 0)
    logger.info(f"Computing target imbalance risk: {imbalance_score}")
    return min((imbalance_score - 0.5) / 0.5, 1.0) if imbalance_score > 0.5 else 0.0


def variance_risk(signals):
    variance = signals.get("target_variance")
    logger.info(f"Computing target variance risk: {variance}")

    if variance is None:
        return 0.0

    risk = np.exp(-variance * 1000)
    return min(risk, 1.0)


def task_uncertainty_risk(signals):
    confidence = signals.get("task_confidence", 1.0)
    logger.info(f"Computing task uncertainty risk: {confidence}")

    risk = (1 - confidence) ** 2
    if confidence < 0.5:
        risk += 0.3

    return min(risk, 1.0)


def aggregate_risk(signals):
    dominant_risks = {
        "task_uncertainty": task_uncertainty_risk(signals),
    }

    additive_risks = {
        "missing": missing_risk(signals),
        "imbalance": imbalance_risk(signals),
        "variance": variance_risk(signals),
    }

    additive_values = list(additive_risks.values())
    additive_total = sum(additive_values) / len(additive_values) if additive_values else 0.0

    dominant_values = list(dominant_risks.values())
    dominant_max = max(dominant_values) if dominant_values else 0.0

    total_risk = max(additive_total, dominant_max)

    logger.info(
        f"Aggregation | dominant={dominant_max:.3f} "
        f"additive={additive_total:.3f} "
        f"total={total_risk:.3f}"
    )

    sorted_risks = dict(
        sorted(
            {**dominant_risks, **additive_risks}.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    return total_risk, {
        "dominant": dominant_risks,
        "additive": additive_risks,
        "sorted_contributors": sorted_risks,
        "additive_total": additive_total,
        "dominant_max": dominant_max,
    }


def decision_from_risk(total_risk):
    logger.info("Deciding target viability status from risk")

    if total_risk < 0.3:
        return "SAFE", "Missingness, balance, and variability are within acceptable range. Low structural risk."
    if total_risk < 0.7:
        return "WARNING", "The target shows moderate structural weakness and should be reviewed."
    return "CRITICAL", "The target is structurally unreliable for supervised learning."


def run_target_viability(signals):
    validate_target_signals(signals)

    try:
        hard_fail = check_target_hard_fail(signals)
        if hard_fail:
            return hard_fail

        total_risk, breakdown = aggregate_risk(signals)
        status, reason = decision_from_risk(total_risk)

        return TestResult(
            dimension=DIMENSION,
            name="target_viability_overall",
            status=status,
            reason=reason,
            risk=round(total_risk, 3),
            metrics={
                "total_risk": total_risk,
                "risk_breakdown": breakdown,
            },
        )
    except Exception as e:
        logger.error(
            "Signal evaluation failed for target viability",
            extra={"error": str(e)},
        )
        raise
