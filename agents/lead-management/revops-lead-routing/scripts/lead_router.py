#!/usr/bin/env python3
"""Deterministic capacity and owner-ranking helpers for LM-03."""

from __future__ import annotations

import argparse
import json
import math
from typing import Iterable, Mapping


CAPACITY_ORDER = {"Green": 0, "Yellow": 1, "Red": 2, "Unknown": 3, "Critical": 4}
TERRITORY_ORDER = {"primary": 0, "secondary": 1, "general": 2}
CRITICAL_FLAGS = {
    "ACCOUNT_TERRITORY_CONFLICT",
    "INACTIVE_OR_INVALID_OWNER",
    "CRITICAL_CAPACITY",
    "MULTIPLE_ACCOUNT_OWNERS",
}
REVIEW_FLAGS = {
    "DUPLICATE_OR_RECENT_SAME_COMPANY_LEAD",
    "MULTI_THREADING_POLICY_CONFLICT",
    "UNMAPPED_TERRITORY",
    "STALE_CAPACITY",
}


def _finite_nonnegative(value: float, label: str) -> float:
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return value


def _ratio_component(numerator: float, denominator: float, weight: float, label: str) -> float:
    numerator = _finite_nonnegative(numerator, label)
    denominator = _finite_nonnegative(denominator, f"{label} denominator")
    if denominator == 0:
        raise ValueError(f"{label} denominator must be positive")
    return min(numerator / denominator, 1.0) * weight


def capacity_state(score: float | None) -> str:
    if score is None:
        return "Unknown"
    score = _finite_nonnegative(score, "capacity score")
    if score < 50:
        return "Green"
    if score < 85:
        return "Yellow"
    if score < 100:
        return "Red"
    return "Critical"


def calculate_capacity(
    *,
    active_opportunities: float,
    average_active_opportunities: float,
    pipeline_amount: float,
    rep_quota: float,
    activities_7d: float,
    weekly_activity_target: float,
) -> dict[str, object]:
    components = {
        "opportunity": _ratio_component(active_opportunities, average_active_opportunities, 50, "active opportunities"),
        "pipeline": _ratio_component(pipeline_amount, rep_quota, 30, "pipeline amount"),
        "activity": _ratio_component(activities_7d, weekly_activity_target, 20, "activities"),
    }
    components = {key: round(value, 4) for key, value in components.items()}
    score = round(sum(components.values()), 2)
    return {"score": score, "state": capacity_state(score), "components": components}


def _validate_candidate(candidate: Mapping[str, object]) -> None:
    owner_id = candidate.get("owner_id")
    if not isinstance(owner_id, str) or not owner_id.strip():
        raise ValueError("candidate owner_id must be a non-empty string")
    role = candidate.get("territory_role", "general")
    if role not in TERRITORY_ORDER:
        raise ValueError(f"unsupported territory role: {role}")
    state = candidate.get("capacity_state", "Unknown")
    if state not in CAPACITY_ORDER:
        raise ValueError(f"unsupported capacity state: {state}")
    position = candidate.get("round_robin_position", 0)
    if not isinstance(position, int) or position < 0:
        raise ValueError("round_robin_position must be a nonnegative integer")


def eligible(candidate: Mapping[str, object]) -> bool:
    _validate_candidate(candidate)
    return all(
        (
            bool(candidate.get("active", True)),
            bool(candidate.get("in_approved_pool", True)),
            not bool(candidate.get("excluded", False)),
            not bool(candidate.get("territory_conflict", False)),
            candidate.get("capacity_state", "Unknown") != "Critical",
        )
    )


def ranking_key(candidate: Mapping[str, object]) -> tuple[object, ...]:
    _validate_candidate(candidate)
    return (
        0 if candidate.get("existing_account_owner", False) else 1,
        TERRITORY_ORDER[str(candidate.get("territory_role", "general"))],
        CAPACITY_ORDER[str(candidate.get("capacity_state", "Unknown"))],
        0 if candidate.get("vertical_specialist", False) else 1,
        int(candidate.get("round_robin_position", 0)),
        str(candidate["owner_id"]),
    )


def rank_candidates(candidates: Iterable[Mapping[str, object]]) -> list[Mapping[str, object]]:
    return sorted((candidate for candidate in candidates if eligible(candidate)), key=ranking_key)


def escalation_decision(flags: Iterable[str]) -> dict[str, object]:
    unique = sorted(set(flags))
    critical = sorted(CRITICAL_FLAGS.intersection(unique))
    review = sorted(REVIEW_FLAGS.intersection(unique))
    manual = bool(critical) or len(review) >= 2
    return {
        "manual_review": manual,
        "critical_flags": critical,
        "review_flags": review,
        "all_flags": unique,
    }


def route(candidates: Iterable[Mapping[str, object]], flags: Iterable[str] = ()) -> dict[str, object]:
    escalation = escalation_decision(flags)
    if escalation["manual_review"]:
        return {"decision": "MANUAL_REVIEW", "selected": None, "escalation": escalation}
    ranked = rank_candidates(candidates)
    if not ranked:
        return {"decision": "MANUAL_REVIEW", "selected": None, "escalation": escalation}
    selected = dict(ranked[0])
    return {"decision": "READY", "selected": selected, "escalation": escalation}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    capacity = commands.add_parser("capacity", help="calculate capacity score and state")
    capacity.add_argument("--active-opportunities", type=float, required=True)
    capacity.add_argument("--average-active-opportunities", type=float, required=True)
    capacity.add_argument("--pipeline-amount", type=float, required=True)
    capacity.add_argument("--rep-quota", type=float, required=True)
    capacity.add_argument("--activities-7d", type=float, required=True)
    capacity.add_argument("--weekly-activity-target", type=float, required=True)

    routing = commands.add_parser("route", help="rank a JSON candidate list")
    routing.add_argument("--candidates-json", required=True)
    routing.add_argument("--flags-json", default="[]")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "capacity":
        result: object = calculate_capacity(
            active_opportunities=args.active_opportunities,
            average_active_opportunities=args.average_active_opportunities,
            pipeline_amount=args.pipeline_amount,
            rep_quota=args.rep_quota,
            activities_7d=args.activities_7d,
            weekly_activity_target=args.weekly_activity_target,
        )
    else:
        candidates = json.loads(args.candidates_json)
        flags = json.loads(args.flags_json)
        if not isinstance(candidates, list) or not isinstance(flags, list):
            raise ValueError("candidates and flags JSON must both be lists")
        result = route(candidates, flags)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
