#!/usr/bin/env python3
"""Exact, fail-closed onboarding milestone helpers."""

from collections import Counter
from datetime import date, timedelta
from decimal import Decimal


def _day(value, name):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be an ISO date")


def milestone_state(start_date, cutoff, expected_days, completion_date=None, evidence_available=True, approved_pause_days=0):
    if isinstance(expected_days, bool) or not isinstance(expected_days, int) or expected_days < 0:
        raise ValueError("expected_days must be a non-negative integer")
    if isinstance(approved_pause_days, bool) or not isinstance(approved_pause_days, int) or approved_pause_days < 0:
        raise ValueError("approved_pause_days must be a non-negative integer")
    if not isinstance(evidence_available, bool):
        raise ValueError("evidence_available must be boolean")
    anchor = _day(start_date, "start_date")
    as_of = _day(cutoff, "cutoff")
    if as_of < anchor:
        raise ValueError("cutoff must not precede start_date")
    due = anchor + timedelta(days=expected_days + approved_pause_days)
    if not evidence_available and completion_date is not None:
        raise ValueError("completion_date conflicts with unavailable evidence")
    if not evidence_available:
        return {"due_date": due.isoformat(), "completion_date": None, "delta_days": None, "state": "UNKNOWN_EVIDENCE"}
    if completion_date is not None:
        completed = _day(completion_date, "completion_date")
        if completed < anchor:
            raise ValueError("completion_date must not precede start_date")
        if completed > as_of:
            raise ValueError("completion_date must not be after cutoff")
        delta = (completed - due).days
        state = "COMPLETED_ON_TIME" if delta <= 0 else "COMPLETED_LATE"
        return {"due_date": due.isoformat(), "completion_date": completed.isoformat(), "delta_days": delta, "state": state}
    delta = (as_of - due).days
    if delta > 0:
        return {"due_date": due.isoformat(), "completion_date": None, "delta_days": delta, "state": "DUE_NOT_RECORDED"}
    return {"due_date": due.isoformat(), "completion_date": None, "delta_days": delta, "state": "PENDING"}


def summarize_states(states):
    allowed = {"COMPLETED_ON_TIME", "COMPLETED_LATE", "DUE_NOT_RECORDED", "PENDING", "UNKNOWN_EVIDENCE"}
    if any(state not in allowed for state in states):
        raise ValueError("unknown milestone state")
    counts = Counter(states)
    return {state: counts.get(state, 0) for state in sorted(allowed)} | {"total": len(states)}


def coverage(known, eligible):
    if isinstance(known, bool) or isinstance(eligible, bool) or not isinstance(known, int) or not isinstance(eligible, int):
        raise ValueError("coverage counts must be integers")
    if known < 0 or eligible < 0 or known > eligible:
        raise ValueError("coverage counts are invalid")
    return None if eligible == 0 else Decimal(known) / Decimal(eligible)
