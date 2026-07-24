"""The Validation/Normalization layer — sits between an LLMProvider's raw
extraction and the deterministic engine. Every provider (Groq, Mock) routes
its extraction through `normalize_signal()` instead of constructing
`SignalVector` directly, so neither can hand the engine an unvalidated,
wrongly-cased, duplicated, or unmatchable value — and any future provider
gets that guarantee for free from one shared implementation.

This module is deliberately pure: no I/O, no vendor knowledge, nothing
non-deterministic. It is the reason the rest of the pipeline can trust
`SignalVector` completely, no matter which provider — or how sloppy that
provider's output was — produced it.

Design choice worth calling out: user-supplied `StructuredHints` always win
over whatever the LLM inferred for the same field. The prompt already asks
providers to echo hints verbatim, but nothing enforced that until now — an
LLM that ignores the instruction no longer gets a silent pass.
"""

from collections import Counter

from app.models.schemas import RawExtractedSignal, SignalVector, StructuredHints, ValidationWarning

# The scalar fields tracked for provenance / confidence purposes. Tags and
# integration_points are lists with no single "value", so they're cleaned
# (normalized, deduped, vocabulary-checked) but not provenance-tracked.
TRACKED_FIELDS: tuple[str, ...] = (
    "data_sensitivity",
    "data_modality",
    "latency_requirement",
    "expected_scale",
    "automation_level",
    "industry",
)

_ALLOWED_VALUES: dict[str, set[str]] = {
    "data_sensitivity": {"none", "pii", "phi"},
    "data_modality": {"text", "image", "structured", "mixed"},
    "latency_requirement": {"batch", "near_realtime", "realtime"},
    "expected_scale": {"pilot", "department", "enterprise"},
    "automation_level": {"assist", "copilot", "autonomous"},
}

_DEFAULTS: dict[str, str] = {
    "data_sensitivity": "none",
    "data_modality": "text",
    "latency_requirement": "near_realtime",
    "expected_scale": "department",
    "automation_level": "assist",
    "industry": "cross-industry",
}

_PROVENANCE_LABEL = {"user": "user-provided", "llm": "LLM-inferred", "default": "defaulted"}


def _match_token(raw: str | None, vocabulary: set[str] | list[str]) -> str | None:
    """Case/whitespace/separator-insensitive match against a fixed
    vocabulary. Matches "PII", " pii ", "Near-Realtime", "near realtime"
    to their canonical forms; returns None for anything that isn't
    recognizably one of the allowed values (that's a reject, not a fuzzy
    guess — we don't want to silently map "dept" to "department")."""
    if not raw or not raw.strip():
        return None
    candidate = "_".join(raw.strip().lower().split()).replace("-", "_")
    vocab = set(vocabulary)
    if candidate in vocab:
        return candidate
    compact = candidate.replace("_", "")
    for value in vocab:
        if value.replace("-", "").replace("_", "") == compact:
            return value
    return None


def _clean_text(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = " ".join(value.strip().split())
    return cleaned or None


def _resolve_enum_field(
    field: str,
    extracted_value: str | None,
    hint_value: str | None,
    warnings: list[ValidationWarning],
) -> tuple[str, str]:
    """Returns (resolved_value, provenance) for one of the five enum
    fields. Hints always win; the LLM's value is used if it matches the
    known vocabulary (after normalization); otherwise the field defaults."""
    allowed = _ALLOWED_VALUES[field]

    if hint_value is not None:
        matched_llm = _match_token(extracted_value, allowed)
        if matched_llm and matched_llm != hint_value:
            warnings.append(
                ValidationWarning(
                    field=field,
                    original_value=extracted_value,
                    corrected_value=hint_value,
                    reason=f"User-provided hint '{hint_value}' takes precedence over LLM-inferred '{matched_llm}'.",
                )
            )
        return hint_value, "user"

    matched = _match_token(extracted_value, allowed)
    if matched is not None:
        if extracted_value is not None and matched != extracted_value:
            warnings.append(
                ValidationWarning(
                    field=field,
                    original_value=extracted_value,
                    corrected_value=matched,
                    reason="Normalized casing/whitespace/separators to a recognized value.",
                )
            )
        return matched, "llm"

    default = _DEFAULTS[field]
    reason = (
        f"'{extracted_value}' is not a recognized {field} (expected one of {sorted(allowed)}); defaulted to '{default}'."
        if extracted_value
        else f"No {field} extracted; defaulted to '{default}'."
    )
    warnings.append(
        ValidationWarning(field=field, original_value=extracted_value, corrected_value=default, reason=reason)
    )
    return default, "default"


def _resolve_industry(
    extracted_value: str | None, hint_value: str | None, warnings: list[ValidationWarning]
) -> tuple[str, str]:
    if hint_value:
        cleaned_hint = _clean_text(hint_value) or _DEFAULTS["industry"]
        return cleaned_hint, "user"

    cleaned = _clean_text(extracted_value)
    if cleaned:
        return cleaned, "llm"

    warnings.append(
        ValidationWarning(
            field="industry",
            original_value=extracted_value,
            corrected_value=_DEFAULTS["industry"],
            reason="No industry specified; defaulted to cross-industry.",
        )
    )
    return _DEFAULTS["industry"], "default"


def _resolve_tags(raw_tags: list[str], known_tags: list[str], warnings: list[ValidationWarning]) -> list[str]:
    seen: set[str] = set()
    resolved: list[str] = []
    rejected: list[str] = []
    duplicate_count = 0

    for raw in raw_tags:
        if known_tags:
            matched = _match_token(raw, known_tags)
        else:
            cleaned = _clean_text(raw)
            matched = cleaned.lower() if cleaned else None
        if matched is None:
            if raw and raw.strip():
                rejected.append(raw)
            continue
        if matched in seen:
            duplicate_count += 1
            continue
        seen.add(matched)
        resolved.append(matched)

    if rejected:
        warnings.append(
            ValidationWarning(
                field="tags",
                original_value=", ".join(rejected),
                corrected_value=None,
                reason=f"Discarded {len(rejected)} tag(s) not in the known Catalog vocabulary: {rejected}.",
            )
        )
    if duplicate_count:
        warnings.append(
            ValidationWarning(
                field="tags",
                original_value=None,
                corrected_value=None,
                reason=f"Removed {duplicate_count} duplicate tag(s).",
            )
        )
    return resolved


def _resolve_integration_points(raw_points: list[str]) -> list[str]:
    seen: set[str] = set()
    resolved: list[str] = []
    for raw in raw_points:
        cleaned = _clean_text(raw)
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            resolved.append(cleaned)
    return resolved


def normalize_signal(
    extracted: RawExtractedSignal, *, hints: StructuredHints, known_tags: list[str]
) -> SignalVector:
    warnings: list[ValidationWarning] = []
    provenance: dict[str, str] = {}

    data_sensitivity, provenance["data_sensitivity"] = _resolve_enum_field(
        "data_sensitivity", extracted.data_sensitivity, hints.data_sensitivity, warnings
    )
    data_modality, provenance["data_modality"] = _resolve_enum_field(
        "data_modality", extracted.data_modality, None, warnings
    )
    latency_requirement, provenance["latency_requirement"] = _resolve_enum_field(
        "latency_requirement", extracted.latency_requirement, None, warnings
    )
    expected_scale, provenance["expected_scale"] = _resolve_enum_field(
        "expected_scale", extracted.expected_scale, hints.expected_scale, warnings
    )
    automation_level, provenance["automation_level"] = _resolve_enum_field(
        "automation_level", extracted.automation_level, hints.automation_level, warnings
    )
    industry, provenance["industry"] = _resolve_industry(extracted.industry, hints.industry, warnings)

    tags = _resolve_tags(extracted.tags, known_tags, warnings)
    integration_points = _resolve_integration_points(extracted.integration_points)
    use_case_type = _clean_text(extracted.use_case_type) or "Unspecified use case"

    return SignalVector(
        use_case_type=use_case_type,
        industry=industry,
        data_sensitivity=data_sensitivity,
        data_modality=data_modality,
        latency_requirement=latency_requirement,
        expected_scale=expected_scale,
        automation_level=automation_level,
        integration_points=integration_points,
        tags=tags,
        field_provenance=provenance,
        validation_warnings=warnings,
    )


def missing_information(field_provenance: dict[str, str]) -> list[str]:
    """Tracked fields that fell all the way through to a default —
    surfaced on DecisionTrace so a reviewer can see what the recommendation
    is silently assuming."""
    return [f for f in TRACKED_FIELDS if field_provenance.get(f) == "default"]


def describe_confidence(field_provenance: dict[str, str]) -> str:
    counts = Counter(field_provenance.get(f, "default") for f in TRACKED_FIELDS)
    parts = [
        f"{counts[key]} {_PROVENANCE_LABEL[key]}"
        for key in ("user", "llm", "default")
        if counts[key]
    ]
    return f"Signal confidence reflects {', '.join(parts)} out of {len(TRACKED_FIELDS)} tracked fields."
