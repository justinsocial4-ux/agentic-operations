#!/usr/bin/env python3
"""Exact, fail-closed calculations for vendor evidence reviews."""

from collections import Counter
from decimal import Decimal, InvalidOperation


ALLOWED_STATES = {"MET", "NOT_MET", "INDETERMINATE", "NOT_APPLICABLE", "CONFLICTING"}
ALLOWED_EVIDENCE_KINDS = {
    "CONTRACTUAL",
    "CUSTOMER_OBSERVED",
    "VENDOR_ATTESTED",
    "INDEPENDENT",
    "UNATTRIBUTED",
}


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


def rate(numerator, denominator):
    numerator = _count(numerator, "numerator")
    denominator = _count(denominator, "denominator")
    if numerator > denominator:
        raise ValueError("numerator cannot exceed denominator")
    if denominator == 0:
        return None
    return Decimal(numerator) / Decimal(denominator)


def availability(total_minutes, excluded_minutes, downtime_minutes):
    total = _decimal(total_minutes, "total_minutes")
    excluded = _decimal(excluded_minutes, "excluded_minutes")
    downtime = _decimal(downtime_minutes, "downtime_minutes")
    if excluded > total:
        raise ValueError("excluded minutes cannot exceed total minutes")
    eligible = total - excluded
    if eligible == 0:
        return {"status": "INDETERMINATE", "eligible_minutes": eligible, "available_minutes": None, "availability_pct": None}
    if downtime > eligible:
        raise ValueError("downtime cannot exceed eligible minutes")
    available = eligible - downtime
    return {
        "status": "CALCULATED",
        "eligible_minutes": eligible,
        "available_minutes": available,
        "availability_pct": available / eligible * Decimal("100"),
    }


def assess_numeric(observed, target, comparator, *, applicable=True, complete=True, conflicting=False):
    for flag, name in ((applicable, "applicable"), (complete, "complete"), (conflicting, "conflicting")):
        if not isinstance(flag, bool):
            raise ValueError(f"{name} must be boolean")
    if conflicting:
        return "CONFLICTING"
    if not applicable:
        return "NOT_APPLICABLE"
    if not complete or observed is None or target is None:
        return "INDETERMINATE"
    value = _decimal(observed, "observed")
    threshold = _decimal(target, "target")
    operations = {
        ">=": value >= threshold,
        ">": value > threshold,
        "<=": value <= threshold,
        "<": value < threshold,
        "==": value == threshold,
    }
    if comparator not in operations:
        raise ValueError("comparator is invalid")
    return "MET" if operations[comparator] else "NOT_MET"


def validate_evidence(rows):
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each evidence row must be an object")
        evidence_id = row.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.strip() or evidence_id in seen:
            raise ValueError("evidence IDs must be unique non-empty strings")
        if row.get("evidence_kind") not in ALLOWED_EVIDENCE_KINDS:
            raise ValueError("evidence kind is invalid")
        for field in ("source_id", "source_version", "extracted_at"):
            value = row.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} is required")
        seen.add(evidence_id)
    return {"status": "VALID", "evidence_count": len(rows)}


def currency_total(rows, currency):
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("currency is required")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    if not rows:
        return {"status": "INDETERMINATE", "currency": currency.upper(), "record_count": 0, "total": None}
    seen = set()
    total = Decimal("0")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each amount row must be an object")
        record_id = row.get("record_id")
        if not isinstance(record_id, str) or not record_id.strip() or record_id in seen:
            raise ValueError("record IDs must be unique non-empty strings")
        row_currency = row.get("currency")
        if not isinstance(row_currency, str) or row_currency.casefold() != currency.casefold():
            raise ValueError("MIXED_CURRENCY")
        total += _decimal(row.get("amount"), "amount")
        seen.add(record_id)
    return {"status": "CALCULATED", "currency": currency.upper(), "record_count": len(rows), "total": total}


def summarize_states(rows):
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    seen = set()
    counts = Counter()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each assessment row must be an object")
        requirement_id = row.get("requirement_id")
        state = row.get("state")
        if not isinstance(requirement_id, str) or not requirement_id.strip() or requirement_id in seen:
            raise ValueError("requirement IDs must be unique non-empty strings")
        if state not in ALLOWED_STATES:
            raise ValueError("assessment state is invalid")
        counts[state] += 1
        seen.add(requirement_id)
    return {state: counts[state] for state in sorted(ALLOWED_STATES)}
