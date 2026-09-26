"""
Hybrid Scorer — combines all scoring signals into a final 0-100 score.

This is the final blending step that takes semantic similarity, career fit,
skill match, behavioral signals, and experience alignment, then produces
the single score used for ranking.
"""

from __future__ import annotations

from api.schemas.candidate import CandidateData
from api.schemas.result import ScoreBreakdown
from config.settings import IDEAL_YOE_MIN, IDEAL_YOE_MAX, ACCEPTABLE_YOE_MIN, ACCEPTABLE_YOE_MAX
from pipeline.scoring.weights import get_weights


def score_experience_fit(candidate: CandidateData) -> tuple[float, dict]:
    """Score how well the candidate's experience level fits the JD range."""
    yoe = candidate.profile.years_of_experience
    details = {"years_of_experience": yoe}

    if IDEAL_YOE_MIN <= yoe <= IDEAL_YOE_MAX:
        score = 1.0
    elif ACCEPTABLE_YOE_MIN <= yoe < IDEAL_YOE_MIN:
        # Below ideal but acceptable — linear ramp
        score = 0.5 + 0.5 * (yoe - ACCEPTABLE_YOE_MIN) / (IDEAL_YOE_MIN - ACCEPTABLE_YOE_MIN)
    elif IDEAL_YOE_MAX < yoe <= ACCEPTABLE_YOE_MAX:
        # Above ideal — gradually penalize
        score = 1.0 - 0.5 * (yoe - IDEAL_YOE_MAX) / (ACCEPTABLE_YOE_MAX - IDEAL_YOE_MAX)
    elif yoe < ACCEPTABLE_YOE_MIN:
        score = max(0.1, yoe / ACCEPTABLE_YOE_MIN * 0.5)
    else:
        score = max(0.1, 0.5 - 0.3 * (yoe - ACCEPTABLE_YOE_MAX) / 5.0)

    details["fit_score"] = round(score, 4)
    return round(score, 4), details


def score_education(candidate: CandidateData) -> tuple[float, dict]:
    """Score education alignment with the AI Engineer role."""
    details = {}

    if not candidate.education:
        return 0.3, {"note": "no education data"}

    best_score = 0.0
    for edu in candidate.education:
        field_lower = edu.field_of_study.lower()
        degree_lower = edu.degree.lower()

        # Field relevance
        if any(kw in field_lower for kw in ["machine learning", "artificial intelligence", "ai",
                                             "data science", "computer science", "cs",
                                             "information technology", "software"]):
            field_score = 0.9
        elif any(kw in field_lower for kw in ["mathematics", "statistics", "physics",
                                               "electrical", "electronics", "computational"]):
            field_score = 0.6
        elif any(kw in field_lower for kw in ["engineering"]):
            field_score = 0.4
        else:
            field_score = 0.2

        # Degree level
        if "ph.d" in degree_lower or "phd" in degree_lower:
            degree_mult = 1.0
        elif any(m in degree_lower for m in ["m.tech", "m.s", "m.sc", "m.e.", "master", "mba"]):
            degree_mult = 0.9
        elif any(b in degree_lower for b in ["b.tech", "b.e.", "b.sc", "b.s", "bachelor"]):
            degree_mult = 0.7
        else:
            degree_mult = 0.5

        # Institution tier
        tier = edu.tier or "unknown"
        tier_mult = {"tier_1": 1.0, "tier_2": 0.85, "tier_3": 0.7, "tier_4": 0.55, "unknown": 0.6}
        tier_score = tier_mult.get(tier, 0.6)

        combined = field_score * 0.5 + degree_mult * 0.3 + tier_score * 0.2
        if combined > best_score:
            best_score = combined
            details["best_match"] = {
                "institution": edu.institution,
                "field": edu.field_of_study,
                "degree": edu.degree,
                "tier": tier,
            }

    details["score"] = round(best_score, 4)
    return round(best_score, 4), details


def compute_hybrid_score(
    candidate: CandidateData,
    semantic_score: float,
    career_score: float,
    skill_score: float,
    behavioral_score: float,
    is_honeypot: bool = False,
    role_type: str = "startup",
) -> tuple[float, ScoreBreakdown]:
    """
    Compute the final hybrid score combining all signals.

    Args:
        candidate: Full candidate data
        semantic_score: Cosine similarity score (0-1)
        career_score: Career fit score (0-1)
        skill_score: Skill match score (0-1)
        behavioral_score: Behavioral signals score (0-1)
        is_honeypot: Whether the candidate is flagged as a honeypot
        role_type: Weight profile to use

    Returns:
        (final_score_0_100, breakdown)
    """
    if is_honeypot:
        breakdown = ScoreBreakdown()
        return 0.0, breakdown

    weights = get_weights(role_type)

    experience_score, _ = score_experience_fit(candidate)
    education_score, _ = score_education(candidate)

    breakdown = ScoreBreakdown(
        semantic_similarity=round(semantic_score * 100, 2),
        career_fit=round(career_score * 100, 2),
        skill_match=round(skill_score * 100, 2),
        behavioral=round(behavioral_score * 100, 2),
        education=round(education_score * 100, 2),
        experience_fit=round(experience_score * 100, 2),
    )

    final = (
        weights["semantic"] * semantic_score
        + weights["career"] * career_score
        + weights["skill"] * skill_score
        + weights["behavioral"] * behavioral_score
        + weights["education"] * education_score
        + weights["experience_fit"] * experience_score
    )

    # Scale to 0-100
    final_score = round(min(max(final * 100, 0.0), 100.0), 4)
    return final_score, breakdown
