"""Tests for explainer reasoning generation."""

from api.schemas.result import ScoreBreakdown
from pipeline.explanation.explainer import generate_reasoning


def test_reasoning_references_candidate_data(strong_ai_candidate):
    """Reasoning should reference specific facts from the candidate's profile."""
    breakdown = ScoreBreakdown(
        career_fit=85.0, skill_match=70.0, behavioral=80.0,
        semantic_similarity=75.0, education=60.0, experience_fit=90.0,
    )
    reasoning = generate_reasoning(
        candidate=strong_ai_candidate,
        rank=1,
        score=85.0,
        breakdown=breakdown,
    )
    assert len(reasoning) > 30, "Reasoning too short"
    # Should mention their company or title
    assert (
        "AI Startup Co" in reasoning
        or "Machine Learning Engineer" in reasoning
        or "6.5" in reasoning
    ), f"Reasoning doesn't reference candidate data: {reasoning}"


def test_reasoning_varies_by_rank(strong_ai_candidate, weak_candidate):
    """Different candidates at different ranks should get different reasoning."""
    breakdown = ScoreBreakdown()
    r1 = generate_reasoning(strong_ai_candidate, rank=1, score=90, breakdown=breakdown)
    r2 = generate_reasoning(weak_candidate, rank=80, score=20, breakdown=breakdown)
    assert r1 != r2, "Reasoning should vary between candidates"


def test_honeypot_reasoning(honeypot_candidate):
    """Honeypot reasoning should mention data integrity concerns."""
    breakdown = ScoreBreakdown()
    reasoning = generate_reasoning(
        honeypot_candidate, rank=99, score=0.0, breakdown=breakdown,
        is_honeypot=True, honeypot_reasons=["10 expert skills with 0 months duration"],
    )
    assert "integrity" in reasoning.lower() or "flagged" in reasoning.lower(), (
        f"Honeypot reasoning doesn't mention data issues: {reasoning}"
    )
