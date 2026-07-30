#!/usr/bin/env python3
"""Deterministic helpers for the frozen DQH-05 pilot routing rules."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


FIELD_WEIGHTS = {
    "email": 40,
    "phone": 30,
    "title": 15,
    "company": 15,
}


@dataclass(frozen=True)
class Candidate:
    value: str
    verified: bool
    observed_at: str
    provider_accuracy: float
    provider: str


def score_missing_fields(missing_fields: Iterable[str]) -> dict[str, object]:
    normalized = [field.strip().lower() for field in missing_fields]
    unknown = sorted(set(normalized) - FIELD_WEIGHTS.keys())
    if unknown:
        raise ValueError(f"unknown missing fields: {', '.join(unknown)}")
    score = sum(FIELD_WEIGHTS[field] for field in set(normalized))
    if score >= 90:
        priority = "critical"
    elif score >= 70:
        priority = "high"
    elif score >= 50:
        priority = "medium"
    else:
        priority = "low"
    return {"score": score, "priority": priority}


def route_provider(score: int, mode: str) -> dict[str, object]:
    if not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")
    if mode not in {"accuracy", "cost"}:
        raise ValueError("mode must be accuracy or cost")

    if score > 70:
        providers = ["Cleanlist"] if mode == "accuracy" else ["Apollo"]
        reason = "high missing score with strict accuracy" if mode == "accuracy" else "high missing score with cost sensitivity"
    elif score >= 50:
        providers = ["Clearbit", "Cognism"]
        reason = "medium missing score; choose using customer-measured cost and accuracy"
    else:
        providers = ["cheapest_available"]
        reason = "low missing score; confirmation enrichment"
    return {"score": score, "mode": mode, "providers": providers, "reason": reason}


def _parse_time(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def resolve_conflict(candidates: Iterable[Candidate]) -> Candidate:
    options = list(candidates)
    if not options:
        raise ValueError("at least one candidate is required")
    counts = Counter(option.value for option in options)
    return max(
        options,
        key=lambda option: (
            option.verified,
            _parse_time(option.observed_at),
            counts[option.value],
            option.provider_accuracy,
        ),
    )


def confidence_tier(score: int) -> str:
    if not 0 <= score <= 100:
        raise ValueError("confidence must be between 0 and 100")
    if score >= 95:
        return "verified_or_multi_provider"
    if score >= 85:
        return "high_accuracy_or_agreement"
    if score >= 75:
        return "single_mid_accuracy"
    return "conflict_or_low_confidence"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    score = subparsers.add_parser("score", help="score missing fields")
    score.add_argument("fields", nargs="+", choices=sorted(FIELD_WEIGHTS))

    route = subparsers.add_parser("route", help="select the pilot provider path")
    route.add_argument("--score", type=int, required=True)
    route.add_argument("--mode", choices=["accuracy", "cost"], required=True)

    confidence = subparsers.add_parser("confidence", help="classify a confidence score")
    confidence.add_argument("score", type=int)

    resolve = subparsers.add_parser("resolve", help="resolve provider conflicts from a JSON list")
    resolve.add_argument(
        "json_candidates",
        help='JSON list with value, verified, observed_at, provider_accuracy, and provider fields',
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "score":
        result: object = score_missing_fields(args.fields)
    elif args.command == "route":
        result = route_provider(args.score, args.mode)
    elif args.command == "confidence":
        result = {"score": args.score, "tier": confidence_tier(args.score)}
    else:
        raw = json.loads(args.json_candidates)
        winner = resolve_conflict(Candidate(**item) for item in raw)
        result = winner.__dict__
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
