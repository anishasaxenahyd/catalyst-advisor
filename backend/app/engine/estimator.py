"""Effort and timeline estimates, looked up from config by the chosen
architecture pattern's complexity tier — no hardcoded durations in code."""

from app.models.schemas import ArchitecturePattern


def estimate_effort(pattern: ArchitecturePattern, rules: dict) -> str:
    return rules["effort_estimate_by_complexity_tier"][str(pattern.complexity_tier)]


def estimate_timeline(pattern: ArchitecturePattern, rules: dict) -> str:
    return rules["timeline_estimate_by_complexity_tier"][str(pattern.complexity_tier)]
