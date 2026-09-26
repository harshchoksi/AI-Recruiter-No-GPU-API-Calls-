"""
Skill Match Scorer — evaluates how well a candidate's skills match JD requirements.

Key design decisions:
- Uses keyword matching against skill names AND career descriptions
- Skill proficiency weighted: expert > advanced > intermediate > beginner
- Cross-validates skills against redrob skill_assessment_scores
- Trap detection: flags candidates with AI keywords in skills but no career context
"""

from __future__ import annotations

from api.schemas.candidate import CandidateData
from config.jd_config import REQUIRED_SKILLS, NICE_TO_HAVE_SKILLS, ANTI_SIGNALS


PROFICIENCY_WEIGHTS = {
    "expert": 1.0,
    "advanced": 0.8,
    "intermediate": 0.5,
    "beginner": 0.2,
}


def score_skills(candidate: CandidateData) -> tuple[float, dict]:
    """
    Score skill match on 0-1 scale.

    Returns:
        (score, detail_dict)
    """
    details = {}

    # Build candidate's skill set (name → proficiency weight)
    candidate_skills = {}
    for skill in candidate.skills:
        name_lower = skill.name.lower().strip()
        weight = PROFICIENCY_WEIGHTS.get(skill.proficiency, 0.2)
        # Duration bonus: longer experience = more credible
        duration_bonus = min(skill.duration_months / 36.0, 1.0) * 0.2  # Up to 0.2 bonus for 3+ years
        candidate_skills[name_lower] = weight + duration_bonus

    # Also extract keywords from career descriptions for contextual matching
    all_text = " ".join(
        entry.description.lower() for entry in candidate.career_history
    )
    all_text += " " + candidate.profile.summary.lower()
    all_text += " " + candidate.profile.headline.lower()

    # ── Required Skills Match ────────────────────────────────────────────
    required_scores = {}
    for cluster_name, cluster in REQUIRED_SKILLS.items():
        best_match = 0.0

        # Check skill list
        for kw in cluster["keywords"]:
            kw_lower = kw.lower()
            for skill_name, skill_weight in candidate_skills.items():
                if kw_lower in skill_name or skill_name in kw_lower:
                    best_match = max(best_match, skill_weight)

        # Check career descriptions (contextual match)
        context_hits = sum(1 for kw in cluster["keywords"] if kw.lower() in all_text)
        if context_hits >= 2:
            context_score = min(context_hits / 4.0, 1.0) * 0.7
            best_match = max(best_match, context_score)

        required_scores[cluster_name] = best_match * cluster["weight"]

    # Weighted average of required skill matches
    if required_scores:
        total_weight = sum(cluster["weight"] for cluster in REQUIRED_SKILLS.values())
        required_score = sum(required_scores.values()) / total_weight
    else:
        required_score = 0.0

    details["required_skills"] = {k: round(v, 3) for k, v in required_scores.items()}
    details["required_score"] = round(required_score, 4)

    # ── Nice-to-Have Skills Match ────────────────────────────────────────
    nice_scores = {}
    for cluster_name, cluster in NICE_TO_HAVE_SKILLS.items():
        best_match = 0.0

        for kw in cluster["keywords"]:
            kw_lower = kw.lower()
            for skill_name, skill_weight in candidate_skills.items():
                if kw_lower in skill_name or skill_name in kw_lower:
                    best_match = max(best_match, skill_weight)

        context_hits = sum(1 for kw in cluster["keywords"] if kw.lower() in all_text)
        if context_hits >= 2:
            context_score = min(context_hits / 3.0, 1.0) * 0.6
            best_match = max(best_match, context_score)

        nice_scores[cluster_name] = best_match * cluster["weight"]

    if nice_scores:
        total_weight = sum(cluster["weight"] for cluster in NICE_TO_HAVE_SKILLS.values())
        nice_score = sum(nice_scores.values()) / total_weight
    else:
        nice_score = 0.0

    details["nice_to_have_skills"] = {k: round(v, 3) for k, v in nice_scores.items()}
    details["nice_score"] = round(nice_score, 4)

    # ── Skill Assessment Validation ──────────────────────────────────────
    # Cross-reference Redrob platform assessments with claimed skills
    assessment_scores = candidate.redrob_signals.skill_assessment_scores
    assessment_bonus = 0.0
    if assessment_scores:
        relevant_assessments = 0
        for skill_name, score in assessment_scores.items():
            skill_lower = skill_name.lower()
            # Check if this assessment is relevant to JD requirements
            for cluster in {**REQUIRED_SKILLS, **NICE_TO_HAVE_SKILLS}.values():
                if any(kw in skill_lower or skill_lower in kw for kw in cluster["keywords"]):
                    if score >= 60:
                        relevant_assessments += 1
                    break
        assessment_bonus = min(relevant_assessments / 3.0, 1.0) * 0.1

    details["assessment_bonus"] = round(assessment_bonus, 4)

    # ── Anti-Signal Detection ────────────────────────────────────────────
    anti_penalty = 0.0

    # Check for CV/speech-only background
    cv_keywords = ANTI_SIGNALS.get("cv_speech_only", {}).get("keywords", [])
    cv_skill_count = sum(
        1 for s in candidate.skills
        if any(kw in s.name.lower() for kw in cv_keywords)
        and s.proficiency in ("expert", "advanced")
    )
    nlp_ir_count = sum(
        1 for s in candidate.skills
        if any(kw in s.name.lower() for kw in ["nlp", "natural language", "retrieval", "search", "ranking", "recommendation"])
    )
    if cv_skill_count >= 3 and nlp_ir_count == 0:
        anti_penalty += 0.15

    # Check for framework-only experience (LangChain enthusiast trap)
    framework_keywords = ANTI_SIGNALS.get("framework_enthusiast", {}).get("keywords", [])
    if any(kw in all_text for kw in framework_keywords):
        # Only penalize if there's no pre-LLM ML experience
        pre_llm_keywords = ["retrieval", "ranking", "recommendation", "search", "embedding",
                           "classification", "regression", "feature engineering"]
        has_pre_llm = any(kw in all_text for kw in pre_llm_keywords)
        if not has_pre_llm:
            anti_penalty += 0.10

    details["anti_penalty"] = round(anti_penalty, 4)

    # ── Combine ─────────────────────────────────────────────────────────
    final_score = (
        0.70 * required_score
        + 0.20 * nice_score
        + assessment_bonus
        - anti_penalty
    )

    return round(min(max(final_score, 0.0), 1.0), 4), details
