"""
Pydantic models for ranking results and explanations.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """Per-dimension score breakdown for a ranked candidate."""
    semantic_similarity: float = 0.0
    career_fit: float = 0.0
    skill_match: float = 0.0
    behavioral: float = 0.0
    education: float = 0.0
    experience_fit: float = 0.0


class RankedCandidate(BaseModel):
    """A single candidate in the ranked output."""
    candidate_id: str
    rank: int
    score: float
    breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    reasoning: str = ""
    is_honeypot: bool = False
    name: str = ""
    current_title: str = ""
    years_of_experience: float = 0.0


class Shortlist(BaseModel):
    """The complete ranked output."""
    candidates: list[RankedCandidate] = Field(default_factory=list)
    total_evaluated: int = 0
    honeypots_detected: int = 0
    latency_ms: float = 0.0


class ExplanationResponse(BaseModel):
    """Deep-dive explanation for a single candidate vs JD."""
    candidate_id: str
    strengths: str = ""
    gaps: str = ""
    confidence: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    confidence_reason: str = ""
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
