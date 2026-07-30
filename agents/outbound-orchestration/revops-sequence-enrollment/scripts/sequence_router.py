#!/usr/bin/env python3
"""Deterministic, fail-closed sequence routing helpers."""

from decimal import Decimal


def normalize(value):
    if value is None:
        return None
    result = " ".join(str(value).casefold().split())
    return result or None


def exact_map(value, mapping):
    source = normalize(value)
    if source is None:
        return None
    normalized = {}
    for key, target in mapping.items():
        key_norm = normalize(key)
        target_norm = normalize(target)
        if key_norm is None or target_norm is None or key_norm in normalized:
            raise ValueError("mapping keys and targets must be unique and non-empty")
        normalized[key_norm] = target_norm
    return normalized.get(source)


def evaluate_eligibility(evidence):
    required_boolean = ["qualified", "contactable", "suppressed", "do_not_contact", "hard_bounce", "owner_in_scope", "cooldown_clear", "frequency_clear"]
    checks = {}
    for key in required_boolean:
        value = evidence.get(key)
        if value is None:
            checks[key] = "UNKNOWN"
        elif not isinstance(value, bool):
            raise ValueError(f"{key} must be boolean or null")
        else:
            should_be_true = key in {"qualified", "contactable", "owner_in_scope", "cooldown_clear", "frequency_clear"}
            checks[key] = "PASS" if value is should_be_true else "FAIL"
    active = evidence.get("active_enrollment_ids")
    if active is None:
        checks["active_enrollment"] = "UNKNOWN"
    elif not isinstance(active, list) or any(not normalize(v) for v in active):
        raise ValueError("active_enrollment_ids must be a list of non-empty IDs")
    else:
        checks["active_enrollment"] = "NONE" if not active else "PRESENT"
    decision_checks = [checks[key] for key in required_boolean]
    if "FAIL" in decision_checks:
        status = "INELIGIBLE"
    elif "UNKNOWN" in decision_checks or checks["active_enrollment"] == "UNKNOWN":
        status = "ELIGIBILITY_UNKNOWN"
    else:
        status = "ELIGIBLE"
    return {"status": status, "checks": checks}


def _dimension_match(value, targets, wildcard_allowed):
    value_norm = normalize(value)
    if value_norm is None:
        return False
    target_values = {normalize(item) for item in targets}
    if None in target_values:
        raise ValueError("target values must be non-empty")
    return value_norm in target_values or (wildcard_allowed and "*" in target_values)


def match_sequences(profile, library, workspace):
    dimensions = ("persona", "vertical", "engagement")
    if any(normalize(profile.get(key)) is None for key in dimensions):
        return {"status": "MAPPING_REQUIRED", "matches": []}
    matches = []
    seen_ids = set()
    for sequence in library:
        sequence_id = normalize(sequence.get("sequence_id"))
        if sequence_id is None or not isinstance(sequence.get("active"), bool):
            raise ValueError("sequence ID and active state are required")
        if sequence_id in seen_ids:
            raise ValueError("sequence IDs must be unique")
        seen_ids.add(sequence_id)
        if not sequence["active"] or normalize(sequence.get("workspace")) != normalize(workspace):
            continue
        priority = sequence.get("priority")
        if isinstance(priority, bool) or not isinstance(priority, int) or priority < 0:
            raise ValueError("sequence priority must be an integer")
        name = str(sequence.get("name", "")).strip()
        if not name:
            raise ValueError("sequence name is required")
        wildcard = sequence.get("wildcard_allowed", {})
        if all(_dimension_match(profile[key], sequence.get(f"target_{key}s", []), bool(wildcard.get(key, False))) for key in dimensions):
            matches.append({"sequence_id": sequence_id, "name": name, "priority": priority})
    if not matches:
        return {"status": "NO_MATCH", "matches": []}
    matches.sort(key=lambda row: (row["priority"], row["sequence_id"]))
    best_priority = matches[0]["priority"]
    best = [row for row in matches if row["priority"] == best_priority]
    if len(best) > 1:
        return {"status": "AMBIGUOUS_MATCH", "matches": matches, "best": best}
    return {"status": "RECOMMENDED_PREVIEW", "matches": matches, "recommended": best[0]}


def resolve_enrollment(recommended_sequence_id, active_enrollment_ids):
    recommended = normalize(recommended_sequence_id)
    if recommended is None or active_enrollment_ids is None:
        return "ENROLLMENT_UNKNOWN"
    if not isinstance(active_enrollment_ids, list):
        raise ValueError("active_enrollment_ids must be a list")
    active = [normalize(value) for value in active_enrollment_ids]
    if any(value is None for value in active) or len(active) != len(set(active)):
        raise ValueError("active enrollment IDs must be unique and non-empty")
    if not active:
        return "CLEAR_TO_PREVIEW"
    if active == [recommended]:
        return "NO_CHANGE"
    return "ENROLLMENT_CONFLICT"


def coverage(known, eligible):
    if isinstance(known, bool) or isinstance(eligible, bool) or not isinstance(known, int) or not isinstance(eligible, int):
        raise ValueError("coverage counts must be integers")
    if known < 0 or eligible < 0 or known > eligible:
        raise ValueError("coverage counts are invalid")
    return None if eligible == 0 else Decimal(known) / Decimal(eligible)
