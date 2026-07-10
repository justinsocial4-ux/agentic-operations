#!/usr/bin/env python3
"""Exact, fail-closed metrics for event performance evidence."""

from decimal import Decimal, InvalidOperation
from statistics import median


def _count(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _decimal(value, name, allow_none=False):
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"{name} must be an exact decimal-compatible value")
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"{name} must be an exact decimal-compatible value") from error
    if not result.is_finite() or result < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return result


def coverage(known, eligible):
    known, eligible = _count(known, "known"), _count(eligible, "eligible")
    if known > eligible:
        raise ValueError("coverage counts are invalid")
    return None if eligible == 0 else Decimal(known) / Decimal(eligible)


def cost_per(cost, count):
    amount, denominator = _decimal(cost, "cost"), _count(count, "count")
    return None if denominator == 0 else amount / Decimal(denominator)


def attribution_rollup(rows, currency):
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("currency is required")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    allowed_states = {"active_pipeline", "closed_won", "closed_lost", "other"}
    seen, by_state, attributed_by_state = set(), {}, {}
    for state in allowed_states:
        by_state[state] = Decimal("0")
        attributed_by_state[state] = Decimal("0")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each row must be an object")
        opportunity_id = row.get("opportunity_id")
        if not isinstance(opportunity_id, str) or not opportunity_id.strip() or opportunity_id in seen:
            raise ValueError("opportunity IDs must be unique non-empty strings")
        row_currency = row.get("currency")
        if not isinstance(row_currency, str) or row_currency.casefold() != currency.casefold():
            raise ValueError("MIXED_CURRENCY")
        state = row.get("state")
        if state not in allowed_states:
            raise ValueError("opportunity state is invalid")
        amount = _decimal(row.get("amount"), "amount")
        credit = _decimal(row.get("credit"), "credit")
        if credit > 1:
            raise ValueError("credit must be between zero and one")
        by_state[state] += amount
        attributed_by_state[state] += amount * credit
        seen.add(opportunity_id)
    return {
        "currency": currency.upper(),
        "opportunity_count": len(rows),
        "crm_amount_by_state": by_state,
        "attributed_amount_by_state": attributed_by_state,
        "crm_amount_total": sum(by_state.values(), Decimal("0")),
        "attributed_amount_total": sum(attributed_by_state.values(), Decimal("0")),
    }


def return_metrics(
    actual_cost,
    cost_currency,
    approved_benefit=None,
    benefit_currency=None,
    finance_approved=False,
    incrementality_approved=False,
):
    cost = _decimal(actual_cost, "actual_cost")
    benefit = _decimal(approved_benefit, "approved_benefit", allow_none=True)
    if not isinstance(cost_currency, str) or not cost_currency.strip():
        raise ValueError("cost_currency is required")
    if cost == 0:
        raise ValueError("actual_cost must be greater than zero")
    if not isinstance(finance_approved, bool) or not isinstance(incrementality_approved, bool):
        raise ValueError("approval flags must be boolean")
    if benefit is None:
        return {"status": "BENEFIT_BASIS_REQUIRED", "finance_defined_return": None, "incremental_roi": None}
    if not isinstance(benefit_currency, str) or not benefit_currency.strip():
        raise ValueError("benefit_currency is required")
    if cost_currency.casefold() != benefit_currency.casefold():
        raise ValueError("MIXED_CURRENCY")
    if not finance_approved:
        return {"status": "FINANCE_APPROVAL_REQUIRED", "finance_defined_return": None, "incremental_roi": None}
    finance_return = (benefit - cost) / cost
    if not incrementality_approved:
        return {"status": "INCREMENTAL_ROI_UNAVAILABLE", "finance_defined_return": finance_return, "incremental_roi": None}
    return {"status": "INCREMENTAL_ROI_AVAILABLE", "finance_defined_return": finance_return, "incremental_roi": finance_return}


def benchmark(value, peers, direction):
    current = _decimal(value, "value")
    if not isinstance(peers, list) or not peers:
        raise ValueError("peers must be a non-empty list")
    peer_values = [_decimal(item, "peer") for item in peers]
    if direction == "lower_is_better":
        at_or_worse = sum(item >= current for item in peer_values)
    elif direction == "higher_is_better":
        at_or_worse = sum(item <= current for item in peer_values)
    else:
        raise ValueError("direction is invalid")
    return {
        "peer_count": len(peer_values),
        "median": Decimal(median(peer_values)),
        "direction": direction,
        "performance_percentile": Decimal(at_or_worse) / Decimal(len(peer_values)),
    }
