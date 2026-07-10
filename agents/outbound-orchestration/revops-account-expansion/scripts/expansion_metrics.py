#!/usr/bin/env python3
"""Deterministic, fail-closed helpers for account expansion reviews."""

from datetime import date
from decimal import Decimal, InvalidOperation


def _decimal(value, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{name} must be numeric")
    if not result.is_finite():
        raise ValueError(f"{name} must be finite")
    return result


def ratio(numerator, denominator, numerator_name="numerator", denominator_name="denominator"):
    numerator_value = _decimal(numerator, numerator_name)
    denominator_value = _decimal(denominator, denominator_name)
    if numerator_value < 0 or denominator_value < 0:
        raise ValueError("ratio inputs must be non-negative")
    if numerator_value > denominator_value:
        raise ValueError(f"{numerator_name} cannot exceed {denominator_name}")
    if denominator_value == 0:
        return None
    return numerator_value / denominator_value


def seat_utilization(active_users, licensed_seats):
    active = _decimal(active_users, "active_users")
    licensed = _decimal(licensed_seats, "licensed_seats")
    if active < 0 or licensed < 0:
        raise ValueError("seat counts must be non-negative")
    if licensed == 0:
        return None
    return {
        "utilization": active / licensed,
        "unused_seats": max(licensed - active, Decimal("0")),
        "overage_users": max(active - licensed, Decimal("0")),
    }


def evidence_coverage(known_count: int, eligible_count: int):
    if isinstance(known_count, bool) or isinstance(eligible_count, bool):
        raise ValueError("coverage counts must be integers")
    if not isinstance(known_count, int) or not isinstance(eligible_count, int):
        raise ValueError("coverage counts must be integers")
    if known_count < 0 or eligible_count < 0 or known_count > eligible_count:
        raise ValueError("coverage counts are invalid")
    return None if eligible_count == 0 else Decimal(known_count) / Decimal(eligible_count)


def renewal_days(cutoff: str, renewal_date: str) -> int:
    try:
        cutoff_value = date.fromisoformat(cutoff)
        renewal_value = date.fromisoformat(renewal_date)
    except (TypeError, ValueError):
        raise ValueError("cutoff and renewal_date must be ISO dates")
    return (renewal_value - cutoff_value).days


def score_candidate(components: dict, weights: dict) -> Decimal:
    if not components or set(components) != set(weights):
        raise ValueError("complete matching component and weight keys are required")
    component_values = {key: _decimal(value, key) for key, value in components.items()}
    weight_values = {key: _decimal(value, f"{key}_weight") for key, value in weights.items()}
    if any(value < 0 or value > 1 for value in component_values.values()):
        raise ValueError("component values must be within 0..1")
    if any(value < 0 or value > 1 for value in weight_values.values()):
        raise ValueError("weights must be within 0..1")
    if sum(weight_values.values(), Decimal("0")) != Decimal("1"):
        raise ValueError("weights must total exactly 1")
    return sum((component_values[key] * weight_values[key] for key in component_values), Decimal("0"))


def evaluate_eligibility(evidence: dict, policy: dict) -> dict:
    required = {"adoption_min", "utilization_min", "renewal_min_days", "renewal_max_days", "health_required"}
    if set(policy) != required:
        raise ValueError("complete approved eligibility policy is required")
    checks = {}
    for field, threshold in (("adoption", "adoption_min"), ("utilization", "utilization_min")):
        value = evidence.get(field)
        if value is None:
            checks[field] = "UNKNOWN"
        else:
            checks[field] = "PASS" if _decimal(value, field) >= _decimal(policy[threshold], threshold) else "FAIL"
    days = evidence.get("renewal_days")
    if days is None:
        checks["renewal"] = "UNKNOWN"
    elif isinstance(days, bool) or not isinstance(days, int):
        raise ValueError("renewal_days must be an integer")
    else:
        lower = int(policy["renewal_min_days"])
        upper = int(policy["renewal_max_days"])
        if lower > upper:
            raise ValueError("renewal day bounds are invalid")
        checks["renewal"] = "PASS" if lower <= days <= upper else "FAIL"
    health = evidence.get("health_eligible")
    if health is None:
        checks["health"] = "UNKNOWN"
    elif not isinstance(health, bool):
        raise ValueError("health_eligible must be boolean")
    else:
        required_health = policy["health_required"]
        if not isinstance(required_health, bool):
            raise ValueError("health_required must be boolean")
        checks["health"] = "PASS" if (not required_health or health) else "FAIL"
    if "FAIL" in checks.values():
        status = "NOT_ELIGIBLE"
    elif "UNKNOWN" in checks.values():
        status = "ELIGIBILITY_UNKNOWN"
    else:
        status = "ELIGIBLE"
    return {"status": status, "checks": checks}


def value_estimate(quantity, unit_price, currency: str) -> dict:
    quantity_value = _decimal(quantity, "quantity")
    price_value = _decimal(unit_price, "unit_price")
    currency_value = str(currency).strip().upper()
    if quantity_value < 0 or price_value < 0:
        raise ValueError("quantity and unit_price must be non-negative")
    if not currency_value:
        raise ValueError("currency is required")
    return {"quantity": str(quantity_value), "unit_price": str(price_value), "currency": currency_value, "value": str(quantity_value * price_value)}
