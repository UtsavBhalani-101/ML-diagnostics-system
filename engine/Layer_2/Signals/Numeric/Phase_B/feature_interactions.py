import itertools

class PhaseBInteractionHypotheses:
    """
    Phase B: Inter-column hypothesis generator.
    Does NOT evaluate usefulness or touch target.
    """

    def __init__(self, phase_a_reports: dict):
        """
        phase_a_reports: {column_name: phase_a_output}
        """
        self.reports = phase_a_reports
        self.hypotheses = []

    def run(self):
        self._ratio_hypotheses()
        self._difference_hypotheses()
        return self.hypotheses

    def _ratio_hypotheses(self):
        numerators = [
            c for c, r in self.reports.items()
            if "high_dispersion" in r.get("tags", [])
        ]
        denominators = [
            c for c, r in self.reports.items()
            if "low_dispersion" in r.get("tags", [])
        ]

        for num, den in itertools.product(numerators, denominators):
            if num == den:
                continue

            self.hypotheses.append({
                "type": "interaction_candidate",
                "interaction": "ratio",
                "columns": [num, den],
                "evidence": {
                    "numerator": "high_dispersion",
                    "denominator": "low_dispersion"
                },
                "risk": "may suppress rare-event magnitude",
                "status": "hypothesis"
            })

    def _difference_hypotheses(self):
        monotonic_cols = [
            c for c, r in self.reports.items()
            if "monotonic_sequence" in r.get("tags", [])
        ]

        for c1, c2 in itertools.combinations(monotonic_cols, 2):
            self.hypotheses.append({
                "type": "interaction_candidate",
                "interaction": "difference",
                "columns": [c1, c2],
                "evidence": {
                    "pattern": "monotonic_sequences"
                },
                "risk": "ordering_may_be_artifact",
                "status": "hypothesis"
            })
