#!/usr/bin/env python3
"""
Benchmark script — measures latency at different pool sizes.

Usage:
    python scripts/benchmark.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from config.settings import SAMPLE_CANDIDATES, ARTIFACTS_DIR
from pipeline.ingestion.candidate_parser import load_candidates
from pipeline.scoring.career_scorer import score_career
from pipeline.scoring.skill_scorer import score_skills
from pipeline.scoring.behavioral_scorer import score_behavioral
from pipeline.scoring.honeypot_detector import detect_honeypot
from pipeline.scoring.hybrid_scorer import compute_hybrid_score


def benchmark_scoring(n_candidates: int):
    """Benchmark scoring speed for N candidates."""
    candidates = load_candidates(str(SAMPLE_CANDIDATES))
    # Repeat to simulate larger pool
    if len(candidates) < n_candidates:
        factor = (n_candidates // len(candidates)) + 1
        candidates = (candidates * factor)[:n_candidates]

    print(f"\nBenchmarking {n_candidates} candidates...")
    start = time.time()

    for cand in candidates:
        detect_honeypot(cand)
        score_career(cand)
        score_skills(cand)
        score_behavioral(cand)
        compute_hybrid_score(
            candidate=cand,
            semantic_score=0.5,
            career_score=0.5,
            skill_score=0.5,
            behavioral_score=0.5,
        )

    elapsed = time.time() - start
    per_candidate = elapsed / n_candidates * 1000

    print(f"  Total: {elapsed:.2f}s")
    print(f"  Per candidate: {per_candidate:.2f}ms")
    print(f"  Throughput: {n_candidates / elapsed:.0f} candidates/sec")

    return elapsed


if __name__ == "__main__":
    for n in [50, 500, 5000]:
        benchmark_scoring(n)
    
    print("\n--- Retrieval benchmark ---")
    dim = 384
    for n in [1000, 10000, 100000]:
        embeddings = np.random.randn(n, dim).astype(np.float32)
        query = np.random.randn(dim).astype(np.float32)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        query = query / np.linalg.norm(query)

        start = time.time()
        scores = embeddings @ query
        top_500 = np.argpartition(-scores, 500)[:500]
        elapsed = (time.time() - start) * 1000

        print(f"  {n:>7} candidates: {elapsed:.1f}ms retrieval")
