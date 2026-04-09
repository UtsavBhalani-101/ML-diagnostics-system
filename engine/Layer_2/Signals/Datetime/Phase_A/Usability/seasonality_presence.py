import numpy as np 
import pandas as pd 
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass(frozen=True)
class Signals:
    pass

@dataclass()
class Result:
    test_name: str 
    layer: str 
    score: float
    label: str
    flag: bool
    meta: Dict[str, float]
    


def get_signals(col: pd.Series) -> dict:
    """Detects whether the datetime column exhibits seasonal patterns via month-level distribution."""
    
    parsed = pd.to_datetime(col, errors="coerce")
    valid = parsed.dropna()
    
    if len(valid) < 12:
        return {"monthly_concentration": 0.0, "dow_concentration": 0.0, "seasonality_score": 0.0}
    
    # monthly distribution: do certain months dominate?
    month_dist = valid.dt.month.value_counts(normalize=True)
    n_active_months = len(month_dist)
    
    # if data covers fewer than 4 months, hard to detect seasonality
    if n_active_months < 4:
        monthly_concentration = float(month_dist.iloc[0]) if len(month_dist) > 0 else 0.0
        return {
            "monthly_concentration": monthly_concentration,
            "dow_concentration": 0.0,
            "seasonality_score": 0.0,
            "n_active_months": n_active_months
        }
    
    # how non-uniform is the monthly distribution
    # uniform = 1/12 ≈ 0.083 per month
    monthly_std = float(month_dist.std())
    expected_uniform_std = 0.0  # in perfectly uniform distribution
    monthly_concentration = float(month_dist.max())
    
    # day-of-week distribution
    dow_dist = valid.dt.dayofweek.value_counts(normalize=True)
    dow_concentration = float(dow_dist.max())
    
    # seasonality score: are months significantly non-uniform?
    # chi-squared-like test: sum of (observed - expected)^2 / expected
    expected_per_month = 1.0 / n_active_months
    chi2_like = float(((month_dist - expected_per_month) ** 2 / expected_per_month).sum())
    
    # normalize chi2 to [0, 1]
    seasonality_score = min(1.0, chi2_like / 2.0)
    
    return {
        "monthly_concentration": round(monthly_concentration, 4),
        "dow_concentration": round(dow_concentration, 4),
        "seasonality_score": round(float(seasonality_score), 4),
        "n_active_months": n_active_months
    }

def infer_signals(signals: Dict) -> Result:
    ss = signals["seasonality_score"]
    mc = signals["monthly_concentration"]
    
    # high seasonality_score → strong seasonal pattern (good for features, but risky for generalization)
    # we report it as informational — score represents how strong the seasonality is
    score = ss
    
    flag = score > 0.7
    
    if score > 0.7:
        label = "CRITICAL"
    elif score > 0.3:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_seasonality_presence",
        layer="usability",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "seasonality_score": round(ss, 4),
            "monthly_concentration": mc,
            "n_active_months": signals["n_active_months"]
        }
    )


def run_seasonality_check():
    # heavy summer bias
    summer_dates = pd.date_range("2023-06-01", periods=80, freq="D")
    winter_dates = pd.date_range("2023-01-01", periods=20, freq="D")
    combined_signals = get_signals(pd.Series(list(summer_dates) + list(winter_dates)))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_seasonality_check()
