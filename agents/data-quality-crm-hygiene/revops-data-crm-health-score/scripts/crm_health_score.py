#!/usr/bin/env python3
"""Deterministic scoring and trend helpers for the frozen DQH-04 pilot."""

from __future__ import annotations

import argparse
import json
import math
from typing import Mapping


DIMENSIONS = (
    "completeness",
    "accuracy",
    "duplicates",
    "freshness",
    "consistency",
    "connectivity",
)

DEFAULT_WEIGHTS = {
    "completeness": 0.20,
    "accuracy": 0.15,
    "duplicates": 0.20,
    "freshness": 0.20,
    "consistency": 0.15,
    "connectivity": 0.10,
}


def _require_percentage(value: float, label: str) -> float:
    if not math.isfinite(value) or not 0 <= value <= 100:
        raise ValueError(f"{label} must be between 0 and 100")
    return value


def dimension_score(dimension: str, raw: float) -> int:
    """Map a raw percentage/rate to the exact published pilot band."""
    raw = _require_percentage(raw, "raw value")
    if dimension == "completeness":
        return 90 if raw >= 90 else 80 if raw >= 80 else 65 if raw >= 65 else 50 if raw >= 50 else 25
    if dimension == "accuracy":
        return 95 if raw >= 95 else 90 if raw >= 90 else 80 if raw >= 80 else 70 if raw >= 70 else 50
    if dimension == "duplicates":
        return 95 if raw < 3 else 90 if raw <= 5 else 75 if raw <= 10 else 50 if raw <= 20 else 25
    if dimension == "freshness":
        return 80 if raw >= 80 else 65 if raw >= 65 else 50 if raw >= 50 else 35 if raw >= 35 else 20
    if dimension == "consistency":
        return 95 if raw > 95 else 85 if raw >= 88 else 70 if raw >= 75 else 50 if raw >= 60 else 30
    if dimension == "connectivity":
        return 90 if raw > 95 else 80 if raw >= 88 else 70 if raw >= 75 else 50 if raw >= 60 else 30
    raise ValueError(f"unknown dimension: {dimension}")


def tier(score: float) -> str:
    score = _require_percentage(score, "score")
    if score >= 85:
        return "EXCELLENT"
    if score >= 75:
        return "GOOD"
    if score >= 65:
        return "AVERAGE"
    if score >= 50:
        return "POOR"
    return "CRITICAL"


def _validate_complete_mapping(values: Mapping[str, float], label: str) -> dict[str, float]:
    missing = sorted(set(DIMENSIONS) - values.keys())
    extra = sorted(values.keys() - set(DIMENSIONS))
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if extra:
            details.append(f"unknown: {', '.join(extra)}")
        raise ValueError(f"{label} must contain exactly six dimensions ({'; '.join(details)})")
    return {name: _require_percentage(float(values[name]), f"{label}.{name}") for name in DIMENSIONS}


def composite_score(
    scores: Mapping[str, float], weights: Mapping[str, float] | None = None
) -> dict[str, object]:
    checked_scores = _validate_complete_mapping(scores, "scores")
    checked_weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
    if set(checked_weights) != set(DIMENSIONS):
        raise ValueError("weights must contain exactly the six dimensions")
    if any(not math.isfinite(float(value)) or float(value) < 0 for value in checked_weights.values()):
        raise ValueError("weights must be finite and nonnegative")
    if not math.isclose(sum(float(value) for value in checked_weights.values()), 1.0, abs_tol=1e-9):
        raise ValueError("weights must sum to 1")

    contributions = {
        name: round(checked_scores[name] * float(checked_weights[name]), 4) for name in DIMENSIONS
    }
    score = round(sum(contributions.values()), 2)
    return {
        "score": score,
        "tier": tier(score),
        "contributions": contributions,
        "weights": {name: float(checked_weights[name]) for name in DIMENSIONS},
    }


def trend(
    current: Mapping[str, float], previous: Mapping[str, float], periods: float = 1
) -> dict[str, object]:
    current_values = _validate_complete_mapping(current, "current")
    previous_values = _validate_complete_mapping(previous, "previous")
    if not math.isfinite(periods) or periods <= 0:
        raise ValueError("periods must be greater than 0")

    deltas = {name: round(current_values[name] - previous_values[name], 2) for name in DIMENSIONS}
    composite_current = float(composite_score(current_values)["score"])
    composite_previous = float(composite_score(previous_values)["score"])
    delta = round(composite_current - composite_previous, 2)
    direction = "improving" if delta > 0 else "declining" if delta < 0 else "stable"
    biggest_movers = sorted(deltas.items(), key=lambda item: (-abs(item[1]), item[0]))
    return {
        "current_score": composite_current,
        "previous_score": composite_previous,
        "delta": delta,
        "direction": direction,
        "rate_per_period": round(delta / periods, 2),
        "dimension_deltas": deltas,
        "biggest_movers": biggest_movers,
    }


def _json_object(value: str) -> dict[str, float]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("JSON input must be an object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    dimension = commands.add_parser("dimension", help="map one raw metric to its pilot score band")
    dimension.add_argument("--dimension", choices=DIMENSIONS, required=True)
    dimension.add_argument("--raw", type=float, required=True)

    composite = commands.add_parser("composite", help="calculate the six-dimension weighted score")
    composite.add_argument("--scores-json", required=True)
    composite.add_argument("--weights-json")

    trend_command = commands.add_parser("trend", help="compare two complete score snapshots")
    trend_command.add_argument("--current-json", required=True)
    trend_command.add_argument("--previous-json", required=True)
    trend_command.add_argument("--periods", type=float, default=1)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "dimension":
        result: object = {
            "dimension": args.dimension,
            "raw": args.raw,
            "score": dimension_score(args.dimension, args.raw),
        }
    elif args.command == "composite":
        weights = _json_object(args.weights_json) if args.weights_json else None
        result = composite_score(_json_object(args.scores_json), weights)
    else:
        result = trend(
            _json_object(args.current_json),
            _json_object(args.previous_json),
            args.periods,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
