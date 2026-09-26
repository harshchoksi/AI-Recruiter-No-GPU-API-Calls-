"""
POST /rank — rank candidates against the JD.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.settings import CANDIDATES_JSONL, ARTIFACTS_DIR, SAMPLE_CANDIDATES
from pipeline.orchestrator import RankingPipeline

router = APIRouter()


class RankRequest(BaseModel):
    candidates_path: str = str(CANDIDATES_JSONL)
    role_type: str = "startup"
    top_n: int = 100
    limit: int | None = None


class ScoreBreakdownResponse(BaseModel):
    career_fit: float = 0
    skill_match: float = 0
    semantic_similarity: float = 0
    behavioral: float = 0
    experience_fit: float = 0
    education: float = 0


class RankResponseCandidate(BaseModel):
    candidate_id: str
    rank: int
    score: float
    name: str = ""
    current_title: str = ""
    years_of_experience: float = 0
    reasoning: str = ""
    breakdown: ScoreBreakdownResponse = Field(default_factory=ScoreBreakdownResponse)


class RankResponse(BaseModel):
    candidates: list[RankResponseCandidate]
    total_evaluated: int
    honeypots_detected: int
    latency_ms: float


@router.post("", response_model=RankResponse)
async def rank_candidates(request: RankRequest):
    """Rank candidates against the JD and return shortlist."""
    try:
        cand_path = Path(request.candidates_path)
        if not cand_path.exists() and CANDIDATES_JSONL.exists():
            cand_path = CANDIDATES_JSONL

        pipeline = RankingPipeline(role_type=request.role_type)
        shortlist = pipeline.rank(
            candidates_path=cand_path,
            artifacts_dir=ARTIFACTS_DIR,
            limit=request.limit,
            top_n=request.top_n,
        )

        return RankResponse(
            candidates=[
                RankResponseCandidate(
                    candidate_id=c.candidate_id,
                    rank=c.rank,
                    score=c.score,
                    name=c.name,
                    current_title=c.current_title,
                    years_of_experience=c.years_of_experience,
                    reasoning=c.reasoning,
                    breakdown=ScoreBreakdownResponse(
                        career_fit=c.breakdown.career_fit,
                        skill_match=c.breakdown.skill_match,
                        semantic_similarity=c.breakdown.semantic_similarity,
                        behavioral=c.breakdown.behavioral,
                        experience_fit=c.breakdown.experience_fit,
                        education=c.breakdown.education,
                    ),
                )
                for c in shortlist.candidates
            ],
            total_evaluated=shortlist.total_evaluated,
            honeypots_detected=shortlist.honeypots_detected,
            latency_ms=shortlist.latency_ms,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ranking failed: {e}")
