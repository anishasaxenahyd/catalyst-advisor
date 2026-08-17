from app.models.schemas import PromptOptimizationResult, RawInput, SignalVector, StructuredHints
from app.providers.llm.base import LLMProvider
from app.providers.llm.fallback_provider import FallbackLLMProvider

_SIGNAL = SignalVector(
    use_case_type="test",
    industry="cross-industry",
    data_sensitivity="none",
    data_modality="text",
    latency_requirement="near_realtime",
    expected_scale="department",
    automation_level="assist",
)

_RAW_INPUT = RawInput(mode="idea", text="test input", hints=StructuredHints())


class _FakeProvider(LLMProvider):
    """Test double — raises on the Nth call if configured, else returns a
    tagged result so we can tell which provider actually answered."""

    def __init__(self, name: str, fail_times: int = 0):
        self.name = name
        self.fail_times = fail_times
        self.calls = 0

    def extract_signal_vector(self, raw_input: RawInput) -> SignalVector:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError(f"{self.name} is unavailable")
        return _SIGNAL.model_copy(update={"use_case_type": self.name})

    def generate_executive_report(self, engine_output):  # pragma: no cover - unused in these tests
        raise NotImplementedError

    def optimize_prompt(self, raw_input: RawInput, prior_answers):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError(f"{self.name} is unavailable")
        return PromptOptimizationResult(
            optimized_text=self.name,
            original_token_estimate=1,
            optimized_token_estimate=1,
        )

    def narrate_kernel_findings(self, narration_input):  # pragma: no cover - unused in these tests
        raise NotImplementedError


def test_primary_success_never_touches_fallback():
    primary = _FakeProvider("primary", fail_times=0)
    fallback = _FakeProvider("fallback", fail_times=0)
    provider = FallbackLLMProvider(primary=primary, fallback=fallback)

    result = provider.extract_signal_vector(_RAW_INPUT)

    assert result.use_case_type == "primary"
    assert primary.calls == 1
    assert fallback.calls == 0


def test_primary_failure_falls_back():
    primary = _FakeProvider("primary", fail_times=99)
    fallback = _FakeProvider("fallback", fail_times=0)
    provider = FallbackLLMProvider(primary=primary, fallback=fallback)

    result = provider.extract_signal_vector(_RAW_INPUT)

    assert result.use_case_type == "fallback"
    assert primary.calls == 1
    assert fallback.calls == 1


def test_both_failing_propagates_fallbacks_error():
    primary = _FakeProvider("primary", fail_times=99)
    fallback = _FakeProvider("fallback", fail_times=99)
    provider = FallbackLLMProvider(primary=primary, fallback=fallback)

    try:
        provider.extract_signal_vector(_RAW_INPUT)
        assert False, "expected an exception when both providers fail"
    except RuntimeError as exc:
        assert "fallback is unavailable" in str(exc)


def test_optimize_prompt_falls_back_on_primary_failure():
    primary = _FakeProvider("primary", fail_times=99)
    fallback = _FakeProvider("fallback", fail_times=0)
    provider = FallbackLLMProvider(primary=primary, fallback=fallback)

    result = provider.optimize_prompt(_RAW_INPUT, [])

    assert result.optimized_text == "fallback"
    assert primary.calls == 1
    assert fallback.calls == 1
