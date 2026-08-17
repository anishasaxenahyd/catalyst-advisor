"""Loads the Knowledge and Policy plane vocabularies from JSON, cached.

Same discipline as `app.engine.config_loader`: nothing in `kernel/` hardcodes
a capability, signature, pattern, or obligation — every one lives in
`data/taxonomy/`, `data/knowledge/`, `data/policy/` and comes through here.
This is deliberately file-backed, not MCP-backed, for the prototype — see
`docs/` for how to swap these for live sources later without touching any
kernel stage, since every stage only ever imports the functions below.
"""

import json
from functools import lru_cache
from pathlib import Path

from app.kernel.schemas import CapabilityDef, ObligationRule, PatternRecord, RequirementSignatureDef, SolutionClassDef

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_capabilities() -> list[CapabilityDef]:
    return [CapabilityDef(**row) for row in _load(DATA_DIR / "taxonomy" / "capabilities.json")]


@lru_cache(maxsize=1)
def get_capability_ids() -> set[str]:
    return {c.id for c in get_capabilities()}


@lru_cache(maxsize=1)
def get_requirement_signatures() -> list[RequirementSignatureDef]:
    return [RequirementSignatureDef(**row) for row in _load(DATA_DIR / "taxonomy" / "requirement_signatures.json")]


@lru_cache(maxsize=1)
def get_signature_ids() -> set[str]:
    return {s.id for s in get_requirement_signatures()}


@lru_cache(maxsize=1)
def get_signature_by_id() -> dict[str, RequirementSignatureDef]:
    return {s.id: s for s in get_requirement_signatures()}


@lru_cache(maxsize=1)
def get_capability_by_id() -> dict[str, CapabilityDef]:
    return {c.id: c for c in get_capabilities()}


@lru_cache(maxsize=1)
def get_solution_classes() -> list[SolutionClassDef]:
    return [SolutionClassDef(**row) for row in _load(DATA_DIR / "taxonomy" / "solution_classes.json")]


@lru_cache(maxsize=1)
def get_patterns() -> list[PatternRecord]:
    return [PatternRecord(**row) for row in _load(DATA_DIR / "knowledge" / "patterns.json")]


@lru_cache(maxsize=1)
def get_pattern_by_id() -> dict[str, PatternRecord]:
    return {p.id: p for p in get_patterns()}


@lru_cache(maxsize=1)
def get_obligation_rules() -> list[ObligationRule]:
    return [ObligationRule(**row) for row in _load(DATA_DIR / "policy" / "obligations.json")]


@lru_cache(maxsize=1)
def get_obligation_by_id() -> dict[str, ObligationRule]:
    return {o.id: o for o in get_obligation_rules()}
