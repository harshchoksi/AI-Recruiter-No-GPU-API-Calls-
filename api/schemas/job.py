"""
Pydantic models for job description data.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ParsedJD(BaseModel):
    """Structured representation of the job description."""
    title: str = "Senior AI Engineer"
    company: str = "Redrob AI"
    seniority: str = "senior"  # junior, mid, senior, staff, principal
    yoe_min: float = 5.0
    yoe_max: float = 9.0
    required_skills: list[str] = Field(default_factory=lambda: [
        "embeddings_retrieval", "vector_databases", "python",
        "ranking_evaluation", "ml_production",
    ])
    nice_to_have_skills: list[str] = Field(default_factory=lambda: [
        "llm_finetuning", "learning_to_rank", "distributed_systems",
        "open_source", "nlp",
    ])
    domain: str = "AI/ML, recruiting tech, marketplace"
    work_mode: str = "hybrid"
    locations: list[str] = Field(default_factory=lambda: ["Pune", "Noida"])
    notice_preference_days: int = 30
    cultural_signals: list[str] = Field(default_factory=lambda: [
        "async_first", "scrappy", "disagree_openly",
        "product_engineering", "startup_stage",
    ])
    anti_patterns: list[str] = Field(default_factory=lambda: [
        "title_chaser", "framework_enthusiast", "consulting_only",
        "pure_research", "no_recent_code", "cv_speech_only",
    ])


class JobDescriptionInput(BaseModel):
    """Input for the /rank endpoint."""
    raw_text: str = ""
    role_type: str = "startup"  # startup, enterprise, default
    top_n: int = 100
