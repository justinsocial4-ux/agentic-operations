#!/usr/bin/env python3
"""Deterministic stage episode and transition helpers."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


def _time(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("timestamps must be ISO-8601")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def episodes(events, cutoff):
    if not events:
        raise ValueError("at least one stage-entry event is required")
    cutoff_time = _time(cutoff)
    parsed = [(str(row.get("stage_id", "")).strip(), _time(row.get("entered_at"))) for row in events]
    if any(not stage for stage, _ in parsed):
        raise ValueError("stage_id is required")
    times = [item[1] for item in parsed]
    if times != sorted(times) or len(times) != len(set(times)) or any(t > cutoff_time for t in times):
        raise ValueError("events must be uniquely ordered and not after cutoff")
    result = []
    for index, (stage, entered) in enumerate(parsed):
        exited = parsed[index + 1][1] if index + 1 < len(parsed) else cutoff_time
        result.append({"stage_id": stage, "entered_at": entered.isoformat(), "exited_at": exited.isoformat(), "days": Decimal(str((exited - entered).total_seconds())) / Decimal("86400")})
    return result


def classify_transition(from_stage, to_stage, ordered_stages, allowed_transitions=()):
    if from_stage not in ordered_stages or to_stage not in ordered_stages:
        return "UNKNOWN_STAGE"
    if (from_stage, to_stage) in set(tuple(v) for v in allowed_transitions):
        return "ALLOWED_TRANSITION"
    source = ordered_stages.index(from_stage)
    target = ordered_stages.index(to_stage)
    if target == source:
        return "REENTRY"
    if target == source + 1:
        return "ADJACENT_FORWARD"
    if target > source + 1:
        return "POLICY_SKIP"
    return "REGRESSION"


def dwell_result(days, benchmark_days, threshold_multiplier, direction="extended"):
    try:
        values = [Decimal(str(v)) for v in (days, benchmark_days, threshold_multiplier)]
    except (InvalidOperation, ValueError):
        raise ValueError("dwell values must be numeric")
    if any(not v.is_finite() or v < 0 for v in values) or values[1] == 0 or values[2] <= 0:
        raise ValueError("dwell values are invalid")
    ratio = values[0] / values[1]
    if direction == "extended":
        flagged = ratio >= values[2]
        label = "EXTENDED_DWELL" if flagged else "WITHIN_RULE"
    elif direction == "rapid":
        flagged = ratio <= values[2]
        label = "RAPID_TRANSITION" if flagged else "WITHIN_RULE"
    else:
        raise ValueError("direction must be extended or rapid")
    return {"ratio": ratio, "flagged": flagged, "label": label}


def coverage(known, eligible):
    if isinstance(known, bool) or isinstance(eligible, bool) or not isinstance(known, int) or not isinstance(eligible, int):
        raise ValueError("coverage counts must be integers")
    if known < 0 or eligible < 0 or known > eligible:
        raise ValueError("coverage counts are invalid")
    return None if eligible == 0 else Decimal(known) / Decimal(eligible)
