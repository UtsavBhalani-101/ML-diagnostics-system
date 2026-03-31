import logging
from dataclasses import dataclass
from typing import Dict, Optional


# ------------------ LOGGING ------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger()


# ------------------ STRUCTURE ------------------

@dataclass
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

    if ratio >= 10:
        risk = 0.0
    elif ratio >= 5:
        risk = 0.2
    elif ratio >= 2:
        risk = 0.5
    elif ratio >= 1:
        risk = 0.7
    else:
        risk = 1.0

    logger.info(f"n_to_d_ratio={ratio:.2f}, risk={risk}")
    return risk


def sample_size_risk(signals):
    n = signals["rows"]

    if n >= 1000:
        risk = 0.0
    elif n >= 500:
        risk = 0.2
    elif n >= 200:
        risk = 0.4
    elif n >= 100:
        risk = 0.6
    else:
        risk = 0.9

    logger.info(f"sample_size={n}, risk={risk}")
    return risk


# ------------------ AGGREGATION ------------------

def aggregate_sample_adequacy(signals):

    risks = {
        "n_to_d": n_to_d_risk(signals),
        "sample_size": sample_size_risk(signals)
    }

    weights = {
        "n_to_d": 0.6,
        "sample_size": 0.4
    }

    total_risk = sum(risks[k] * weights[k] for k in risks)

    logger.info(f"Aggregated risk={total_risk:.3f}")

    return total_risk, risks


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
    
    