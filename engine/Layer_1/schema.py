
# & this file is for defining the data holder format and intra 
# & and inter module contract

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# * Signal Structure
@dataclass(frozen=True)
class Signal_Structure:
    dimension: str
    name: str
    value: Any
    status: str  # "ok", "no_value", "error"
    meta: Dict[str, Any]

# ^ Signal extraction init 
@dataclass
class SignalExtractionResult:
    dimensions: Dict[str, List[Signal_Structure]]
    
    def get(self, dimension: str, signal_name: str) -> Signal_Structure | None:
        signals = self.dimensions.get(dimension, [])
        return next((s for s in signals if s.name == signal_name), None)
    
  
# * Logic Structure   
@dataclass(frozen=True)
class Logic_Structure:
    dimension: str
    name: str
    label: str
    risk: float
    metrics: Optional[Dict]

# * Logic overall result
@dataclass(frozen=True)
class Logic_OverallResult:
    dimension: str
    status: str
    peak_risk : float | None
    severity_score : float | None
    composite : float | None
    critical: List[str]    # names of CRITICAL signals
    warnings: List[str]    # names of WARNING signals
    safe: List[str]        # names of SAFE signals
    errors: List[str]      # names of ERROR signals
    
    
# ^ Logic extraction init
@dataclass
class LogicExtractionResult:
    dimensions: Dict[str, tuple]  # dimension -> (results, overall)
    
    def get(self, dimension: str):
        return self.dimensions.get(dimension)