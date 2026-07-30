#!/usr/bin/env python3
"""Deterministic, fail-closed playbook eligibility and matching."""

from datetime import date
from decimal import Decimal


def normalize(value):
    if value is None:
        return None
    result = " ".join(str(value).casefold().split())
    return result or None


def _day(value, name):
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ValueError(f"{name} must be an ISO date")


def catalog_eligibility(playbook, cutoff, rep_groups):
    required = ["playbook_id", "version", "title", "owner", "approved", "active", "valid_from", "valid_to", "superseded", "workspace", "access_groups", "criteria", "priority"]
    if any(key not in playbook for key in required):
        raise ValueError("complete catalog metadata is required")
    if any(normalize(playbook[key]) is None for key in ("playbook_id", "version", "title", "owner", "workspace")):
        raise ValueError("catalog identity fields must be non-empty")
    for key in ("approved", "active", "superseded"):
        if not isinstance(playbook[key], bool):
            raise ValueError(f"{key} must be boolean")
    if isinstance(playbook["priority"], bool) or not isinstance(playbook["priority"], int) or playbook["priority"] < 0:
        raise ValueError("priority must be a non-negative integer")
    if not isinstance(playbook["access_groups"], list) or not isinstance(rep_groups, list):
        raise ValueError("access groups must be lists")
    if not isinstance(playbook["criteria"], dict):
        raise ValueError("criteria must be a mapping")
    cutoff_day = _day(cutoff, "cutoff")
    valid_from = _day(playbook["valid_from"], "valid_from")
    valid_to = _day(playbook["valid_to"], "valid_to")
    if valid_from > valid_to:
        raise ValueError("valid_from must not be after valid_to")
    valid = valid_from <= cutoff_day <= valid_to
    content_groups = [normalize(v) for v in playbook["access_groups"]]
    user_groups = [normalize(v) for v in rep_groups]
    if any(v is None for v in content_groups + user_groups):
        raise ValueError("access groups must be non-empty")
    access = bool(set(content_groups) & set(user_groups))
    reasons = []
    if not playbook["approved"]: reasons.append("UNAPPROVED")
    if not playbook["active"]: reasons.append("INACTIVE")
    if playbook["superseded"]: reasons.append("SUPERSEDED")
    if not valid: reasons.append("OUTSIDE_ACTIVE_DATES")
    if not access: reasons.append("ACCESS_DENIED")
    return {"eligible": not reasons, "reasons": reasons}


def match_catalog(context, catalog, cutoff, rep_groups, workspace):
    seen = set()
    matches, excluded, missing = [], [], set()
    for playbook in catalog:
        pid = normalize(playbook.get("playbook_id"))
        if pid in seen: raise ValueError("playbook IDs must be unique")
        seen.add(pid)
        eligibility = catalog_eligibility(playbook, cutoff, rep_groups)
        if normalize(playbook["workspace"]) != normalize(workspace):
            eligibility = {"eligible": False, "reasons": eligibility["reasons"] + ["WRONG_WORKSPACE"]}
        if not eligibility["eligible"]:
            excluded.append({"playbook_id": pid, "reasons": eligibility["reasons"]})
            continue
        criteria_match = True
        for field, allowed in playbook["criteria"].items():
            value = normalize(context.get(field))
            if value is None:
                missing.add(field)
                criteria_match = False
                continue
            if not isinstance(allowed, list) or not allowed:
                raise ValueError("criteria values must be non-empty lists")
            normalized_allowed = {normalize(item) for item in allowed}
            if None in normalized_allowed:
                raise ValueError("criteria values must be non-empty lists")
            if value not in normalized_allowed:
                criteria_match = False
        if criteria_match:
            matches.append({"playbook_id": pid, "version": str(playbook["version"]), "title": str(playbook["title"]), "priority": playbook["priority"]})
    if missing:
        return {"status": "CONTEXT_REQUIRED", "missing": sorted(missing), "matches": matches, "excluded": excluded}
    if not matches:
        return {"status": "NO_MATCH", "matches": [], "excluded": excluded}
    matches.sort(key=lambda row: (row["priority"], row["playbook_id"]))
    best = [row for row in matches if row["priority"] == matches[0]["priority"]]
    if len(best) > 1:
        return {"status": "AMBIGUOUS_MATCH", "matches": matches, "best": best, "excluded": excluded}
    return {"status": "RECOMMENDED_PREVIEW", "recommended": best[0], "matches": matches, "excluded": excluded}


def coverage(known, eligible):
    if isinstance(known, bool) or isinstance(eligible, bool) or not isinstance(known, int) or not isinstance(eligible, int):
        raise ValueError("coverage counts must be integers")
    if known < 0 or eligible < 0 or known > eligible:
        raise ValueError("coverage counts are invalid")
    return None if eligible == 0 else Decimal(known) / Decimal(eligible)
