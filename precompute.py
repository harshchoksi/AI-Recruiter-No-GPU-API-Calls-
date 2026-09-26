#!/usr/bin/env python3
"""
Pre-computation script — generates embeddings and saves artifacts to disk.

This step runs ONCE before the ranking step. It can take several minutes
and downloads the sentence-transformers model on first run.

Usage:
    python precompute.py
    python precompute.py --limit 1000  # Test with subset
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import CANDIDATES_JSONL, ARTIFACTS_DIR
from pipeline.orchestrator import RankingPipeline


def main():
    parser = argparse.ArgumentParser(description="Pre-compute embeddings for candidate ranking")
    parser.add_argument(
        "--candidates", type=str, default=str(CANDIDATES_JSONL),
        help="Path to candidates JSONL file"
    )
    parser.add_argument(
        "--output", type=str, default=str(ARTIFACTS_DIR),
        help="Output directory for artifacts"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit number of candidates to process (for testing)"
    )
    args = parser.parse_args()

    pipeline = RankingPipeline()
    pipeline.precompute(
        candidates_path=args.candidates,
        output_dir=args.output,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
