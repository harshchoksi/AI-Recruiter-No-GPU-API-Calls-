"""
Shared test fixtures.
"""

import pytest
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.schemas.candidate import (
    CandidateData, CandidateProfile, CareerEntry, Education, Skill,
    RedrobSignals, SalaryRange,
)


@pytest.fixture
def strong_ai_candidate() -> CandidateData:
    """A strong AI Engineer candidate matching the JD well."""
    return CandidateData(
        candidate_id="CAND_TEST001",
        profile=CandidateProfile(
            anonymized_name="Test Strong",
            headline="Senior ML Engineer | Retrieval & Ranking Systems",
            summary="6 years building production ML systems focused on search, retrieval, "
                    "and ranking. Built embedding-based candidate matching at scale.",
            location="Pune, Maharashtra",
            country="India",
            years_of_experience=6.5,
            current_title="Senior Machine Learning Engineer",
            current_company="AI Startup Co",
            current_company_size="51-200",
            current_industry="Software",
        ),
        career_history=[
            CareerEntry(
                company="AI Startup Co",
                title="Senior Machine Learning Engineer",
                start_date="2022-01-01",
                end_date=None,
                duration_months=42,
                is_current=True,
                industry="Software",
                company_size="51-200",
                description="Built the core retrieval and ranking system for a talent matching "
                            "platform. Deployed embedding-based search using FAISS and sentence "
                            "transformers. Designed evaluation framework using NDCG and MRR. "
                            "Set up A/B testing for ranking model improvements.",
            ),
            CareerEntry(
                company="Product Corp",
                title="ML Engineer",
                start_date="2019-06-01",
                end_date="2021-12-31",
                duration_months=31,
                is_current=False,
                industry="E-Commerce",
                company_size="201-500",
                description="Built recommendation system serving 10M users. Production ML "
                            "pipeline with feature store, model training, and real-time inference. "
                            "Python, PyTorch, Elasticsearch, Redis.",
            ),
        ],
        education=[
            Education(
                institution="IIT Bombay",
                degree="M.Tech",
                field_of_study="Computer Science",
                start_year=2017,
                end_year=2019,
                grade="8.9 CGPA",
                tier="tier_1",
            ),
        ],
        skills=[
            Skill(name="Python", proficiency="expert", endorsements=50, duration_months=72),
            Skill(name="PyTorch", proficiency="advanced", endorsements=30, duration_months=48),
            Skill(name="Retrieval Systems", proficiency="advanced", endorsements=20, duration_months=36),
            Skill(name="FAISS", proficiency="advanced", endorsements=15, duration_months=24),
            Skill(name="NLP", proficiency="advanced", endorsements=25, duration_months=40),
            Skill(name="Elasticsearch", proficiency="intermediate", endorsements=10, duration_months=24),
        ],
        redrob_signals=RedrobSignals(
            profile_completeness_score=92.0,
            signup_date="2025-01-01",
            last_active_date="2026-05-28",
            open_to_work_flag=True,
            recruiter_response_rate=0.85,
            avg_response_time_hours=4.0,
            notice_period_days=30,
            expected_salary_range_inr_lpa=SalaryRange(min=30, max=45),
            preferred_work_mode="hybrid",
            willing_to_relocate=True,
            github_activity_score=72.0,
            interview_completion_rate=0.95,
            profile_views_received_30d=35,
            saved_by_recruiters_30d=8,
            search_appearance_30d=150,
            verified_email=True,
            verified_phone=True,
            linkedin_connected=True,
        ),
    )


@pytest.fixture
def weak_candidate() -> CandidateData:
    """A poor-fit candidate: marketing manager with AI keywords stuffed in skills."""
    return CandidateData(
        candidate_id="CAND_TEST002",
        profile=CandidateProfile(
            anonymized_name="Test Weak",
            headline="Marketing Manager | Driving business outcomes",
            summary="12 years in marketing management.",
            location="Sydney",
            country="Australia",
            years_of_experience=12.0,
            current_title="Marketing Manager",
            current_company="Acme Corp",
            current_company_size="201-500",
            current_industry="Manufacturing",
        ),
        career_history=[
            CareerEntry(
                company="Acme Corp",
                title="Marketing Manager",
                start_date="2020-01-01",
                end_date=None,
                duration_months=77,
                is_current=True,
                industry="Manufacturing",
                company_size="201-500",
                description="Brand strategy and marketing campaigns for consumer products.",
            ),
        ],
        education=[
            Education(
                institution="Local College",
                degree="B.Sc",
                field_of_study="Business Administration",
                start_year=2008,
                end_year=2012,
                tier="tier_4",
            ),
        ],
        skills=[
            Skill(name="NLP", proficiency="advanced", endorsements=20, duration_months=5),
            Skill(name="PyTorch", proficiency="advanced", endorsements=15, duration_months=3),
            Skill(name="Marketing", proficiency="expert", endorsements=50, duration_months=120),
        ],
        redrob_signals=RedrobSignals(
            profile_completeness_score=45.0,
            last_active_date="2025-06-01",
            recruiter_response_rate=0.15,
            github_activity_score=-1,
            notice_period_days=90,
            preferred_work_mode="onsite",
        ),
    )


@pytest.fixture
def honeypot_candidate() -> CandidateData:
    """A honeypot candidate with impossible profile."""
    return CandidateData(
        candidate_id="CAND_TEST003",
        profile=CandidateProfile(
            anonymized_name="Test Honeypot",
            headline="AI Expert | 20+ Skills",
            summary="Expert in everything AI.",
            location="Mumbai",
            country="India",
            years_of_experience=8.0,
            current_title="AI Engineer",
            current_company="Startup X",
            current_company_size="11-50",
            current_industry="Software",
        ),
        career_history=[
            CareerEntry(
                company="Startup X",
                title="AI Engineer",
                start_date="2025-01-01",
                end_date=None,
                duration_months=6,
                is_current=True,
                industry="Software",
                company_size="11-50",
                description="Building AI systems.",
            ),
        ],
        skills=[
            Skill(name="Python", proficiency="expert", endorsements=80, duration_months=0),
            Skill(name="PyTorch", proficiency="expert", endorsements=70, duration_months=0),
            Skill(name="TensorFlow", proficiency="expert", endorsements=65, duration_months=0),
            Skill(name="NLP", proficiency="expert", endorsements=55, duration_months=1),
            Skill(name="FAISS", proficiency="expert", endorsements=45, duration_months=0),
            Skill(name="Kubernetes", proficiency="expert", endorsements=40, duration_months=2),
            Skill(name="AWS", proficiency="expert", endorsements=35, duration_months=0),
            Skill(name="MLOps", proficiency="expert", endorsements=30, duration_months=0),
            Skill(name="LLM", proficiency="expert", endorsements=50, duration_months=1),
            Skill(name="Ranking", proficiency="expert", endorsements=20, duration_months=0),
        ],
        redrob_signals=RedrobSignals(
            profile_completeness_score=95.0,
            github_activity_score=90,
        ),
    )
