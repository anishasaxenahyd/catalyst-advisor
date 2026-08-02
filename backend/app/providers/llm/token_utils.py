"""Approximate token counting for the prompt optimizer.

There's no local tokenizer for Llama models (Groq doesn't expose one, and
`tiktoken` is calibrated for OpenAI's BPE, not Llama's — pulling it in would
buy false precision, not accuracy). This uses the standard rough heuristic
for English text instead: ~4 characters per token. It's good enough to show
a user a before/after trend on the optimizer panel; it is never treated as
an exact count, and never trusted from an LLM's own claimed token usage.
"""

_CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, round(len(stripped) / _CHARS_PER_TOKEN))
