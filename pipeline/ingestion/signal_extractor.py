"""
Signal Extractor — normalizes Redrob behavioral signals for scoring.

This module doesn't make external API calls (GitHub, LinkedIn).
Instead, it works with the structured redrob_signals data in each candidate profile.
"""

from __future__ import annotations

from api.schemas.candidate import CandidateData


def extract_signals_summary(candidate: CandidateData) -> dict:
    """
    Extract a normalized summary of behavioral signals for a candidate.

    Returns a dict of signal categories with 0-1 normalized scores.
    """
    signals = candidate.redrob_signals

    return {
        "responsiveness": signals.recruiter_response_rate,
        "platform_activity": min(signals.profile_completeness_score / 100.0, 1.0),
        "github_active": max(signals.github_activity_score / 100.0, 0.0) if signals.github_activity_score >= 0 else 0.0,
        "has_github": signals.github_activity_score >= 0,
        "open_to_work": signals.open_to_work_flag,
        "actively_applying": signals.applications_submitted_30d > 0,
        "interview_reliable": signals.interview_completion_rate,
        "notice_days": signals.notice_period_days,
        "verified": signals.verified_email and signals.verified_phone,
        "linkedin_connected": signals.linkedin_connected,
        "recruiter_interest": min(signals.saved_by_recruiters_30d / 10.0, 1.0),
        "search_visibility": min(signals.search_appearance_30d / 100.0, 1.0),
    }
