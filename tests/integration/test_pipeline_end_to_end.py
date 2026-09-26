"""
Integration test — runs the full pipeline on sample data.

Requires pre-computed artifacts (run precompute.py first on sample data).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import SAMPLE_CANDIDATES, ARTIFACTS_DIR


@pytest.fixture
def artifacts_exist():
    """Check that pre-computed artifacts exist."""
    artifacts = Path(ARTIFACTS_DIR)
    required = ["jd_embedding.npy", "candidate_embeddings.npy", "candidate_ids.txt"]
    for f in required:
        if not (artifacts / f).exists():
            pytest.skip(f"Missing artifact {f}. Run precompute.py first.")


def test_full_pipeline(artifacts_exist):
    """Run the full ranking pipeline on sample data."""
    from pipeline.orchestrator import RankingPipeline

    pipeline = RankingPipeline(role_type="startup")
    shortlist = pipeline.rank(
        candidates_path=str(SAMPLE_CANDIDATES),
        artifacts_dir=str(ARTIFACTS_DIR),
        top_n=50,  # Sample only has 50 candidates
    )

    # Basic assertions
    assert len(shortlist.candidates) == 50
    assert shortlist.total_evaluated == 50

    # Scores should be monotonically non-increasing
    scores = [c.score for c in shortlist.candidates]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], f"Scores not monotonic at positions {i},{i+1}"

    # All candidates should have reasoning
    for c in shortlist.candidates:
        assert c.reasoning, f"Candidate {c.candidate_id} missing reasoning"
        assert len(c.reasoning) > 20, f"Reasoning too short for {c.candidate_id}"

    # Ranks should be 1 through N
    ranks = [c.rank for c in shortlist.candidates]
    assert ranks == list(range(1, 51))

    # No honeypots should be in top 5
    top_5_honeypots = sum(1 for c in shortlist.candidates[:5] if c.is_honeypot)
    assert top_5_honeypots == 0, "Honeypots found in top 5!"

    print(f"\n✅ Integration test passed!")
    print(f"   Top 3: {[(c.candidate_id, c.current_title, c.score) for c in shortlist.candidates[:3]]}")
