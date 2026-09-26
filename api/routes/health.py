"""
Health check endpoint.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from config.settings import ARTIFACTS_DIR

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check system health and dependency availability."""
    checks = {}

    # Check artifacts exist
    artifacts_dir = Path(ARTIFACTS_DIR)
    required = ["jd_embedding.npy", "candidate_embeddings.npy", "candidate_ids.txt"]
    artifacts_ok = all((artifacts_dir / f).exists() for f in required)
    checks["artifacts"] = "ok" if artifacts_ok else "missing — run precompute.py"

    # Overall status
    status = "healthy" if artifacts_ok else "degraded"

    return {
        "status": status,
        "checks": checks,
        "version": "1.0.0",
    }
