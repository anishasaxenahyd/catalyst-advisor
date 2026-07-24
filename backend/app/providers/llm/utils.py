"""Small helpers shared by the vendor provider implementations only.
Never imported by engine/ or api/."""

import re


def strip_json_fences(text: str) -> str:
    """Some vendors wrap JSON in ```json ... ``` despite instructions not to."""
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    return match.group(1) if match else text.strip()
