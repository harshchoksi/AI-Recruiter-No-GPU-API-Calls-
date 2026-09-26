#!/usr/bin/env python3
"""
Ranking script — produces the submission CSV.

This is the main entry point for the hackathon. It must:
- Complete in ≤5 minutes on CPU
- Use ≤16 GB RAM
- Make NO network calls
- Produce exactly 100 ranked candidates

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import CANDIDATES_JSONL, ARTIFACTS_DIR
from pipeline.orchestrator import RankingPipeline


def main():
    parser = argparse.ArgumentParser(
        description="Rank candidates against the JD and produce submission CSV"
    )
    parser.add_argument(
        "--candidates", type=str, default=str(CANDIDATES_JSONL),
        help="Path to candidates JSONL file"
    )
    parser.add_argument(
        "--out", type=str, default="submission.csv",
        help="Output CSV path"
    )
    parser.add_argument(
        "--artifacts", type=str, default=str(ARTIFACTS_DIR),
        help="Directory containing pre-computed artifacts"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit number of candidates (for testing)"
    )
    parser.add_argument(
        "--top-n", type=int, default=100,
        help="Number of candidates in output (default: 100)"
    )
    parser.add_argument(
        "--role-type", type=str, default="startup",
        choices=["startup", "enterprise", "default"],
        help="Weight profile to use"
    )
    args = parser.parse_args()

    # Validate artifacts exist
    artifacts_dir = Path(args.artifacts)
    required_files = ["jd_embedding.npy", "candidate_embeddings.npy", "candidate_ids.txt"]
    for fname in required_files:
        if not (artifacts_dir / fname).exists():
            print(f"ERROR: Missing artifact: {artifacts_dir / fname}")
            print("Run `python precompute.py` first to generate embeddings.")
            sys.exit(1)

    pipeline = RankingPipeline(role_type=args.role_type)
    shortlist = pipeline.rank(
        candidates_path=args.candidates,
        artifacts_dir=args.artifacts,
        output_path=args.out,
        limit=args.limit,
        top_n=args.top_n,
    )

    # Print summary
    print(f"\nTop 5 candidates:")
    for c in shortlist.candidates[:5]:
        print(f"  #{c.rank}: {c.candidate_id} — {c.name} ({c.current_title}) — Score: {c.score:.4f}")
        print(f"         {c.reasoning[:100]}...")

    honeypots_in_top100 = sum(1 for c in shortlist.candidates if c.is_honeypot)
    print(f"\nHoneypots in top-100: {honeypots_in_top100} (must be <10 for qualification)")


if __name__ == "__main__":
    main()
