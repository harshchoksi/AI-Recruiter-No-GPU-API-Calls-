"""
Candidate Embedder — creates composite embedding for each candidate.

Combines headline, summary, career descriptions, and skill names into
a single rich text representation, then embeds it.

Design decision: single text concatenation rather than weighted-average
of chunks, because candidates have less structured importance hierarchy
than JDs. The career descriptions naturally carry more weight due to
length.
"""

from __future__ import annotations

from api.schemas.candidate import CandidateData


def build_candidate_text(candidate: CandidateData) -> str:
    """
    Build a comprehensive text representation of a candidate for embedding.

    Prioritizes information most relevant to matching against the AI Engineer JD:
    - Professional headline and summary (who they say they are)
    - Career descriptions (what they actually did — most important)
    - Skill names (what they claim to know)
    """
    parts = []

    # Headline — concise self-description
    if candidate.profile.headline:
        parts.append(candidate.profile.headline)

    # Current context
    parts.append(
        f"{candidate.profile.current_title} at {candidate.profile.current_company} "
        f"with {candidate.profile.years_of_experience:.0f} years of experience "
        f"in {candidate.profile.current_industry}"
    )

    # Summary — their own pitch
    if candidate.profile.summary:
        # Truncate very long summaries to keep embedding focused
        summary = candidate.profile.summary[:500]
        parts.append(summary)

    # Career descriptions — the richest signal of what they actually did
    for entry in candidate.career_history[:5]:  # Cap at 5 most recent roles
        role_text = f"{entry.title} at {entry.company}: {entry.description[:300]}"
        parts.append(role_text)

    # Skills with proficiency — weighted by importance
    skill_parts = []
    for skill in candidate.skills:
        if skill.proficiency in ("expert", "advanced"):
            skill_parts.append(f"{skill.name} (expert)")
        elif skill.proficiency == "intermediate":
            skill_parts.append(skill.name)
        # Skip beginner skills — they add noise

    if skill_parts:
        parts.append("Key skills: " + ", ".join(skill_parts))

    # Education context
    for edu in candidate.education[:2]:
        parts.append(f"{edu.degree} in {edu.field_of_study} from {edu.institution}")

    return " . ".join(parts)


def build_candidate_texts_batch(candidates: list[CandidateData]) -> list[str]:
    """Build text representations for a batch of candidates."""
    return [build_candidate_text(c) for c in candidates]
