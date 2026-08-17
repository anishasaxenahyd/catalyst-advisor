"""Loads decision rules from config JSON.

No threshold or band is hardcoded anywhere in `engine/` — every number that
shapes an estimate lives in `data/config/decision_rules.json` and comes
through here. Retuning behavior means editing JSON, not code. (The old
`get_scoring_weights()` was removed with the weighted-scoring engine it
served — see `app.kernel` for the elimination-based reasoning that replaced it.)
"""

import json
from functools import lru_cache
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[2] / "data" / "config"


@lru_cache(maxsize=1)
def get_decision_rules() -> dict:
    with (CONFIG_DIR / "decision_rules.json").open("r", encoding="utf-8") as f:
        return json.load(f)
