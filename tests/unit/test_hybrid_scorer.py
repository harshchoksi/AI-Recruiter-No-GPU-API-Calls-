"""Tests for the hybrid scorer."""

from pipeline.scoring.hybrid_scorer import compute_hybrid_score, score_experience_fit, score_education


def test_honeypot_zeroed(honeypot_candidate):
    """Honeypots should always get score 0."""
    score, breakdown = compute_hybrid_score(
        candidate=honeypot_candidate,
        semantic_score=0.9,
        career_score=0.8,
        skill_score=0.9,
        behavioral_score=0.7,
        is_honeypot=True,
    )
    assert score == 0.0, f"Honeypot should be zeroed but got {score}"


def test_strong_higher_than_weak(strong_ai_candidate, weak_candidate):
    """Strong candidate should score higher than weak."""
    strong_score, _ = compute_hybrid_score(
        candidate=strong_ai_candidate,
        semantic_score=0.8, career_score=0.9, skill_score=0.7,
        behavioral_score=0.8,
    )
    weak_score, _ = compute_hybrid_score(
        candidate=weak_candidate,
        semantic_score=0.3, career_score=0.1, skill_score=0.2,
        behavioral_score=0.2,
    )
    assert strong_score > weak_score + 20, (
        f"Insufficient separation: strong={strong_score}, weak={weak_score}"
    )


def test_experience_fit_ideal_range(strong_ai_candidate):
    """6.5 years should be in the ideal range (5-9)."""
    score, details = score_experience_fit(strong_ai_candidate)
    assert score == 1.0, f"6.5 yrs should be ideal fit, got {score}"


def test_experience_fit_below_range(weak_candidate):
    """Experience outside acceptable range should be penalized."""
    # weak_candidate has 12 years, above ideal
    score, _ = score_experience_fit(weak_candidate)
    assert score < 1.0, f"12 yrs should not be perfect fit, got {score}"


def test_score_range(strong_ai_candidate):
    """Final score should be 0-100."""
    score, _ = compute_hybrid_score(
        candidate=strong_ai_candidate,
        semantic_score=0.5, career_score=0.5, skill_score=0.5,
        behavioral_score=0.5,
    )
    assert 0 <= score <= 100
