"""
Global settings for the AI Recruiter pipeline.
All tunable parameters in one place for easy experimentation.
"""

from pathlib import Path


# ─── Paths ───────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "[PUB] India_runs_data_and_ai_challenge" / "India_runs_data_and_ai_challenge"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)

CANDIDATES_JSONL = DATA_DIR / "candidates.jsonl"
SAMPLE_CANDIDATES = DATA_DIR / "sample_candidates.json"

# ─── Embedding Model ────────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
EMBEDDING_BATCH_SIZE = 256

# ─── Scoring Weights ────────────────────────────────────────────────────────
# These control the relative importance of each scoring signal.
# Tuned for the Redrob JD which emphasizes career fit and production AI experience.
SCORING_WEIGHTS = {
    "semantic": 0.20,       # Embedding cosine similarity
    "career": 0.30,         # Title relevance, trajectory, production experience
    "skill": 0.20,          # Skill match against JD requirements
    "behavioral": 0.15,     # Redrob platform signals (response rate, recency, etc.)
    "education": 0.05,      # Education alignment
    "experience_fit": 0.10, # Years of experience alignment with JD range
}

# ─── Ranking Parameters ─────────────────────────────────────────────────────
TOP_K_RETRIEVAL = 500       # Candidates to retrieve in semantic pass
TOP_N_OUTPUT = 100          # Final ranked output size (hackathon requires exactly 100)
MIN_SCORE_THRESHOLD = 0.01  # Minimum score to be considered

# ─── Honeypot Detection Thresholds ───────────────────────────────────────────
HONEYPOT_MAX_EXPERT_SKILLS_ZERO_DURATION = 3  # Flag if >3 expert skills with 0 months
HONEYPOT_MAX_YOE_CAREER_GAP = 5.0            # Flag if YoE exceeds career sum by >5 years
HONEYPOT_MIN_SKILL_DURATION_FOR_EXPERT = 6   # Expert should have ≥6 months in skill

# ─── Career Scoring ─────────────────────────────────────────────────────────
# Title relevance tiers (higher = more relevant to the AI Engineer JD)
TITLE_RELEVANCE = {
    # Tier 1: Direct match (0.9-1.0)
    "ai engineer": 1.0,
    "machine learning engineer": 1.0,
    "ml engineer": 1.0,
    "senior ai engineer": 1.0,
    "senior machine learning engineer": 1.0,
    "senior ml engineer": 1.0,
    "applied ai engineer": 0.95,
    "nlp engineer": 0.95,
    "applied scientist": 0.90,
    "research engineer": 0.90,

    # Tier 2: Adjacent (0.7-0.89)
    "data scientist": 0.85,
    "senior data scientist": 0.85,
    "data engineer": 0.75,
    "senior data engineer": 0.75,
    "backend engineer": 0.70,
    "senior backend engineer": 0.70,
    "software engineer": 0.70,
    "senior software engineer": 0.70,
    "full stack engineer": 0.65,
    "platform engineer": 0.65,

    # Tier 3: Tangential (0.3-0.69)
    "junior ml engineer": 0.60,
    "junior data scientist": 0.55,
    "data analyst": 0.50,
    "devops engineer": 0.45,
    "frontend engineer": 0.40,
    "qa engineer": 0.35,
    "technical lead": 0.65,
    "engineering manager": 0.55,
    "product manager": 0.40,
    "project manager": 0.30,

    # Tier 4: Poor match (0.0-0.29)
    "business analyst": 0.20,
    "marketing manager": 0.10,
    "sales executive": 0.05,
    "hr manager": 0.05,
    "accountant": 0.05,
    "content writer": 0.10,
    "graphic designer": 0.08,
    "operations manager": 0.08,
    "customer support": 0.05,
    "mechanical engineer": 0.15,
    "civil engineer": 0.10,
    "electrical engineer": 0.20,
}

# ─── Consulting Companies (JD explicitly flags these) ────────────────────────
CONSULTING_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "tech mahindra", "mindtree", "l&t infotech", "mphasis",
    "persistent systems", "cyient", "hexaware", "zensar",
}

# ─── Experience Range from JD ───────────────────────────────────────────────
IDEAL_YOE_MIN = 5.0
IDEAL_YOE_MAX = 9.0
ACCEPTABLE_YOE_MIN = 3.0  # Lower bound with strong trajectory
ACCEPTABLE_YOE_MAX = 14.0  # Upper bound before over-senior

# ─── Location Preferences ───────────────────────────────────────────────────
PREFERRED_LOCATIONS = {"pune", "noida", "delhi", "gurgaon", "gurugram", "mumbai", "hyderabad", "bangalore", "bengaluru"}
PREFERRED_COUNTRIES = {"india"}
