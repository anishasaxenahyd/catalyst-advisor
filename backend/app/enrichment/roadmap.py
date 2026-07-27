"""Deterministic implementation roadmap — phase templates looked up from
config by the chosen pattern's complexity tier, mirroring how
`app.engine.estimator` looks up effort/timeline. No hardcoded phase content
in code; retuning the roadmap means editing `data/config/decision_rules.json`.
"""

from app.models.schemas import ArchitecturePattern, ImplementationRoadmap, RoadmapPhase


def build_implementation_roadmap(
    pattern: ArchitecturePattern, timeline_estimate: str, rules: dict
) -> ImplementationRoadmap:
    phase_templates = rules["roadmap_phases_by_complexity_tier"][str(pattern.complexity_tier)]
    phases = [
        RoadmapPhase(
            name=template["name"],
            duration=template["duration"],
            goals=template["goals"],
            deliverables=template["deliverables"],
        )
        for template in phase_templates
    ]
    return ImplementationRoadmap(phases=phases, total_timeline=timeline_estimate)
