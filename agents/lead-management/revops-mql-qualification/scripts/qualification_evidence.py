#!/usr/bin/env python3
"""Deterministic pseudonymous marketing-qualification rule evidence review."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_marketing_qualification_rule_evidence_review"
SOURCE_KIND = "customer-supplied-pseudonymous-condition-evidence"
CONDITION_KINDS = {"required", "disqualifying"}
OBSERVATION_STATES = {
    "recorded-true", "recorded-false", "missing", "conflicting", "suppressed", "unauthorized",
}
UNRESOLVED = {
    "unauthorized": "UNAUTHORIZED",
    "suppressed": "SUPPRESSED",
    "conflicting": "EVIDENCE_CONFLICT",
    "missing": "EVIDENCE_MISSING",
}
UNRESOLVED_PRECEDENCE = ("unauthorized", "suppressed", "conflicting", "missing")
REQUIRED_PROHIBITIONS = {
    "account-health-inference", "alert", "archive-action", "behavioral-inference",
    "confidence-score", "contact-validity-inference", "conversion-prediction", "crm-read",
    "crm-write", "direct-identifier", "downstream-decision", "enrichment", "fit-inference",
    "intent-inference", "lead-score", "lifecycle-label", "message-send", "monitoring",
    "nurture-action", "outreach-action", "protected-trait", "publication", "ranking",
    "readiness-inference", "routing-action", "scheduling", "worker-data",
}
BOUNDARY = "NO LEAD SCORE, INTENT, FIT, READINESS, MQL LABEL, RANKING, ROUTING, OUTREACH, CRM, OR DOWNSTREAM ACTION"
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_./:+-]*$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _arr(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _keys(row: dict[str, Any], required: set[str], label: str) -> None:
    actual = set(row)
    if actual != required:
        raise ValueError(f"{label} keys mismatch; missing={sorted(required-actual)}; extra={sorted(actual-required)}")


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ValueError(f"{label} must be a stable lowercase ID")
    return value


def _anonymous(value: Any, label: str) -> str:
    result = _id(value, label)
    if not result.startswith("record-"):
        raise ValueError(f"{label} must begin with record-")
    return result


def _token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} must be a structured token")
    return value


def _bool(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{label} must be boolean")
    return value


def _time(value: Any, label: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        raise ValueError(f"{label} must be second-precision UTC ending in Z")
    return value, datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


def _optional_time(value: Any, label: str) -> tuple[str | None, datetime | None]:
    if value is None:
        return None, None
    return _time(value, label)


def _ids(values: Any, label: str, *, anonymous: bool = False) -> list[str]:
    validate = _anonymous if anonymous else _id
    result = [validate(value, f"{label}[]") for value in _arr(values, label)]
    if len(result) != len(set(result)):
        raise ValueError(f"{label} contains duplicates")
    return result


def _policy(raw: Any) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    row = _obj(raw, "policy")
    required = {
        "policy_id", "policy_version", "effective_at", "expires_at", "cutoff_at", "timezone",
        "approved_purpose", "owner_role_id", "human_reviewer_role_id",
        "marketing_approval_receipt_id", "sales_approval_receipt_id", "privacy_review_receipt_id",
        "legal_review_receipt_id", "lawful_basis_receipt_id", "notice_program_receipt_id",
        "objection_path_receipt_id", "correction_path_receipt_id", "recipient_policy_receipt_id",
        "retention_policy_receipt_id", "qualification_policy_receipt_id",
        "allowed_recipient_role_ids", "prohibited_uses", "source_bindings", "conditions",
    }
    _keys(row, required, "policy")
    effective_text, effective = _time(row["effective_at"], "policy.effective_at")
    expires_text, expires = _optional_time(row["expires_at"], "policy.expires_at")
    cutoff_text, cutoff = _time(row["cutoff_at"], "policy.cutoff_at")
    if effective > cutoff or (expires is not None and expires < cutoff):
        raise ValueError("policy is not effective at cutoff")
    timezone_name = _token(row["timezone"], "policy.timezone")
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("policy.timezone must be an IANA timezone") from exc
    if row["approved_purpose"] != PURPOSE:
        raise ValueError("policy purpose is not allowed")
    prohibited = _ids(row["prohibited_uses"], "policy.prohibited_uses")
    if not REQUIRED_PROHIBITIONS.issubset(prohibited):
        raise ValueError("policy.prohibited_uses is missing a required boundary")
    roles = _ids(row["allowed_recipient_role_ids"], "policy.allowed_recipient_role_ids")
    if not roles:
        raise ValueError("at least one recipient role is required")

    receipt_fields = (
        "marketing_approval_receipt_id", "sales_approval_receipt_id", "privacy_review_receipt_id",
        "legal_review_receipt_id", "lawful_basis_receipt_id", "notice_program_receipt_id",
        "objection_path_receipt_id", "correction_path_receipt_id", "recipient_policy_receipt_id",
        "retention_policy_receipt_id", "qualification_policy_receipt_id",
    )
    receipts = [_id(row[field], f"policy.{field}") for field in receipt_fields]
    if len(receipts) != len(set(receipts)):
        raise ValueError("governance receipts must be separate")

    bindings: dict[tuple[str, str], dict[str, Any]] = {}
    binding_fields = {
        "source_id", "source_version", "source_kind", "schema_id", "schema_version",
        "authorization_receipt_id", "authorization_effective_at", "authorization_expires_at",
        "query_receipt_id", "page_receipt_id", "pseudonymization_receipt_id",
    }
    for index, raw_binding in enumerate(_arr(row["source_bindings"], "policy.source_bindings")):
        binding = _obj(raw_binding, f"source_bindings[{index}]")
        _keys(binding, binding_fields, f"source_bindings[{index}]")
        source_id = _id(binding["source_id"], "binding.source_id")
        source_version = _id(binding["source_version"], "binding.source_version")
        if binding["source_kind"] != SOURCE_KIND:
            raise ValueError("source kind is not allowed")
        auth_effective_text, auth_effective = _time(binding["authorization_effective_at"], "binding.authorization_effective_at")
        auth_expires_text, auth_expires = _optional_time(binding["authorization_expires_at"], "binding.authorization_expires_at")
        if auth_effective > cutoff or (auth_expires is not None and auth_expires < cutoff):
            raise ValueError("source authorization does not cover cutoff")
        source_receipts = [
            _id(binding["authorization_receipt_id"], "binding.authorization_receipt_id"),
            _id(binding["query_receipt_id"], "binding.query_receipt_id"),
            _id(binding["page_receipt_id"], "binding.page_receipt_id"),
            _id(binding["pseudonymization_receipt_id"], "binding.pseudonymization_receipt_id"),
        ]
        if len(source_receipts) != len(set(source_receipts)):
            raise ValueError("source receipts must be separate")
        normalized = {
            "source_id": source_id,
            "source_version": source_version,
            "source_kind": SOURCE_KIND,
            "schema_id": _id(binding["schema_id"], "binding.schema_id"),
            "schema_version": _id(binding["schema_version"], "binding.schema_version"),
            "authorization_receipt_id": source_receipts[0],
            "authorization_effective_at": auth_effective_text,
            "authorization_expires_at": auth_expires_text,
            "query_receipt_id": source_receipts[1],
            "page_receipt_id": source_receipts[2],
            "pseudonymization_receipt_id": source_receipts[3],
        }
        key = (source_id, source_version)
        if key in bindings:
            raise ValueError("duplicate source binding")
        bindings[key] = normalized
    if not bindings:
        raise ValueError("at least one source binding is required")

    conditions: dict[tuple[str, str], dict[str, Any]] = {}
    condition_fields = {
        "condition_id", "condition_version", "condition_kind", "source_id", "source_version",
        "field_definition_receipt_id", "condition_definition_receipt_id",
    }
    for index, raw_condition in enumerate(_arr(row["conditions"], "policy.conditions")):
        condition = _obj(raw_condition, f"conditions[{index}]")
        _keys(condition, condition_fields, f"conditions[{index}]")
        condition_id = _id(condition["condition_id"], "condition.condition_id")
        condition_version = _id(condition["condition_version"], "condition.condition_version")
        if condition["condition_kind"] not in CONDITION_KINDS:
            raise ValueError("condition kind is not allowed")
        source_key = (_id(condition["source_id"], "condition.source_id"), _id(condition["source_version"], "condition.source_version"))
        if source_key not in bindings:
            raise ValueError("condition source is not approved")
        normalized = {
            "condition_id": condition_id,
            "condition_version": condition_version,
            "condition_kind": condition["condition_kind"],
            "source_id": source_key[0],
            "source_version": source_key[1],
            "field_definition_receipt_id": _id(condition["field_definition_receipt_id"], "condition.field_definition_receipt_id"),
            "condition_definition_receipt_id": _id(condition["condition_definition_receipt_id"], "condition.condition_definition_receipt_id"),
        }
        key = (condition_id, condition_version)
        if key in conditions:
            raise ValueError("duplicate condition")
        conditions[key] = normalized
    if not conditions or not any(item["condition_kind"] == "required" for item in conditions.values()):
        raise ValueError("at least one required condition is required")
    definition_receipts = [item["condition_definition_receipt_id"] for item in conditions.values()]
    if len(definition_receipts) != len(set(definition_receipts)):
        raise ValueError("condition definition receipts must be unique")

    policy = {
        "policy_id": _id(row["policy_id"], "policy.policy_id"),
        "policy_version": _id(row["policy_version"], "policy.policy_version"),
        "effective_at": effective_text,
        "expires_at": expires_text,
        "cutoff_at": cutoff_text,
        "timezone": timezone_name,
        "approved_purpose": PURPOSE,
        "owner_role_id": _id(row["owner_role_id"], "policy.owner_role_id"),
        "human_reviewer_role_id": _id(row["human_reviewer_role_id"], "policy.human_reviewer_role_id"),
        **dict(zip(receipt_fields, receipts)),
        "allowed_recipient_role_ids": sorted(roles),
        "prohibited_uses": sorted(prohibited),
        "source_bindings": [bindings[key] for key in sorted(bindings)],
        "conditions": [conditions[key] for key in sorted(conditions)],
    }
    return policy, bindings, conditions


def review_qualification_evidence(document: Any) -> dict[str, Any]:
    root = _obj(document, "document")
    _keys(root, {"review_declaration", "policy", "source_populations", "condition_observations"}, "document")
    declaration = _obj(root["review_declaration"], "review_declaration")
    _keys(declaration, {"review_id", "policy_id", "policy_version", "reviewed_at", "recipient_role_id", "record_ids"}, "review_declaration")
    review_id = _id(declaration["review_id"], "review_declaration.review_id")
    reviewed_text, reviewed = _time(declaration["reviewed_at"], "review_declaration.reviewed_at")
    declared_ids = _ids(declaration["record_ids"], "review_declaration.record_ids", anonymous=True)
    if not declared_ids:
        raise ValueError("declared record population cannot be empty")

    policy, bindings, conditions = _policy(root["policy"])
    if declaration["policy_id"] != policy["policy_id"] or declaration["policy_version"] != policy["policy_version"]:
        raise ValueError("declaration conflicts with policy")
    cutoff = _time(policy["cutoff_at"], "policy.cutoff_at")[1]
    effective = _time(policy["effective_at"], "policy.effective_at")[1]
    expires = _optional_time(policy["expires_at"], "policy.expires_at")[1]
    if reviewed < cutoff or (expires is not None and expires < reviewed):
        raise ValueError("policy does not cover review")
    recipient_role_id = _id(declaration["recipient_role_id"], "review_declaration.recipient_role_id")
    if recipient_role_id not in policy["allowed_recipient_role_ids"]:
        raise ValueError("review recipient is not allowed")
    for binding in bindings.values():
        auth_expires = _optional_time(binding["authorization_expires_at"], "binding.authorization_expires_at")[1]
        if auth_expires is not None and auth_expires < reviewed:
            raise ValueError("source authorization does not cover review")

    populations: dict[tuple[str, str], dict[str, Any]] = {}
    population_fields = {
        "population_receipt_id", "source_id", "source_version", "schema_id", "schema_version",
        "authorization_receipt_id", "query_receipt_id", "page_receipt_id",
        "pseudonymization_receipt_id", "complete", "record_ids", "captured_at",
    }
    population_receipt_ids: set[str] = set()
    for index, raw_population in enumerate(_arr(root["source_populations"], "source_populations")):
        row = _obj(raw_population, f"source_populations[{index}]")
        _keys(row, population_fields, f"source_populations[{index}]")
        key = (_id(row["source_id"], "population.source_id"), _id(row["source_version"], "population.source_version"))
        binding = bindings.get(key)
        if binding is None:
            raise ValueError("population source is not approved")
        for field in ("schema_id", "schema_version", "authorization_receipt_id", "query_receipt_id", "page_receipt_id", "pseudonymization_receipt_id"):
            if _id(row[field], f"population.{field}") != binding[field]:
                raise ValueError(f"population {field} conflicts with source binding")
        if not _bool(row["complete"], "population.complete"):
            raise ValueError("source population must be complete")
        record_ids = _ids(row["record_ids"], "population.record_ids", anonymous=True)
        if set(record_ids) != set(declared_ids):
            raise ValueError("source population does not reconcile to declaration")
        captured_text, captured = _time(row["captured_at"], "population.captured_at")
        if captured > cutoff:
            raise ValueError("source population was captured after cutoff")
        if key in populations:
            raise ValueError("duplicate source population")
        population_receipt_id = _id(row["population_receipt_id"], "population.population_receipt_id")
        if population_receipt_id in population_receipt_ids:
            raise ValueError("duplicate population receipt")
        population_receipt_ids.add(population_receipt_id)
        populations[key] = {
            "population_receipt_id": population_receipt_id,
            "source_id": key[0], "source_version": key[1], "schema_id": binding["schema_id"],
            "schema_version": binding["schema_version"], "authorization_receipt_id": binding["authorization_receipt_id"],
            "query_receipt_id": binding["query_receipt_id"], "page_receipt_id": binding["page_receipt_id"],
            "pseudonymization_receipt_id": binding["pseudonymization_receipt_id"], "complete": True,
            "record_ids": sorted(record_ids), "member_count": str(len(record_ids)), "captured_at": captured_text,
        }
    if set(populations) != set(bindings):
        raise ValueError("every approved source requires one complete population")

    observations: list[dict[str, Any]] = []
    matrix: dict[tuple[str, str, str], dict[str, Any]] = {}
    receipt_ids: set[str] = set()
    observation_fields = {
        "record_id", "condition_id", "condition_version", "source_id", "source_version",
        "schema_id", "schema_version", "authorization_receipt_id", "query_receipt_id",
        "page_receipt_id", "pseudonymization_receipt_id", "population_receipt_id",
        "field_definition_receipt_id", "condition_definition_receipt_id",
        "evidence_receipt_id", "state", "observed_at", "captured_at",
    }
    for index, raw_observation in enumerate(_arr(root["condition_observations"], "condition_observations")):
        row = _obj(raw_observation, f"condition_observations[{index}]")
        _keys(row, observation_fields, f"condition_observations[{index}]")
        record_id = _anonymous(row["record_id"], "observation.record_id")
        if record_id not in declared_ids:
            raise ValueError("observation record is not declared")
        condition_key = (_id(row["condition_id"], "observation.condition_id"), _id(row["condition_version"], "observation.condition_version"))
        condition = conditions.get(condition_key)
        if condition is None:
            raise ValueError("observation condition is not approved")
        source_key = (_id(row["source_id"], "observation.source_id"), _id(row["source_version"], "observation.source_version"))
        if source_key != (condition["source_id"], condition["source_version"]):
            raise ValueError("observation source conflicts with condition")
        binding = bindings[source_key]
        population = populations[source_key]
        for field in ("schema_id", "schema_version", "authorization_receipt_id", "query_receipt_id", "page_receipt_id", "pseudonymization_receipt_id"):
            if _id(row[field], f"observation.{field}") != binding[field]:
                raise ValueError(f"observation {field} conflicts with source binding")
        if _id(row["population_receipt_id"], "observation.population_receipt_id") != population["population_receipt_id"]:
            raise ValueError("observation population receipt conflicts")
        if _id(row["field_definition_receipt_id"], "observation.field_definition_receipt_id") != condition["field_definition_receipt_id"]:
            raise ValueError("observation field definition receipt conflicts")
        if _id(row["condition_definition_receipt_id"], "observation.condition_definition_receipt_id") != condition["condition_definition_receipt_id"]:
            raise ValueError("observation condition definition receipt conflicts")
        receipt_id = _id(row["evidence_receipt_id"], "observation.evidence_receipt_id")
        if receipt_id in receipt_ids:
            raise ValueError("duplicate evidence receipt")
        receipt_ids.add(receipt_id)
        if row["state"] not in OBSERVATION_STATES:
            raise ValueError("observation state is not allowed")
        observed_text, observed = _time(row["observed_at"], "observation.observed_at")
        captured_text, captured = _time(row["captured_at"], "observation.captured_at")
        auth_effective = _time(binding["authorization_effective_at"], "binding.authorization_effective_at")[1]
        auth_expires = _optional_time(binding["authorization_expires_at"], "binding.authorization_expires_at")[1]
        population_captured = _time(population["captured_at"], "population.captured_at")[1]
        if not (effective <= observed <= captured <= cutoff and captured <= population_captured and auth_effective <= observed):
            raise ValueError("observation timestamps are invalid")
        if auth_expires is not None and captured > auth_expires:
            raise ValueError("observation falls outside source authorization")
        matrix_key = (record_id, condition_key[0], condition_key[1])
        if matrix_key in matrix:
            raise ValueError("duplicate record-condition observation")
        normalized = {
            "record_id": record_id, "condition_id": condition_key[0], "condition_version": condition_key[1],
            "condition_kind": condition["condition_kind"], "source_id": source_key[0], "source_version": source_key[1],
            "schema_id": binding["schema_id"], "schema_version": binding["schema_version"],
            "authorization_receipt_id": binding["authorization_receipt_id"], "query_receipt_id": binding["query_receipt_id"],
            "page_receipt_id": binding["page_receipt_id"], "pseudonymization_receipt_id": binding["pseudonymization_receipt_id"],
            "population_receipt_id": population["population_receipt_id"],
            "field_definition_receipt_id": condition["field_definition_receipt_id"],
            "condition_definition_receipt_id": condition["condition_definition_receipt_id"],
            "evidence_receipt_id": receipt_id,
            "state": row["state"], "observed_at": observed_text, "captured_at": captured_text,
        }
        matrix[matrix_key] = normalized
        observations.append(normalized)

    expected_matrix = {(record_id, condition_id, condition_version) for record_id in declared_ids for condition_id, condition_version in conditions}
    if set(matrix) != expected_matrix:
        raise ValueError("record-condition evidence matrix is incomplete or contains extras")

    record_receipts: list[dict[str, Any]] = []
    for record_id in sorted(declared_ids):
        rows = [matrix[(record_id, condition_id, condition_version)] for condition_id, condition_version in conditions]
        unresolved_state = next((state for state in UNRESOLVED_PRECEDENCE if any(item["state"] == state for item in rows)), None)
        if unresolved_state is not None:
            state = UNRESOLVED[unresolved_state]
        else:
            met = all(
                (item["condition_kind"] == "required" and item["state"] == "recorded-true")
                or (item["condition_kind"] == "disqualifying" and item["state"] == "recorded-false")
                for item in rows
            )
            state = "CUSTOMER_POLICY_CONDITIONS_MET" if met else "CUSTOMER_POLICY_CONDITIONS_NOT_MET"
        record_receipts.append({
            "record_id": record_id,
            "condition_evidence_receipt_ids": sorted(item["evidence_receipt_id"] for item in rows),
            "state": state,
        })

    return {
        "archive_action_authorized": False,
        "boundary": BOUNDARY,
        "condition_observation_receipts": sorted(observations, key=lambda item: (item["record_id"], item["condition_id"], item["condition_version"])),
        "declared_population_receipt": {"record_ids": sorted(declared_ids), "member_count": str(len(declared_ids))},
        "downstream_decision_authorized": False,
        "lifecycle_label_authorized": False,
        "nurture_action_authorized": False,
        "outreach_action_authorized": False,
        "policy_receipt": policy,
        "publication_authorized": False,
        "record_receipts": record_receipts,
        "recipient_role_id": recipient_role_id,
        "review_id": review_id,
        "review_state": "HUMAN_REVIEW_REQUIRED",
        "review_type": "MARKETING_QUALIFICATION_RULE_EVIDENCE_REVIEW",
        "reviewed_at": reviewed_text,
        "routing_action_authorized": False,
        "source_population_receipts": [populations[key] for key in sorted(populations)],
        "system_action_authorized": False,
    }


def render_review_output(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n\n"


def main(argv: list[str]) -> int:
    try:
        if len(argv) > 2:
            raise ValueError("usage: qualification_evidence.py [input.json]")
        raw = Path(argv[1]).read_text(encoding="utf-8") if len(argv) == 2 else sys.stdin.read()
        sys.stdout.write(render_review_output(review_qualification_evidence(json.loads(raw))))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f"marketing qualification rule evidence review failed: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
