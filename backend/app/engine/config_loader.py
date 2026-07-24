"""Loads scoring weights and decision rules from config JSON.

No scoring weight or threshold is hardcoded anywhere in `engine/` — every
number that shapes a recommendation lives in `data/config/*.json` and comes
through here. Retuning the engine's behavior means editing JSON, not code.
"""

import json
from functools import lru_cache
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[2] / "data" / "config"


@lru_cache(maxsize=1)
def get_scoring_weights() -> dict[str, float]:
    with (CONFIG_DIR / "scoring_weights.json").open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_decision_rules() -> dict:
    with (CONFIG_DIR / "decision_rules.json").open("r", encoding="utf-8") as f:
        return json.load(f)
