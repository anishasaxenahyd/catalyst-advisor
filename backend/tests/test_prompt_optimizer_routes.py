import os

os.environ["LLM_PROVIDER"] = "mock"

from fastapi.testclient import TestClient

from app.main import app
from app.providers.llm.factory import get_llm_provider

client = TestClient(app)


def setup_function():
    get_llm_provider.cache_clear()


def test_optimize_prompt_returns_result_with_gaps():
    response = client.post(
        "/api/prompt-optimizer",
        json={"mode": "idea", "description": "Automate invoice review for the finance team.", "hints": {}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["optimized_text"]
    assert body["original_token_estimate"] > 0
    assert "industry" in body["gaps"]


def test_optimize_prompt_rejects_empty_description():
    response = client.post("/api/prompt-optimizer", json={"mode": "idea", "description": "   ", "hints": {}})

    assert response.status_code == 400


def test_optimize_prompt_carries_prior_answers():
    response = client.post(
        "/api/prompt-optimizer",
        json={
            "mode": "idea",
            "description": "Automate invoice review.",
            "hints": {},
            "prior_answers": [{"field": "industry", "question": "What industry?", "answer": "Finance"}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "industry" not in body["gaps"]
