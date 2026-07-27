"""Deterministic "business understanding" restatement — the opening section
of an architect-style report. Built entirely from the already-validated
`SignalVector` plus the raw stated need; no LLM call, no new inference.
"""

from app.models.schemas import BusinessUnderstanding, SignalVector

_LATENCY_PHRASES = {
    "batch": "batch (non-real-time)",
    "near_realtime": "near-real-time",
    "realtime": "real-time",
}


def _problem_narrative(sv: SignalVector) -> str:
    return (
        f"The stated need is a {sv.use_case_type} capability for the {sv.industry} sector, "
        f"operating on {sv.data_modality} data classified as '{sv.data_sensitivity}' sensitivity. "
        f"It requires {_LATENCY_PHRASES.get(sv.latency_requirement, sv.latency_requirement)} "
        f"responses at {sv.expected_scale} scale, with a {sv.automation_level} level of automation."
    )


def _key_signals(sv: SignalVector) -> list[str]:
    signals: list[str] = []
    if sv.data_sensitivity == "phi":
        signals.append("Handles PHI — elevated governance and compliance controls apply.")
    elif sv.data_sensitivity == "pii":
        signals.append("Handles PII — data minimization and access controls apply.")

    if sv.automation_level == "autonomous":
        signals.append("Autonomous automation — requires human-override and audit-logging design.")
    elif sv.automation_level == "copilot":
        signals.append("Copilot-level automation — a human executes the final action.")

    if sv.expected_scale == "enterprise":
        signals.append("Enterprise-scale rollout — cross-team coordination and governance sign-off expected.")

    if sv.latency_requirement == "realtime":
        signals.append("Real-time latency requirement — architecture must minimize round-trip time.")

    if sv.integration_points:
        signals.append(f"Integrates with: {', '.join(sv.integration_points)}.")

    if not signals:
        signals.append("No elevated risk signals identified from the stated requirements.")
    return signals


def build_business_understanding(signal_vector: SignalVector, raw_text: str) -> BusinessUnderstanding:
    return BusinessUnderstanding(
        stated_need=raw_text.strip(),
        problem_narrative=_problem_narrative(signal_vector),
        industry=signal_vector.industry,
        use_case_type=signal_vector.use_case_type,
        data_sensitivity=signal_vector.data_sensitivity,
        data_modality=signal_vector.data_modality,
        latency_requirement=signal_vector.latency_requirement,
        expected_scale=signal_vector.expected_scale,
        automation_level=signal_vector.automation_level,
        integration_points=signal_vector.integration_points,
        key_signals=_key_signals(signal_vector),
    )
