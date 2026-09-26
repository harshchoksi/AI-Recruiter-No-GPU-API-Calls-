"""
JD Embedder — creates a weighted embedding of the job description.

Strategy: embed separate chunks (requirements, nice-to-haves, cultural signals)
with different weights, then compute a weighted average vector.

This captures the nuance that "production embeddings experience" matters more
than "open-source contributions" in the JD.
"""

from __future__ import annotations

import numpy as np

from pipeline.embedding.embedder import EmbeddingService


# The full JD text, chunked by importance
JD_CHUNKS = {
    "core_requirements": {
        "weight": 3.0,
        "text": (
            "Senior AI Engineer with production experience building embeddings-based retrieval "
            "and ranking systems deployed to real users. Must have hands-on experience with "
            "vector databases and hybrid search infrastructure including Pinecone Weaviate Qdrant "
            "Milvus FAISS Elasticsearch. Strong Python developer who has designed evaluation "
            "frameworks for ranking systems using NDCG MRR MAP metrics and A/B testing. "
            "Production ML system experience deploying models at scale with monitoring."
        ),
    },
    "role_context": {
        "weight": 2.0,
        "text": (
            "Own the intelligence layer of an AI recruiting platform. Build ranking retrieval "
            "and matching systems for candidate-JD matching. Ship v2 ranking system with "
            "embeddings hybrid retrieval and LLM-based re-ranking. Set up evaluation "
            "infrastructure with offline benchmarks online A/B testing and recruiter feedback loops. "
            "Series A startup growing engineering team from 4 to 12."
        ),
    },
    "nice_to_have": {
        "weight": 1.0,
        "text": (
            "LLM fine-tuning experience with LoRA QLoRA PEFT. Learning-to-rank models "
            "XGBoost neural ranking. HR-tech recruiting tech marketplace product experience. "
            "Distributed systems large-scale inference optimization. Open-source contributions "
            "in AI ML space. NLP natural language processing transformer models."
        ),
    },
    "cultural_fit": {
        "weight": 1.5,
        "text": (
            "Scrappy product-engineering mindset willing to ship fast and iterate. "
            "Async-first communication style writes a lot. Comfortable with ambiguity "
            "at early-stage startup. Can disagree openly and decide quickly. "
            "Thinks about product and user experience not just code. "
            "Plans to stay 3+ years not a title-chaser."
        ),
    },
    "anti_patterns": {
        "weight": 1.5,
        "text": (
            "NOT someone from pure consulting background TCS Infosys Wipro without product "
            "company experience. NOT pure research without production deployment. NOT framework "
            "enthusiast whose experience is just LangChain tutorials. NOT primarily computer "
            "vision speech robotics without NLP information retrieval experience. "
            "NOT someone who hasn't written production code in 18 months."
        ),
    },
}


def embed_jd(embedding_service: EmbeddingService) -> np.ndarray:
    """
    Create a weighted composite embedding of the JD.

    Each chunk is embedded separately, then combined via weighted average.
    This gives more influence to core requirements while still capturing
    cultural and anti-pattern signals.
    """
    chunk_embeddings = []
    chunk_weights = []

    for chunk_name, chunk_data in JD_CHUNKS.items():
        emb = embedding_service.embed(chunk_data["text"])
        chunk_embeddings.append(emb)
        chunk_weights.append(chunk_data["weight"])

    # Weighted average
    weights = np.array(chunk_weights, dtype=np.float32)
    embeddings = np.stack(chunk_embeddings)
    weighted = np.average(embeddings, axis=0, weights=weights)

    # Re-normalize to unit length
    norm = np.linalg.norm(weighted)
    if norm > 0:
        weighted = weighted / norm

    return weighted.astype(np.float32)
