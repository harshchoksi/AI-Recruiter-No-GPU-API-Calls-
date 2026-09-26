"""Tests for career scoring."""

from pipeline.scoring.career_scorer import score_career


def test_strong_candidate_high_career_score(strong_ai_candidate):
    """Strong AI candidate should score high on career fit."""
    score, details = score_career(strong_ai_candidate)
    assert score > 0.6, f"Strong candidate career score too low: {score}, details: {details}"
    assert details["title_relevance"] > 0.7, f"Title relevance too low: {details}"
    assert details["production_ai_experience"] > 0.5, f"Prod AI too low: {details}"


def test_weak_candidate_low_career_score(weak_candidate):
    """Marketing manager should score low on career fit."""
    score, details = score_career(weak_candidate)
    assert score < 0.3, f"Weak candidate career score too high: {score}, details: {details}"
    assert details["title_relevance"] < 0.2, f"Title relevance too high for Marketing Manager"


def test_career_score_range(strong_ai_candidate, weak_candidate):
    """Strong should score significantly higher than weak."""
    strong_score, _ = score_career(strong_ai_candidate)
    weak_score, _ = score_career(weak_candidate)
    assert strong_score > weak_score + 0.3, (
        f"Insufficient separation: strong={strong_score}, weak={weak_score}"
    )
