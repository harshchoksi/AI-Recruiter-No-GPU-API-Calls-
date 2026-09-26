"""
Evaluation Metrics — NDCG@K, MAP, P@K, and custom quality checks.

These match the hackathon's scoring formula:
  Final = 0.50 × NDCG@10 + 0.30 × NDCG@50 + 0.15 × MAP + 0.05 × P@10
"""

from __future__ import annotations

import math
import re


def ndcg_at_k(predicted_ids: list[str], relevance: dict[str, float], k: int) -> float:
    """
    Compute Normalized Discounted Cumulative Gain at K.

    Args:
        predicted_ids: Ordered list of candidate IDs (rank 1 first)
        relevance: Dict mapping candidate_id → relevance score (higher = more relevant)
        k: Cutoff position
    """
    dcg = 0.0
    for i, cid in enumerate(predicted_ids[:k]):
        rel = relevance.get(cid, 0.0)
        dcg += (2 ** rel - 1) / math.log2(i + 2)  # i+2 because log2(1) = 0

    # Ideal DCG: sort by relevance descending
    ideal_rels = sorted(relevance.values(), reverse=True)[:k]
    idcg = sum(
        (2 ** rel - 1) / math.log2(i + 2)
        for i, rel in enumerate(ideal_rels)
    )

    return dcg / idcg if idcg > 0 else 0.0


def precision_at_k(predicted_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Fraction of top-K that are relevant."""
    top_k = predicted_ids[:k]
    hits = sum(1 for cid in top_k if cid in relevant_ids)
    return hits / k if k > 0 else 0.0


def mean_average_precision(predicted_ids: list[str], relevant_ids: set[str]) -> float:
    """
    Mean Average Precision across all positions.
    """
    if not relevant_ids:
        return 0.0

    precision_sum = 0.0
    hits = 0

    for i, cid in enumerate(predicted_ids):
        if cid in relevant_ids:
            hits += 1
            precision_sum += hits / (i + 1)

    return precision_sum / len(relevant_ids)


def composite_score(
    predicted_ids: list[str],
    relevance: dict[str, float],
    relevant_ids: set[str],
) -> dict[str, float]:
    """
    Compute the hackathon's composite score.

    Final = 0.50 × NDCG@10 + 0.30 × NDCG@50 + 0.15 × MAP + 0.05 × P@10
    """
    ndcg10 = ndcg_at_k(predicted_ids, relevance, 10)
    ndcg50 = ndcg_at_k(predicted_ids, relevance, 50)
    map_score = mean_average_precision(predicted_ids, relevant_ids)
    p10 = precision_at_k(predicted_ids, relevant_ids, 10)

    final = 0.50 * ndcg10 + 0.30 * ndcg50 + 0.15 * map_score + 0.05 * p10

    return {
        "ndcg@10": round(ndcg10, 4),
        "ndcg@50": round(ndcg50, 4),
        "map": round(map_score, 4),
        "p@10": round(p10, 4),
        "composite": round(final, 4),
    }


def check_reasoning_quality(reasonings: list[str]) -> dict[str, any]:
    """
    Check reasoning quality per hackathon Stage 4 criteria.
    """
    results = {
        "total": len(reasonings),
        "empty_count": 0,
        "all_identical": False,
        "avg_length": 0,
        "unique_ratio": 0.0,
    }

    if not reasonings:
        return results

    results["empty_count"] = sum(1 for r in reasonings if not r or not r.strip())
    results["all_identical"] = len(set(reasonings)) == 1
    results["avg_length"] = sum(len(r) for r in reasonings) / len(reasonings)
    results["unique_ratio"] = len(set(reasonings)) / len(reasonings)

    return results


def check_honeypot_rate(predicted_ids: list[str], honeypot_ids: set[str], k: int = 100) -> float:
    """Fraction of top-K that are honeypots. Must be <10% to qualify."""
    top_k = predicted_ids[:k]
    honeypots_in_top = sum(1 for cid in top_k if cid in honeypot_ids)
    return honeypots_in_top / k if k > 0 else 0.0
