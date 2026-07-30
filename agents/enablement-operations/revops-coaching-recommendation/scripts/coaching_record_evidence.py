#!/usr/bin/env python3
"""Deterministic pseudonymous coaching-record evidence review."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_coaching_record_evidence_review"
SOURCE_KIND = "customer-authored-pseudonymous-coaching-record"
LANE_IDS = {
    "appeal", "correction", "recipient-authorization", "retention-binding",
    "source-observation", "worker-access", "worker-notice", "worker-response",
}
LANE_STATES = {"present", "missing", "conflicting", "suppressed", "unauthorized"}
STATE_PRECEDENCE = (
    ("unauthorized", "UNAUTHORIZED"),
    ("conflicting", "EVIDENCE_CONFLICT"),
    ("suppressed", "SUPPRESSED"),
    ("missing", "EVIDENCE_MISSING"),
)
REQUIRED_PROHIBITIONS = {
    "alert", "causal-claim", "coaching-generation", "coaching-priority",
    "confidence-score", "crm-read", "crm-write", "customer-action",
    "deal-action", "direct-identifier", "employment-action", "hr-read",
    "hr-write", "manager-action", "message-send", "methodology-scoring",
    "performance-management", "performance-ranking", "predictive-score",
    "sentiment-inference", "transcript-analysis", "worker-diagnosis",
    "worker-monitoring", "worker-ranking",
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


def _policy(raw: Any) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, Any]], set[str]]:
    row = _object(raw, "policy")
    _keys(row, {
        "policy_id", "policy_version", "owner_role_id", "human_reviewer_role_id",
        "effective_at", "expires_at", "cutoff_at", "timezone", "approved_purpose",
        "workforce_review_receipt_id", "privacy_review_receipt_id",
        "worker_notice_program_receipt_id", "worker_access_path_receipt_id",
        "worker_response_path_receipt_id", "correction_path_receipt_id",
        "appeal_path_receipt_id", "recipient_policy_receipt_id",
        "retention_policy_receipt_id", "retention_rule_id", "allowed_recipient_role_ids",
        "prohibited_uses", "evidence_rule", "source_bindings",
    }, "policy")
    effective_text, effective = _when(row["effective_at"], "policy.effective_at")
    expires_text, expires = _optional_when(row["expires_at"], "policy.expires_at")
    cutoff_text, cutoff = _when(row["cutoff_at"], "policy.cutoff_at")
    if effective > cutoff or (expires is not None and expires < cutoff):
        raise ValueError("policy is not effective at cutoff")
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

    raw_rule = _object(row["evidence_rule"], "policy.evidence_rule")
    _keys(raw_rule, {"rule_id", "required_lane_ids", "matched_state"}, "policy.evidence_rule")
    required_lanes = set(_unique_ids(raw_rule["required_lane_ids"], "required_lane_ids"))
    if required_lanes != LANE_IDS:
        raise ValueError("evidence rule must require every fixed evidence lane")
    if raw_rule["matched_state"] != "RULE_MATCHED":
        raise ValueError("evidence rule matched_state is not allowed")
    rule = {
        "rule_id": _id(raw_rule["rule_id"], "rule_id"),
        "required_lane_ids": sorted(required_lanes),
        "matched_state": "RULE_MATCHED",
    }

    bindings: dict[tuple[str, str], dict[str, Any]] = {}
    binding_fields = {
        "source_id", "source_version", "source_kind", "schema_id", "schema_version",
        "authorization_receipt_id", "authorization_effective_at", "authorization_expires_at",
    }
    for index, raw_binding in enumerate(_list(row["source_bindings"], "policy.source_bindings")):
        binding = _object(raw_binding, f"source_bindings[{index}]")
        _keys(binding, binding_fields, f"source_bindings[{index}]")
        source_id = _id(binding["source_id"], "source_id")
        source_version = _id(binding["source_version"], "source_version")
        if _id(binding["source_kind"], "source_kind") != SOURCE_KIND:
            raise ValueError("source_kind is not allowed")
        auth_effective_text, auth_effective = _when(binding["authorization_effective_at"], "authorization_effective_at")
        auth_expires_text, auth_expires = _optional_when(binding["authorization_expires_at"], "authorization_expires_at")
        if auth_effective > cutoff or (auth_expires is not None and auth_expires < cutoff):
            raise ValueError("source authorization does not cover cutoff")
        normalized = {
            "source_id": source_id,
            "source_version": source_version,
            "source_kind": SOURCE_KIND,
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
    if not bindings:
        raise ValueError("at least one source binding is required")

    receipt_fields = (
        "workforce_review_receipt_id", "privacy_review_receipt_id",
        "worker_notice_program_receipt_id", "worker_access_path_receipt_id",
        "worker_response_path_receipt_id", "correction_path_receipt_id",
        "appeal_path_receipt_id", "recipient_policy_receipt_id", "retention_policy_receipt_id",
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
        "timezone": timezone_name,
        "approved_purpose": PURPOSE,
        **dict(zip(receipt_fields, receipt_values)),
        "retention_rule_id": _id(row["retention_rule_id"], "retention_rule_id"),
        "allowed_recipient_role_ids": sorted(allowed_roles),
        "prohibited_uses": sorted(prohibited),
        "evidence_rule": rule,
        "source_bindings": [bindings[key] for key in sorted(bindings)],
    }
    return policy, bindings, set(allowed_roles)


def review_coaching_records(document: Any) -> dict[str, Any]:
    root = _object(document, "document")
    _keys(root, {"review_id", "policy", "population", "records"}, "document")
    review_id = _id(root["review_id"], "review_id")
    policy, bindings, allowed_roles = _policy(root["policy"])
    cutoff = _when(policy["cutoff_at"], "policy.cutoff_at")[1]
    policy_effective = _when(policy["effective_at"], "policy.effective_at")[1]

    population = _object(root["population"], "population")
    _keys(population, {
        "population_receipt_id", "complete", "record_ids", "observed_at", "captured_at",
    }, "population")
    if not _boolean(population["complete"], "population.complete"):
        raise ValueError("population must be complete")
    declared_ids = _unique_ids(population["record_ids"], "population.record_ids")
    if not declared_ids:
        raise ValueError("population must declare at least one record")
    population_observed_text, population_observed = _when(population["observed_at"], "population.observed_at")
    population_captured_text, population_captured = _when(population["captured_at"], "population.captured_at")
    if not (population_observed <= population_captured <= cutoff):
        raise ValueError("population timestamps are not ordered")

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    states: Counter[str] = Counter()
    record_fields = {
        "record_id", "anonymous_subject_id", "anonymous_coach_id", "rule_id",
        "source_id", "source_version", "source_kind", "schema_id", "schema_version",
        "authorization_receipt_id", "observation_receipt_id", "observed_at", "captured_at",
        "recipient_role_ids", "retention_rule_id", "evidence_lanes",
    }
    for index, raw_record in enumerate(_list(root["records"], "records")):
        row = _object(raw_record, f"records[{index}]")
        _keys(row, record_fields, f"records[{index}]")
        record_id = _id(row["record_id"], "record_id")
        if record_id in seen:
            raise ValueError("duplicate record")
        seen.add(record_id)
        if record_id not in declared_ids:
            raise ValueError("record is not in declared population")
        if _id(row["rule_id"], "rule_id") != policy["evidence_rule"]["rule_id"]:
            raise ValueError("record rule does not match policy")
        source_id = _id(row["source_id"], "source_id")
        source_version = _id(row["source_version"], "source_version")
        binding = bindings.get((source_id, source_version))
        if binding is None:
            raise ValueError("record does not match an approved source binding")
        for field in ("source_kind", "schema_id", "schema_version", "authorization_receipt_id"):
            if _id(row[field], field) != binding[field]:
                raise ValueError(f"record {field} conflicts with source binding")
        observed_text, observed = _when(row["observed_at"], "observed_at")
        captured_text, captured = _when(row["captured_at"], "captured_at")
        auth_effective = _when(binding["authorization_effective_at"], "authorization_effective_at")[1]
        auth_expires = _optional_when(binding["authorization_expires_at"], "authorization_expires_at")[1]
        if not (policy_effective <= observed and auth_effective <= observed <= captured <= population_observed <= population_captured <= cutoff):
            raise ValueError("record timestamps are not ordered")
        if auth_expires is not None and observed > auth_expires:
            raise ValueError("record observation is outside source authorization")
        recipients = _unique_ids(row["recipient_role_ids"], "recipient_role_ids")
        if not recipients or not set(recipients).issubset(allowed_roles):
            raise ValueError("record recipients are not allowed")

        lanes: dict[str, dict[str, str]] = {}
        for lane_index, raw_lane in enumerate(_list(row["evidence_lanes"], "evidence_lanes")):
            lane = _object(raw_lane, f"evidence_lanes[{lane_index}]")
            _keys(lane, {"lane_id", "state", "receipt_id"}, f"evidence_lanes[{lane_index}]")
            lane_id = _id(lane["lane_id"], "lane_id")
            if lane_id not in LANE_IDS or lane_id in lanes:
                raise ValueError("evidence lanes are unknown or duplicated")
            state = lane["state"]
            if state not in LANE_STATES:
                raise ValueError("evidence lane state is not allowed")
            receipt_id = lane["receipt_id"]
            if state == "present":
                receipt_id = _id(receipt_id, "receipt_id")
            elif receipt_id is not None:
                raise ValueError("unresolved evidence lane cannot claim a receipt")
            lanes[lane_id] = {"lane_id": lane_id, "state": state, "receipt_id": receipt_id}
        if set(lanes) != LANE_IDS:
            raise ValueError("record must include every fixed evidence lane")
        present_receipts = [lane["receipt_id"] for lane in lanes.values() if lane["state"] == "present"]
        if len(present_receipts) != len(set(present_receipts)):
            raise ValueError("present evidence lanes must use separate receipts")
        if lanes["source-observation"]["state"] == "present" and lanes["source-observation"]["receipt_id"] != row["observation_receipt_id"]:
            raise ValueError("source-observation lane must bind to observation receipt")
        if _id(row["retention_rule_id"], "retention_rule_id") != policy["retention_rule_id"]:
            raise ValueError("record retention rule does not match policy")

        evidence_state = "RULE_MATCHED"
        lane_states = {lane["state"] for lane in lanes.values()}
        for candidate, output_state in STATE_PRECEDENCE:
            if candidate in lane_states:
                evidence_state = output_state
                break
        states[evidence_state] += 1
        results.append({
            "record_id": record_id,
            "anonymous_subject_id": _anonymous(row["anonymous_subject_id"], "anonymous_subject_id", "anonymous-worker-"),
            "anonymous_coach_id": _anonymous(row["anonymous_coach_id"], "anonymous_coach_id", "anonymous-coach-"),
            "rule_id": policy["evidence_rule"]["rule_id"],
            "evidence_state": evidence_state,
            "source_receipt": {
                "source_id": source_id,
                "source_version": source_version,
                "source_kind": SOURCE_KIND,
                "schema_id": binding["schema_id"],
                "schema_version": binding["schema_version"],
                "authorization_receipt_id": binding["authorization_receipt_id"],
                "observation_receipt_id": _id(row["observation_receipt_id"], "observation_receipt_id"),
                "observed_at": observed_text,
                "captured_at": captured_text,
            },
            "recipient_role_ids": sorted(recipients),
            "retention_rule_id": policy["retention_rule_id"],
            "evidence_lanes": [lanes[key] for key in sorted(lanes)],
        })
    if seen != set(declared_ids):
        raise ValueError("records do not reconcile to declared population")

    return {
        "review_id": review_id,
        "review_status": "HUMAN_REVIEW_REQUIRED",
        "purpose": PURPOSE,
        "policy_receipt": policy,
        "population_receipt": {
            "population_receipt_id": _id(population["population_receipt_id"], "population_receipt_id"),
            "complete": True,
            "record_ids": sorted(declared_ids),
            "observed_at": population_observed_text,
            "captured_at": population_captured_text,
        },
        "records": sorted(results, key=lambda item: item["record_id"]),
        "state_summary": [
            {"state": state, "record_count": states[state]}
            for state in sorted(states)
        ],
        "limitations": [
            "evidence-state-only",
            "no-coaching-generation",
            "no-worker-judgment",
            "no-performance-or-employment-use",
            "no-system-or-human-action-authorized",
            "not-legal-compliance-proof",
        ],
        "coaching_authorized": False,
        "worker_judgment_authorized": False,
        "action_authorized": False,
    }


def render_review_output(result: dict[str, Any]) -> str:
    """Render exactly once with an explicit empty terminal line."""
    return json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n\n"


def main() -> None:
    import sys

    document = json.load(sys.stdin)
    sys.stdout.write(render_review_output(review_coaching_records(document)))


if __name__ == "__main__":
    main()
