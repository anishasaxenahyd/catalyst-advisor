"""Stages 1-3: Framing, Problem Interpretation, Requirement Extraction.

Reuses the existing `LLMProvider.extract_signal_vector()` call unchanged —
that call already does the interpretation work (Stage 1-2: free text ->
structured signal) under a schema contract, and its output already carries
per-field provenance from `app.validation.signal_normalizer`. What was
missing was Stage 3: translating that signal into the closed requirement-
signature vocabulary the rest of the kernel reasons over, instead of the
free-form `tags` list a scoring model used to match. That translation is
deterministic and lives here — no new LLM call needed for it.

Every signature this stage produces traces back to either a `SignalVector`
field (provenance inherited from that field) or a matched tag (provenance
`model_inference`, since tags are LLM extraction output, not a user hint).
"""

from app.kernel.loaders import get_requirement_signatures
from app.kernel.schemas import Assumption, RequirementSignatureInstance
from app.models.schemas import SignalVector

_SOLUTION_SHAPED_WORDS = {
    "chatbot": "The request names a conversational interface ('chatbot') — interaction modality is a proposed solution, not a stated requirement.",
    "bot": "The request names a bot — treat conversational modality as an assumption to confirm, not a requirement.",
    "agent": "The request names an 'agent' — agentic/autonomous execution is a proposed solution, not a stated requirement.",
    "copilot": "The request names a 'copilot' — treat the interaction pattern as a proposed solution to validate against the underlying job to be done.",
    "dashboard": "The request names a 'dashboard' — treat the presentation surface as a proposed solution, not a requirement.",
}


def detect_solution_assumptions(raw_text: str) -> list[str]:
    lowered = raw_text.lower()
    return [note for word, note in _SOLUTION_SHAPED_WORDS.items() if word in lowered]


def _field_provenance(signal: SignalVector, field: str) -> str:
    return {"user": "user_stated", "llm": "model_inference", "default": "model_inference"}.get(
        signal.field_provenance.get(field, "default"), "model_inference"
    )


_DEFERRED_ACTION_PHRASES = ("eventually", "in a future", "in the future", "later phase", "next release", "next phase", "down the road", "roadmap item")


def derive_requirement_signatures(signal: SignalVector, raw_text: str = "") -> list[RequirementSignatureInstance]:
    """Stage 3. Deterministic mapping from the already-extracted SignalVector
    into the closed requirement-signature vocabulary (data/taxonomy/requirement_signatures.json).
    A signature not in this list simply isn't asserted — there is no
    fallback to free-text tag matching downstream of this function.

    `raw_text` is used for exactly one textual heuristic (ACTION_REQUIRED_DEFERRED
    phrasing) that a tag/enum-based SignalVector can't otherwise represent —
    everything else derives from the already-structured signal, never from
    a second independent read of the free text."""
    signatures: dict[str, RequirementSignatureInstance] = {}
    defs_by_id = {s.id: s for s in get_requirement_signatures()}
    legacy_tag_index: dict[str, list[str]] = {}
    for sig_def in get_requirement_signatures():
        for tag in sig_def.legacy_tags:
            legacy_tag_index.setdefault(tag, []).append(sig_def.id)

    def add(sig_id: str, source_span: str, provenance: str) -> None:
        if sig_id in signatures or sig_id not in defs_by_id:
            return
        signatures[sig_id] = RequirementSignatureInstance(
            id=sig_id, category=defs_by_id[sig_id].category, source_span=source_span, provenance=provenance
        )

    for tag in signal.tags:
        for sig_id in legacy_tag_index.get(tag, []):
            add(sig_id, source_span=f"tag:{tag}", provenance="model_inference")

    if signal.data_sensitivity == "phi":
        add("SENSITIVE_DATA_PHI", "signal.data_sensitivity=phi", _field_provenance(signal, "data_sensitivity"))
    elif signal.data_sensitivity == "pii":
        add("SENSITIVE_DATA_PII", "signal.data_sensitivity=pii", _field_provenance(signal, "data_sensitivity"))

    if signal.data_modality == "structured":
        add("STRUCTURED_DATA_SOURCE", "signal.data_modality=structured", _field_provenance(signal, "data_modality"))
    if signal.data_modality in ("image", "mixed"):
        add("IMAGE_MODALITY", f"signal.data_modality={signal.data_modality}", _field_provenance(signal, "data_modality"))

    if signal.latency_requirement == "realtime":
        add("LOW_LATENCY_REQUIRED", "signal.latency_requirement=realtime", _field_provenance(signal, "latency_requirement"))
        add("INTERACTION_CONVERSATIONAL", "signal.latency_requirement=realtime", _field_provenance(signal, "latency_requirement"))
    elif signal.latency_requirement == "batch":
        add("INTERACTION_BATCH", "signal.latency_requirement=batch", _field_provenance(signal, "latency_requirement"))
    else:
        add("INTERACTION_CONVERSATIONAL", "signal.latency_requirement=near_realtime", _field_provenance(signal, "latency_requirement"))

    if signal.expected_scale == "enterprise":
        add("HIGH_SCALE_VOLUME", "signal.expected_scale=enterprise", _field_provenance(signal, "expected_scale"))

    if signal.automation_level == "autonomous":
        add("ACTION_REQUIRED", "signal.automation_level=autonomous", _field_provenance(signal, "automation_level"))
        add("PARALLEL_INDEPENDENT_SUBTASKS", "signal.automation_level=autonomous", "model_inference")
    elif "workflow" in signal.tags or "agentic" in signal.tags:
        add("ACTION_REQUIRED", "tags include workflow/agentic", "model_inference")

    if "reasoning" in signal.tags or "multi-step" in signal.tags:
        add("TASK_DECOMPOSITION_REQUIRED", "tags include reasoning/multi-step", "model_inference")

    if not signal.tags and not signal.integration_points:
        add("ENTERPRISE_PRIVATE_DATA", "no corpus/system signals present", "model_inference")

    lowered_text = raw_text.lower()
    if "ACTION_REQUIRED" in signatures and any(phrase in lowered_text for phrase in _DEFERRED_ACTION_PHRASES):
        del signatures["ACTION_REQUIRED"]
        add("ACTION_REQUIRED_DEFERRED", "deferred-action phrasing in request text", "model_inference")
    elif any(phrase in lowered_text for phrase in _DEFERRED_ACTION_PHRASES) and any(
        w in lowered_text for w in ("action", "act on", "execute", "tool", "workflow", "automate")
    ):
        add("ACTION_REQUIRED_DEFERRED", "deferred-action phrasing in request text", "model_inference")

    return list(signatures.values())


def build_assumptions(signal: SignalVector, solution_assumptions: list[str]) -> list[Assumption]:
    """Any signal field the LLM inferred or the system defaulted, and any
    detected solution-shaped language, becomes an explicit, visible
    Assumption — the load-bearing rule from Part 10.2: MODEL_INFERENCE
    claims may not silently support a decision."""
    assumptions: list[Assumption] = []
    for field, provenance in signal.field_provenance.items():
        if provenance in ("llm", "default"):
            assumptions.append(
                Assumption(
                    id=f"ASM-{field.upper()}",
                    field=field,
                    statement=f"'{field}' was {'inferred by the model' if provenance == 'llm' else 'not specified and defaulted'} "
                    f"to '{getattr(signal, field, '?')}'; confirm before treating this as a firm requirement.",
                )
            )
    for idx, note in enumerate(solution_assumptions, start=1):
        assumptions.append(Assumption(id=f"ASM-SOLUTION-{idx}", field="problem_framing", statement=note))
    return assumptions
