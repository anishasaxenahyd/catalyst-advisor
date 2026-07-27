"""Data shape for the Solution Registry.

A `SolutionRecord` is a fictional-but-realistic account of a past enterprise
AI implementation. `architecture_pattern_id` deliberately reuses the same
five pattern ids the deterministic engine already selects from
(`app/providers/knowledge`'s `architecture_templates.json`), so the
enrichment layer can match a recommendation to similar past solutions with
a plain id comparison instead of fuzzy text matching.
"""

from typing import Literal

from pydantic import BaseModel, Field

CloudProvider = Literal["Azure", "AWS", "GCP"]


class SolutionRecord(BaseModel):
    id: str
    title: str
    industry: str
    business_problem: str
    architecture_pattern_id: str
    architecture_pattern_name: str
    ai_models: list[str] = Field(default_factory=list)
    cloud_provider: CloudProvider
    reused_catalog_assets: list[str] = Field(default_factory=list)
    security_considerations: list[str] = Field(default_factory=list)
    business_outcome: str
    lessons_learned: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
