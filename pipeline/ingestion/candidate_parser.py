"""
Candidate Parser — loads and validates candidate data from JSONL.

Handles both the full 100K JSONL and the sample_candidates.json.
Uses streaming for the large file to keep memory manageable.
"""

from __future__ import annotations

import json
from pathlib import Path

from api.schemas.candidate import CandidateData


def load_candidates_jsonl(path: str | Path, limit: int | None = None) -> list[CandidateData]:
    """
    Load candidates from a JSONL file (one JSON object per line).

    Args:
        path: Path to the .jsonl file
        limit: Optional limit on number of candidates to load (for testing)

    Returns:
        List of parsed CandidateData objects
    """
    path = Path(path)
    candidates = []
    errors = 0

    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and len(candidates) >= limit:
                break

            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                candidate = CandidateData(**data)
                candidates.append(candidate)
            except Exception as e:
                errors += 1
                if errors <= 5:  # Only log first 5 errors
                    print(f"  Warning: Failed to parse line {i + 1}: {e}")

    print(f"Loaded {len(candidates)} candidates from {path.name} ({errors} parse errors)")
    return candidates


def load_candidates_json(path: str | Path, limit: int | None = None) -> list[CandidateData]:
    """
    Load candidates from a JSON array file (sample_candidates.json).

    Args:
        path: Path to the .json file
        limit: Optional limit

    Returns:
        List of parsed CandidateData objects
    """
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    candidates = []
    for item in data[:limit]:
        try:
            candidate = CandidateData(**item)
            candidates.append(candidate)
        except Exception as e:
            print(f"  Warning: Failed to parse candidate {item.get('candidate_id', '?')}: {e}")

    print(f"Loaded {len(candidates)} candidates from {path.name}")
    return candidates


def load_candidates(path: str | Path, limit: int | None = None) -> list[CandidateData]:
    """Auto-detect file format and load candidates."""
    path = Path(path)
    if path.suffix == ".jsonl":
        return load_candidates_jsonl(path, limit)
    elif path.suffix == ".json":
        return load_candidates_json(path, limit)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .jsonl or .json")
