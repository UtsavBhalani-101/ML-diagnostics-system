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
    """Detects periodic/cyclical patterns in a datetime column based on hour-of-day and day-of-week distributions."""
    
    parsed = pd.to_datetime(col, errors="coerce")
    valid = parsed.dropna()
    
    if len(valid) < 10:
        return {"hourly_concentration": 0.0, "weekly_concentration": 0.0, "periodic_score": 0.0}
    
    # hourly pattern: are certain hours heavily concentrated?
    hour_dist = valid.dt.hour.value_counts(normalize=True)
    max_hour_freq = float(hour_dist.iloc[0]) if len(hour_dist) > 0 else 0.0
    n_active_hours = int((hour_dist > 0.01).sum())
    hourly_concentration = max_hour_freq
    
    # weekly pattern: are certain weekdays heavily concentrated?
    dow_dist = valid.dt.dayofweek.value_counts(normalize=True)
    max_dow_freq = float(dow_dist.iloc[0]) if len(dow_dist) > 0 else 0.0
    weekly_concentration = max_dow_freq
    
    # periodic score: how non-uniform are these distributions
    # uniform hour dist would be ~0.042 per hour, uniform dow would be ~0.143 per day
    periodic_score = 0.5 * min(1.0, hourly_concentration / 0.15) + 0.5 * min(1.0, weekly_concentration / 0.3)
    
    return {
        "hourly_concentration": round(hourly_concentration, 4),
        "weekly_concentration": round(weekly_concentration, 4),
        "n_active_hours": n_active_hours,
        "periodic_score": round(float(periodic_score), 4)
    }

def infer_signals(signals: Dict) -> Result:
    ps = signals["periodic_score"]
    
    # high periodic score → strong cyclical pattern exists → good for modeling
    # low periodic score → no cyclical signal → poor periodic affordance
    # invert: score = 1 - periodic_score (higher = worse = no periodicity)
    score = 1.0 - ps
    
    flag = score > 0.8
    
    if score > 0.8:
        label = "CRITICAL"
    elif score > 0.5:
        label = "WARNING"
    else:
        label = "SAFE"
    
    return Result(
        test_name="datetime_periodic_signals",
        layer="affordance",
        score=round(score, 4),
        label=label,
        flag=flag,
        meta={
            "periodic_score": ps,
            "hourly_concentration": signals["hourly_concentration"],
            "weekly_concentration": signals["weekly_concentration"]
        }
    )


def run_periodic_signals_check():
    # business hours pattern: only weekday 9-17
    dates = pd.bdate_range("2023-01-01", periods=200, freq="h")
    dates = dates[dates.hour.isin(range(9, 18))]
    combined_signals = get_signals(pd.Series(dates[:100]))
    print("signals: ", combined_signals)
    print(infer_signals(combined_signals))

if __name__ == "__main__":
    run_periodic_signals_check()
