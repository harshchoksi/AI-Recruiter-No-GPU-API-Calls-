"""
Honeypot Detection — identifies candidates with subtly impossible profiles.

The dataset contains ~80 honeypots that are forced to relevance tier 0 in ground truth.
Having >10% honeypots in top 100 = disqualification.

Detection signals:
- Expert proficiency with 0 or very low duration_months
- years_of_experience wildly exceeds sum of career durations
- Too many skills at expert level relative to career length
- Impossible date overlaps in career history
"""

from __future__ import annotations

from datetime import datetime

from api.schemas.candidate import CandidateData
from config.settings import (
    HONEYPOT_MAX_EXPERT_SKILLS_ZERO_DURATION,
    HONEYPOT_MAX_YOE_CAREER_GAP,
    HONEYPOT_MIN_SKILL_DURATION_FOR_EXPERT,
)


def detect_honeypot(candidate: CandidateData) -> tuple[bool, list[str]]:
    """
    Check if a candidate is a honeypot with an impossible profile.

    Returns:
        (is_honeypot, list_of_reasons)
    """
    reasons: list[str] = []

    # ── Check 1: Expert/advanced skills with 0 or very low duration ──────
    expert_zero_count = 0
    for skill in candidate.skills:
        if skill.proficiency in ("expert", "advanced") and skill.duration_months < HONEYPOT_MIN_SKILL_DURATION_FOR_EXPERT:
            expert_zero_count += 1

    if expert_zero_count > HONEYPOT_MAX_EXPERT_SKILLS_ZERO_DURATION:
        reasons.append(
            f"{expert_zero_count} expert/advanced skills with <{HONEYPOT_MIN_SKILL_DURATION_FOR_EXPERT} months duration"
        )

    # ── Check 2: YoE vs career history sum ───────────────────────────────
    total_career_months = sum(c.duration_months for c in candidate.career_history)
    total_career_years = total_career_months / 12.0
    stated_yoe = candidate.profile.years_of_experience
    yoe_gap = stated_yoe - total_career_years

    if yoe_gap > HONEYPOT_MAX_YOE_CAREER_GAP and stated_yoe > 2:
        reasons.append(
            f"Stated {stated_yoe:.1f} yrs experience but career history sums to {total_career_years:.1f} yrs "
            f"(gap: {yoe_gap:.1f} yrs)"
        )

    # ── Check 3: Excessive expert-level skills ────────────────────────────
    expert_skills = [s for s in candidate.skills if s.proficiency == "expert"]
    if len(expert_skills) >= 10:
        reasons.append(
            f"{len(expert_skills)} skills all at expert level (statistically implausible)"
        )

    # ── Check 4: Career history date impossibilities ─────────────────────
    for entry in candidate.career_history:
        try:
            start = datetime.strptime(entry.start_date, "%Y-%m-%d")
            if entry.end_date:
                end = datetime.strptime(entry.end_date, "%Y-%m-%d")
                actual_months = (end.year - start.year) * 12 + (end.month - start.month)
                # If stated duration is wildly different from date-computed duration
                if abs(actual_months - entry.duration_months) > 12 and entry.duration_months > 0:
                    reasons.append(
                        f"Role at {entry.company}: dates imply ~{actual_months} months "
                        f"but duration_months={entry.duration_months}"
                    )
            # Check for future start dates (impossibly early career)
            if start.year < 1990 and stated_yoe < 30:
                reasons.append(f"Career entry at {entry.company} starts in {start.year}")
        except (ValueError, TypeError):
            pass

    # ── Check 5: Skill endorsements without any usage ────────────────────
    high_endorse_zero_use = sum(
        1 for s in candidate.skills
        if s.endorsements > 30 and s.duration_months == 0
    )
    if high_endorse_zero_use >= 3:
        reasons.append(
            f"{high_endorse_zero_use} skills with >30 endorsements but 0 months of use"
        )

    # ── Check 6: Profile completeness vs data sparsity mismatch ──────────
    signals = candidate.redrob_signals
    if (signals.profile_completeness_score > 90
        and len(candidate.career_history) <= 1
        and len(candidate.skills) <= 2
        and stated_yoe > 8):
        reasons.append(
            f"Profile completeness {signals.profile_completeness_score}% "
            f"but only {len(candidate.career_history)} career entries, "
            f"{len(candidate.skills)} skills, and {stated_yoe} yrs stated"
        )

    # ── Check 7: High YoE but only 1 short job ───────────────────────────
    if stated_yoe >= 6 and len(candidate.career_history) <= 1 and total_career_months < 12:
        reasons.append(
            f"Claims {stated_yoe:.1f} yrs experience but only {len(candidate.career_history)} "
            f"job totaling {total_career_months} months"
        )

    # ── Check 8: Non-tech title with multiple AI expert skills ───────────
    title_lower = candidate.profile.current_title.lower()
    non_tech_title = any(kw in title_lower for kw in [
        'marketing', 'sales', 'hr', 'finance', 'accountant',
        'content writer', 'support', 'recruiter', 'admin',
    ])
    ai_expert_count = sum(
        1 for s in candidate.skills
        if s.proficiency == 'expert'
        and any(kw in s.name.lower() for kw in [
            'python', 'pytorch', 'tensorflow', 'nlp', 'ml',
            'deep learning', 'embedding', 'ai', 'transformer',
        ])
    )
    if non_tech_title and ai_expert_count >= 3:
        reasons.append(
            f"Non-tech title '{candidate.profile.current_title}' but "
            f"{ai_expert_count} AI-related expert skills"
        )

    is_honeypot = len(reasons) >= 1  # Single strong signal is enough
    return is_honeypot, reasons
