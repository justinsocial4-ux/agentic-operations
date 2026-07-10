#!/usr/bin/env python3
"""Deterministic weekly revenue calculations with explicit unknown states."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping


def _decimal(value: object, name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite nonnegative number")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{name} must be a finite nonnegative number") from error
    if not number.is_finite() or number < 0:
        raise ValueError(f"{name} must be a finite nonnegative number")
    return number


def _date(value: object, name: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO 8601 date") from error


def percent_delta(current: object, prior: object) -> dict[str, object]:
    current_value = _decimal(current, "current")
    prior_value = _decimal(prior, "prior")
    if prior_value == 0:
        return {"status": "UNCHANGED_ZERO" if current_value == 0 else "NEW", "percent": None}
    value = ((current_value - prior_value) / prior_value * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"status": "PERCENT", "percent": float(value)}


def classify_risk(score: float) -> str:
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError("risk score must be between 0 and 1")
    if score >= 0.70:
        return "HIGH"
    if score >= 0.40:
        return "MEDIUM"
    return "LOW"


def deal_risk(*, days_in_stage: object | None, median_stage_days: object | None, days_since_activity: object | None) -> dict[str, object]:
    result: dict[str, object] = {"stall_score": None, "silence_score": None, "composite_score": None, "risk_level": "UNKNOWN", "missing": []}
    if days_in_stage is None or median_stage_days is None:
        result["missing"].append("stage_history")
    else:
        stage_days = _decimal(days_in_stage, "days_in_stage")
        median_days = _decimal(median_stage_days, "median_stage_days")
        if median_days == 0:
            raise ValueError("median_stage_days must be positive")
        multiplier = stage_days / median_days
        result["stage_multiplier"] = float(multiplier.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        result["stall_score"] = float(max(Decimal("0"), min(Decimal("1"), (multiplier - 1) / 2)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))

    if days_since_activity is None:
        result["missing"].append("activity_history")
    else:
        silence_days = _decimal(days_since_activity, "days_since_activity")
        silence = Decimal("0") if silence_days < 7 else max(Decimal("0"), min(Decimal("1"), (silence_days - 6) / 14))
        result["silence_score"] = float(silence.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))

    if result["stall_score"] is not None and result["silence_score"] is not None:
        composite = float(result["stall_score"]) * 0.60 + float(result["silence_score"]) * 0.40
        composite = round(composite + 1e-12, 4)
        result["composite_score"] = composite
        result["risk_level"] = classify_risk(composite)
    return result


def close_date_slip(prior_close_date: object | None, current_close_date: object | None, urgent_days: int = 7) -> dict[str, object]:
    if prior_close_date is None or current_close_date is None:
        return {"status": "UNKNOWN", "slip_days": None, "urgent": None}
    if urgent_days < 0:
        raise ValueError("urgent_days must be nonnegative")
    days = (_date(current_close_date, "current_close_date") - _date(prior_close_date, "prior_close_date")).days
    return {"status": "SLIPPED" if days > 0 else "NOT_SLIPPED", "slip_days": max(0, days), "urgent": days > urgent_days}


def velocity_signal(current: int, completed_week_counts: Iterable[int]) -> dict[str, object]:
    history = list(completed_week_counts)
    if not isinstance(current, int) or isinstance(current, bool) or current < 0 or any(not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in history):
        raise ValueError("weekly counts must be nonnegative integers")
    if len(history) < 8:
        return {"status": "INSUFFICIENT_HISTORY", "weeks": len(history)}
    mean = statistics.fmean(history)
    deviation = statistics.pstdev(history)
    if deviation == 0:
        return {"status": "NO_VARIANCE_BASELINE", "mean": mean, "standard_deviation": 0.0}
    if current > mean + 2.0 * deviation:
        status = "SURGE"
    elif current < mean - 1.5 * deviation:
        status = "SLOWDOWN"
    else:
        status = "NORMAL"
    return {"status": status, "mean": round(mean, 2), "standard_deviation": round(deviation, 2)}


def weekly_metrics(records: Iterable[Mapping[str, object]], window_start: object, window_end: object) -> dict[str, object]:
    start_date = _date(window_start, "window_start")
    end_date = _date(window_end, "window_end")
    if end_date <= start_date:
        raise ValueError("window_end must be after window_start")
    rows = list(records)
    won: list[Mapping[str, object]] = []
    lost: list[Mapping[str, object]] = []
    opened: list[Mapping[str, object]] = []
    created: list[Mapping[str, object]] = []
    currencies: set[str] = set()
    for row in rows:
        if "amount" not in row:
            raise ValueError("amount is required; missing amounts cannot be treated as zero")
        amount = _decimal(row["amount"], "amount")
        currency = row.get("currency")
        if not isinstance(currency, str) or not currency.strip():
            raise ValueError("currency is required for every amount")
        currencies.add(currency.strip().upper())
        closed = row.get("is_closed")
        won_state = row.get("is_won")
        if not isinstance(closed, bool) or not isinstance(won_state, bool):
            raise ValueError("is_closed and is_won must be booleans")
        if won_state and not closed:
            raise ValueError("a nonclosed record cannot be marked won")
        normalized = dict(row)
        normalized["_amount"] = amount
        if not closed:
            opened.append(normalized)
        close_date = _date(row["close_date"], "close_date")
        if start_date <= close_date < end_date and closed:
            (won if won_state else lost).append(normalized)
        created_date = _date(row["created_date"], "created_date")
        if start_date <= created_date < end_date:
            created.append(normalized)

    won_count = len(won)
    lost_count = len(lost)
    if len(currencies) > 1:
        raise ValueError("mixed currencies must be reported separately")
    denominator = won_count + lost_count
    win_rate = None if denominator == 0 else round(won_count / denominator * 100, 2)
    money = lambda items: float(sum((row["_amount"] for row in items), Decimal("0")))
    return {
        "currency": next(iter(currencies), None),
        "closed_won_count": won_count,
        "closed_won_amount": money(won),
        "closed_lost_count": lost_count,
        "closed_lost_amount": money(lost),
        "win_rate_percent": win_rate,
        "open_pipeline_count": len(opened),
        "open_pipeline_amount": money(opened),
        "new_deal_count": len(created),
        "new_deal_amount": money(created),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path, help="JSON array of normalized records")
    parser.add_argument("--from-date", required=True)
    parser.add_argument("--to-date", required=True)
    args = parser.parse_args(argv)
    data = json.loads(args.records.read_text())
    print(json.dumps(weekly_metrics(data, args.from_date, args.to_date), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
