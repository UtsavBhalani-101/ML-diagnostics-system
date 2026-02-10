import pandas as pd
from Backend.states import SystemState, Verdict

class SessionEngine:
    def __init__(self):
        self._state = SystemState.NO_SESSION
        self._verdict = Verdict.UNKNOWN
        
        # Data Containers
        self._df = None
        self._diagnostic_report = None
        self._metadata = {}
        
        print(f"[System] Engine initialized. Waiting for data.")

    # ==========================================
    # PROPERTIES
    # ==========================================
    @property
    def current_state(self):
        return self._state

    @property
    def current_verdict(self):
        return self._verdict
    
    @property
    def is_data_loaded(self):
        return self._df is not None

    # ==========================================
    # THE GATEKEEPER (Upload Logic)
    # ==========================================
    def load_data(self, filepath: str):
        """
        Loads the dataset into the engine.
        
        RESTRICTION: 
        Can ONLY be called if current state is NO_SESSION.
        If called while busy, it raises a PermissionError.
        """
        # 1. Check The Lock
        if self._state != SystemState.NO_SESSION:
            raise PermissionError(
                f"ACCESS DENIED: Session is busy ({self._state.name}). "
                "You must call reset_session() before uploading new data."
            )

        print(f"[System] Attempting to load: {filepath}...")
        
        try:
            # 2. Perform the Action
            self._df = pd.read_csv(filepath)
            
            # 3. Capture Metadata (The Truth)
            self._metadata = {
                "rows": len(self._df),
                "cols": len(self._df.columns),
                "columns": list(self._df.columns)
            }
            
            # 4. Update State
            self._state = SystemState.DATA_LOADED
            print(f"[System] Success. State -> DATA_LOADED. (Rows: {self._metadata['rows']})")
            
        except Exception as e:
            # If loading fails (e.g., bad CSV), we strictly reset.
            print(f"[System] CRITICAL LOAD FAILURE: {e}")
            self.reset_session()
            raise e

    # ==========================================
    # THE KILL SWITCH
    # ==========================================
    def reset_session(self):
        print("--- [SYSTEM RESET] Initiated ---")
        self._df = None
        self._diagnostic_report = None
        self._metadata = {}
        self._verdict = Verdict.UNKNOWN
        self._state = SystemState.NO_SESSION
        print("--- [SYSTEM RESET] Complete. Memory Wiped. ---")
        
    # ==========================================
    # THE SCANNER (Verdict Logic)
    # ==========================================
    def _synthesize_verdict(self, full_report: dict):
        """
        INTERNAL: Scans the report for 'Kill Flags'.
        Decides the Verdict based on the worst severity found.
        Transitions state to MODEL_DECIDED.
        """
        print("[System] Synthesizing Verdict...")
        self._diagnostic_report = full_report
        
        # 1. Extract all severity tags from the JSON tree
        found_severities = []
        
        # We assume structure: { "section_name": { "check_name": { "severity": "..." } } }
        for section_name, section_data in full_report.items():
            if isinstance(section_data, dict):
                for check_name, check_data in section_data.items():
                    if isinstance(check_data, dict) and "severity" in check_data:
                        found_severities.append(check_data["severity"])

        # 2. Apply The Law (The Hierarchy of Severity)
        if "CRITICAL" in found_severities:
            self._verdict = Verdict.BLOCKED
            print(f"   -> BLOCKED (Found Critical Issues)")
            
        elif "WARNING" in found_severities:
            self._verdict = Verdict.CONSTRAINED
            print(f"   -> CONSTRAINED (Found Warnings)")
            
        else:
            self._verdict = Verdict.ALLOWED
            print(f"   -> ALLOWED (Clean Data)")

        # 3. Lock the State
        self._state = SystemState.MODEL_DECIDED

    # ==========================================
    # TEMPORARY: For Testing Phase 4
    # ==========================================
    def debug_run_verdict_logic(self, dummy_report):
        """
        Helper to test the scanner without running real pipelines.
        """
        if self._state != SystemState.DATA_LOADED:
            # We allow it if we are already in DATA_LOADED for testing
            pass
        self._synthesize_verdict(dummy_report)
    # ==========================================
    # DEBUG HELPERS (Add this back)
    # ==========================================
    def debug_force_state(self, new_state):
        """
        Temporary helper to force state for testing.
        """
        print(f"[DEBUG] Forcing state to {new_state.name}")
        self._state = new_state