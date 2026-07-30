#!/usr/bin/env python3
"""Exact, fail-closed account policy scoring."""

from decimal import Decimal, InvalidOperation


REQUIRED_POLICY_FIELDS = ("policy_id", "version", "owner", "effective_date", "population_id", "entity_level", "cutoff")
REQUIRED_APPROVAL_FIELDS = ("analysis_scope_status", "privacy_scope_status", "downstream_use_status")


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _decimal(value, name):
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"{name} must be exact decimal-compatible data")
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"{name} must be exact decimal-compatible data") from error
    if not result.is_finite():
        raise ValueError(f"{name} must be finite")
    return result


def policy_gate(policy):
    if not isinstance(policy, dict):
        raise ValueError("policy must be an object")
    missing = [field for field in REQUIRED_POLICY_FIELDS if not isinstance(policy.get(field), str) or not policy.get(field).strip()]
    blocked = []
    for field in REQUIRED_APPROVAL_FIELDS:
        value = policy.get(field)
        if not isinstance(value, str) or not value.strip():
            missing.append(field)
        elif value != "APPROVED":
            blocked.append(field)
    status = "POLICY_EVIDENCE_REQUIRED" if missing else "POLICY_SCOPE_NOT_APPROVED" if blocked else "POLICY_EVIDENCE_PRESENT"
    return {"status": status, "missing_fields": missing, "blocked_fields": blocked}


def score_account(evidence, policy):
    gate = policy_gate(policy)
    if gate["status"] != "POLICY_EVIDENCE_PRESENT":
        return {"status": gate["status"], "gate": gate}
    if not isinstance(evidence, list) or not isinstance(policy.get("feature_rules"), list):
        raise ValueError("evidence and feature_rules must be lists")
    rules, rows = {}, {}
    for rule in policy["feature_rules"]:
        if not isinstance(rule, dict): raise ValueError("each feature rule must be an object")
        feature_id = _text(rule.get("feature_id"), "feature_id")
        if feature_id in rules: raise ValueError("feature rule IDs must be unique")
        if rule.get("component") not in {"fit", "engagement"}: raise ValueError("component is invalid")
        low, high = _decimal(rule.get("min_points"), "min_points"), _decimal(rule.get("max_points"), "max_points")
        if low > high: raise ValueError("feature point bounds are invalid")
        missing_rule = rule.get("missing_rule")
        if missing_rule not in {"UNAVAILABLE", "ZERO", "FIXED"}: raise ValueError("missing_rule is invalid")
        if missing_rule == "ZERO" and not (low <= 0 <= high): raise ValueError("ZERO missing treatment is outside feature bounds")
        fixed = None
        if missing_rule == "FIXED":
            fixed = _decimal(rule.get("fixed_points"), "fixed_points")
            if fixed < low or fixed > high: raise ValueError("fixed_points is outside feature bounds")
        rules[feature_id] = dict(rule, min_points=low, max_points=high, fixed_points=fixed)
    for row in evidence:
        if not isinstance(row, dict): raise ValueError("each evidence row must be an object")
        feature_id = _text(row.get("feature_id"), "feature_id")
        if feature_id in rows or feature_id not in rules: raise ValueError("evidence feature IDs must be unique and approved")
        if row.get("status") not in {"VERIFIED", "UNKNOWN", "CONFLICT"}: raise ValueError("evidence status is invalid")
        rows[feature_id] = row
    extra_missing = set(rules) - set(rows)
    for feature_id in extra_missing:
        rows[feature_id] = {"feature_id": feature_id, "status": "UNKNOWN", "points": None}

    receipts, totals = [], {"fit": Decimal("0"), "engagement": Decimal("0")}
    unavailable, conflicts = set(), []
    for feature_id, rule in rules.items():
        row, status, treatment = rows[feature_id], rows[feature_id]["status"], "OBSERVED"
        points = None
        if status != "VERIFIED" and row.get("points") is not None:
            raise ValueError("unknown or conflicting evidence cannot supply points")
        if status == "CONFLICT":
            conflicts.append(feature_id); unavailable.add(rule["component"]); treatment = "CONFLICT_REVIEW"
        elif status == "UNKNOWN":
            treatment = rule["missing_rule"]
            if treatment == "UNAVAILABLE": unavailable.add(rule["component"])
            elif treatment == "ZERO": points = Decimal("0")
            else: points = rule["fixed_points"]
        else:
            points = _decimal(row.get("points"), "points")
            if points < rule["min_points"] or points > rule["max_points"]: raise ValueError("observed points are outside feature bounds")
        if points is not None: totals[rule["component"]] += points
        receipts.append({"feature_id": feature_id, "component": rule["component"], "evidence_status": status, "treatment": treatment, "points": points})

    limits = policy.get("component_limits")
    if not isinstance(limits, dict): raise ValueError("component_limits must be an object")
    component_scores = {}
    for component in ("fit", "engagement"):
        limit = _decimal(limits.get(component), f"{component} limit")
        maximum_possible = sum((rule["max_points"] for rule in rules.values() if rule["component"] == component), Decimal("0"))
        if limit <= 0 or maximum_possible > limit or totals[component] > limit: raise ValueError("component limit is invalid")
        component_scores[component] = None if component in unavailable else totals[component] / limit

    combined = None
    weights = policy.get("combined_weights")
    if weights is not None:
        if not isinstance(weights, dict): raise ValueError("combined_weights must be an object")
        fit_weight, engagement_weight = _decimal(weights.get("fit"), "fit weight"), _decimal(weights.get("engagement"), "engagement weight")
        if fit_weight < 0 or engagement_weight < 0 or fit_weight + engagement_weight != 1: raise ValueError("combined weights must be non-negative and sum to one")
        if all(component_scores[item] is not None for item in ("fit", "engagement")):
            combined = (component_scores["fit"] * fit_weight + component_scores["engagement"] * engagement_weight) * Decimal("100")

    label = None
    if combined is not None and policy.get("thresholds") is not None:
        if not isinstance(policy["thresholds"], list): raise ValueError("thresholds must be a list")
        matches = []
        intervals = []
        for threshold in policy["thresholds"]:
            if not isinstance(threshold, dict): raise ValueError("each threshold must be an object")
            label_name = _text(threshold.get("label"), "label")
            minimum = _decimal(threshold.get("min_inclusive"), "min_inclusive")
            maximum = threshold.get("max_exclusive")
            maximum = None if maximum is None else _decimal(maximum, "max_exclusive")
            if minimum < 0 or minimum > 100 or (maximum is not None and (maximum <= minimum or maximum > 100)): raise ValueError("threshold bounds are invalid")
            intervals.append((minimum, Decimal("Infinity") if maximum is None else maximum, label_name))
            if combined >= minimum and (maximum is None or combined < maximum): matches.append(label_name)
        ordered = sorted(intervals)
        for previous, current in zip(ordered, ordered[1:]):
            if current[0] < previous[1]: raise ValueError("policy thresholds overlap")
        if len(matches) == 1: label = matches[0]
        elif len(matches) > 1: raise ValueError("policy thresholds overlap")

    status = "FEATURE_CONFLICT_REVIEW" if conflicts else "COMPONENT_UNAVAILABLE" if unavailable else "POLICY_SCORE_AVAILABLE"
    return {"status": status, "feature_receipts": receipts, "component_points": totals, "component_scores": component_scores, "combined_policy_score": combined, "policy_label": label, "unavailable_components": sorted(unavailable), "conflict_features": conflicts}
