"""
Pydantic models for candidate profiles, matching the Redrob dataset schema.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CareerEntry(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: str | None = None
    duration_months: int
    is_current: bool
    industry: str
    company_size: str
    description: str


class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_year: int
    end_year: int
    grade: str | None = None
    tier: str | None = None


class Skill(BaseModel):
    name: str
    proficiency: str  # beginner, intermediate, advanced, expert
    endorsements: int = 0
    duration_months: int = 0


class Certification(BaseModel):
    name: str
    issuer: str
    year: int


class Language(BaseModel):
    language: str
    proficiency: str  # basic, conversational, professional, native


class SalaryRange(BaseModel):
    min: float
    max: float


class RedrobSignals(BaseModel):
    profile_completeness_score: float = 0.0
    signup_date: str = ""
    last_active_date: str = ""
    open_to_work_flag: bool = False
    profile_views_received_30d: int = 0
    applications_submitted_30d: int = 0
    recruiter_response_rate: float = 0.0
    avg_response_time_hours: float = 0.0
    skill_assessment_scores: dict[str, float] = Field(default_factory=dict)
    connection_count: int = 0
    endorsements_received: int = 0
    notice_period_days: int = 0
    expected_salary_range_inr_lpa: SalaryRange = Field(
        default_factory=lambda: SalaryRange(min=0, max=0)
    )
    preferred_work_mode: str = "flexible"
    willing_to_relocate: bool = False
    github_activity_score: float = -1.0
    search_appearance_30d: int = 0
    saved_by_recruiters_30d: int = 0
    interview_completion_rate: float = 0.0
    offer_acceptance_rate: float = -1.0
    verified_email: bool = False
    verified_phone: bool = False
    linkedin_connected: bool = False


class CandidateProfile(BaseModel):
    anonymized_name: str
    headline: str = ""
    summary: str = ""
    location: str = ""
    country: str = ""
    years_of_experience: float = 0.0
    current_title: str = ""
    current_company: str = ""
    current_company_size: str = ""
    current_industry: str = ""


class CandidateData(BaseModel):
    """Full candidate record from the JSONL dataset."""
    candidate_id: str
    profile: CandidateProfile
    career_history: list[CareerEntry] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    redrob_signals: RedrobSignals = Field(default_factory=RedrobSignals)
