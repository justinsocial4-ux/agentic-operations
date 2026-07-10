#!/usr/bin/env python3
"""Deterministic health-score and stall helpers for PM-01."""

from __future__ import annotations

import argparse
import json
import math
from typing import Mapping


DEFAULT_STALL_THRESHOLDS = {
    "Prospecting": 30,
    "Qualification": 30,
    "Proposal": 21,
    "Negotiation": 21,
    "Pending Signature": 14,
}


def _days(value: float, label: str) -> float:
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return value


def activity_points(days_since_activity: float | None, *, source_available: bool) -> tuple[int, int]:
    if not source_available:
        return 0, 0
    if days_since_activity is None:
        return 0, 30
    days = _days(days_since_activity, "days since activity")
    if days < 7:
        return 30, 30
    if days < 14:
        return 22, 30
    if days < 21:
        return 14, 30
    if days < 30:
        return 7, 30
    return 0, 30


def stage_age_points(days_in_stage: float | None, expected_stage_days: float | None) -> tuple[int, int]:
    if days_in_stage is None or expected_stage_days is None:
        return 0, 0
    days = _days(days_in_stage, "days in stage")
    expected = _days(expected_stage_days, "expected stage days")
    if expected == 0:
        raise ValueError("expected stage days must be positive")
    ratio = days / expected
    if ratio <= 0.5:
        return 30, 30
    if ratio <= 1.0:
        return 20, 30
    if ratio <= 1.5:
        return 10, 30
    return 0, 30


def field_points(fields: Mapping[str, bool | None]) -> tuple[int, int]:
    required = ("stage", "amount", "close_date", "next_step")
    unknown = set(fields).difference(required)
    if unknown:
        raise ValueError(f"unsupported fields: {sorted(unknown)}")
    points = 0
    coverage = 0
    for name in required:
        value = fields.get(name)
        if value is None:
            continue
        coverage += 10
        points += 10 if value else 0
    return points, coverage


def status(score: float | None, coverage: int, minimum_coverage: int = 80) -> str:
    if not 0 <= coverage <= 100:
        raise ValueError("coverage must be between 0 and 100")
    if not 0 <= minimum_coverage <= 100:
        raise ValueError("minimum coverage must be between 0 and 100")
    if coverage < minimum_coverage or score is None:
        return "Unknown"
    if score >= 60:
        return "Green"
    if score >= 40:
        return "Yellow"
    return "Red"


def score_health(
    *,
    fields: Mapping[str, bool | None],
    days_since_activity: float | None,
    activity_source_available: bool,
    days_in_stage: float | None,
    expected_stage_days: float | None,
    minimum_coverage: int = 80,
) -> dict[str, object]:
    field_score, field_coverage = field_points(fields)
    activity_score, activity_coverage = activity_points(
        days_since_activity, source_available=activity_source_available
    )
    stage_score, stage_coverage = stage_age_points(days_in_stage, expected_stage_days)
    raw = field_score + activity_score + stage_score
    coverage = field_coverage + activity_coverage + stage_coverage
    score = round(raw / coverage * 100, 1) if coverage else None
    return {
        "raw_points": raw,
        "evidence_coverage": coverage,
        "health_score": score,
        "health_status": status(score, coverage, minimum_coverage),
        "components": {
            "fields": {"points": field_score, "coverage": field_coverage},
            "activity": {"points": activity_score, "coverage": activity_coverage},
            "stage_age": {"points": stage_score, "coverage": stage_coverage},
        },
    }


def stall_status(
    *,
    stage: str,
    days_since_activity: float | None,
    activity_source_available: bool,
    deal_age_days: float,
    grace_days: int = 7,
    thresholds: Mapping[str, int] = DEFAULT_STALL_THRESHOLDS,
) -> dict[str, object]:
    age = _days(deal_age_days, "deal age days")
    if grace_days < 0:
        raise ValueError("grace days must be nonnegative")
    if not activity_source_available:
        return {"status": "STALL_UNKNOWN", "severity": None, "basis": "activity_unavailable"}
    threshold = thresholds.get(stage)
    if threshold is None or threshold <= 0:
        return {"status": "STALL_UNKNOWN", "severity": None, "basis": "stage_threshold_unavailable"}
    if age < grace_days:
        return {"status": "NOT_STALLED", "severity": None, "basis": "new_deal_grace"}
    basis = "buyer_activity"
    inactivity = days_since_activity
    if inactivity is None:
        inactivity = age
        basis = "created_age_no_activity"
    inactivity = _days(inactivity, "days since activity")
    if inactivity < threshold:
        return {"status": "NOT_STALLED", "severity": None, "basis": basis}
    severity = "CRITICAL" if inactivity >= 30 or stage == "Pending Signature" else "ALERT"
    return {
        "status": "STALLED",
        "severity": severity,
        "basis": basis,
        "threshold_days": threshold,
        "inactivity_days": inactivity,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", required=True, help="JSON object accepted by score_health")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = json.loads(args.input_json)
    if not isinstance(payload, dict):
        raise ValueError("input JSON must be an object")
    print(json.dumps(score_health(**payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
