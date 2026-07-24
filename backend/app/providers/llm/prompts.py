"""Prompt templates for the two operations any LLMProvider performs.

Vendor-neutral by design — a single shared source so switching providers
never means maintaining two copies of the same prompt.
"""

SIGNAL_VECTOR_PROMPT = """You are extracting a structured signal vector from an enterprise AI use case description. Read the input below and respond with ONLY a JSON object matching this exact shape (no markdown fences, no commentary):

{{
  "use_case_type": string (a short label for the use case),
  "industry": string,
  "data_sensitivity": "none" | "pii" | "phi",
  "data_modality": "text" | "image" | "structured" | "mixed",
  "latency_requirement": "batch" | "near_realtime" | "realtime",
  "expected_scale": "pilot" | "department" | "enterprise",
  "automation_level": "assist" | "copilot" | "autonomous",
  "integration_points": string[],
  "tags": string[]
}}

Where the user already supplied a structured hint, use it verbatim rather than re-inferring it: {hints}

For "tags": choose ONLY from this fixed vocabulary — these are the only values the downstream scoring engine can match against, so a tag outside this list is worse than no tag at all. Include every one that plausibly applies; omit any that don't:
{known_tags}

Input:
\"\"\"{text}\"\"\"
"""

NARRATIVE_PROMPT = """You are writing the prose sections of an enterprise AI executive report. A deterministic recommendation engine has already decided every fact below — you are NOT choosing or changing any recommendation, only explaining it in polished executive language. Respond with ONLY a JSON object matching this exact shape (no markdown fences, no commentary):

{{
  "executive_summary": string (3-5 sentences),
  "risks": string[],
  "assumptions": string[],
  "next_best_actions": string[]
}}

Decided facts (do not contradict any of these):
{engine_output}
"""
