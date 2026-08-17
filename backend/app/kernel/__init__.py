"""The Decision Kernel — the Decision Plane from the five-plane redesign.

Replaces the old `User -> Catalog MCP -> LLM -> Architecture` pipeline
(`app.engine.recommend.build_report`, weighted scoring in
`app.engine.scoring`) with a staged pipeline: framing -> requirements ->
sufficiency -> obligations -> solution class -> capability requirements ->
pattern admissibility -> precedents -> catalog resolution ->
sourcing -> candidates -> elimination -> selection -> evidence validation.

The governing invariant, enforced structurally rather than by convention:
no catalog asset may enter a candidate architecture except as the
resolution of a capability requirement derived independently of the
catalog (see `catalog_resolution.py`'s docstring for where that's enforced).

Elimination (`elimination.py`) and validation (`validation.py`) are the two
stages that must never call an LLM — see each module's docstring.
"""
