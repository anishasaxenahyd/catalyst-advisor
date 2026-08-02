from app.providers.llm.token_utils import estimate_tokens


def test_empty_text_is_zero_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("   ") == 0


def test_short_text_is_at_least_one_token():
    assert estimate_tokens("hi") == 1


def test_longer_text_scales_roughly_with_length():
    short = estimate_tokens("a" * 40)
    long = estimate_tokens("a" * 400)
    assert long > short
    assert long == round(len("a" * 400) / 4)
