"""
Candidate Retriever — fast ANN retrieval using numpy cosine similarity.

For the hackathon, we use pre-computed embeddings loaded from disk.
At 100K candidates × 384 dims, the full matrix is ~150MB — fits easily in 16GB RAM.
Cosine similarity against all 100K takes <100ms with numpy.

No need for FAISS at this scale; numpy broadcasting is fast enough
and avoids the dependency complexity.
"""

from __future__ import annotations

import numpy as np


class CandidateRetriever:
    """Retrieve top-K candidates by cosine similarity against a JD embedding."""

    def __init__(self, candidate_embeddings: np.ndarray, candidate_ids: list[str]):
        """
        Args:
            candidate_embeddings: (N, dim) array of pre-computed, normalized candidate vectors
            candidate_ids: list of candidate IDs matching the embedding rows
        """
        assert len(candidate_ids) == candidate_embeddings.shape[0], (
            f"ID count {len(candidate_ids)} != embedding count {candidate_embeddings.shape[0]}"
        )
        self._embeddings = candidate_embeddings  # (N, dim), L2-normalized
        self._ids = candidate_ids

    def retrieve(self, jd_embedding: np.ndarray, top_k: int = 500) -> list[tuple[str, float]]:
        """
        Retrieve top-K candidates by cosine similarity.

        Since both JD and candidate embeddings are L2-normalized,
        cosine similarity = dot product.

        Args:
            jd_embedding: (dim,) normalized JD vector
            top_k: Number of candidates to retrieve

        Returns:
            List of (candidate_id, similarity_score) sorted descending
        """
        # Dot product = cosine similarity for normalized vectors
        similarities = self._embeddings @ jd_embedding  # (N,)

        # Get top-K indices
        top_k = min(top_k, len(self._ids))
        if top_k >= len(self._ids):
            # If top_k covers all candidates, just sort everything
            top_indices = np.argsort(-similarities)
        else:
            top_indices = np.argpartition(-similarities, top_k)[:top_k]
            top_indices = top_indices[np.argsort(-similarities[top_indices])]

        results = [
            (self._ids[idx], float(similarities[idx]))
            for idx in top_indices
        ]

        return results

    def retrieve_all_scores(self, jd_embedding: np.ndarray) -> dict[str, float]:
        """
        Get similarity scores for ALL candidates (for hybrid scoring).

        Returns:
            Dict mapping candidate_id → similarity score
        """
        similarities = self._embeddings @ jd_embedding
        return {
            cid: float(sim)
            for cid, sim in zip(self._ids, similarities)
        }
