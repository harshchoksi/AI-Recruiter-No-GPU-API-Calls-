"""
Behavioral Signal Scorer — scores Redrob platform engagement signals.

These signals measure "hirability" — whether a candidate is actually available
and responsive, beyond just having the right skills on paper.

Key insight from JD: "A perfect-on-paper candidate who hasn't logged in for 6 months
and has a 5% recruiter response rate is, for hiring purposes, not actually available."
"""

from __future__ import annotations

from datetime import datetime, timedelta

from api.schemas.candidate import CandidateData
from config.settings import PREFERRED_LOCATIONS, PREFERRED_COUNTRIES


def score_behavioral(candidate: CandidateData) -> tuple[float, dict]:
    """
    Score behavioral signals on 0-1 scale.

    Returns:
        (score, detail_dict)
    """
    signals = candidate.redrob_signals
    details = {}

    # ── 1. Recruiter Response Rate (25% of behavioral) ──────────────────
    # Higher = more responsive = more hireable
    response_score = signals.recruiter_response_rate  # Already 0-1
    details["response_rate"] = round(response_score, 4)

    # ── 2. Recency / Activity (20% of behavioral) ───────────────────────
    try:
        last_active = datetime.strptime(signals.last_active_date, "%Y-%m-%d")
        # Reference date: use June 2026 as "now" (dataset context)
        ref_date = datetime(2026, 6, 1)
        days_since_active = (ref_date - last_active).days
        if days_since_active <= 7:
            recency_score = 1.0
        elif days_since_active <= 30:
            recency_score = 0.9
        elif days_since_active <= 90:
            recency_score = 0.7
        elif days_since_active <= 180:
            recency_score = 0.4
        elif days_since_active <= 365:
            recency_score = 0.2
        else:
            recency_score = 0.05
    except (ValueError, TypeError):
        recency_score = 0.3  # Unknown, neutral-ish

    details["recency"] = round(recency_score, 4)

    # ── 3. Open-to-Work + Applications (15% of behavioral) ──────────────
    availability_score = 0.3  # Base
    if signals.open_to_work_flag:
        availability_score += 0.4
    if signals.applications_submitted_30d > 0:
        availability_score += 0.2
    if signals.applications_submitted_30d > 3:
        availability_score += 0.1
    availability_score = min(availability_score, 1.0)
    details["availability"] = round(availability_score, 4)

    # ── 4. Interview Completion Rate (10% of behavioral) ─────────────────
    interview_score = signals.interview_completion_rate  # 0-1
    details["interview_completion"] = round(interview_score, 4)

    # ── 5. Profile Completeness (10% of behavioral) ─────────────────────
    completeness_score = signals.profile_completeness_score / 100.0
    details["profile_completeness"] = round(completeness_score, 4)

    # ── 6. GitHub Activity (5% of behavioral) ────────────────────────────
    github = signals.github_activity_score
    if github < 0:
        github_score = 0.2  # No GitHub linked — slight penalty but not dealbreaker
    else:
        github_score = min(github / 70.0, 1.0)  # 70+ = full marks
    details["github_activity"] = round(github_score, 4)

    # ── 7. Notice Period (5% of behavioral) ──────────────────────────────
    notice = signals.notice_period_days
    if notice <= 30:
        notice_score = 1.0
    elif notice <= 60:
        notice_score = 0.7
    elif notice <= 90:
        notice_score = 0.4
    else:
        notice_score = 0.2
    details["notice_period"] = round(notice_score, 4)

    # ── 8. Location / Work Mode Alignment (5% of behavioral) ────────────
    location_score = 0.3  # Base
    candidate_location = candidate.profile.location.lower()
    candidate_country = candidate.profile.country.lower()

    if candidate_country in PREFERRED_COUNTRIES:
        location_score += 0.3
    if any(loc in candidate_location for loc in PREFERRED_LOCATIONS):
        location_score += 0.3

    # Work mode alignment (JD is hybrid)
    if signals.preferred_work_mode in ("hybrid", "flexible"):
        location_score += 0.1
    elif signals.preferred_work_mode == "onsite":
        location_score += 0.05

    if signals.willing_to_relocate:
        location_score = max(location_score, 0.5)

    location_score = min(location_score, 1.0)
    details["location_alignment"] = round(location_score, 4)

    # ── 9. Recruiter Interest Signals (5% of behavioral) ────────────────
    recruiter_interest = 0.0
    if signals.saved_by_recruiters_30d > 0:
        recruiter_interest += min(signals.saved_by_recruiters_30d / 10.0, 0.5)
    if signals.search_appearance_30d > 50:
        recruiter_interest += 0.3
    elif signals.search_appearance_30d > 10:
        recruiter_interest += 0.15
    if signals.profile_views_received_30d > 10:
        recruiter_interest += 0.2
    recruiter_interest = min(recruiter_interest, 1.0)
    details["recruiter_interest"] = round(recruiter_interest, 4)

    # ── Combine ─────────────────────────────────────────────────────────
    final_score = (
        0.25 * response_score
        + 0.20 * recency_score
        + 0.15 * availability_score
        + 0.10 * interview_score
        + 0.10 * completeness_score
        + 0.05 * github_score
        + 0.05 * notice_score
        + 0.05 * location_score
        + 0.05 * recruiter_interest
    )

    return round(min(max(final_score, 0.0), 1.0), 4), details
