"""
Embedding Service — local sentence-transformers model for CPU-only operation.

Uses all-MiniLM-L6-v2 (384-dim) for a good balance of quality and speed.
All embedding happens during pre-computation, not during the ranking step.
"""

from __future__ import annotations

import numpy as np
from config.settings import EMBEDDING_MODEL_NAME, EMBEDDING_BATCH_SIZE


class EmbeddingService:
    """Lazy-loaded sentence-transformers embedding service."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self._model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string. Returns a normalized vector."""
        model = self._load_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return np.array(embedding, dtype=np.float32)

    def embed_batch(self, texts: list[str], batch_size: int = EMBEDDING_BATCH_SIZE,
                    show_progress: bool = True) -> np.ndarray:
        """
        Embed a batch of texts. Returns (N, dim) array of normalized vectors.

        Args:
            texts: List of text strings to embed
            batch_size: Processing batch size for GPU/CPU efficiency
            show_progress: Whether to show a progress bar
        """
        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
        )
        return np.array(embeddings, dtype=np.float32)

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        model = self._load_model()
        return model.get_sentence_embedding_dimension()
