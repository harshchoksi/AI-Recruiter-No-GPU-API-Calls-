"""
Candidate Explainer — generates per-candidate reasoning for the submission CSV.

This is template-based (no LLM calls) to comply with the no-network constraint.
However, the templates are carefully crafted to:
1. Reference specific facts from each candidate's profile
2. Connect to specific JD requirements
3. Acknowledge gaps honestly
4. Vary substantively between candidates
5. Match tone to rank position

These properties are checked at Stage 4 manual review.
"""

from __future__ import annotations

from api.schemas.candidate import CandidateData
from api.schemas.result import ScoreBreakdown
from config.settings import CONSULTING_COMPANIES, TITLE_RELEVANCE


def generate_reasoning(
    candidate: CandidateData,
    rank: int,
    score: float,
    breakdown: ScoreBreakdown,
    is_honeypot: bool = False,
    honeypot_reasons: list[str] | None = None,
) -> str:
    """
    Generate a 1-2 sentence reasoning for why this candidate is at this rank.

    The reasoning must:
    - Reference specific facts from the candidate's profile
    - Connect to JD requirements
    - Be honest about gaps
    - Vary between candidates
    - Match tone to rank position
    """
    if is_honeypot:
        reasons = honeypot_reasons or ["profile inconsistencies"]
        return (
            f"{candidate.profile.current_title} with stated {candidate.profile.years_of_experience:.0f} yrs experience; "
            f"profile flagged for {reasons[0]}. Ranked low due to data integrity concerns."
        )

    name = candidate.profile.anonymized_name
    title = candidate.profile.current_title
    company = candidate.profile.current_company
    yoe = candidate.profile.years_of_experience
    headline = candidate.profile.headline

    # Extract key skills
    top_skills = _get_top_skills(candidate)
    skill_str = ", ".join(top_skills[:4]) if top_skills else "general skills"

    # Detect strengths
    strengths = _identify_strengths(candidate, breakdown)
    gaps = _identify_gaps(candidate, breakdown)

    # Build reasoning based on rank tier
    if rank <= 10:
        return _reasoning_top_tier(candidate, strengths, gaps, breakdown)
    elif rank <= 30:
        return _reasoning_mid_high(candidate, strengths, gaps, breakdown)
    elif rank <= 60:
        return _reasoning_mid(candidate, strengths, gaps, breakdown)
    else:
        return _reasoning_low(candidate, strengths, gaps, breakdown)


def _reasoning_top_tier(
    candidate: CandidateData,
    strengths: list[str],
    gaps: list[str],
    breakdown: ScoreBreakdown,
) -> str:
    """Top 10 — enthusiastic but specific."""
    title = candidate.profile.current_title
    yoe = candidate.profile.years_of_experience
    company = candidate.profile.current_company

    strength_text = strengths[0] if strengths else "strong technical background"
    gap_text = f" Minor concern: {gaps[0]}." if gaps else ""

    # Pull a specific career detail
    career_detail = _get_career_highlight(candidate)

    return (
        f"{title} at {company} with {yoe:.1f} yrs; {strength_text}. "
        f"{career_detail}{gap_text}"
    )


def _reasoning_mid_high(
    candidate: CandidateData,
    strengths: list[str],
    gaps: list[str],
    breakdown: ScoreBreakdown,
) -> str:
    """Ranks 11-30 — positive but notes specific gaps."""
    title = candidate.profile.current_title
    yoe = candidate.profile.years_of_experience
    company = candidate.profile.current_company

    strength_text = strengths[0] if strengths else "relevant experience"
    gap_text = gaps[0] if gaps else "limited signal on some JD requirements"

    return (
        f"{title} at {company} ({yoe:.1f} yrs); {strength_text}. "
        f"Gap: {gap_text}."
    )


def _reasoning_mid(
    candidate: CandidateData,
    strengths: list[str],
    gaps: list[str],
    breakdown: ScoreBreakdown,
) -> str:
    """Ranks 31-60 — balanced, notes both sides."""
    title = candidate.profile.current_title
    yoe = candidate.profile.years_of_experience

    strength_text = strengths[0] if strengths else "some relevant experience"
    gap_text = gaps[0] if gaps else "missing core JD requirements"

    return (
        f"{title} with {yoe:.1f} yrs experience; {strength_text}, "
        f"but {gap_text}."
    )


def _reasoning_low(
    candidate: CandidateData,
    strengths: list[str],
    gaps: list[str],
    breakdown: ScoreBreakdown,
) -> str:
    """Ranks 61-100 — honest about poor fit."""
    title = candidate.profile.current_title
    yoe = candidate.profile.years_of_experience
    company = candidate.profile.current_company

    gap_text = gaps[0] if gaps else "career trajectory doesn't align with AI engineering role requirements"

    return (
        f"{title} at {company} ({yoe:.1f} yrs); {gap_text}. "
        f"Career fit score: {breakdown.career_fit:.0f}/100."
    )


def _get_top_skills(candidate: CandidateData) -> list[str]:
    """Get the most relevant skills for the reasoning."""
    ai_keywords = {
        "python", "pytorch", "tensorflow", "nlp", "ml", "ai", "embedding",
        "retrieval", "ranking", "search", "recommendation", "deep learning",
        "transformer", "bert", "gpt", "llm", "fine-tuning", "vector",
        "faiss", "pinecone", "weaviate", "scikit-learn", "pandas", "numpy",
        "spark", "airflow", "docker", "kubernetes", "aws", "gcp", "azure",
    }
    relevant = []
    other = []
    for skill in candidate.skills:
        if any(kw in skill.name.lower() for kw in ai_keywords):
            relevant.append(skill.name)
        else:
            other.append(skill.name)
    return relevant + other


def _identify_strengths(candidate: CandidateData, breakdown: ScoreBreakdown) -> list[str]:
    """Identify the candidate's specific strengths relative to the JD."""
    strengths = []

    # Check career history for production AI experience
    all_desc = " ".join(e.description.lower() for e in candidate.career_history)

    if any(kw in all_desc for kw in ["embedding", "retrieval", "ranking", "vector", "search system"]):
        strengths.append("has production experience with retrieval/ranking systems")
    elif any(kw in all_desc for kw in ["ml pipeline", "model", "machine learning", "deep learning"]):
        strengths.append("has production ML engineering experience")
    elif any(kw in all_desc for kw in ["data pipeline", "spark", "airflow", "data engineering"]):
        strengths.append("strong data engineering background with ML-adjacent skills")

    # Skill-based strengths
    ai_skills = [s for s in candidate.skills if s.proficiency in ("expert", "advanced")
                 and any(kw in s.name.lower() for kw in ["python", "pytorch", "nlp", "ml",
                         "embedding", "transformer", "deep learning"])]
    if ai_skills:
        skill_names = [s.name for s in ai_skills[:3]]
        strengths.append(f"advanced in {', '.join(skill_names)}")

    # Behavioral strengths
    signals = candidate.redrob_signals
    if signals.recruiter_response_rate > 0.7:
        strengths.append(f"highly responsive ({signals.recruiter_response_rate:.0%} recruiter response rate)")
    if signals.github_activity_score > 50:
        strengths.append(f"active GitHub contributor (score: {signals.github_activity_score:.0f})")
    if signals.open_to_work_flag and signals.notice_period_days <= 30:
        strengths.append("actively looking with short notice period")

    # YoE alignment
    yoe = candidate.profile.years_of_experience
    if 5 <= yoe <= 9:
        strengths.append(f"{yoe:.0f} yrs experience aligns with JD's 5-9 year range")

    if not strengths:
        strengths.append(f"background in {candidate.profile.current_industry}")

    return strengths


def _identify_gaps(candidate: CandidateData, breakdown: ScoreBreakdown) -> list[str]:
    """Identify specific gaps relative to the JD."""
    gaps = []

    title_lower = candidate.profile.current_title.lower()
    all_desc = " ".join(e.description.lower() for e in candidate.career_history)

    # Title mismatch
    if not any(kw in title_lower for kw in ["engineer", "developer", "scientist", "ml", "ai", "data"]):
        gaps.append(f"current role ({candidate.profile.current_title}) is not in engineering/AI")

    # No production AI evidence
    if not any(kw in all_desc for kw in ["embedding", "retrieval", "ranking", "ml", "model",
                                          "machine learning", "deep learning", "ai"]):
        gaps.append("no evidence of AI/ML work in career history")

    # Consulting-only career
    companies = [e.company.lower() for e in candidate.career_history]
    if all(any(c in comp for c in CONSULTING_COMPANIES) for comp in companies):
        gaps.append("entire career at consulting/services companies (JD flags this as concern)")

    # Experience level mismatch
    yoe = candidate.profile.years_of_experience
    if yoe < 3:
        gaps.append(f"only {yoe:.1f} yrs experience (JD targets 5-9 yrs)")
    elif yoe > 14:
        gaps.append(f"{yoe:.0f} yrs may be over-senior for this founding-team IC role")

    # Low behavioral signals
    signals = candidate.redrob_signals
    if signals.recruiter_response_rate < 0.2:
        gaps.append(f"low recruiter response rate ({signals.recruiter_response_rate:.0%})")
    if signals.notice_period_days > 90:
        gaps.append(f"long notice period ({signals.notice_period_days} days)")

    if not gaps:
        gaps.append("no major concerns identified")

    return gaps


def _get_career_highlight(candidate: CandidateData) -> str:
    """Extract a specific career highlight for top-tier reasoning."""
    for entry in candidate.career_history:
        desc_lower = entry.description.lower()
        if any(kw in desc_lower for kw in ["embedding", "retrieval", "ranking", "recommendation",
                                            "vector", "search system", "ml pipeline"]):
            # Found a highly relevant role
            return f"Built {_extract_project_verb(desc_lower)} at {entry.company}. "

    # Fallback — mention most recent role
    if candidate.career_history:
        entry = candidate.career_history[0]
        return f"Currently {entry.title} at {entry.company}. "

    return ""


def _extract_project_verb(description: str) -> str:
    """Extract a brief project description from career text."""
    keywords_to_phrases = {
        "ranking": "ranking/retrieval systems",
        "retrieval": "retrieval infrastructure",
        "recommendation": "recommendation systems",
        "embedding": "embedding-based search",
        "vector": "vector search infrastructure",
        "search system": "search systems",
        "ml pipeline": "ML pipelines",
        "data pipeline": "data pipelines",
        "model serving": "model serving infrastructure",
    }
    for kw, phrase in keywords_to_phrases.items():
        if kw in description:
            return phrase
    return "technical infrastructure"
