#!/usr/bin/env python3
"""Deterministic scoring and routing extracted from the frozen DQH-03 pilot."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping


WEIGHTS = {
    "email_engagement": Decimal("0.35"),
    "phone_engagement": Decimal("0.25"),
    "title_staleness": Decimal("0.15"),
    "company_departure": Decimal("0.15"),
    "overall_engagement": Decimal("0.10"),
}


def _signal(value: object, name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number from 0 to 100")
    try:
        number = Decimal(str(value))
    except Exception as error:
        raise ValueError(f"{name} must be a finite number from 0 to 100") from error
    if not number.is_finite() or number < 0 or number > 100:
        raise ValueError(f"{name} must be a finite number from 0 to 100")
    return number


def classify(display_score: int) -> tuple[str, str]:
    if isinstance(display_score, bool) or not isinstance(display_score, int) or not 0 <= display_score <= 100:
        raise ValueError("display score must be an integer from 0 to 100")
    if display_score <= 30:
        return "ACTIVE", "MONITOR"
    if display_score <= 60:
        return "DECAYING", "RE_ENGAGE"
    if display_score <= 85:
        return "STALE", "ENRICH_AND_DECIDE"
    return "ARCHIVED_CANDIDATE", "ARCHIVE_RECOMMEND"


def score_contact(signals: Mapping[str, object]) -> dict[str, object]:
    missing = [name for name in WEIGHTS if name not in signals]
    extras = [name for name in signals if name not in WEIGHTS]
    if missing or extras:
        raise ValueError(f"signals must contain exactly {list(WEIGHTS)}; missing={missing}; extra={extras}")

    normalized = {name: _signal(signals[name], name) for name in WEIGHTS}
    contributions = {name: normalized[name] * weight for name, weight in WEIGHTS.items()}
    raw = sum(contributions.values(), Decimal("0"))
    display = int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    tier, route = classify(display)
    return {
        "raw_score": float(raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "display_score": display,
        "tier": tier,
        "route": route,
        "requires_explicit_approval": route == "ARCHIVE_RECOMMEND",
        "contributions": {name: float(value) for name, value in contributions.items()},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in WEIGHTS:
        parser.add_argument(f"--{name.replace('_', '-')}", type=float, required=True)
    args = parser.parse_args(argv)
    values = {name: getattr(args, name) for name in WEIGHTS}
    print(json.dumps(score_contact(values), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
