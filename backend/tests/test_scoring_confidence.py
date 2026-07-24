from app.engine.config_loader import get_decision_rules, get_scoring_weights
from app.engine.scoring import score_item
from app.models.schemas import SignalVector
from app.validation.signal_normalizer import TRACKED_FIELDS


class _DummyItem:
    """Only carries `suitable_for_tags`, so technical_fit is the only
    scored dimension — isolates the confidence calculation from the rest
    of score_item's weighted-sum logic."""

    def __init__(self, suitable_for_tags: list[str]):
        self.suitable_for_tags = suitable_for_tags


def _signal_with_provenance(provenance_value: str) -> SignalVector:
    return SignalVector(
        use_case_type="test",
        industry="cross-industry",
        data_sensitivity="none",
        data_modality="text",
        latency_requirement="realtime",
        expected_scale="department",
        automation_level="assist",
        tags=["realtime"],
        field_provenance={field: provenance_value for field in TRACKED_FIELDS},
    )


def test_all_user_provided_fields_yield_full_confidence():
    rules = get_decision_rules()
    weights = get_scoring_weights()
    signal = _signal_with_provenance("user")

    result = score_item(signal, _DummyItem(["realtime"]), weights, rules)

    assert result.weighted_total == 100.0
    assert result.confidence == 100.0


def test_all_defaulted_fields_yield_lower_but_nonzero_confidence():
    rules = get_decision_rules()
    weights = get_scoring_weights()
    signal = _signal_with_provenance("default")

    result = score_item(signal, _DummyItem(["realtime"]), weights, rules)

    floor = rules["confidence_completeness_floor"]
    default_weight = rules["provenance_confidence_weight"]["default"]
    expected_factor = floor + default_weight * (1 - floor)

    assert result.confidence == round(result.weighted_total * expected_factor, 1)
    assert result.confidence < 100.0
    assert result.confidence > 0.0  # floored, never reads as zero


def test_llm_inferred_confidence_sits_between_user_and_default():
    rules = get_decision_rules()
    weights = get_scoring_weights()

    user_result = score_item(_signal_with_provenance("user"), _DummyItem(["realtime"]), weights, rules)
    llm_result = score_item(_signal_with_provenance("llm"), _DummyItem(["realtime"]), weights, rules)
    default_result = score_item(_signal_with_provenance("default"), _DummyItem(["realtime"]), weights, rules)

    assert default_result.confidence < llm_result.confidence < user_result.confidence


def test_mixed_provenance_averages_correctly():
    rules = get_decision_rules()
    weights = get_scoring_weights()
    provenance = {field: "user" for field in TRACKED_FIELDS}
    # flip exactly one field to "default"
    provenance[TRACKED_FIELDS[0]] = "default"
    signal = SignalVector(
        use_case_type="test",
        industry="cross-industry",
        data_sensitivity="none",
        data_modality="text",
        latency_requirement="realtime",
        expected_scale="department",
        automation_level="assist",
        tags=["realtime"],
        field_provenance=provenance,
    )

    result = score_item(signal, _DummyItem(["realtime"]), weights, rules)

    weight_map = rules["provenance_confidence_weight"]
    floor = rules["confidence_completeness_floor"]
    n = len(TRACKED_FIELDS)
    avg = (weight_map["user"] * (n - 1) + weight_map["default"]) / n
    expected_factor = floor + avg * (1 - floor)

    assert result.confidence == round(result.weighted_total * expected_factor, 1)
