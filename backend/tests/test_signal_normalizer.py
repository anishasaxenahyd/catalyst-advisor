from app.models.schemas import RawExtractedSignal, StructuredHints
from app.validation.signal_normalizer import describe_confidence, missing_information, normalize_signal

_KNOWN_TAGS = ["document-heavy", "realtime", "low-latency", "agentic", "batch"]


def _extracted(**overrides) -> RawExtractedSignal:
    base = dict(
        use_case_type="Support copilot",
        industry="Retail",
        data_sensitivity="none",
        data_modality="text",
        latency_requirement="realtime",
        expected_scale="department",
        automation_level="copilot",
        integration_points=[],
        tags=[],
    )
    base.update(overrides)
    return RawExtractedSignal(**base)


def test_valid_enum_values_pass_through_as_llm_provenance():
    signal = normalize_signal(_extracted(), hints=StructuredHints(), known_tags=_KNOWN_TAGS)

    assert signal.data_sensitivity == "none"
    assert signal.field_provenance["data_sensitivity"] == "llm"
    assert signal.validation_warnings == []


def test_casing_and_whitespace_are_normalized_with_a_warning():
    signal = normalize_signal(
        _extracted(data_sensitivity=" PII ", expected_scale="Enterprise"),
        hints=StructuredHints(),
        known_tags=_KNOWN_TAGS,
    )

    assert signal.data_sensitivity == "pii"
    assert signal.expected_scale == "enterprise"
    assert signal.field_provenance["data_sensitivity"] == "llm"
    reasons = [w.reason for w in signal.validation_warnings]
    assert any("Normalized casing" in r for r in reasons)


def test_separator_insensitive_matching_recovers_hyphenated_variants():
    # "Near-Realtime" should resolve to the canonical "near_realtime", not
    # get rejected just because the LLM used a hyphen instead of underscore.
    signal = normalize_signal(
        _extracted(latency_requirement="Near-Realtime"), hints=StructuredHints(), known_tags=_KNOWN_TAGS
    )
    assert signal.latency_requirement == "near_realtime"
    assert signal.field_provenance["latency_requirement"] == "llm"


def test_unknown_enum_value_defaults_with_warning():
    signal = normalize_signal(
        _extracted(data_sensitivity="super-secret"), hints=StructuredHints(), known_tags=_KNOWN_TAGS
    )

    assert signal.data_sensitivity == "none"  # the configured default
    assert signal.field_provenance["data_sensitivity"] == "default"
    reasons = [w.reason for w in signal.validation_warnings]
    assert any("not a recognized data_sensitivity" in r for r in reasons)


def test_missing_value_defaults_with_warning():
    signal = normalize_signal(_extracted(automation_level=None), hints=StructuredHints(), known_tags=_KNOWN_TAGS)

    assert signal.automation_level == "assist"
    assert signal.field_provenance["automation_level"] == "default"
    reasons = [w.reason for w in signal.validation_warnings]
    assert any("No automation_level extracted" in r for r in reasons)


def test_user_hint_overrides_llm_value_and_is_recorded():
    signal = normalize_signal(
        _extracted(data_sensitivity="none"),
        hints=StructuredHints(data_sensitivity="phi"),
        known_tags=_KNOWN_TAGS,
    )

    assert signal.data_sensitivity == "phi"
    assert signal.field_provenance["data_sensitivity"] == "user"
    reasons = [w.reason for w in signal.validation_warnings]
    assert any("takes precedence" in r for r in reasons)


def test_user_hint_matching_llm_value_produces_no_override_warning():
    signal = normalize_signal(
        _extracted(expected_scale="enterprise"),
        hints=StructuredHints(expected_scale="enterprise"),
        known_tags=_KNOWN_TAGS,
    )

    assert signal.expected_scale == "enterprise"
    assert signal.field_provenance["expected_scale"] == "user"
    assert signal.validation_warnings == []


def test_tags_are_deduplicated_and_normalized():
    signal = normalize_signal(
        _extracted(tags=["realtime", "Realtime", " realtime ", "low-latency"]),
        hints=StructuredHints(),
        known_tags=_KNOWN_TAGS,
    )

    assert signal.tags == ["realtime", "low-latency"]
    reasons = [w.reason for w in signal.validation_warnings]
    assert any("duplicate tag" in r for r in reasons)


def test_tags_outside_known_vocabulary_are_rejected_with_warning():
    signal = normalize_signal(
        _extracted(tags=["realtime", "customer support", "retail"]),
        hints=StructuredHints(),
        known_tags=_KNOWN_TAGS,
    )

    assert signal.tags == ["realtime"]
    reasons = [w.reason for w in signal.validation_warnings]
    assert any("Discarded 2 tag(s)" in r for r in reasons)


def test_empty_known_tags_falls_back_to_light_cleaning_only():
    signal = normalize_signal(
        _extracted(tags=["Custom Tag", "custom tag"]), hints=StructuredHints(), known_tags=[]
    )
    # no vocabulary to check against — still cleaned, lowercased, and deduped
    assert signal.tags == ["custom tag"]


def test_integration_points_deduplicated_case_insensitively():
    signal = normalize_signal(
        _extracted(integration_points=["Salesforce", "salesforce", " Salesforce "]),
        hints=StructuredHints(),
        known_tags=_KNOWN_TAGS,
    )
    assert signal.integration_points == ["Salesforce"]


def test_industry_prefers_hint_over_llm_over_default():
    hinted = normalize_signal(
        _extracted(industry="Retail"), hints=StructuredHints(industry="Healthcare"), known_tags=_KNOWN_TAGS
    )
    assert hinted.industry == "Healthcare"
    assert hinted.field_provenance["industry"] == "user"

    inferred = normalize_signal(_extracted(industry="Retail"), hints=StructuredHints(), known_tags=_KNOWN_TAGS)
    assert inferred.industry == "Retail"
    assert inferred.field_provenance["industry"] == "llm"

    defaulted = normalize_signal(_extracted(industry=None), hints=StructuredHints(), known_tags=_KNOWN_TAGS)
    assert defaulted.industry == "cross-industry"
    assert defaulted.field_provenance["industry"] == "default"


def test_blank_use_case_type_falls_back_to_placeholder():
    signal = normalize_signal(_extracted(use_case_type="   "), hints=StructuredHints(), known_tags=_KNOWN_TAGS)
    assert signal.use_case_type == "Unspecified use case"


def test_missing_information_reflects_only_defaulted_fields():
    signal = normalize_signal(
        _extracted(data_sensitivity="bogus", industry=None),
        hints=StructuredHints(),
        known_tags=_KNOWN_TAGS,
    )
    missing = missing_information(signal.field_provenance)
    assert set(missing) == {"data_sensitivity", "industry"}


def test_describe_confidence_mentions_each_provenance_bucket_present():
    provenance = {
        "data_sensitivity": "user",
        "data_modality": "llm",
        "latency_requirement": "llm",
        "expected_scale": "default",
        "automation_level": "default",
        "industry": "default",
    }
    text = describe_confidence(provenance)
    assert "1 user-provided" in text
    assert "2 LLM-inferred" in text
    assert "3 defaulted" in text
