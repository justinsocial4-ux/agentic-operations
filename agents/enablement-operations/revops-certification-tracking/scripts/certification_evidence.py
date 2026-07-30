#!/usr/bin/env python3
"""Deterministic pseudonymous certification-assignment evidence review."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_certification_assignment_evidence_review"
ASSIGNMENT_SOURCE_KIND = "customer-supplied-pseudonymous-assignment-evidence"
COMPLETION_SOURCE_KIND = "customer-supplied-pseudonymous-completion-evidence"
COMPLETION_STATES = {
    "recorded-complete", "recorded-incomplete", "missing", "conflicting", "suppressed", "unauthorized",
}
UNRESOLVED_MAP = {
    "missing": "EVIDENCE_MISSING",
    "conflicting": "EVIDENCE_CONFLICT",
    "suppressed": "SUPPRESSED",
    "unauthorized": "UNAUTHORIZED",
}
EXACT_STATES = {
    "recorded_complete_state": "RECORDED_COMPLETE_BY_CUTOFF",
    "recorded_incomplete_due_at_or_before_state": "RECORDED_INCOMPLETE_DUE_AT_OR_BEFORE_CUTOFF",
    "recorded_incomplete_due_after_state": "RECORDED_INCOMPLETE_DUE_AFTER_CUTOFF",
    "no_due_date_rule_state": "NO_DUE_DATE_RULE",
}
REQUIRED_PROHIBITIONS = {
    "alert", "causal-claim", "compliance-claim", "crm-read", "crm-write",
    "deadline-change", "direct-identifier", "employment-action", "enrollment-inference",
    "hr-read", "hr-write", "lms-read", "lms-write", "manager-action", "message-send",
    "performance-claim", "predictive-score", "readiness-claim", "reminder-send",
    "requirement-change", "role-inference", "worker-diagnosis", "worker-monitoring", "worker-ranking",
}
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_./:-]*$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _keys(row: dict[str, Any], required: set[str], label: str) -> None:
    actual = set(row)
    if actual != required:
        raise ValueError(
            f"{label} keys mismatch; missing={sorted(required - actual)}; extra={sorted(actual - required)}"
        )


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ValueError(f"{label} must be a stable lowercase ID")
    return value


def _anonymous(value: Any, label: str, prefix: str) -> str:
    result = _id(value, label)
    if not result.startswith(prefix):
        raise ValueError(f"{label} must begin with {prefix}")
    return result


def _token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} must be a structured token")
    return value


def _boolean(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{label} must be boolean")
    return value


def _when(value: Any, label: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        raise ValueError(f"{label} must be second-precision UTC ending in Z")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    return value, parsed.astimezone(timezone.utc)


def _optional_when(value: Any, label: str) -> tuple[str | None, datetime | None]:
    if value is None:
        return None, None
    return _when(value, label)


def _unique_ids(values: Any, label: str) -> list[str]:
    result = [_id(value, f"{label}[]") for value in _list(values, label)]
    if len(result) != len(set(result)):
        raise ValueError(f"{label} contains duplicates")
    return result


def _policy(raw: Any) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, Any]], set[str], set[tuple[str, str]]]:
    row = _object(raw, "policy")
    _keys(row, {
        "policy_id", "policy_version", "owner_role_id", "human_reviewer_role_id",
        "effective_at", "expires_at", "cutoff_at", "reviewed_at", "timezone", "approved_purpose",
        "workforce_review_receipt_id", "privacy_review_receipt_id",
        "worker_notice_program_receipt_id", "worker_access_path_receipt_id",
        "worker_response_path_receipt_id", "correction_path_receipt_id",
        "appeal_path_receipt_id", "recipient_policy_receipt_id", "retention_policy_receipt_id",
        "assignment_policy_receipt_id", "retention_rule_id", "allowed_recipient_role_ids",
        "prohibited_uses", "assignment_rules", "state_rule", "source_bindings",
    }, "policy")
    effective_text, effective = _when(row["effective_at"], "policy.effective_at")
    expires_text, expires = _optional_when(row["expires_at"], "policy.expires_at")
    cutoff_text, cutoff = _when(row["cutoff_at"], "policy.cutoff_at")
    reviewed_text, reviewed = _when(row["reviewed_at"], "policy.reviewed_at")
    if not (effective <= cutoff <= reviewed):
        raise ValueError("policy dates are not ordered")
    if expires is not None and expires < reviewed:
        raise ValueError("policy is expired at review time")
    timezone_name = _token(row["timezone"], "policy.timezone")
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("policy.timezone must be an IANA timezone") from exc
    if row["approved_purpose"] != PURPOSE:
        raise ValueError("policy.approved_purpose is not allowed")
    prohibited = _unique_ids(row["prohibited_uses"], "policy.prohibited_uses")
    if not REQUIRED_PROHIBITIONS.issubset(prohibited):
        raise ValueError("policy.prohibited_uses is missing a required boundary")
    allowed_roles = _unique_ids(row["allowed_recipient_role_ids"], "policy.allowed_recipient_role_ids")
    if not allowed_roles:
        raise ValueError("at least one allowed recipient role is required")

    raw_rule = _object(row["state_rule"], "policy.state_rule")
    _keys(raw_rule, {"rule_id", *EXACT_STATES}, "policy.state_rule")
    for field, exact_value in EXACT_STATES.items():
        if raw_rule[field] != exact_value:
            raise ValueError(f"policy.state_rule.{field} is not allowed")
    rule = {"rule_id": _id(raw_rule["rule_id"], "rule_id"), **EXACT_STATES}

    assignment_pairs: set[tuple[str, str]] = set()
    normalized_assignment_rules: list[dict[str, str]] = []
    for index, raw_assignment_rule in enumerate(_list(row["assignment_rules"], "policy.assignment_rules")):
        assignment_rule = _object(raw_assignment_rule, f"assignment_rules[{index}]")
        _keys(assignment_rule, {"anonymous_group_id", "certification_id"}, f"assignment_rules[{index}]")
        group_id = _anonymous(assignment_rule["anonymous_group_id"], "anonymous_group_id", "anonymous-group-")
        certification_id = _id(assignment_rule["certification_id"], "certification_id")
        pair = (group_id, certification_id)
        if pair in assignment_pairs:
            raise ValueError("duplicate assignment rule")
        assignment_pairs.add(pair)
        normalized_assignment_rules.append({"anonymous_group_id": group_id, "certification_id": certification_id})
    if not assignment_pairs:
        raise ValueError("at least one assignment rule is required")

    bindings: dict[tuple[str, str], dict[str, Any]] = {}
    kinds: set[str] = set()
    binding_fields = {
        "source_id", "source_version", "source_kind", "schema_id", "schema_version",
        "authorization_receipt_id", "authorization_effective_at", "authorization_expires_at",
    }
    for index, raw_binding in enumerate(_list(row["source_bindings"], "policy.source_bindings")):
        binding = _object(raw_binding, f"source_bindings[{index}]")
        _keys(binding, binding_fields, f"source_bindings[{index}]")
        source_id = _id(binding["source_id"], "source_id")
        source_version = _id(binding["source_version"], "source_version")
        source_kind = _id(binding["source_kind"], "source_kind")
        if source_kind not in {ASSIGNMENT_SOURCE_KIND, COMPLETION_SOURCE_KIND}:
            raise ValueError("source_kind is not allowed")
        auth_effective_text, auth_effective = _when(binding["authorization_effective_at"], "authorization_effective_at")
        auth_expires_text, auth_expires = _optional_when(binding["authorization_expires_at"], "authorization_expires_at")
        if auth_effective > cutoff or (auth_expires is not None and auth_expires < reviewed):
            raise ValueError("source authorization does not cover review")
        normalized = {
            "source_id": source_id,
            "source_version": source_version,
            "source_kind": source_kind,
            "schema_id": _id(binding["schema_id"], "schema_id"),
            "schema_version": _id(binding["schema_version"], "schema_version"),
            "authorization_receipt_id": _id(binding["authorization_receipt_id"], "authorization_receipt_id"),
            "authorization_effective_at": auth_effective_text,
            "authorization_expires_at": auth_expires_text,
        }
        key = (source_id, source_version)
        if key in bindings:
            raise ValueError("duplicate source binding")
        bindings[key] = normalized
        kinds.add(source_kind)
    if kinds != {ASSIGNMENT_SOURCE_KIND, COMPLETION_SOURCE_KIND}:
        raise ValueError("both assignment and completion source kinds are required")

    receipt_fields = (
        "workforce_review_receipt_id", "privacy_review_receipt_id",
        "worker_notice_program_receipt_id", "worker_access_path_receipt_id",
        "worker_response_path_receipt_id", "correction_path_receipt_id",
        "appeal_path_receipt_id", "recipient_policy_receipt_id", "retention_policy_receipt_id",
        "assignment_policy_receipt_id",
    )
    receipt_values = [_id(row[field], field) for field in receipt_fields]
    if len(receipt_values) != len(set(receipt_values)):
        raise ValueError("governance receipts must be separate")
    policy = {
        "policy_id": _id(row["policy_id"], "policy.policy_id"),
        "policy_version": _id(row["policy_version"], "policy.policy_version"),
        "owner_role_id": _id(row["owner_role_id"], "policy.owner_role_id"),
        "human_reviewer_role_id": _id(row["human_reviewer_role_id"], "policy.human_reviewer_role_id"),
        "effective_at": effective_text,
        "expires_at": expires_text,
        "cutoff_at": cutoff_text,
        "reviewed_at": reviewed_text,
        "timezone": timezone_name,
        "approved_purpose": PURPOSE,
        **dict(zip(receipt_fields, receipt_values)),
        "retention_rule_id": _id(row["retention_rule_id"], "retention_rule_id"),
        "allowed_recipient_role_ids": sorted(allowed_roles),
        "prohibited_uses": sorted(prohibited),
        "assignment_rules": sorted(normalized_assignment_rules, key=lambda item: (item["anonymous_group_id"], item["certification_id"])),
        "state_rule": rule,
        "source_bindings": [bindings[key] for key in sorted(bindings)],
    }
    return policy, bindings, set(allowed_roles), assignment_pairs


def _bound_source(row: dict[str, Any], prefix: str, bindings: dict[tuple[str, str], dict[str, Any]], expected_kind: str) -> dict[str, Any]:
    source_id = _id(row[f"{prefix}_source_id"], f"{prefix}_source_id")
    source_version = _id(row[f"{prefix}_source_version"], f"{prefix}_source_version")
    binding = bindings.get((source_id, source_version))
    if binding is None or binding["source_kind"] != expected_kind:
        raise ValueError(f"{prefix} source is not approved")
    for field in ("source_kind", "schema_id", "schema_version", "authorization_receipt_id"):
        if _id(row[f"{prefix}_{field}"], f"{prefix}_{field}") != binding[field]:
            raise ValueError(f"{prefix} {field} conflicts with source binding")
    return binding


def review_certification_evidence(document: Any) -> dict[str, Any]:
    root = _object(document, "document")
    _keys(root, {"review_id", "policy", "population", "assignments"}, "document")
    review_id = _id(root["review_id"], "review_id")
    policy, bindings, allowed_roles, assignment_pairs = _policy(root["policy"])
    cutoff = _when(policy["cutoff_at"], "policy.cutoff_at")[1]
    reviewed = _when(policy["reviewed_at"], "policy.reviewed_at")[1]
    effective = _when(policy["effective_at"], "policy.effective_at")[1]

    population = _object(root["population"], "population")
    _keys(population, {
        "population_receipt_id", "complete", "assignment_ids", "observed_at", "captured_at",
    }, "population")
    if not _boolean(population["complete"], "population.complete"):
        raise ValueError("population must be complete")
    declared_ids = _unique_ids(population["assignment_ids"], "population.assignment_ids")
    if not declared_ids:
        raise ValueError("population must declare at least one assignment")
    population_observed_text, population_observed = _when(population["observed_at"], "population.observed_at")
    population_captured_text, population_captured = _when(population["captured_at"], "population.captured_at")
    if population_observed != cutoff or not (cutoff <= population_captured <= reviewed):
        raise ValueError("population must be observed at cutoff and captured by review")

    assignment_fields = {
        "assignment_id", "anonymous_worker_id", "anonymous_group_id", "certification_id", "rule_id",
        "due_at", "no_due_date_rule",
        "assignment_source_id", "assignment_source_version", "assignment_source_kind",
        "assignment_schema_id", "assignment_schema_version", "assignment_authorization_receipt_id",
        "assignment_receipt_id", "assigned_at", "assignment_captured_at",
        "completion_source_id", "completion_source_version", "completion_source_kind",
        "completion_schema_id", "completion_schema_version", "completion_authorization_receipt_id",
        "completion_observation_receipt_id", "completion_state", "completed_at",
        "completion_observed_at", "completion_captured_at", "recipient_role_ids", "retention_rule_id",
    }
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    states: Counter[str] = Counter()
    completion_receipts: set[str] = set()
    assignment_receipts: set[str] = set()
    for index, raw_assignment in enumerate(_list(root["assignments"], "assignments")):
        row = _object(raw_assignment, f"assignments[{index}]")
        _keys(row, assignment_fields, f"assignments[{index}]")
        assignment_id = _id(row["assignment_id"], "assignment_id")
        if assignment_id in seen or assignment_id not in declared_ids:
            raise ValueError("assignment is duplicated or undeclared")
        seen.add(assignment_id)
        if _id(row["rule_id"], "rule_id") != policy["state_rule"]["rule_id"]:
            raise ValueError("assignment rule does not match policy")
        assignment_binding = _bound_source(row, "assignment", bindings, ASSIGNMENT_SOURCE_KIND)
        completion_binding = _bound_source(row, "completion", bindings, COMPLETION_SOURCE_KIND)
        assigned_text, assigned = _when(row["assigned_at"], "assigned_at")
        assignment_captured_text, assignment_captured = _when(row["assignment_captured_at"], "assignment_captured_at")
        completion_observed_text, completion_observed = _when(row["completion_observed_at"], "completion_observed_at")
        completion_captured_text, completion_captured = _when(row["completion_captured_at"], "completion_captured_at")
        if not (effective <= assigned <= assignment_captured <= cutoff):
            raise ValueError("assignment timestamps are not ordered")
        if completion_observed != cutoff or not (cutoff <= completion_captured <= population_captured):
            raise ValueError("completion evidence must be observed at cutoff and captured in population")
        for binding, observed_time, label in (
            (assignment_binding, assigned, "assignment"),
            (completion_binding, completion_observed, "completion"),
        ):
            auth_effective = _when(binding["authorization_effective_at"], "authorization_effective_at")[1]
            auth_expires = _optional_when(binding["authorization_expires_at"], "authorization_expires_at")[1]
            if observed_time < auth_effective or (auth_expires is not None and observed_time > auth_expires):
                raise ValueError(f"{label} evidence is outside authorization")

        no_due = _boolean(row["no_due_date_rule"], "no_due_date_rule")
        due_text, due = _optional_when(row["due_at"], "due_at")
        if no_due != (due is None):
            raise ValueError("due_at and no_due_date_rule conflict")
        if due is not None and due < assigned:
            raise ValueError("due_at precedes assignment")
        group_id = _anonymous(row["anonymous_group_id"], "anonymous_group_id", "anonymous-group-")
        certification_id = _id(row["certification_id"], "certification_id")
        if (group_id, certification_id) not in assignment_pairs:
            raise ValueError("assignment is not authorized by group-certification rule")
        assignment_receipt_id = _id(row["assignment_receipt_id"], "assignment_receipt_id")
        if assignment_receipt_id in assignment_receipts:
            raise ValueError("assignment receipt is reused")
        assignment_receipts.add(assignment_receipt_id)
        recipients = _unique_ids(row["recipient_role_ids"], "recipient_role_ids")
        if not recipients or not set(recipients).issubset(allowed_roles):
            raise ValueError("assignment recipients are not allowed")
        if _id(row["retention_rule_id"], "retention_rule_id") != policy["retention_rule_id"]:
            raise ValueError("assignment retention rule does not match policy")

        completion_state = row["completion_state"]
        if completion_state not in COMPLETION_STATES:
            raise ValueError("completion_state is not allowed")
        receipt = row["completion_observation_receipt_id"]
        completed_text, completed = _optional_when(row["completed_at"], "completed_at")
        if completion_state in {"recorded-complete", "recorded-incomplete"}:
            receipt = _id(receipt, "completion_observation_receipt_id")
            if receipt in completion_receipts:
                raise ValueError("completion observation receipt is reused")
            completion_receipts.add(receipt)
        elif receipt is not None or completed is not None:
            raise ValueError("unresolved completion evidence cannot claim receipt or completion time")

        if completion_state == "recorded-complete":
            if completed is None or not (assigned <= completed <= cutoff):
                raise ValueError("recorded completion time is missing or outside assignment window")
            evidence_state = EXACT_STATES["recorded_complete_state"]
        elif completion_state == "recorded-incomplete":
            if completed is not None:
                raise ValueError("recorded incomplete evidence cannot have completed_at")
            if no_due:
                evidence_state = EXACT_STATES["no_due_date_rule_state"]
            elif due <= cutoff:
                evidence_state = EXACT_STATES["recorded_incomplete_due_at_or_before_state"]
            else:
                evidence_state = EXACT_STATES["recorded_incomplete_due_after_state"]
        else:
            evidence_state = UNRESOLVED_MAP[completion_state]
        states[evidence_state] += 1

        results.append({
            "assignment_id": assignment_id,
            "anonymous_worker_id": _anonymous(row["anonymous_worker_id"], "anonymous_worker_id", "anonymous-worker-"),
            "anonymous_group_id": group_id,
            "certification_id": certification_id,
            "rule_id": policy["state_rule"]["rule_id"],
            "due_at": due_text,
            "no_due_date_rule": no_due,
            "evidence_state": evidence_state,
            "assignment_source_receipt": {
                "source_id": assignment_binding["source_id"],
                "source_version": assignment_binding["source_version"],
                "source_kind": assignment_binding["source_kind"],
                "schema_id": assignment_binding["schema_id"],
                "schema_version": assignment_binding["schema_version"],
                "authorization_receipt_id": assignment_binding["authorization_receipt_id"],
                "assignment_receipt_id": assignment_receipt_id,
                "assigned_at": assigned_text,
                "captured_at": assignment_captured_text,
            },
            "completion_source_receipt": {
                "source_id": completion_binding["source_id"],
                "source_version": completion_binding["source_version"],
                "source_kind": completion_binding["source_kind"],
                "schema_id": completion_binding["schema_id"],
                "schema_version": completion_binding["schema_version"],
                "authorization_receipt_id": completion_binding["authorization_receipt_id"],
                "observation_receipt_id": receipt,
                "recorded_state": completion_state,
                "completed_at": completed_text,
                "observed_at": completion_observed_text,
                "captured_at": completion_captured_text,
            },
            "recipient_role_ids": sorted(recipients),
            "retention_rule_id": policy["retention_rule_id"],
        })
    if seen != set(declared_ids):
        raise ValueError("assignments do not reconcile to declared population")

    return {
        "review_id": review_id,
        "review_status": "HUMAN_REVIEW_REQUIRED",
        "purpose": PURPOSE,
        "policy_receipt": policy,
        "population_receipt": {
            "population_receipt_id": _id(population["population_receipt_id"], "population_receipt_id"),
            "complete": True,
            "assignment_ids": sorted(declared_ids),
            "observed_at": population_observed_text,
            "captured_at": population_captured_text,
        },
        "assignments": sorted(results, key=lambda item: item["assignment_id"]),
        "state_summary": [
            {"state": state, "assignment_count": states[state]}
            for state in sorted(states)
        ],
        "limitations": [
            "evidence-and-time-state-only",
            "no-compliance-or-readiness-claim",
            "no-enrollment-inference",
            "no-worker-judgment",
            "no-reminder-escalation-or-system-action",
            "no-performance-or-employment-use",
            "not-legal-compliance-proof",
        ],
        "compliance_authorized": False,
        "worker_judgment_authorized": False,
        "action_authorized": False,
    }


def render_review_output(result: dict[str, Any]) -> str:
    """Render exactly once with an explicit empty terminal line."""
    return json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n\n"


def main() -> None:
    import sys

    document = json.load(sys.stdin)
    sys.stdout.write(render_review_output(review_certification_evidence(document)))


if __name__ == "__main__":
    main()
