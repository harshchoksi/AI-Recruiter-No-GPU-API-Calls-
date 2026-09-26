"""
FastAPI application — main entrypoint.

Provides REST endpoints for the ranking pipeline:
- POST /rank — rank candidates against a JD
- POST /explain — deep-dive on one candidate
- GET /health — system health check
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import rank, explain, health
from api.middleware.logging import RequestLoggingMiddleware

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    print("AI Recruiter API starting up...")
    yield
    print("AI Recruiter API shutting down...")


app = FastAPI(
    title="AI Recruiter — Intelligent Candidate Ranking",
    description=(
        "Semantic candidate ranking system that replaces keyword-filter recruiting "
        "with genuine understanding of roles and people."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Routes
app.include_router(health.router, tags=["Health"])
app.include_router(rank.router, prefix="/rank", tags=["Ranking"])
app.include_router(explain.router, prefix="/explain", tags=["Explanation"])

# Static files (dashboard UI)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def serve_dashboard():
    """Serve the web dashboard."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "AI Recruiter API. Visit /docs for API documentation."}

