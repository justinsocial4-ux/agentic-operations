#!/usr/bin/env python3
"""Deterministic pseudonymous inbound-signal evidence review."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_inbound_signal_evidence_review"
SOURCE_KIND = "customer-supplied-pseudonymous-signal-evidence"
EVIDENCE_STATES = {"observed", "missing", "conflicting", "suppressed", "unauthorized"}
STATE_MAP = {
    "missing": "EVIDENCE_MISSING",
    "conflicting": "EVIDENCE_CONFLICT",
    "suppressed": "SUPPRESSED",
    "unauthorized": "UNAUTHORIZED",
}
REQUIRED_PROHIBITIONS = {
    "account-ranking", "alert", "behavioral-profiling", "buying-intent-inference",
    "campaign-trigger", "causal-claim", "confidence-score", "contact-selection",
    "crm-read", "crm-write", "customer-action", "direct-identifier", "forecast-change",
    "identity-resolution", "outreach-draft", "outreach-send", "person-level-tracking",
    "predictive-score", "priority-label", "rep-monitoring", "routing", "worker-action",
}
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/-]*$")
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


def _anonymous_org(value: Any, label: str) -> str:
    result = _id(value, label)
    if not result.startswith("anonymous-org-"):
        raise ValueError(f"{label} must begin with anonymous-org-")
    return result


def _token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} must be a structured token")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be non-empty trimmed text")
    return value


def _boolean(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{label} must be boolean")
    return value


def _integer(value: Any, label: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{label} must be an integer from {minimum} through {maximum}")
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


def _unique_ids(values: list[Any], label: str) -> list[str]:
    result = [_id(value, f"{label}[]") for value in values]
    if len(result) != len(set(result)):
        raise ValueError(f"{label} contains duplicates")
    return result


def _policy(raw: Any) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    row = _object(raw, "policy")
    _keys(row, {
        "policy_id", "policy_version", "owner_role_id", "human_reviewer_role_id",
        "effective_at", "expires_at", "cutoff_at", "observation_window_start",
        "observation_window_end", "timezone", "approved_purpose", "prohibited_uses",
        "correction_path", "objection_path", "privacy_review_receipt_id",
        "marketing_review_receipt_id", "notice_program_receipt_id",
        "classification_rules", "source_bindings",
    }, "policy")
    effective_text, effective = _when(row["effective_at"], "policy.effective_at")
    expires_text, expires = _optional_when(row["expires_at"], "policy.expires_at")
    cutoff_text, cutoff = _when(row["cutoff_at"], "policy.cutoff_at")
    window_start_text, window_start = _when(row["observation_window_start"], "policy.observation_window_start")
    window_end_text, window_end = _when(row["observation_window_end"], "policy.observation_window_end")
    if not (effective <= window_start <= window_end <= cutoff):
        raise ValueError("policy dates are not ordered")
    if expires is not None and expires < cutoff:
        raise ValueError("policy is expired at cutoff")
    timezone_name = _token(row["timezone"], "policy.timezone")
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("policy.timezone must be an IANA timezone") from exc
    if row["approved_purpose"] != PURPOSE:
        raise ValueError("policy.approved_purpose is not allowed")
    prohibited = _unique_ids(_list(row["prohibited_uses"], "policy.prohibited_uses"), "policy.prohibited_uses")
    if not REQUIRED_PROHIBITIONS.issubset(prohibited):
        raise ValueError("policy.prohibited_uses is missing a required boundary")

    rules: dict[str, dict[str, Any]] = {}
    rule_ids: set[str] = set()
    for index, raw_rule in enumerate(_list(row["classification_rules"], "policy.classification_rules")):
        rule = _object(raw_rule, f"classification_rules[{index}]")
        _keys(rule, {"rule_id", "event_type_id", "max_age_seconds", "matched_state", "stale_state"}, f"classification_rules[{index}]")
        event_type_id = _id(rule["event_type_id"], "event_type_id")
        rule_id = _id(rule["rule_id"], "rule_id")
        if event_type_id in rules or rule_id in rule_ids:
            raise ValueError("duplicate event-type or rule ID")
        rule_ids.add(rule_id)
        if rule["matched_state"] != "OBSERVED_WITHIN_RULE_WINDOW" or rule["stale_state"] != "OBSERVED_OUTSIDE_RULE_WINDOW":
            raise ValueError("classification states are not allowed")
        rules[event_type_id] = {
            "rule_id": rule_id,
            "event_type_id": event_type_id,
            "max_age_seconds": _integer(rule["max_age_seconds"], "max_age_seconds", 0, 31536000),
            "matched_state": rule["matched_state"],
            "stale_state": rule["stale_state"],
        }
    if not rules:
        raise ValueError("at least one classification rule is required")

    bindings: dict[tuple[str, str], dict[str, Any]] = {}
    binding_fields = {
        "source_id", "source_version", "source_kind", "schema_id", "schema_version",
        "authorization_id", "authorization_effective_at", "authorization_expires_at",
        "collection_authority_receipt_id", "purpose_compatibility_receipt_id",
        "notice_receipt_id", "objection_sync_receipt_id", "retention_receipt_id",
        "allowed_event_type_ids",
    }
    for index, raw_binding in enumerate(_list(row["source_bindings"], "policy.source_bindings")):
        binding = _object(raw_binding, f"source_bindings[{index}]")
        _keys(binding, binding_fields, f"source_bindings[{index}]")
        source_id = _id(binding["source_id"], "source_id")
        source_version = _id(binding["source_version"], "source_version")
        source_kind = _id(binding["source_kind"], "source_kind")
        if source_kind != SOURCE_KIND:
            raise ValueError("source_kind is not allowed")
        auth_effective_text, auth_effective = _when(binding["authorization_effective_at"], "authorization_effective_at")
        auth_expires_text, auth_expires = _optional_when(binding["authorization_expires_at"], "authorization_expires_at")
        if auth_effective > window_start or (auth_expires is not None and auth_expires < cutoff):
            raise ValueError("source authorization does not cover the review window")
        allowed = _unique_ids(_list(binding["allowed_event_type_ids"], "allowed_event_type_ids"), "allowed_event_type_ids")
        if not allowed or not set(allowed).issubset(rules):
            raise ValueError("allowed event types must have exact policy rules")
        normalized = {
            "source_id": source_id, "source_version": source_version, "source_kind": source_kind,
            "schema_id": _id(binding["schema_id"], "schema_id"),
            "schema_version": _id(binding["schema_version"], "schema_version"),
            "authorization_id": _id(binding["authorization_id"], "authorization_id"),
            "authorization_effective_at": auth_effective_text,
            "authorization_expires_at": auth_expires_text,
            "collection_authority_receipt_id": _id(binding["collection_authority_receipt_id"], "collection_authority_receipt_id"),
            "purpose_compatibility_receipt_id": _id(binding["purpose_compatibility_receipt_id"], "purpose_compatibility_receipt_id"),
            "notice_receipt_id": _id(binding["notice_receipt_id"], "notice_receipt_id"),
            "objection_sync_receipt_id": _id(binding["objection_sync_receipt_id"], "objection_sync_receipt_id"),
            "retention_receipt_id": _id(binding["retention_receipt_id"], "retention_receipt_id"),
            "allowed_event_type_ids": sorted(allowed),
        }
        key = (source_id, source_version)
        if key in bindings:
            raise ValueError("duplicate source binding")
        bindings[key] = normalized
    if not bindings:
        raise ValueError("at least one source binding is required")

    policy = {
        "policy_id": _id(row["policy_id"], "policy.policy_id"),
        "policy_version": _id(row["policy_version"], "policy.policy_version"),
        "owner_role_id": _id(row["owner_role_id"], "policy.owner_role_id"),
        "human_reviewer_role_id": _id(row["human_reviewer_role_id"], "policy.human_reviewer_role_id"),
        "effective_at": effective_text, "expires_at": expires_text, "cutoff_at": cutoff_text,
        "observation_window_start": window_start_text, "observation_window_end": window_end_text,
        "timezone": timezone_name, "approved_purpose": PURPOSE,
        "prohibited_uses": sorted(prohibited),
        "correction_path": _text(row["correction_path"], "policy.correction_path"),
        "objection_path": _text(row["objection_path"], "policy.objection_path"),
        "privacy_review_receipt_id": _id(row["privacy_review_receipt_id"], "privacy_review_receipt_id"),
        "marketing_review_receipt_id": _id(row["marketing_review_receipt_id"], "marketing_review_receipt_id"),
        "notice_program_receipt_id": _id(row["notice_program_receipt_id"], "notice_program_receipt_id"),
        "classification_rules": [rules[key] for key in sorted(rules)],
        "source_bindings": [bindings[key] for key in sorted(bindings)],
    }
    return policy, rules, bindings


def review_signal_evidence(document: Any) -> dict[str, Any]:
    root = _object(document, "document")
    _keys(root, {"review_id", "policy", "source_populations", "observations"}, "document")
    review_id = _id(root["review_id"], "review_id")
    policy, rules, bindings = _policy(root["policy"])
    cutoff = _when(policy["cutoff_at"], "policy.cutoff_at")[1]
    window_start = _when(policy["observation_window_start"], "policy.observation_window_start")[1]
    window_end = _when(policy["observation_window_end"], "policy.observation_window_end")[1]

    populations: dict[str, dict[str, Any]] = {}
    populated_bindings: set[tuple[str, str]] = set()
    declared: set[str] = set()
    population_fields = {
        "population_receipt_id", "source_id", "source_version", "source_kind", "schema_id",
        "schema_version", "authorization_id", "complete", "observation_ids", "observed_at", "captured_at",
    }
    for index, raw_population in enumerate(_list(root["source_populations"], "source_populations")):
        row = _object(raw_population, f"source_populations[{index}]")
        _keys(row, population_fields, f"source_populations[{index}]")
        population_id = _id(row["population_receipt_id"], "population_receipt_id")
        if population_id in populations:
            raise ValueError("duplicate population receipt")
        source_id = _id(row["source_id"], "source_id")
        source_version = _id(row["source_version"], "source_version")
        binding = bindings.get((source_id, source_version))
        if binding is None:
            raise ValueError("population does not match an approved source binding")
        binding_key = (source_id, source_version)
        if binding_key in populated_bindings:
            raise ValueError("source binding has more than one complete population")
        populated_bindings.add(binding_key)
        for field in ("source_kind", "schema_id", "schema_version", "authorization_id"):
            if _id(row[field], field) != binding[field]:
                raise ValueError("population lineage does not match source binding")
        if _boolean(row["complete"], "population.complete") is not True:
            raise ValueError("source population must be complete")
        observation_ids = _unique_ids(_list(row["observation_ids"], "population.observation_ids"), "population.observation_ids")
        if not observation_ids or declared.intersection(observation_ids):
            raise ValueError("source population is empty or overlaps another population")
        declared.update(observation_ids)
        observed_text, observed = _when(row["observed_at"], "population.observed_at")
        captured_text, captured = _when(row["captured_at"], "population.captured_at")
        if observed > captured or captured > cutoff:
            raise ValueError("population timestamps are inconsistent with cutoff")
        populations[population_id] = {
            "population_receipt_id": population_id,
            "source_id": source_id, "source_version": source_version,
            "source_kind": binding["source_kind"], "schema_id": binding["schema_id"],
            "schema_version": binding["schema_version"], "authorization_id": binding["authorization_id"],
            "observed_at": observed_text, "captured_at": captured_text,
            "observation_ids": sorted(observation_ids), "binding": binding,
        }
    if not populations or {(p["source_id"], p["source_version"]) for p in populations.values()} != set(bindings):
        raise ValueError("source binding population is incomplete or contains extras")

    observation_fields = {
        "observation_id", "population_receipt_id", "source_id", "source_version", "source_kind",
        "schema_id", "schema_version", "authorization_id", "pseudonymous_organization_id",
        "event_type_id", "evidence_state", "occurred_at", "captured_at", "evidence_receipt_ids",
    }
    seen: set[str] = set()
    receipts: list[dict[str, Any]] = []
    for index, raw_observation in enumerate(_list(root["observations"], "observations")):
        row = _object(raw_observation, f"observations[{index}]")
        _keys(row, observation_fields, f"observations[{index}]")
        observation_id = _id(row["observation_id"], "observation_id")
        if observation_id in seen:
            raise ValueError("duplicate observation")
        seen.add(observation_id)
        population_id = _id(row["population_receipt_id"], "population_receipt_id")
        population = populations.get(population_id)
        if population is None or observation_id not in population["observation_ids"]:
            raise ValueError("observation is absent from its complete source population")
        for field in ("source_id", "source_version", "source_kind", "schema_id", "schema_version", "authorization_id"):
            if _id(row[field], field) != population[field]:
                raise ValueError("observation lineage does not match population")
        event_type_id = _id(row["event_type_id"], "event_type_id")
        if event_type_id not in population["binding"]["allowed_event_type_ids"]:
            raise ValueError("event type is not allowed for source")
        evidence_state = _id(row["evidence_state"], "evidence_state")
        if evidence_state not in EVIDENCE_STATES:
            raise ValueError("evidence_state is not allowed")
        captured_text, captured = _when(row["captured_at"], "observation.captured_at")
        if captured > cutoff or captured_text != population["captured_at"]:
            raise ValueError("observation capture time does not match population")
        receipt_ids = _unique_ids(_list(row["evidence_receipt_ids"], "evidence_receipt_ids"), "evidence_receipt_ids")
        occurred_text, occurred = _optional_when(row["occurred_at"], "observation.occurred_at")
        rule = rules[event_type_id]
        if evidence_state == "observed":
            if occurred is None or len(receipt_ids) != 1:
                raise ValueError("observed evidence requires one occurrence and one receipt")
            if not window_start <= occurred <= window_end or occurred > captured:
                raise ValueError("observed occurrence is outside the approved window or after capture")
            age_seconds = int((cutoff - occurred).total_seconds())
            result_state = rule["matched_state"] if age_seconds <= rule["max_age_seconds"] else rule["stale_state"]
        elif evidence_state == "missing":
            if occurred is not None or receipt_ids:
                raise ValueError("missing evidence cannot contain occurrence or receipts")
            result_state = STATE_MAP[evidence_state]
        elif evidence_state == "conflicting":
            if occurred is not None or len(receipt_ids) < 2:
                raise ValueError("conflicting evidence requires no occurrence and at least two receipts")
            result_state = STATE_MAP[evidence_state]
        else:
            if occurred is not None or len(receipt_ids) != 1:
                raise ValueError("suppressed or unauthorized evidence requires one control receipt and no occurrence")
            result_state = STATE_MAP[evidence_state]
        receipts.append({
            "observation_id": observation_id,
            "pseudonymous_organization_id": _anonymous_org(row["pseudonymous_organization_id"], "pseudonymous_organization_id"),
            "source_receipt": {
                "population_receipt_id": population_id, "source_id": population["source_id"],
                "source_version": population["source_version"], "schema_id": population["schema_id"],
                "schema_version": population["schema_version"], "authorization_id": population["authorization_id"],
                "collection_authority_receipt_id": population["binding"]["collection_authority_receipt_id"],
                "purpose_compatibility_receipt_id": population["binding"]["purpose_compatibility_receipt_id"],
                "notice_receipt_id": population["binding"]["notice_receipt_id"],
                "objection_sync_receipt_id": population["binding"]["objection_sync_receipt_id"],
                "retention_receipt_id": population["binding"]["retention_receipt_id"],
            },
            "event_receipt": {
                "event_type_id": event_type_id, "rule_id": rule["rule_id"],
                "occurred_at": occurred_text, "captured_at": captured_text,
                "evidence_receipt_ids": sorted(receipt_ids), "evidence_state": evidence_state,
                "result_state": result_state,
            },
            "inference_authorized": False, "action_authorized": False,
        })
    if seen != declared:
        raise ValueError("observation population is incomplete or contains extras")
    receipts.sort(key=lambda item: item["observation_id"])
    counts = Counter(item["event_receipt"]["result_state"] for item in receipts)
    return {
        "review_id": review_id,
        "review_state": "HUMAN_REVIEW_REQUIRED",
        "policy_receipt": policy,
        "source_population_receipts": [
            {key: value for key, value in populations[population_id].items() if key != "binding"}
            for population_id in sorted(populations)
        ],
        "observation_receipts": receipts,
        "state_summary": {key: counts[key] for key in sorted(counts)},
        "inference_authorized": False,
        "action_authorized": False,
    }


def render_review_output(result: dict[str, Any]) -> str:
    return json.dumps(result, sort_keys=True, indent=2, ensure_ascii=True) + "\n\n"


if __name__ == "__main__":
    import sys
    payload = json.load(sys.stdin)
    sys.stdout.write(render_review_output(review_signal_evidence(payload)))
