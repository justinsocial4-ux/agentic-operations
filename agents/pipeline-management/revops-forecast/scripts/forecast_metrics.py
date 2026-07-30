#!/usr/bin/env python3
"""Decimal-safe deterministic helpers for revenue forecast analysis."""

from decimal import Decimal, InvalidOperation


def money(value, name="amount") -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{name} must be numeric")
    if not result.is_finite() or result < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return result


def _single_currency(rows):
    currencies = {str(row.get("currency", "")).strip() for row in rows}
    if "" in currencies or len(currencies) != 1:
        raise ValueError("exactly one non-empty reporting currency is required")
    return currencies.pop()


def category_rollup(rows) -> dict:
    if not rows:
        return {"currency": None, "count": 0, "total": "0", "categories": {}}
    currency = _single_currency(rows)
    totals = {}
    counts = {}
    for row in rows:
        category = str(row.get("category", "")).strip()
        if not category:
            raise ValueError("category is required")
        amount = money(row.get("amount"))
        totals[category] = totals.get(category, Decimal("0")) + amount
        counts[category] = counts.get(category, 0) + 1
    categories = {key: {"count": counts[key], "amount": str(totals[key])} for key in sorted(totals)}
    return {"currency": currency, "count": len(rows), "total": str(sum(totals.values(), Decimal("0"))), "categories": categories}


def weighted_expectation(rows) -> dict:
    if not rows:
        return {"currency": None, "count": 0, "total_amount": "0", "weighted_expectation": "0"}
    currency = _single_currency(rows)
    total = Decimal("0")
    weighted = Decimal("0")
    for row in rows:
        amount = money(row.get("amount"))
        try:
            probability = Decimal(str(row.get("probability")))
        except (InvalidOperation, ValueError):
            raise ValueError("probability must be numeric")
        if not probability.is_finite() or not Decimal("0") <= probability <= Decimal("1"):
            raise ValueError("probability must be within 0..1")
        total += amount
        weighted += amount * probability
    return {"currency": currency, "count": len(rows), "total_amount": str(total), "weighted_expectation": str(weighted)}


def delta(current, prior) -> dict:
    current_value = money(current, "current")
    prior_value = money(prior, "prior")
    absolute = current_value - prior_value
    relative = None if prior_value == 0 else absolute / prior_value
    return {"absolute": str(absolute), "relative": None if relative is None else str(relative)}


def validate_scenarios(downside, base, upside) -> dict:
    values = [money(downside, "downside"), money(base, "base"), money(upside, "upside")]
    if not values[0] <= values[1] <= values[2]:
        raise ValueError("scenario order must be downside <= base <= upside")
    return {"downside": str(values[0]), "base": str(values[1]), "upside": str(values[2])}


def coverage(known_count: int, total_count: int):
    if isinstance(known_count, bool) or isinstance(total_count, bool) or not isinstance(known_count, int) or not isinstance(total_count, int):
        raise ValueError("coverage counts must be integers")
    if known_count < 0 or total_count < 0 or known_count > total_count:
        raise ValueError("coverage counts are invalid")
    return None if total_count == 0 else known_count / total_count


def backtest_metrics(forecasts, actuals) -> dict:
    if len(forecasts) != len(actuals) or not forecasts:
        raise ValueError("forecast and actual series must be non-empty and equal length")
    f_values = [money(v, "forecast") for v in forecasts]
    a_values = [money(v, "actual") for v in actuals]
    errors = [f - a for f, a in zip(f_values, a_values)]
    absolute_errors = [abs(v) for v in errors]
    count = Decimal(len(errors))
    total_actual = sum(a_values, Decimal("0"))
    mae = sum(absolute_errors, Decimal("0")) / count
    wape = None if total_actual == 0 else sum(absolute_errors, Decimal("0")) / total_actual
    bias = None if total_actual == 0 else sum(errors, Decimal("0")) / total_actual
    return {
        "period_count": len(errors),
        "mae": str(mae),
        "wape": None if wape is None else str(wape),
        "aggregate_bias": None if bias is None else str(bias),
        "errors": [str(v) for v in errors],
        "total_actual": str(total_actual),
    }
