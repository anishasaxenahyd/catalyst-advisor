"""Shared confidence-label banding — one function, reused by
`readiness.py` and `business_value.py` so "Very High"/"High"/"Good"/"Needs
More Information" always mean the same thresholds everywhere in a Report.
The frontend mirrors these exact thresholds in `lib/confidenceLabel.ts`.
"""


def confidence_label(score: float) -> str:
    if score >= 95:
        return "Very High"
    if score >= 90:
        return "High"
    if score >= 80:
        return "Good"
    return "Needs More Information"
