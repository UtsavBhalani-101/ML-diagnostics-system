from enum import Enum, auto

class SystemState(Enum):
    """
    The rigid timeline of a user session.
    
    The system moves FORWARD only:
    NO_SESSION -> DATA_LOADED -> DIAGNOSTICS_RUNNING -> MODEL_DECIDED -> MODEL_EXECUTION
    
    The ONLY way to move backward is to call reset(), which forces a return to NO_SESSION.
    """
    NO_SESSION = auto()           # 1. System is empty. Waiting for file.
    DATA_LOADED = auto()          # 2. File is in memory. Unchecked.
    DIAGNOSTICS_RUNNING = auto()  # 3. Pipelines are executing (Structural + Statistical).
    MODEL_DECIDED = auto()        # 4. Diagnostics complete. Verdict is set.
    MODEL_EXECUTION = auto()      # 5. User is viewing/training models (subject to Verdict).

class Verdict(Enum):
    """
    The Permission Slip granted by the Diagnostics.
    
    This dictates what the user is allowed to do in the MODEL_EXECUTION state.
    """
    UNKNOWN = auto()              # Diagnostics haven't run yet.
    ALLOWED = auto()              # Green Light: Full modeling access.
    CONSTRAINED = auto()          # Yellow Light: Modeling allowed with warnings/limits.
    BLOCKED = auto()              # Red Light: STOP. Critical issues found. Modeling disabled.

class DiagnosticStatus(Enum):
    """
    Granular status for individual checks within a report.
    """
    PASS = auto()
    WARNING = auto()
    CRITICAL = auto()