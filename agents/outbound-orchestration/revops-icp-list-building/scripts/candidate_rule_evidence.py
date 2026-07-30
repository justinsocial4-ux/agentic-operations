#!/usr/bin/env python3
"""Deterministic pseudonymous prospect-candidate rule evidence review."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_candidate_rule_evidence_review"
SOURCE_KIND = "customer-supplied-pseudonymous-candidate-observation"
VALUE_KINDS = {"code", "count", "currency", "decimal", "percentage"}
NUMERIC_KINDS = VALUE_KINDS - {"code"}
NUMERIC_OPERATORS = {"lt", "lte", "eq", "ne", "gte", "gt"}
CODE_OPERATORS = {"in", "not-in"}
UNRESOLVED = {
    "unauthorized": "UNAUTHORIZED",
    "suppressed": "SUPPRESSED",
    "conflicting": "EVIDENCE_CONFLICT",
    "missing": "EVIDENCE_MISSING",
}
PRECEDENCE = ("UNAUTHORIZED", "SUPPRESSED", "EVIDENCE_CONFLICT", "EVIDENCE_MISSING", "SOURCE_OBSERVATION_EVIDENCE_NOT_MATCHED")
REQUIRED_PROHIBITIONS = {
    "contact-data", "credential-input", "crm-write", "downstream-decision",
    "enrichment", "export-list", "fuzzy-inference", "identity-data",
    "message-send", "notification", "outreach-authorization", "priority-label",
    "proxy-inference", "publication", "ranking", "readiness-label", "retry-action",
    "scheduling", "scoring", "threshold-relaxation", "workflow-action",
}
BOUNDARY = "NO IDENTITY, ENRICHMENT, FUZZY MATCH, SCORE, RANK, PRIORITY, OUTREACH, EXPORT, CRM WRITE, OR DOWNSTREAM ACTION"
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
CODE_RE = re.compile(r"^source-code-[0-9]{2,6}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
DEC_RE = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?$")


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


def _id(value: Any, label: str, prefix: str | None = None) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ValueError(f"{label} must be a stable lowercase ID")
    if prefix and not value.startswith(prefix):
        raise ValueError(f"{label} must begin with {prefix}")
    return value


def _ids(values: Any, label: str, prefix: str | None = None, nonempty: bool = False) -> list[str]:
    result = [_id(value, f"{label}[]", prefix) for value in _arr(values, label)]
    if nonempty and not result:
        raise ValueError(f"{label} must not be empty")
    if len(result) != len(set(result)):
        raise ValueError(f"{label} contains duplicates")
    return result


def _time(value: Any, label: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        raise ValueError(f"{label} must be second-precision UTC ending in Z")
    return value, datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


def _optional_time(value: Any, label: str) -> tuple[str | None, datetime | None]:
    if value is None:
        return None, None
    return _time(value, label)


def _reserve(receipts: set[str], value: Any, label: str) -> str:
    receipt = _id(value, label, "receipt-")
    if receipt in receipts:
        raise ValueError("receipts must be globally unique")
    receipts.add(receipt)
    return receipt


def _decimal(value: Any, label: str, kind: str) -> str:
    if not isinstance(value, str) or not DEC_RE.fullmatch(value):
        raise ValueError(f"{label} must be a nonnegative canonical decimal string")
    integer, separator, fraction = value.partition(".")
    if len(integer) > 18 or (separator and len(fraction) > 9):
        raise ValueError(f"{label} exceeds numeric precision bounds")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} is not decimal") from exc
    if kind == "count" and number != number.to_integral_value():
        raise ValueError(f"{label} count must be integral")
    if kind == "percentage" and number > Decimal("100"):
        raise ValueError(f"{label} percentage exceeds 100")
    return value


def _value(value: Any, kind: str, label: str) -> str:
    if kind == "code":
        if not isinstance(value, str) or not CODE_RE.fullmatch(value):
            raise ValueError(f"{label} must be an opaque source-bound code")
        return value
    return _decimal(value, label, kind)


def _condition(value: str, thresholds: list[str], kind: str, operator: str) -> str:
    if kind == "code":
        result = value in thresholds
        if operator == "not-in":
            result = not result
    else:
        left, right = Decimal(value), Decimal(thresholds[0])
        if operator == "lt":
            result = left < right
        elif operator == "lte":
            result = left <= right
        elif operator == "eq":
            result = left == right
        elif operator == "ne":
            result = left != right
        elif operator == "gte":
            result = left >= right
        else:
            result = left > right
    return "CUSTOMER_RULE_CONDITION_MET" if result else "CUSTOMER_RULE_CONDITION_NOT_MET"


def _policy(raw: Any) -> tuple[dict[str, Any], dict[str, dict[str, Any]], set[str], datetime]:
    row = _obj(raw, "policy")
    fields = {
        "policy_id", "policy_version", "effective_at", "expires_at", "cutoff_at", "timezone",
        "approved_purpose", "owner_role_id", "human_reviewer_role_id", "actual_recipient_role_id",
        "review_authorization_effective_at", "review_authorization_expires_at",
        "operations_approval_receipt_id", "security_review_receipt_id", "privacy_review_receipt_id",
        "legal_review_receipt_id", "collection_policy_receipt_id", "lawful_basis_review_receipt_id",
        "notice_policy_receipt_id", "objection_policy_receipt_id", "suppression_policy_receipt_id",
        "correction_access_policy_receipt_id", "recipient_policy_receipt_id", "retention_policy_receipt_id",
        "pseudonymization_policy_receipt_id", "rule_policy_receipt_id", "population_policy_receipt_id",
        "review_authorization_receipt_id", "allowed_recipient_role_ids", "prohibited_uses", "rule_contracts",
    }
    _keys(row, fields, "policy")
    effective_text, effective = _time(row["effective_at"], "policy.effective_at")
    expires_text, expires = _optional_time(row["expires_at"], "policy.expires_at")
    cutoff_text, cutoff = _time(row["cutoff_at"], "policy.cutoff_at")
    review_effective_text, review_effective = _time(row["review_authorization_effective_at"], "policy.review_authorization_effective_at")
    review_expires_text, review_expires = _optional_time(row["review_authorization_expires_at"], "policy.review_authorization_expires_at")
    if effective > cutoff or review_effective > cutoff:
        raise ValueError("policy or review authorization begins after cutoff")
    if (expires is not None and expires < cutoff) or (review_expires is not None and review_expires < cutoff):
        raise ValueError("policy or review authorization does not cover cutoff")
    timezone_name = row["timezone"] if isinstance(row["timezone"], str) and re.fullmatch(r"^[A-Za-z_+-]+(?:/[A-Za-z0-9_+.-]+)*$", row["timezone"]) else ""
    try:
        ZoneInfo(row["timezone"])
    except (ZoneInfoNotFoundError, TypeError) as exc:
        raise ValueError("policy.timezone must be an IANA timezone") from exc
    if not timezone_name or row["approved_purpose"] != PURPOSE:
        raise ValueError("policy purpose or timezone is not allowed")
    recipients = sorted(_ids(row["allowed_recipient_role_ids"], "policy.allowed_recipient_role_ids", "role-", True))
    owner = _id(row["owner_role_id"], "policy.owner_role_id", "role-")
    reviewer = _id(row["human_reviewer_role_id"], "policy.human_reviewer_role_id", "role-")
    actual = _id(row["actual_recipient_role_id"], "policy.actual_recipient_role_id", "role-")
    if reviewer not in recipients or actual != reviewer:
        raise ValueError("actual recipient must equal an allowed human reviewer")
    prohibited = set(_ids(row["prohibited_uses"], "policy.prohibited_uses"))
    if not REQUIRED_PROHIBITIONS.issubset(prohibited):
        raise ValueError("policy.prohibited_uses is missing a required boundary")
    receipts: set[str] = set()
    receipt_fields = (
        "operations_approval_receipt_id", "security_review_receipt_id", "privacy_review_receipt_id",
        "legal_review_receipt_id", "collection_policy_receipt_id", "lawful_basis_review_receipt_id",
        "notice_policy_receipt_id", "objection_policy_receipt_id", "suppression_policy_receipt_id",
        "correction_access_policy_receipt_id", "recipient_policy_receipt_id", "retention_policy_receipt_id",
        "pseudonymization_policy_receipt_id", "rule_policy_receipt_id", "population_policy_receipt_id",
        "review_authorization_receipt_id",
    )
    governance = {field: _reserve(receipts, row[field], f"policy.{field}") for field in receipt_fields}
    rule_fields = {
        "rule_id", "rule_version", "rule_effective_at", "rule_expires_at", "source_id", "source_version",
        "source_kind", "schema_id", "schema_version", "field_definition_id", "value_kind", "unit_id",
        "denominator_definition_id", "rule_operator", "rule_threshold_values", "window_starts_at", "window_ends_at",
        "authorization_effective_at", "authorization_expires_at", "declared_candidate_ids",
        "source_authorization_receipt_id", "field_definition_receipt_id", "denominator_definition_receipt_id",
        "rule_receipt_id", "rule_approval_receipt_id", "population_receipt_id", "completeness_receipt_id",
        "privacy_receipt_id", "source_documentation_receipt_id",
    }
    rules: dict[str, dict[str, Any]] = {}
    signatures: set[tuple[Any, ...]] = set()
    for index, raw_rule in enumerate(_arr(row["rule_contracts"], "policy.rule_contracts")):
        item = _obj(raw_rule, f"rule_contracts[{index}]")
        _keys(item, rule_fields, f"rule_contracts[{index}]")
        rule_id = _id(item["rule_id"], "rule.rule_id", "rule-")
        if rule_id in rules:
            raise ValueError("duplicate rule contract")
        kind = _id(item["value_kind"], "rule.value_kind")
        if kind not in VALUE_KINDS:
            raise ValueError("rule value kind is not allowed")
        operator = _id(item["rule_operator"], "rule.rule_operator")
        if operator not in (CODE_OPERATORS if kind == "code" else NUMERIC_OPERATORS):
            raise ValueError("rule operator is not allowed for value kind")
        thresholds = sorted(_value(value, kind, "rule.rule_threshold_values[]") for value in _arr(item["rule_threshold_values"], "rule.rule_threshold_values"))
        if not thresholds or len(thresholds) != len(set(thresholds)) or (kind != "code" and len(thresholds) != 1):
            raise ValueError("rule threshold values are invalid")
        if item["source_kind"] != SOURCE_KIND:
            raise ValueError("rule source kind is not allowed")
        rule_effective_text, rule_effective = _time(item["rule_effective_at"], "rule.rule_effective_at")
        rule_expires_text, rule_expires = _optional_time(item["rule_expires_at"], "rule.rule_expires_at")
        starts_text, starts = _time(item["window_starts_at"], "rule.window_starts_at")
        ends_text, ends = _time(item["window_ends_at"], "rule.window_ends_at")
        auth_effective_text, auth_effective = _time(item["authorization_effective_at"], "rule.authorization_effective_at")
        auth_expires_text, auth_expires = _optional_time(item["authorization_expires_at"], "rule.authorization_expires_at")
        if starts > ends or ends > cutoff or rule_effective > starts or auth_effective > starts:
            raise ValueError("rule or authorization window does not cover observations")
        if (rule_expires is not None and rule_expires < ends) or (auth_expires is not None and auth_expires < ends):
            raise ValueError("rule or authorization expires before observation window ends")
        unit = item["unit_id"]
        denominator = item["denominator_definition_id"]
        if kind == "code":
            if unit is not None or denominator is not None:
                raise ValueError("code rules cannot have unit or denominator")
        else:
            unit = _id(unit, "rule.unit_id", "unit-")
            if kind == "percentage":
                denominator = _id(denominator, "rule.denominator_definition_id", "definition-")
            elif denominator is not None:
                raise ValueError("denominator is allowed only for percentage")
        candidate_ids = sorted(_ids(item["declared_candidate_ids"], "rule.declared_candidate_ids", "candidate-", True))
        receipt_names = (
            "source_authorization_receipt_id", "field_definition_receipt_id", "rule_receipt_id",
            "rule_approval_receipt_id", "population_receipt_id", "completeness_receipt_id", "privacy_receipt_id",
            "source_documentation_receipt_id",
        )
        rule_receipts = {name: _reserve(receipts, item[name], f"rule.{name}") for name in receipt_names}
        if kind == "percentage":
            rule_receipts["denominator_definition_receipt_id"] = _reserve(receipts, item["denominator_definition_receipt_id"], "rule.denominator_definition_receipt_id")
        elif item["denominator_definition_receipt_id"] is not None:
            raise ValueError("denominator receipt is allowed only for percentage")
        source_id = _id(item["source_id"], "rule.source_id", "source-")
        source_version = _id(item["source_version"], "rule.source_version")
        schema_id = _id(item["schema_id"], "rule.schema_id", "schema-")
        schema_version = _id(item["schema_version"], "rule.schema_version")
        definition_id = _id(item["field_definition_id"], "rule.field_definition_id", "definition-")
        signature = (source_id, source_version, schema_id, schema_version, definition_id, kind, unit, denominator, operator, tuple(thresholds), starts_text, ends_text)
        if signature in signatures:
            raise ValueError("duplicate rule signature")
        signatures.add(signature)
        rules[rule_id] = {
            "rule_id": rule_id, "rule_version": _id(item["rule_version"], "rule.rule_version"),
            "rule_effective_at": rule_effective_text, "rule_expires_at": rule_expires_text,
            "source_id": source_id, "source_version": source_version, "source_kind": SOURCE_KIND,
            "schema_id": schema_id, "schema_version": schema_version, "field_definition_id": definition_id,
            "value_kind": kind, "unit_id": unit, "denominator_definition_id": denominator,
            "rule_operator": operator, "rule_threshold_values": thresholds,
            "window_starts_at": starts_text, "window_ends_at": ends_text,
            "authorization_effective_at": auth_effective_text, "authorization_expires_at": auth_expires_text,
            "declared_candidate_ids": candidate_ids, "receipts": rule_receipts,
            "_starts": starts, "_ends": ends,
        }
    if not rules:
        raise ValueError("policy.rule_contracts must not be empty")
    if effective > min(rule["_starts"] for rule in rules.values()):
        raise ValueError("policy must be effective before every rule observation window")
    policy = {
        "policy_id": _id(row["policy_id"], "policy.policy_id", "policy-"),
        "policy_version": _id(row["policy_version"], "policy.policy_version"),
        "effective_at": effective_text, "expires_at": expires_text, "cutoff_at": cutoff_text,
        "timezone": row["timezone"], "approved_purpose": PURPOSE, "owner_role_id": owner,
        "human_reviewer_role_id": reviewer, "actual_recipient_role_id": actual,
        "review_authorization_effective_at": review_effective_text,
        "review_authorization_expires_at": review_expires_text,
        "allowed_recipient_role_ids": recipients, "prohibited_uses": sorted(prohibited),
        "governance_receipts": governance,
    }
    return policy, rules, receipts, cutoff


def _population(raw: Any, receipts: set[str], rules: dict[str, dict[str, Any]], policy: dict[str, Any], cutoff: datetime) -> tuple[dict[str, Any], list[str]]:
    row = _obj(raw, "candidate_population")
    fields = {"population_id", "declared_candidate_ids", "packet_generated_at", "assigned_reviewer_role_id", "packet_receipt_id", "population_receipt_id", "completeness_receipt_id", "pseudonymization_receipt_id", "review_assignment_receipt_id"}
    _keys(row, fields, "candidate_population")
    candidate_ids = sorted(_ids(row["declared_candidate_ids"], "candidate_population.declared_candidate_ids", "candidate-", True))
    for rule in rules.values():
        if set(rule["declared_candidate_ids"]) != set(candidate_ids):
            raise ValueError("every rule population must equal the declared candidate population")
    packet_generated_text, packet_generated = _time(row["packet_generated_at"], "candidate_population.packet_generated_at")
    if packet_generated < max(rule["_ends"] for rule in rules.values()) or packet_generated > cutoff:
        raise ValueError("candidate packet must be generated after every rule window and no later than cutoff")
    assigned_reviewer = _id(row["assigned_reviewer_role_id"], "candidate_population.assigned_reviewer_role_id", "role-")
    if assigned_reviewer != policy["human_reviewer_role_id"] or assigned_reviewer != policy["actual_recipient_role_id"]:
        raise ValueError("candidate packet must be assigned to the exact authorized human reviewer")
    population_receipts = {
        name: _reserve(receipts, row[name], f"candidate_population.{name}")
        for name in ("packet_receipt_id", "population_receipt_id", "completeness_receipt_id", "pseudonymization_receipt_id", "review_assignment_receipt_id")
    }
    return {"population_id": _id(row["population_id"], "candidate_population.population_id", "population-"), "declared_candidate_ids": candidate_ids, "packet_generated_at": packet_generated_text, "assigned_reviewer_role_id": assigned_reviewer, "receipts": population_receipts}, candidate_ids


def _binding_matches(row: dict[str, Any], rule: dict[str, Any]) -> bool:
    fields = ("source_id", "source_version", "source_kind", "schema_id", "schema_version", "field_definition_id", "value_kind", "unit_id", "denominator_definition_id")
    return all(row[field] == rule[field] for field in fields)


def _validate_observation_binding(row: dict[str, Any]) -> str:
    _id(row["source_id"], "observation.source_id", "source-")
    _id(row["source_version"], "observation.source_version")
    _id(row["source_kind"], "observation.source_kind")
    _id(row["schema_id"], "observation.schema_id", "schema-")
    _id(row["schema_version"], "observation.schema_version")
    _id(row["field_definition_id"], "observation.field_definition_id", "definition-")
    kind = _id(row["value_kind"], "observation.value_kind")
    if kind not in VALUE_KINDS:
        raise ValueError("observation value kind is not allowed")
    if kind == "code":
        if row["unit_id"] is not None or row["denominator_definition_id"] is not None:
            raise ValueError("code observation cannot have unit or denominator")
    else:
        _id(row["unit_id"], "observation.unit_id", "unit-")
        if kind == "percentage":
            _id(row["denominator_definition_id"], "observation.denominator_definition_id", "definition-")
        elif row["denominator_definition_id"] is not None:
            raise ValueError("observation denominator is allowed only for percentage")
    return kind


def _review_candidate(raw: Any, rules: dict[str, dict[str, Any]], receipts: set[str], cutoff: datetime) -> dict[str, Any]:
    row = _obj(raw, "candidate")
    _keys(row, {"candidate_id", "observations"}, "candidate")
    candidate_id = _id(row["candidate_id"], "candidate.candidate_id", "candidate-")
    observation_fields = {
        "candidate_id", "rule_id", "source_id", "source_version", "source_kind", "schema_id", "schema_version",
        "field_definition_id", "value_kind", "unit_id", "denominator_definition_id", "observed_at",
        "evidence_state", "value", "capture_authorization_receipt_id", "capture_receipt_id",
        "candidate_binding_receipt_id", "privacy_receipt_id",
    }
    observations: dict[str, dict[str, Any]] = {}
    for index, raw_observation in enumerate(_arr(row["observations"], "candidate.observations")):
        item = _obj(raw_observation, f"candidate.observations[{index}]")
        _keys(item, observation_fields, f"candidate.observations[{index}]")
        if _id(item["candidate_id"], "observation.candidate_id", "candidate-") != candidate_id:
            raise ValueError("observation candidate binding mismatch")
        rule_id = _id(item["rule_id"], "observation.rule_id", "rule-")
        if rule_id not in rules or rule_id in observations:
            raise ValueError("unknown or duplicate observation rule")
        rule = rules[rule_id]
        state = _id(item["evidence_state"], "observation.evidence_state")
        if state not in UNRESOLVED and state != "available":
            raise ValueError("observation evidence state is not allowed")
        submitted_kind = _validate_observation_binding(item)
        for name in ("capture_authorization_receipt_id", "capture_receipt_id", "candidate_binding_receipt_id", "privacy_receipt_id"):
            _reserve(receipts, item[name], f"observation.{name}")
        bound = _binding_matches(item, rule)
        if state == "available":
            observed_text, observed = _time(item["observed_at"], "observation.observed_at")
            value = _value(item["value"], submitted_kind, "observation.value")
            if observed > cutoff or observed < rule["_starts"] or observed > rule["_ends"]:
                raise ValueError("observation timestamp is future or outside rule window")
            if bound:
                evidence_state = "SOURCE_OBSERVATION_EVIDENCE_PRESENT"
                condition_state = _condition(value, rule["rule_threshold_values"], rule["value_kind"], rule["rule_operator"])
                output_value = value
            else:
                evidence_state = "SOURCE_OBSERVATION_EVIDENCE_NOT_MATCHED"
                condition_state = None
                output_value = None
        else:
            if item["observed_at"] is not None or item["value"] is not None:
                raise ValueError("unresolved observation cannot carry timestamp or value")
            observed_text = None
            evidence_state = UNRESOLVED[state]
            condition_state = None
            output_value = None
        observations[rule_id] = {
            "rule_id": rule_id, "evidence_state": evidence_state, "condition_state": condition_state,
            "observed_at": observed_text, "observed_value": output_value,
            "capture_authorization_receipt_id": item["capture_authorization_receipt_id"],
            "capture_receipt_id": item["capture_receipt_id"],
            "candidate_binding_receipt_id": item["candidate_binding_receipt_id"],
            "privacy_receipt_id": item["privacy_receipt_id"],
        }
    if set(observations) != set(rules):
        raise ValueError("candidate must contain exactly one observation for every rule")
    evidence = [observations[rule_id] for rule_id in sorted(rules)]
    states = {item["evidence_state"] for item in evidence}
    candidate_state = next((state for state in PRECEDENCE if state in states), None)
    if candidate_state is None:
        candidate_state = "AT_LEAST_ONE_CUSTOMER_RULE_CONDITION_NOT_MET" if any(item["condition_state"] == "CUSTOMER_RULE_CONDITION_NOT_MET" for item in evidence) else "ALL_CUSTOMER_RULE_CONDITIONS_MET"
    return {"candidate_id": candidate_id, "rule_evidence": evidence, "candidate_state": candidate_state}


def review_candidate_evidence(document: dict[str, Any]) -> dict[str, Any]:
    """Validate and review one frozen pseudonymous candidate packet."""
    root = _obj(document, "document")
    _keys(root, {"schema_version", "review_id", "policy", "candidate_population", "candidates"}, "document")
    if root["schema_version"] != "candidate-rule-evidence-v1":
        raise ValueError("unsupported schema_version")
    review_id = _id(root["review_id"], "review_id", "review-")
    policy, rules, receipts, cutoff = _policy(root["policy"])
    population, declared = _population(root["candidate_population"], receipts, rules, policy, cutoff)
    candidates: dict[str, dict[str, Any]] = {}
    for raw_candidate in _arr(root["candidates"], "candidates"):
        reviewed = _review_candidate(raw_candidate, rules, receipts, cutoff)
        candidate_id = reviewed["candidate_id"]
        if candidate_id in candidates:
            raise ValueError("duplicate candidate row")
        candidates[candidate_id] = reviewed
    if set(candidates) != set(declared):
        raise ValueError("candidate rows must equal declared population")
    ordered_candidates = [candidates[candidate_id] for candidate_id in sorted(declared)]
    candidate_states = {item["candidate_state"] for item in ordered_candidates}
    review_state = next((state for state in PRECEDENCE if state in candidate_states), "CUSTOMER_RULE_CONDITIONS_REVIEWED")
    public_rules = []
    for rule_id in sorted(rules):
        public_rules.append({key: value for key, value in rules[rule_id].items() if not key.startswith("_")})
    return {
        "schema_version": root["schema_version"], "review_id": review_id, "purpose": PURPOSE,
        "policy": policy, "candidate_population": population, "rule_contracts": public_rules,
        "candidates": ordered_candidates, "review_state": review_state,
        "action_flags": {
            "identity_resolution_authorized": False, "contact_data_release_authorized": False,
            "enrichment_authorized": False, "fuzzy_matching_authorized": False,
            "scoring_authorized": False, "ranking_authorized": False,
            "prioritization_authorized": False, "outreach_authorized": False,
            "export_authorized": False, "crm_write_authorized": False,
            "notification_authorized": False, "retry_authorized": False,
            "scheduling_authorized": False, "publication_authorized": False,
            "downstream_action_authorized": False,
        },
        "boundary": BOUNDARY,
    }


def render_review_output(result: dict[str, Any]) -> str:
    """Render exactly once with one explicit empty terminal line."""
    return json.dumps(result, indent=2, ensure_ascii=True) + "\n\n"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: candidate_rule_evidence.py INPUT.json", file=sys.stderr)
        return 2
    try:
        document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        sys.stdout.write(render_review_output(review_candidate_evidence(document)))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
