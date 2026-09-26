"""
Configurable weight profiles for the hybrid scorer.
Different weight distributions for different role types.
"""

from __future__ import annotations

WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "default": {
        "semantic": 0.20,
        "career": 0.30,
        "skill": 0.20,
        "behavioral": 0.15,
        "education": 0.05,
        "experience_fit": 0.10,
    },
    "startup": {
        "semantic": 0.18,
        "career": 0.32,
        "skill": 0.18,
        "behavioral": 0.17,
        "education": 0.03,
        "experience_fit": 0.12,
    },
    "enterprise": {
        "semantic": 0.20,
        "career": 0.25,
        "skill": 0.25,
        "behavioral": 0.10,
        "education": 0.08,
        "experience_fit": 0.12,
    },
}


def get_weights(role_type: str = "startup") -> dict[str, float]:
    """Get weight profile by role type. Defaults to startup (matches Redrob JD)."""
    return WEIGHT_PROFILES.get(role_type, WEIGHT_PROFILES["default"])
