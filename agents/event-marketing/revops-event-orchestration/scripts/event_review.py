#!/usr/bin/env python3
"""Deterministic, fail-closed helpers for event evidence review."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal


def normalize(value):
    if value is None:
        return None
    result = " ".join(str(value).casefold().split())
    return result or None


def _tokens(values, name, allow_empty=False):
    if not isinstance(values, list):
        raise ValueError(f"{name} must be a list")
    if any(not isinstance(value, str) for value in values):
        raise ValueError(f"{name} must contain strings")
    normalized = [normalize(value) for value in values]
    if any(value is None for value in normalized) or len(normalized) != len(set(normalized)):
        raise ValueError(f"{name} must contain unique non-empty values")
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _identifier(value, name):
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{name} must be a string or null")
    return normalize(value)


def _instant(value, name):
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return parsed.astimezone(timezone.utc)


def evaluate_lane(signals, rules, anchor_at):
    signal_set = set(_tokens(signals, "signals", allow_empty=True))
    anchor = _instant(anchor_at, "anchor_at")
    if not isinstance(rules, list) or not rules:
        raise ValueError("rules must be a non-empty list")
    prepared = []
    seen_ids, seen_priorities = set(), set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("each rule must be an object")
        rule_id = _identifier(rule.get("rule_id"), "rule_id")
        lane_id = _identifier(rule.get("lane_id"), "lane_id")
        priority, hours = rule.get("priority"), rule.get("response_hours")
        if rule_id is None or lane_id is None or rule_id in seen_ids:
            raise ValueError("rule IDs and lane IDs must be non-empty; rule IDs must be unique")
        if isinstance(priority, bool) or not isinstance(priority, int) or priority < 0 or priority in seen_priorities:
            raise ValueError("rule priorities must be unique non-negative integers")
        if isinstance(hours, bool) or not isinstance(hours, int) or hours < 0:
            raise ValueError("response_hours must be a non-negative integer")
        all_signals = set(_tokens(rule.get("all_signals"), "all_signals"))
        any_signals = set(_tokens(rule.get("any_signals", []), "any_signals", allow_empty=True))
        prepared.append((priority, rule_id, lane_id, hours, all_signals, any_signals))
        seen_ids.add(rule_id)
        seen_priorities.add(priority)
    matches = []
    for priority, rule_id, lane_id, hours, required, optional in prepared:
        if required.issubset(signal_set) and (not optional or optional.intersection(signal_set)):
            matches.append({
                "rule_id": rule_id,
                "lane_id": lane_id,
                "priority": priority,
                "response_hours": hours,
                "matched_signals": sorted(required | optional.intersection(signal_set)),
                "due_at": (anchor + timedelta(hours=hours)).isoformat(),
            })
    if not matches:
        return {"status": "NO_POLICY_MATCH", "matches": []}
    matches.sort(key=lambda row: row["priority"])
    return {"status": "LANE_PREVIEW", "matches": matches, "selected": matches[0]}


def action_gate(lane_status, identity_state, contactability_state, enrollment_state, owner_id, approved):
    lane = normalize(lane_status)
    identity = normalize(identity_state)
    contactability = normalize(contactability_state)
    enrollment = normalize(enrollment_state)
    owner = _identifier(owner_id, "owner_id")
    if lane not in {"lane_preview", "no_policy_match"}:
        raise ValueError("lane_status is invalid")
    if identity not in {"exact", "review", "unmatched", "conflict"}:
        raise ValueError("identity_state is invalid")
    if contactability not in {"eligible", "suppressed", "ineligible", "unknown"}:
        raise ValueError("contactability_state is invalid")
    if enrollment not in {"none", "present", "unknown"}:
        raise ValueError("enrollment_state is invalid")
    if approved is not None and not isinstance(approved, bool):
        raise ValueError("approved must be boolean or null")
    if lane == "no_policy_match":
        return "NO_POLICY_MATCH"
    if identity != "exact":
        return "IDENTITY_REVIEW"
    if contactability in {"suppressed", "ineligible"}:
        return "CONTACT_BLOCKED"
    if contactability == "unknown":
        return "CONTACTABILITY_UNKNOWN"
    if enrollment == "present":
        return "ENROLLMENT_REVIEW"
    if enrollment == "unknown":
        return "ENROLLMENT_UNKNOWN"
    if owner is None:
        return "OWNER_REQUIRED"
    if approved is not True:
        return "APPROVAL_REQUIRED"
    return "PREVIEW_ELIGIBLE"


def coverage(known, eligible):
    if isinstance(known, bool) or isinstance(eligible, bool) or not isinstance(known, int) or not isinstance(eligible, int):
        raise ValueError("coverage counts must be integers")
    if known < 0 or eligible < 0 or known > eligible:
        raise ValueError("coverage counts are invalid")
    return None if eligible == 0 else Decimal(known) / Decimal(eligible)
