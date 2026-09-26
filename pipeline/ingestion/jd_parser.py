"""
JD Parser — reads the job description from the docx file.

For the hackathon, the JD is fixed (Senior AI Engineer at Redrob).
We pre-parse it into structured config in config/jd_config.py.
This module provides the raw text loading and structured extraction.
"""

from __future__ import annotations

from pathlib import Path

from api.schemas.job import ParsedJD


# The JD is pre-parsed into structured config. This module provides
# a convenience function to get the parsed JD without needing to
# read the docx at runtime.
def get_parsed_jd() -> ParsedJD:
    """Return the pre-parsed JD for the hackathon challenge."""
    return ParsedJD()


def get_jd_raw_text() -> str:
    """Return the raw JD text for embedding purposes."""
    return """
Senior AI Engineer — Founding Team at Redrob AI (Series A AI-native talent intelligence platform).
Location: Pune/Noida, India (Hybrid). Experience: 5-9 years.

We need someone who is simultaneously comfortable with deep technical depth in modern ML systems
(embeddings, retrieval, ranking, LLMs, fine-tuning) and scrappy product-engineering attitude
(willing to ship a working ranker in a week even if suboptimal).

You would own the intelligence layer: ranking, retrieval, and matching systems that decide what
recruiters see when they search for candidates.

Required: Production experience with embeddings-based retrieval systems deployed to real users.
Production experience with vector databases or hybrid search infrastructure.
Strong Python. Hands-on experience designing evaluation frameworks for ranking systems (NDCG, MRR, MAP).

Nice to have: LLM fine-tuning (LoRA, QLoRA, PEFT). Learning-to-rank models.
HR-tech or marketplace experience. Distributed systems. Open-source contributions.

NOT wanted: Title-chasers. Framework enthusiasts (LangChain-only). Consulting-only careers
(TCS, Infosys, Wipro etc). Pure research without production. Computer vision/speech-only
without NLP/IR experience.
"""
