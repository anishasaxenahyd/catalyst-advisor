from app.engine.readiness import compute_implementation_readiness
from app.models.schemas import ConfidenceScores, FeasibilityScore


def test_high_confidence_low_complexity_yields_very_high_readiness():
    feasibility = FeasibilityScore(technical=95, business=95)
    confidence = ConfidenceScores(overall=98, architecture=98, model=98, workbench=98)
    readiness = compute_implementation_readiness(feasibility, confidence, complexity_tier=1)
    assert readiness.score >= 95
    assert readiness.label == "Very High"


def test_low_confidence_high_complexity_yields_needs_more_information():
    feasibility = FeasibilityScore(technical=40, business=40)
    confidence = ConfidenceScores(overall=40, architecture=40, model=40, workbench=40)
    readiness = compute_implementation_readiness(feasibility, confidence, complexity_tier=5)
    assert readiness.score < 80
    assert readiness.label == "Needs More Information"


def test_higher_complexity_tier_lowers_readiness_all_else_equal():
    feasibility = FeasibilityScore(technical=80, business=80)
    confidence = ConfidenceScores(overall=80, architecture=80, model=80, workbench=80)
    low_complexity = compute_implementation_readiness(feasibility, confidence, complexity_tier=1)
    high_complexity = compute_implementation_readiness(feasibility, confidence, complexity_tier=5)
    assert low_complexity.score > high_complexity.score
