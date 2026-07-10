#!/usr/bin/env python3
"""Deterministic stakeholder coverage and candidate-priority helpers."""

from __future__ import annotations

import math
from typing import Iterable, Mapping


WEIGHTS = {
    "role_fit": 0.30,
    "department_fit": 0.20,
    "seniority_fit": 0.15,
    "relationship_evidence": 0.20,
    "engagement_evidence": 0.15,
}


def engagement_status(days_since_activity: object | None, *, activity_coverage_available: bool = True) -> str:
    if not activity_coverage_available:
        return "UNKNOWN"
    if days_since_activity is None:
        return "UNCONTACTED"
    if isinstance(days_since_activity, bool) or not isinstance(days_since_activity, (int, float)) or not math.isfinite(days_since_activity) or days_since_activity < 0:
        raise ValueError("days_since_activity must be a finite nonnegative number")
    if days_since_activity <= 30:
        return "ACTIVE"
    if days_since_activity <= 90:
        return "COLD"
    return "DORMANT"


def candidate_score(components: Mapping[str, object]) -> dict[str, object]:
    missing = [name for name in WEIGHTS if name not in components]
    extras = [name for name in components if name not in WEIGHTS]
    if missing or extras:
        return {"status": "INCOMPLETE", "score": None, "missing": missing, "extra": extras}
    normalized: dict[str, float] = {}
    for name in WEIGHTS:
        value = components[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"{name} must be a finite number from 0 to 1")
        normalized[name] = float(value)
    contributions = {name: round(normalized[name] * weight, 4) for name, weight in WEIGHTS.items()}
    return {"status": "COMPLETE", "score": round(sum(contributions.values()), 4), "contributions": contributions}


def assess_coverage(
    required_roles: Iterable[str],
    assignments: Iterable[Mapping[str, object]],
    *,
    late_stage: bool,
    activity_coverage_available: bool = True,
) -> dict[str, object]:
    required = list(dict.fromkeys(required_roles))
    if not required:
        return {"status": "DATA_GAP", "reasons": ["required_role_policy_missing"]}
    rows = list(assignments)
    active_contacts: set[str] = set()
    verified_active: set[str] = set()
    inferred_active: set[str] = set()
    cold_verified: set[str] = set()
    identified: set[str] = set()
    for row in rows:
        role = str(row["role"])
        if role not in required:
            continue
        contact_id = str(row["contact_id"])
        evidence = str(row["evidence_level"]).upper()
        status = str(row["engagement_status"]).upper()
        if evidence not in {"VERIFIED", "INFERRED_CANDIDATE", "UNKNOWN"}:
            raise ValueError("invalid evidence_level")
        if status not in {"ACTIVE", "COLD", "DORMANT", "UNCONTACTED", "UNKNOWN"}:
            raise ValueError("invalid engagement_status")
        if evidence != "UNKNOWN":
            identified.add(role)
        if status == "ACTIVE":
            active_contacts.add(contact_id)
            if evidence == "VERIFIED":
                verified_active.add(role)
            elif evidence == "INFERRED_CANDIDATE":
                inferred_active.add(role)
        elif evidence == "VERIFIED" and status in {"COLD", "DORMANT"}:
            cold_verified.add(role)

    activity_unknown = any(str(row["engagement_status"]).upper() == "UNKNOWN" for row in rows)
    if not activity_coverage_available or activity_unknown:
        single_point = None
    else:
        single_point = len(active_contacts) == 1
    missing = sorted(set(required) - identified)
    inferred_only = sorted((inferred_active - verified_active) & set(required))
    inactive_verified = sorted((cold_verified - verified_active) & set(required))
    missing_verified_active = sorted(set(required) - verified_active)
    reasons: list[str] = []
    if single_point:
        reasons.append("single_active_stakeholder")
    if missing_verified_active:
        reasons.append("required_roles_not_verified_active")
    if not activity_coverage_available or activity_unknown:
        priority = "DATA_GAP"
        reasons.append("activity_coverage_missing")
    elif late_stage and (single_point or missing_verified_active):
        priority = "URGENT_REVIEW"
    elif single_point or missing_verified_active:
        priority = "REVIEW"
    else:
        priority = "HEALTHY"
    return {
        "status": priority,
        "distinct_active_stakeholders": len(active_contacts) if activity_coverage_available else None,
        "verified_active_roles": sorted(verified_active),
        "inferred_only_active_roles": inferred_only,
        "inactive_verified_roles": inactive_verified,
        "missing_roles": missing,
        "missing_verified_active_roles": missing_verified_active,
        "single_point_of_failure": single_point,
        "reasons": reasons,
    }


def rank_candidates(candidates: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    results = []
    for candidate in candidates:
        result = candidate_score(candidate["components"])
        row = dict(candidate)
        row.update(result)
        results.append(row)
    complete = [row for row in results if row["status"] == "COMPLETE"]
    incomplete = [row for row in results if row["status"] != "COMPLETE"]
    complete.sort(key=lambda row: (-float(row["score"]), -float(row["components"]["relationship_evidence"]), -float(row["components"]["engagement_evidence"]), str(row["contact_id"])))
    return complete + incomplete
