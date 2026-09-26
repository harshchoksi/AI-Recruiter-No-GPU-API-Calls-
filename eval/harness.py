"""
Evaluation Harness — runs the pipeline on sample data and reports quality metrics.

Usage:
    python -m eval.harness
    python -m eval.harness --verbose
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import SAMPLE_CANDIDATES, ARTIFACTS_DIR
from pipeline.orchestrator import RankingPipeline
from pipeline.ingestion.candidate_parser import load_candidates
from pipeline.scoring.honeypot_detector import detect_honeypot
from eval.metrics import check_reasoning_quality, check_honeypot_rate


def run_harness(verbose: bool = False):
    """Run evaluation harness on sample candidates."""
    print("=" * 60)
    print("EVALUATION HARNESS")
    print("=" * 60)

    # Check if artifacts exist
    artifacts_dir = Path(ARTIFACTS_DIR)
    if not (artifacts_dir / "jd_embedding.npy").exists():
        print("\nArtifacts not found. Running pre-computation on sample data first...")
        pipeline = RankingPipeline()
        pipeline.precompute(
            candidates_path=str(SAMPLE_CANDIDATES),
            output_dir=str(artifacts_dir),
        )

    # Run ranking
    print("\nRunning ranking pipeline...")
    pipeline = RankingPipeline(role_type="startup")
    start = time.time()
    shortlist = pipeline.rank(
        candidates_path=str(SAMPLE_CANDIDATES),
        artifacts_dir=str(artifacts_dir),
    )
    elapsed = time.time() - start

    # ── Quality Checks ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("QUALITY REPORT")
    print("=" * 60)

    # 1. Latency
    print(f"\n📊 Latency: {elapsed:.1f}s (limit: 300s)")
    if elapsed > 300:
        print("  ❌ FAIL: Exceeded 5-minute limit")
    else:
        print("  ✅ PASS")

    # 2. Output format
    print(f"\n📊 Output: {len(shortlist.candidates)} candidates (required: 100)")
    candidate_count = len(shortlist.candidates)
    # For sample data we may have fewer than 100
    if candidate_count > 0:
        print("  ✅ Output produced successfully")
    else:
        print("  ❌ FAIL: No candidates ranked")

    # 3. Score distribution
    if shortlist.candidates:
        scores = [c.score for c in shortlist.candidates]
        print(f"\n📊 Score Distribution:")
        print(f"  Max: {max(scores):.4f}")
        print(f"  Min: {min(scores):.4f}")
        print(f"  Mean: {sum(scores)/len(scores):.4f}")
        # Check scores are monotonically non-increasing
        is_monotonic = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
        print(f"  Monotonically decreasing: {'✅' if is_monotonic else '❌'}")

    # 4. Reasoning quality
    reasonings = [c.reasoning for c in shortlist.candidates]
    rq = check_reasoning_quality(reasonings)
    print(f"\n📊 Reasoning Quality:")
    print(f"  Empty: {rq['empty_count']}/{rq['total']} {'❌' if rq['empty_count'] > 0 else '✅'}")
    print(f"  All identical: {rq['all_identical']} {'❌' if rq['all_identical'] else '✅'}")
    print(f"  Unique ratio: {rq['unique_ratio']:.2f} {'✅' if rq['unique_ratio'] > 0.9 else '⚠️'}")
    print(f"  Avg length: {rq['avg_length']:.0f} chars")

    # 5. Honeypot detection
    print(f"\n📊 Honeypot Detection:")
    print(f"  Detected: {shortlist.honeypots_detected} honeypots in pool")
    honeypot_ids = set()
    candidates = load_candidates(str(SAMPLE_CANDIDATES))
    for c in candidates:
        is_hp, _ = detect_honeypot(c)
        if is_hp:
            honeypot_ids.add(c.candidate_id)

    predicted_ids = [c.candidate_id for c in shortlist.candidates]
    hp_rate = check_honeypot_rate(predicted_ids, honeypot_ids)
    print(f"  Honeypot rate in output: {hp_rate:.1%} (limit: 10%)")
    print(f"  {'✅ PASS' if hp_rate < 0.10 else '❌ FAIL'}")

    # 6. Top candidates analysis
    print(f"\n📊 Top 10 Candidates:")
    for c in shortlist.candidates[:10]:
        hp_flag = " 🚩HONEYPOT" if c.is_honeypot else ""
        print(f"  #{c.rank}: {c.candidate_id} — {c.name} ({c.current_title})"
              f" — Score: {c.score:.4f}{hp_flag}")
        if verbose:
            print(f"       Reasoning: {c.reasoning}")
            print(f"       Breakdown: career={c.breakdown.career_fit:.0f} "
                  f"skill={c.breakdown.skill_match:.0f} "
                  f"behavioral={c.breakdown.behavioral:.0f} "
                  f"semantic={c.breakdown.semantic_similarity:.0f}")

    # 7. Career title distribution in top results
    if shortlist.candidates:
        print(f"\n📊 Title Distribution in Top 20:")
        title_counts: dict[str, int] = {}
        for c in shortlist.candidates[:20]:
            title = c.current_title
            title_counts[title] = title_counts.get(title, 0) + 1
        for title, count in sorted(title_counts.items(), key=lambda x: -x[1]):
            print(f"  {title}: {count}")

    print(f"\n{'=' * 60}")
    print("Harness complete.")


def main():
    parser = argparse.ArgumentParser(description="Run evaluation harness")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    run_harness(verbose=args.verbose)


if __name__ == "__main__":
    main()
