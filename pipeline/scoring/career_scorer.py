"""
Career Fit Scorer — the highest-weight signal (0.30).

Evaluates how well a candidate's career trajectory matches the Senior AI Engineer JD.
This is where we catch the keyword-stuffing traps: candidates whose skills list
contains AI keywords but whose actual career history is in Marketing/Accounting/etc.

Scoring dimensions:
1. Title relevance (current + historical)
2. Production AI experience in career descriptions
3. Product company vs consulting trajectory
4. Career progression direction (toward or away from AI)
5. Company size/stage alignment (startup experience valued)
"""

from __future__ import annotations

import re

from api.schemas.candidate import CandidateData
from config.settings import CONSULTING_COMPANIES, TITLE_RELEVANCE
from config.jd_config import PRODUCTION_AI_KEYWORDS


def score_career(candidate: CandidateData) -> tuple[float, dict]:
    """
    Score career fit on 0-1 scale.

    Returns:
        (score, detail_dict) where detail_dict has sub-scores for transparency.
    """
    details = {}

    # ── 1. Title Relevance (40% of career score) ────────────────────────
    current_title = candidate.profile.current_title.lower().strip()
    current_title_score = _match_title(current_title)

    # Also check career history titles for trajectory
    history_title_scores = []
    for entry in candidate.career_history:
        title = entry.title.lower().strip()
        history_title_scores.append(_match_title(title))

    # Weight recent titles more heavily
    if history_title_scores:
        # Most recent roles first (career_history is typically most recent first)
        weighted_history = 0.0
        weight_sum = 0.0
        for i, score in enumerate(history_title_scores):
            w = 1.0 / (1 + i * 0.5)  # Decay: 1.0, 0.67, 0.5, 0.4, ...
            weighted_history += score * w
            weight_sum += w
        avg_history_score = weighted_history / weight_sum if weight_sum > 0 else 0
    else:
        avg_history_score = current_title_score

    title_score = 0.6 * current_title_score + 0.4 * avg_history_score
    details["title_relevance"] = round(title_score, 4)

    # ── 2. Production AI Experience (30% of career score) ───────────────
    all_descriptions = " ".join(
        entry.description.lower() for entry in candidate.career_history
    )
    all_descriptions += " " + candidate.profile.summary.lower()

    prod_ai_hits = sum(
        1 for kw in PRODUCTION_AI_KEYWORDS
        if kw in all_descriptions
    )
    # Normalize: hitting 8+ keywords = perfect score
    prod_ai_score = min(prod_ai_hits / 8.0, 1.0)
    details["production_ai_experience"] = round(prod_ai_score, 4)

    # ── 3. Product vs Consulting Trajectory (15% of career score) ───────
    consulting_count = 0
    product_count = 0
    total_months_consulting = 0
    total_months_product = 0

    for entry in candidate.career_history:
        company_lower = entry.company.lower().strip()
        is_consulting = any(c in company_lower for c in CONSULTING_COMPANIES)
        if is_consulting:
            consulting_count += 1
            total_months_consulting += entry.duration_months
        else:
            product_count += 1
            total_months_product += entry.duration_months

    total_months = total_months_consulting + total_months_product
    if total_months > 0:
        product_ratio = total_months_product / total_months
    else:
        product_ratio = 0.5  # Unknown, neutral

    # JD says consulting-only careers are a disqualifier
    if consulting_count > 0 and product_count == 0:
        consulting_penalty = 0.1  # Very heavy penalty
    elif consulting_count > product_count:
        consulting_penalty = 0.4  # Majority consulting
    else:
        consulting_penalty = product_ratio  # Mostly product = good

    details["product_vs_consulting"] = round(consulting_penalty, 4)

    # ── 4. Career Direction / Trajectory (10% of career score) ──────────
    # Is the career moving toward AI/ML roles or away from them?
    if len(candidate.career_history) >= 2:
        # Compare earliest role(s) vs most recent role(s)
        early_scores = [_match_title(e.title.lower()) for e in candidate.career_history[-2:]]
        recent_scores = [_match_title(e.title.lower()) for e in candidate.career_history[:2]]
        early_avg = sum(early_scores) / len(early_scores)
        recent_avg = sum(recent_scores) / len(recent_scores)

        if recent_avg > early_avg + 0.1:
            trajectory_score = min(1.0, 0.7 + (recent_avg - early_avg))  # Moving toward AI
        elif recent_avg < early_avg - 0.1:
            trajectory_score = max(0.2, 0.5 - (early_avg - recent_avg))  # Moving away
        else:
            trajectory_score = 0.5 + recent_avg * 0.3  # Stable, boost if already in AI
    else:
        trajectory_score = 0.5  # Single role, neutral

    details["career_trajectory"] = round(trajectory_score, 4)

    # ── 5. Company Stage Alignment (5% of career score) ─────────────────
    # JD is Series A startup, prefers candidates from smaller companies
    startup_experience = any(
        entry.company_size in ("1-10", "11-50", "51-200")
        for entry in candidate.career_history
    )
    mid_stage = any(
        entry.company_size in ("201-500", "501-1000")
        for entry in candidate.career_history
    )
    stage_score = 0.3
    if startup_experience:
        stage_score = 0.9
    elif mid_stage:
        stage_score = 0.6

    details["company_stage"] = round(stage_score, 4)

    # ── Combine ─────────────────────────────────────────────────────────
    final_score = (
        0.40 * title_score
        + 0.30 * prod_ai_score
        + 0.15 * consulting_penalty
        + 0.10 * trajectory_score
        + 0.05 * stage_score
    )

    return round(min(max(final_score, 0.0), 1.0), 4), details


def _match_title(title: str) -> float:
    """
    Match a title against known relevance tiers.
    Uses substring matching for flexibility.
    """
    title = title.lower().strip()

    # Direct match first
    if title in TITLE_RELEVANCE:
        return TITLE_RELEVANCE[title]

    # Substring match (e.g., "senior machine learning engineer ii" → "machine learning engineer")
    best_score = 0.0
    for known_title, score in TITLE_RELEVANCE.items():
        if known_title in title or title in known_title:
            best_score = max(best_score, score)

    # Fallback: check for key indicator words
    if best_score == 0:
        if any(w in title for w in ["ml", "machine learning", "ai", "artificial intelligence"]):
            best_score = 0.75
        elif any(w in title for w in ["data scientist", "data science"]):
            best_score = 0.70
        elif any(w in title for w in ["engineer", "developer", "programmer"]):
            best_score = 0.45
        elif any(w in title for w in ["analyst", "researcher"]):
            best_score = 0.35
        elif any(w in title for w in ["manager", "lead", "director"]):
            best_score = 0.25
        else:
            best_score = 0.10  # Unknown title, low score

    return best_score
