"""Tests for skill scoring."""

from pipeline.scoring.skill_scorer import score_skills


def test_strong_candidate_high_skill_score(strong_ai_candidate):
    """Strong AI candidate should match many required skills."""
    score, details = score_skills(strong_ai_candidate)
    assert score > 0.4, f"Strong candidate skill score too low: {score}"
    assert details["required_score"] > 0.3, f"Required skill match too low: {details}"


def test_weak_candidate_low_skill_score(weak_candidate):
    """Marketing manager with AI keywords should still score low due to context validation."""
    score, details = score_skills(weak_candidate)
    # Even though they have NLP/PyTorch listed, career context doesn't support it
    assert score < 0.5, f"Keyword stuffer skill score too high: {score}, details: {details}"


def test_skill_score_in_range(strong_ai_candidate):
    """Skill score should be between 0 and 1."""
    score, _ = score_skills(strong_ai_candidate)
    assert 0.0 <= score <= 1.0
