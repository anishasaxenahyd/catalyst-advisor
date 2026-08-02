"""Prompt templates for the operations any LLMProvider performs.

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

PROMPT_OPTIMIZER_PROMPT = """You are a prompt optimizer for an enterprise AI solution advisor. Your job is NOT to recommend anything — a separate deterministic engine owns that decision. Your job is to (1) rewrite the user's input into a denser, clearer prompt that will be fed to that engine's extraction step, and (2) flag which specific facts are still missing so the engine doesn't have to silently guess.

Rewrite rules:
- Preserve every fact already present — never invent details that weren't stated or answered.
- Fold in any prior question/answer exchanges below as if the user had said them originally.
- Cut filler and redundancy; do not pad the rewrite to sound more impressive.
- If the input is already tight, return it close to unchanged rather than padding it.

Gap-detection rules — check specifically whether each of these tracked fields is answered clearly by the text, hints, or prior answers below:
{tracked_fields}

For any field that is still ambiguous or unstated, list it in "gaps". For at most the 3 highest-impact gaps, write one short, specific clarifying question each (grounded in the user's actual scenario, not generic).

Respond with ONLY a JSON object matching this exact shape (no markdown fences, no commentary):

{{
  "optimized_text": string,
  "gaps": string[] (subset of the tracked field names above),
  "questions": [{{"field": string, "question": string}}] (at most 3),
  "notes": string (one short sentence on what changed, or "")
}}

Structured hints already supplied by the user (treat as ground truth, do not ask about these again): {hints}

Prior clarifying questions already asked and answered this session (fold these into the rewrite, do not ask again): {prior_answers}

Input:
\"\"\"{text}\"\"\"
"""
