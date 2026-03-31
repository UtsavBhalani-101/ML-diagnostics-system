import numpy as np
import logging
from dataclasses import dataclass
from typing import Dict, Optional

# ------------------ LOGGING ------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger('ml_diag')


# ------------------ STRUCTURE ------------------

@dataclass
class TestResult:
    dimension: str
    name: str
    status: str
    reason: str
    risk: float
    metrics: Optional[Dict] = None


DIMENSION = "target_viability"

# ------------------ VALIDATION ------------------

def validate_target_signals(signals: dict):

    required = [
        "target_missing_ratio",
        "target_unique_count"
    ]

    for key in required:
        if key not in signals:
            raise ValueError(f"Missing target signal: {key}")

    # Range checks
    r = signals["target_missing_ratio"]
    if not (0.0 <= r <= 1.0):
        raise ValueError("target_missing_ratio must be between 0 and 1")

    u = signals["target_unique_count"]
    if u < 0:
        raise ValueError("target_unique_count must be >= 0")

    # Logical consistency
    if r == 1.0 and u > 0:
        raise ValueError("Inconsistent: all target missing but unique_count > 0")

# ------------------ HARD FAILURES ------------------

def check_target_hard_fail(signals):

    # All missing
    logger.info(f"Checking target missing...")

    if signals["target_missing_ratio"] == 1.0:
        return TestResult(
            dimension=DIMENSION,
            name="target_missing",
            status="CRITICAL",
            reason="Target is completely missing",
            risk=1.0
        )

    # Single class / zero variance
    logger.info(f"Checking variance...")

    if signals["target_unique_count"] <= 1:
        return TestResult(
            dimension=DIMENSION,
            name="target_variance",
            status="CRITICAL",
            reason="Target has no variability; nothing to predict",
            risk=1.0
        )

    # Mixed types
    logger.info(f"Checking mixed types...")

    if signals.get("target_mixed_type", False):
        return TestResult(
            dimension=DIMENSION,
            name="target_mixed_type",
            status="CRITICAL",
            reason="Target has mixed types; ambiguous label definition",
            risk=1.0
        )

    return None


# ------------------ RISK FUNCTIONS ------------------

def missing_risk(signals):
    r = signals["target_missing_ratio"]

    logger.info(f"Computing missing_risk: {r}")
    return min(r / 0.3, 1.0)


def imbalance_risk(signals):
    r = signals.get("class_imbalance_score", 0)

    logger.info(f"Computing imbalance_risk: {r}")
    return min((r - 0.5) / 0.5, 1.0) if r > 0.5 else 0.0


def variance_risk(signals):
    var = signals.get("target_variance")
    logger.info(f"Computing variance_risk: {var}")

    if var is None:
        return 0.0

    return 1.0 if var < 1e-5 else 0.2 if var < 1e-3 else 0.0


def task_uncertainty_risk(signals):
    conf = signals.get("task_confidence", 1.0)
    risk = (1 - conf) ** 2

    if conf < 0.5:
        risk += 0.3

    return min(risk, 1.0)


# ------------------ AGGREGATION ------------------

def aggregate_risk(signals):

    #  DOMINANT RISKS
    dominant_risks = {
        "task_uncertainty": task_uncertainty_risk(signals)
    }

    # ADDITIVE RISKS 
    additive_risks = {
        "missing": missing_risk(signals),
        "imbalance": imbalance_risk(signals),
        "variance": variance_risk(signals)
    }

    # Avoid division by zero (edge safety)
    if additive_risks:
        additive_total = sum(additive_risks.values()) / len(additive_risks)
    else:
        additive_total = 0.0

    dominant_max = max(dominant_risks.values()) if dominant_risks else 0.0

    # FINAL COMBINATION 
    total_risk = max(additive_total, dominant_max)

    return total_risk, {
        "dominant": dominant_risks,
        "additive": additive_risks,
        "additive_total": additive_total,
        "dominant_max": dominant_max
    }


# ------------------ FINAL DECISION ------------------

def decision_from_risk(total_risk):
    
    logger.info(f"Deciding a label based on risk")

    if total_risk < 0.3:
        return "SAFE", "Target is usable"
    elif total_risk < 0.7:
        return "WARNING", "Target has potential issues"
    else:
        return "CRITICAL", "Target is unreliable for learning"


# ------------------ MAIN ------------------

def run_target_viability(signals):

    validate_target_signals(signals)

    try:
        # 1. Hard fail
        hard = check_target_hard_fail(signals)
        if hard:
            return hard

        # 2. Aggregate
        total_risk, breakdown = aggregate_risk(signals)

        # 3. Decide
        status, reason = decision_from_risk(total_risk)

        return TestResult(
            dimension=DIMENSION,
            name="target_viability_overall",
            status=status,
            reason=reason,
            risk=round(total_risk, 3),
            metrics={
                "total_risk": total_risk,
                "risk_breakdown": breakdown
            }
        )
        
    except Exception as e:
        logger.error(
            f"Signal failed: {signals.__name__}",
            extra={"signal": signals.__name__, "error": str(e)}
        )
        
# ------------------ Entry ------------------

if __name__ == "__main__":
    run_target_viability(signals)
