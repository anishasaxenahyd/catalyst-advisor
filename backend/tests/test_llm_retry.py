from app.providers.llm.retry import RetryConfig, call_with_retries


class _FlakyError(Exception):
    pass


class _OtherError(Exception):
    pass


def test_retries_transient_error_until_success():
    calls = {"n": 0}

    def flaky_then_ok():
        calls["n"] += 1
        if calls["n"] < 3:
            raise _FlakyError("not yet")
        return "ok"

    result = call_with_retries(
        flaky_then_ok,
        retryable=(_FlakyError,),
        config=RetryConfig(max_attempts=5, base_delay_seconds=0.001, max_delay_seconds=0.01),
        op_name="test",
    )

    assert result == "ok"
    assert calls["n"] == 3


def test_exhausts_attempts_and_raises_last_error():
    calls = {"n": 0}

    def always_fails():
        calls["n"] += 1
        raise _FlakyError(f"failure {calls['n']}")

    try:
        call_with_retries(
            always_fails,
            retryable=(_FlakyError,),
            config=RetryConfig(max_attempts=3, base_delay_seconds=0.001, max_delay_seconds=0.01),
            op_name="test",
        )
        assert False, "expected _FlakyError to propagate"
    except _FlakyError as exc:
        assert "failure 3" in str(exc)

    assert calls["n"] == 3


def test_non_retryable_error_propagates_on_first_attempt():
    calls = {"n": 0}

    def raises_other():
        calls["n"] += 1
        raise _OtherError("not transient")

    try:
        call_with_retries(
            raises_other,
            retryable=(_FlakyError,),
            config=RetryConfig(max_attempts=5, base_delay_seconds=0.001, max_delay_seconds=0.01),
            op_name="test",
        )
        assert False, "expected _OtherError to propagate"
    except _OtherError:
        pass

    assert calls["n"] == 1
