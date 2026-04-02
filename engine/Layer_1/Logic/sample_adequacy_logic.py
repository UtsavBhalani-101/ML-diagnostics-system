import numpy as np
import logging
from dataclasses import dataclass
from typing import Dict, Optional


# ------------------ LOGGING ------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger()


# ------------------ STRUCTURE ------------------

@dataclass(frozen=True)
class TestResult:
    dimension: str
    name: str
    status: str
    reason: str
    risk: float
    metrics: Optional[Dict] = None


DIMENSION = "sample_adequacy"


# ------------------ VALIDATION ------------------

def validate_sample_signals(signals: dict):

    required = ["rows", "cols"]

    for key in required:
        if key not in signals:
            logger.error(f"Missing signal: {key}")
            raise ValueError(f"Missing required signal: {key}")

    rows = signals["rows"]
    cols = signals["cols"]

    if rows < 0 or cols < 0:
        logger.error("Invalid rows/cols values")
        raise ValueError("rows and cols must be non-negative")

    if cols == 0:
        logger.warning("Zero columns detected")

    logger.info(f"Validation passed: rows={rows}, cols={cols}")


# ------------------ RISK FUNCTIONS ------------------

def n_to_d_risk(signals):
    n = signals["rows"]
    d = signals["cols"]

    if d == 0:
        logger.warning("Division by zero in n_to_d_ratio")
        return 1.0

    ratio = n / d

    # Smooth decay (log-based)
    risk = np.exp(-ratio / 5)

    logger.info(f"n_to_d_ratio={ratio:.2f}, risk={risk:.3f}")
    return min(risk, 1.0)


def sample_size_risk(signals):
    n = signals["rows"]

    # diminishing returns curve
    risk = np.exp(-n / 300)

    logger.info(f"sample_size={n}, risk={risk:.3f}")
    return min(risk, 1.0)


# ------------------ AGGREGATION ------------------

def aggregate_sample_adequacy(signals):

    # -------------------------
    # RISKS
    # -------------------------
    dominant_risks = {
        "n_to_d": n_to_d_risk(signals)
    }

    additive_risks = {
        "sample_size": sample_size_risk(signals)
    }

    # -------------------------
    # COMPUTE
    # -------------------------
    dominant_max = max(dominant_risks.values()) if dominant_risks else 0.0

    additive_values = list(additive_risks.values())
    additive_total = sum(additive_values) / len(additive_values) if additive_values else 0.0

    # -------------------------
    # FINAL
    # -------------------------
    total_risk = max(dominant_max, additive_total)

    logger.info(
        f"Aggregation | dominant={dominant_max:.3f} "
        f"additive={additive_total:.3f} "
        f"total={total_risk:.3f}"
    )

    return total_risk, {
        "dominant": dominant_risks,
        "additive": additive_risks,
        "dominant_max": dominant_max,
        "additive_total": additive_total
    }


# ------------------ DECISION ------------------

def decision_from_risk(total_risk):

    if total_risk < 0.3:
        status = "SAFE"
        reason = "Sufficient data for modeling"
    elif total_risk < 0.7:
        status = "WARNING"
        reason = "Limited data; risk of instability"
    else:
        status = "CRITICAL"
        reason = "Insufficient data; high overfitting risk"

    logger.info(f"Decision: {status}")
    return status, reason


# ------------------ MAIN PIPELINE ------------------

def run_sample_adequacy(signals: dict) -> TestResult:

    logger.info("Running sample adequacy checks")

    # 1. Validation
    validate_sample_signals(signals)

    try:
        # 2. Aggregation
        total_risk, breakdown = aggregate_sample_adequacy(signals)

        # 3. Decision
        status, reason = decision_from_risk(total_risk)

        # 4. Metrics
        n = signals["rows"]
        d = signals["cols"]
        ratio = n / d if d > 0 else None

        result = TestResult(
            dimension=DIMENSION,
            name="sample_adequacy_overall",
            status=status,
            reason=reason,
            risk=round(total_risk, 3),
            metrics={
                "total_risk": total_risk,
                "risk_breakdown": breakdown,
                "n_to_d_ratio": ratio,
                "rows": n,
                "cols": d
            }
        )
        
        logger.info(f"Final result: {result}")
        return result
    
    except Exception as e:
        logger.error(
            f"Signal failed: {signals.__name__}",
            extra={"signal": signals.__name__, "error": str(e)}
        )
        
    
# ------------------ Entry ------------------

if __name__ == "__main__":
    run_sample_adequacy(signals)
    
    