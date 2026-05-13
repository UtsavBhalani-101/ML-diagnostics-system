
# & this file is for defining the data holder format and intra 
# & and inter module contract

from dataclasses import dataclass
from typing import Any, Dict, List


# * Signal Structure
@dataclass(frozen=True)
class Signal_Structure:
    dimension: str
    name: str
    value: Any
    status: str  # "ok", "no_value", "error"
    meta: Dict[str, Any]

# * Signal Structure init 
@dataclass
class SignalExtractionResult:
    dimensions: Dict[str, List[Signal_Structure]]
    
    def get(self, dimension: str, signal_name: str) -> Signal_Structure | None:
        signals = self.dimensions.get(dimension, [])
        return next((s for s in signals if s.name == signal_name), None)