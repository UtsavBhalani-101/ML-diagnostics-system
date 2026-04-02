import numpy as np
from dataclasses import dataclass
import logging
from typing import Dict, List, Optional


# ------------------ LOGGING ------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger('ml_diag')


# ------------------ STRUCTURE ------------------

@dataclass(frozen=True)
class TestResult:
    dimension: str
    name: str
    status: str
    reason: str
    risk: float
    metrics: Optional[Dict] = None


DIMENSION = "data_integrity"


# ------------------ VALIDATION ------------------

def validate_signals(signals: dict):
    required = [
        "rows", "cols",
        "global_missing_ratio",
        "column_missing_ratio",
        "duplicate_ratio",
        "constant_columns", "constant_ratio",
        "hidden_missing_ratio",
        "mixed_type_columns", "mixed_ratio"
    ]

    for key in required:
        if key not in signals:
            raise ValueError(f"Missing signal: {key}")


# ------------------ RISK FUNCTIONS ------------------

def missing_risk(signals):
    ratio = signals["global_missing_ratio"]
    
    logger.info(f"Compute missing_risk: {ratio}")
    return min(ratio / 0.3, 1.0)  # 30% = max risk


def duplicate_risk(signals):
    ratio = signals["duplicate_ratio"]
    
    logger.info(f"Compute duplicate_risk: {ratio}")
    return min(ratio / 0.2, 1.0)  # 20% = max risk


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


# ------------------ HARD FAILURES ------------------

def check_hard_failures(signals):
    
    
    # Mixed types → immediate failure
    logger.info(f"Checking hard failures: Mixed type")
    if signals["mixed_ratio"] > 0:
        return TestResult(
            dimension=DIMENSION,
            name="mixed_type_columns",
            status="CRITICAL",
            reason="Mixed data types detected; structure is ambiguous",
            risk=1.0,
            metrics={"mixed_ratio": signals["mixed_ratio"]}
        )

    # Extreme hidden missing
    logger.info(f"Checking hard failures: Hidden missing")
    if signals["hidden_missing_ratio"]:
        max_hidden = max(signals["hidden_missing_ratio"].values())
        if max_hidden > 0.5:
            return TestResult(
                dimension=DIMENSION,
                name="hidden_missing",
                status="CRITICAL",
                reason="Extreme hidden missing values detected",
                risk=1.0,
                metrics={"max_hidden_missing": max_hidden}
            )

    return None


# ------------------ AGGREGATION ------------------

def aggregate_risk(signals):
    """
    Hybrid aggregation:
    - dominant risks → max()
    - additive risks → average
    - final → max(dominant, additive)
    """

    # --- Compute all risks ---
    risks = {
        "missing": missing_risk(signals),
        "duplicates": duplicate_risk(signals),
        "constant": constant_risk(signals),
        "hidden": hidden_missing_risk(signals),
    }

    logger.info(f"Computed individual risks: {risks}")

    # -------------------------
    # CLASSIFICATION (CRITICAL STEP)
    # -------------------------
    dominant_keys = [
        "hidden",      # localized corruption → dangerous
    ]

    additive_keys = [
        "missing",
        "duplicates",
        "constant",
    ]

    # -------------------------
    # DOMINANT
    # -------------------------
    dominant_values = [risks[k] for k in dominant_keys if k in risks]
    dominant_max = max(dominant_values) if dominant_values else 0.0

    # -------------------------
    # ADDITIVE
    # -------------------------
    additive_values = [risks[k] for k in additive_keys if k in risks]

    if additive_values:
        additive_total = sum(additive_values) / len(additive_values)
    else:
        additive_total = 0.0

    # -------------------------
    # FINAL RISK
    # -------------------------
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

# ------------------ FINAL DECISION ------------------

def decision_from_risk(total_risk):
    
    logger.info(f"Taking a decision based on risk")

    if total_risk < 0.3:
        return "SAFE", "Dataset structure is clean"
    elif total_risk < 0.7:
        return "WARNING", "Dataset has moderate structural issues"
    else:
        return "CRITICAL", "Dataset structure is unreliable"


# ------------------ MAIN PIPELINE ------------------

def run_data_integrity(signals: dict) -> TestResult:
    
    validate_signals(signals)
    try:
        # 1. Hard failures first
        hard_fail = check_hard_failures(signals)
        if hard_fail:
            return hard_fail

        # 2. Aggregate risk
        total_risk, individual_risks = aggregate_risk(signals)

        # 3. Final decision
        status, reason = decision_from_risk(total_risk)

        return TestResult(
            dimension=DIMENSION,
            name="data_integrity_overall",
            status=status,
            reason=reason,
            risk=round(total_risk, 3),
            metrics={
                "total_risk": total_risk,
                "risk_breakdown": individual_risks
            }
        )
    
    except Exception as e:
        logger.error(
            f"Signal failed: {signals.__name__}",
            extra={"signal": signals.__name__, "error": str(e)}
        )
        
        
# ------------------ Entry ------------------

if __name__ == "__main__":
    run_data_integrity(signals)
    
    