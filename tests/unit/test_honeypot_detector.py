"""Tests for honeypot detection."""

from pipeline.scoring.honeypot_detector import detect_honeypot


def test_honeypot_detected(honeypot_candidate):
    """Honeypot with 10 expert skills at 0 duration should be flagged."""
    is_hp, reasons = detect_honeypot(honeypot_candidate)
    assert is_hp is True, f"Expected honeypot but got: {reasons}"
    assert len(reasons) >= 2, f"Expected multiple reasons, got: {reasons}"


def test_strong_candidate_not_honeypot(strong_ai_candidate):
    """Legitimate strong candidate should NOT be flagged."""
    is_hp, reasons = detect_honeypot(strong_ai_candidate)
    assert is_hp is False, f"Legitimate candidate falsely flagged: {reasons}"


def test_weak_candidate_not_honeypot(weak_candidate):
    """Weak but real candidate should NOT be flagged as honeypot."""
    is_hp, reasons = detect_honeypot(weak_candidate)
    assert is_hp is False, f"Weak but real candidate falsely flagged: {reasons}"
