"""
POST /explain — deep-dive explanation for a single candidate vs JD.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.schemas.result import ExplanationResponse, ScoreBreakdown
from config.settings import SAMPLE_CANDIDATES
from pipeline.ingestion.candidate_parser import load_candidates
from pipeline.scoring.career_scorer import score_career
from pipeline.scoring.skill_scorer import score_skills
from pipeline.scoring.behavioral_scorer import score_behavioral
from pipeline.scoring.honeypot_detector import detect_honeypot
from pipeline.scoring.hybrid_scorer import compute_hybrid_score
from pipeline.explanation.explainer import _identify_strengths, _identify_gaps

router = APIRouter()


class ExplainRequest(BaseModel):
    candidate_id: str
    candidates_path: str = str(SAMPLE_CANDIDATES)


@router.post("", response_model=ExplanationResponse)
async def explain_candidate(request: ExplainRequest):
    """Deep-dive explanation for a single candidate vs the JD."""
    try:
        candidates = load_candidates(request.candidates_path)
        cand_map = {c.candidate_id: c for c in candidates}

        if request.candidate_id not in cand_map:
            raise HTTPException(
                status_code=404,
                detail=f"Candidate {request.candidate_id} not found"
            )

        cand = cand_map[request.candidate_id]

        # Score all dimensions
        career_s, _ = score_career(cand)
        skill_s, _ = score_skills(cand)
        behavioral_s, _ = score_behavioral(cand)
        is_hp, hp_reasons = detect_honeypot(cand)

        final_score, breakdown = compute_hybrid_score(
            candidate=cand,
            semantic_score=0.5,  # No embedding available in this endpoint
            career_score=career_s,
            skill_score=skill_s,
            behavioral_score=behavioral_s,
            is_honeypot=is_hp,
        )

        strengths = _identify_strengths(cand, breakdown)
        gaps = _identify_gaps(cand, breakdown)

        # Confidence based on data completeness
        data_points = sum([
            len(cand.career_history) > 0,
            len(cand.skills) > 3,
            len(cand.education) > 0,
            cand.redrob_signals.profile_completeness_score > 50,
            cand.redrob_signals.github_activity_score >= 0,
            cand.profile.summary != "",
        ])
        if data_points >= 5:
            confidence = "HIGH"
            conf_reason = "Profile has comprehensive data across all dimensions."
        elif data_points >= 3:
            confidence = "MEDIUM"
            conf_reason = "Some profile sections are sparse or missing."
        else:
            confidence = "LOW"
            conf_reason = "Limited profile data available for evaluation."

        return ExplanationResponse(
            candidate_id=request.candidate_id,
            strengths=". ".join(strengths),
            gaps=". ".join(gaps),
            confidence=confidence,
            confidence_reason=conf_reason,
            score_breakdown=breakdown,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {e}")
