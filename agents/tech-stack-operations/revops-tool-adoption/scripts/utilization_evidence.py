#!/usr/bin/env python3
"""Exact, fail-closed calculations for SaaS utilization evidence."""

from decimal import Decimal, InvalidOperation


def _count(value, name, allow_none=False):
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _decimal(value, name):
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
    return None if denominator == 0 else Decimal(numerator) / Decimal(denominator)


def cost_per(amount, count):
    amount = _decimal(amount, "amount")
    count = _count(count, "count")
    return None if count == 0 else amount / Decimal(count)


def population_receipt(
    *,
    paid_entitlements,
    assigned_entitlements,
    eligible_assigned,
    active_eligible,
    excluded=0,
    unmatched=0,
    unknown=0,
    withheld=0,
    conflicting=0,
    named_seat_model=True,
):
    if not isinstance(named_seat_model, bool):
        raise ValueError("named_seat_model must be boolean")
    paid = _count(paid_entitlements, "paid_entitlements", allow_none=not named_seat_model)
    assigned = _count(assigned_entitlements, "assigned_entitlements", allow_none=not named_seat_model)
    eligible = _count(eligible_assigned, "eligible_assigned")
    active = _count(active_eligible, "active_eligible")
    partitions = {
        "excluded": _count(excluded, "excluded"),
        "unmatched": _count(unmatched, "unmatched"),
        "unknown": _count(unknown, "unknown"),
        "withheld": _count(withheld, "withheld"),
        "conflicting": _count(conflicting, "conflicting"),
    }
    if active > eligible:
        raise ValueError("active eligible cannot exceed eligible assigned")
    if assigned is not None:
        if eligible + sum(partitions.values()) > assigned:
            raise ValueError("assigned population partitions exceed assigned entitlements")
        unclassified = assigned - eligible - sum(partitions.values())
    else:
        unclassified = None
    if named_seat_model:
        if assigned > paid:
            raise ValueError("assigned entitlements cannot exceed paid entitlements")
        assignment_rate = rate(assigned, paid)
        active_entitlement_rate = rate(active, paid)
        unassigned = paid - assigned
    else:
        assignment_rate = None
        active_entitlement_rate = None
        unassigned = None
    if partitions["conflicting"]:
        state = "CONFLICTING"
    elif partitions["unmatched"] or partitions["unknown"] or partitions["withheld"] or unclassified:
        state = "IDENTITY_REVIEW"
    elif eligible == 0:
        state = "ZERO_DENOMINATOR"
    else:
        state = "CALCULATED"
    return {
        "state": state,
        "named_seat_model": named_seat_model,
        "paid_entitlements": paid,
        "assigned_entitlements": assigned,
        "eligible_assigned": eligible,
        "active_eligible": active,
        "unassigned_entitlements": unassigned,
        "unclassified_assigned": unclassified,
        **partitions,
        "assignment_rate": assignment_rate,
        "observed_active_assigned_rate": rate(active, eligible),
        "observed_active_entitlement_rate": active_entitlement_rate,
    }


def compare_windows(
    *,
    current_numerator,
    current_denominator,
    prior_numerator,
    prior_denominator,
    same_policy,
    equal_duration,
    non_overlapping,
    comparable_coverage,
    current_mature=True,
    prior_mature=True,
):
    current_numerator = _count(current_numerator, "current_numerator")
    current_denominator = _count(current_denominator, "current_denominator")
    prior_numerator = _count(prior_numerator, "prior_numerator")
    prior_denominator = _count(prior_denominator, "prior_denominator")
    if current_numerator > current_denominator:
        raise ValueError("current numerator cannot exceed current denominator")
    if prior_numerator > prior_denominator:
        raise ValueError("prior numerator cannot exceed prior denominator")
    flags = {
        "same_policy": same_policy,
        "equal_duration": equal_duration,
        "non_overlapping": non_overlapping,
        "comparable_coverage": comparable_coverage,
        "current_mature": current_mature,
        "prior_mature": prior_mature,
    }
    if any(not isinstance(value, bool) for value in flags.values()):
        raise ValueError("comparison flags must be boolean")
    if not current_mature or not prior_mature:
        return {"state": "IMMATURE_WINDOW", "current_rate": None, "prior_rate": None, "percentage_point_change": None, "relative_change": None}
    if not all((same_policy, equal_duration, non_overlapping, comparable_coverage)):
        return {"state": "INCOMPARABLE", "current_rate": None, "prior_rate": None, "percentage_point_change": None, "relative_change": None}
    current = rate(current_numerator, current_denominator)
    prior = rate(prior_numerator, prior_denominator)
    if current is None or prior is None:
        return {"state": "ZERO_DENOMINATOR", "current_rate": current, "prior_rate": prior, "percentage_point_change": None, "relative_change": None}
    difference = current - prior
    relative = None if prior == 0 else difference / prior
    return {
        "state": "CALCULATED" if relative is not None else "RELATIVE_CHANGE_UNAVAILABLE",
        "current_rate": current,
        "prior_rate": prior,
        "percentage_point_change": difference * Decimal("100"),
        "relative_change": relative,
        "denominator_change": current_denominator - prior_denominator,
    }


def currency_total(rows, currency):
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("currency is required")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    if not rows:
        return {"state": "SOURCE_REQUIRED", "currency": currency.upper(), "record_count": 0, "total": None}
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
    return {"state": "CALCULATED", "currency": currency.upper(), "record_count": len(rows), "total": total}


def validate_evidence(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("evidence rows must be a non-empty list")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each evidence row must be an object")
        evidence_id = row.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.strip() or evidence_id in seen:
            raise ValueError("evidence IDs must be unique non-empty strings")
        for field in ("source_id", "source_version", "extracted_at", "policy_id", "event_taxonomy_version"):
            value = row.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} is required")
        aggregate_only = row.get("aggregate_only")
        if not isinstance(aggregate_only, bool):
            raise ValueError("aggregate_only must be boolean")
        seen.add(evidence_id)
    return {"state": "VALID", "evidence_count": len(rows)}


def build_tso03_handoff(
    *,
    tool_id,
    window_start,
    window_end,
    cutoff,
    timezone,
    policy_ids,
    evidence_rows,
    population,
    coverage,
    comparison_inputs,
    cost_basis=None,
):
    for value, name in ((tool_id, "tool_id"), (window_start, "window_start"), (window_end, "window_end"), (cutoff, "cutoff"), (timezone, "timezone")):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} is required")
    required_policies = {"utilization", "population", "identity", "event", "privacy", "comparison", "cost", "downstream"}
    if not isinstance(policy_ids, dict) or not required_policies.issubset(policy_ids):
        raise ValueError("required policy IDs are missing")
    for key, value in policy_ids.items():
        if not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip():
            raise ValueError("policy IDs must use non-empty string keys and values")
    verified_policies = {key: policy_ids[key].strip() for key in sorted(policy_ids)}
    validate_evidence(evidence_rows)
    verified_evidence = sorted(
        ({field: row[field] for field in ("evidence_id", "source_id", "source_version", "extracted_at", "policy_id", "event_taxonomy_version", "aggregate_only")} for row in evidence_rows),
        key=lambda row: row["evidence_id"],
    )
    population_fields = {
        "paid_entitlements",
        "assigned_entitlements",
        "eligible_assigned",
        "active_eligible",
        "excluded",
        "unmatched",
        "unknown",
        "withheld",
        "conflicting",
        "named_seat_model",
    }
    if not isinstance(population, dict) or not population_fields.issubset(population):
        raise ValueError("population receipt is required")
    verified_population = population_receipt(**{field: population[field] for field in population_fields})
    if population.get("state") != verified_population["state"]:
        raise ValueError("population state is inconsistent with population counts")
    coverage_fields = {"state", "lag", "missingness"}
    if not isinstance(coverage, dict) or set(coverage) != coverage_fields:
        raise ValueError("coverage fields are invalid")
    for field in coverage_fields:
        if not isinstance(coverage[field], str) or not coverage[field].strip():
            raise ValueError(f"coverage {field} is required")
    verified_coverage = {field: coverage[field].strip() for field in sorted(coverage)}
    comparison_fields = {
        "current_numerator",
        "current_denominator",
        "prior_numerator",
        "prior_denominator",
        "same_policy",
        "equal_duration",
        "non_overlapping",
        "comparable_coverage",
        "current_mature",
        "prior_mature",
    }
    if not isinstance(comparison_inputs, dict) or set(comparison_inputs) != comparison_fields:
        raise ValueError("comparison input fields are invalid")
    verified_comparison = compare_windows(**comparison_inputs)
    allowed_cost = None
    if cost_basis is not None:
        if not isinstance(cost_basis, dict) or set(cost_basis) != {"basis", "currency", "period", "amount"}:
            raise ValueError("cost_basis fields are invalid")
        for field in ("basis", "currency", "period"):
            if not isinstance(cost_basis[field], str) or not cost_basis[field].strip():
                raise ValueError(f"cost_basis {field} is required")
        allowed_cost = {
            "basis": cost_basis["basis"].strip(),
            "currency": cost_basis["currency"].strip().upper(),
            "period": cost_basis["period"].strip(),
            "amount": _decimal(cost_basis["amount"], "cost_basis amount"),
        }
    return {
        "lane": "ADOPTION",
        "tool_id": tool_id,
        "window_start": window_start,
        "window_end": window_end,
        "cutoff": cutoff,
        "timezone": timezone,
        "policy_ids": verified_policies,
        "evidence_ids": [row["evidence_id"] for row in verified_evidence],
        "evidence": verified_evidence,
        "population_state": verified_population["state"],
        "paid_entitlements": verified_population["paid_entitlements"],
        "assigned_entitlements": verified_population["assigned_entitlements"],
        "unassigned_entitlements": verified_population["unassigned_entitlements"],
        "eligible_assigned": verified_population["eligible_assigned"],
        "active_eligible": verified_population["active_eligible"],
        "unclassified_assigned": verified_population["unclassified_assigned"],
        "excluded": verified_population["excluded"],
        "unmatched": verified_population["unmatched"],
        "unknown": verified_population["unknown"],
        "withheld": verified_population["withheld"],
        "conflicting": verified_population["conflicting"],
        "assignment_rate": verified_population["assignment_rate"],
        "observed_active_assigned_rate": verified_population["observed_active_assigned_rate"],
        "observed_active_entitlement_rate": verified_population["observed_active_entitlement_rate"],
        "coverage": verified_coverage,
        "comparison": verified_comparison,
        "cost_basis": allowed_cost,
    }
