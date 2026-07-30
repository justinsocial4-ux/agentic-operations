#!/usr/bin/env python3
"""Deterministic pseudonymous integration-observation evidence review."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_integration_observation_evidence_review"
SOURCE_KIND = "customer-supplied-pseudonymous-integration-observation"
LANES = (
    "source-endpoint", "connector-job", "destination-endpoint", "checkpoint", "reconciliation",
)
UNRESOLVED = {
    "unauthorized": "UNAUTHORIZED",
    "suppressed": "SUPPRESSED",
    "conflicting": "EVIDENCE_CONFLICT",
    "missing": "EVIDENCE_MISSING",
}
UNRESOLVED_PRECEDENCE = ("unauthorized", "suppressed", "conflicting", "missing")
REQUIRED_PROHIBITIONS = {
    "alert", "business-impact-inference", "cause-inference", "confidence-score",
    "credential-access", "downstream-decision", "escalation", "health-label",
    "live-system-access", "message-send", "monitoring", "outage-label", "polling",
    "publication", "remediation", "risk-label", "scheduling", "severity-label",
    "system-write",
}
BOUNDARY = "NO HEALTH, OUTAGE, CAUSE, IMPACT, SEVERITY, ALERT, REMEDIATION, SYSTEM, OR DOWNSTREAM DECISION"
FORBIDDEN_STATE_TOKENS = {"healthy", "degraded", "critical", "high-risk", "low-risk", "reliable", "unreliable", "available", "unavailable", "down", "recovered"}
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


def _integration_id(value: Any, label: str) -> str:
    result = _id(value, label)
    if not result.startswith("integration-"):
        raise ValueError(f"{label} must begin with integration-")
    return result


def _source_id(value: Any, label: str) -> str:
    result = _id(value, label)
    if not result.startswith("source-"):
        raise ValueError(f"{label} must begin with source-")
    return result


def _token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} must be a structured token")
    return value


def _recorded_state(value: Any, label: str) -> str:
    result = _id(value, label)
    if result in FORBIDDEN_STATE_TOKENS:
        raise ValueError(f"{label} cannot be a health, risk, availability, or recovery label")
    return result


def _time(value: Any, label: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        raise ValueError(f"{label} must be second-precision UTC ending in Z")
    return value, datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


def _optional_time(value: Any, label: str) -> tuple[str | None, datetime | None]:
    if value is None:
        return None, None
    return _time(value, label)


def _integer(value: Any, label: str, *, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0):
        qualifier = "positive" if positive else "non-negative"
        raise ValueError(f"{label} must be a {qualifier} integer")
    return value


def _ids(values: Any, label: str, *, integrations: bool = False) -> list[str]:
    validate = _integration_id if integrations else _id
    result = [validate(item, f"{label}[]") for item in _arr(values, label)]
    if len(result) != len(set(result)):
        raise ValueError(f"{label} contains duplicates")
    return result


def _policy(raw: Any) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, Any]], dict[str, dict[str, Any]], set[str]]:
    row = _obj(raw, "policy")
    fields = {
        "policy_id", "policy_version", "effective_at", "expires_at", "cutoff_at", "timezone",
        "approved_purpose", "owner_role_id", "human_reviewer_role_id",
        "operations_approval_receipt_id", "security_review_receipt_id", "privacy_review_receipt_id",
        "recipient_policy_receipt_id", "retention_policy_receipt_id", "observation_policy_receipt_id",
        "allowed_recipient_role_ids", "prohibited_uses", "source_bindings", "integration_contracts",
    }
    _keys(row, fields, "policy")
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
    recipients = _ids(row["allowed_recipient_role_ids"], "policy.allowed_recipient_role_ids")
    if not recipients:
        raise ValueError("at least one recipient role is required")
    receipt_fields = (
        "operations_approval_receipt_id", "security_review_receipt_id", "privacy_review_receipt_id",
        "recipient_policy_receipt_id", "retention_policy_receipt_id", "observation_policy_receipt_id",
    )
    governance_receipts = [_id(row[field], f"policy.{field}") for field in receipt_fields]
    if len(governance_receipts) != len(set(governance_receipts)):
        raise ValueError("governance receipts must be separate")
    reserved_receipts = set(governance_receipts)

    bindings: dict[tuple[str, str], dict[str, Any]] = {}
    binding_fields = {
        "source_id", "source_version", "source_kind", "schema_id", "schema_version",
        "authorization_receipt_id", "authorization_effective_at", "authorization_expires_at",
        "query_receipt_id", "page_receipt_id", "pseudonymization_receipt_id",
    }
    for index, raw_binding in enumerate(_arr(row["source_bindings"], "policy.source_bindings")):
        binding = _obj(raw_binding, f"source_bindings[{index}]")
        _keys(binding, binding_fields, f"source_bindings[{index}]")
        source_id = _source_id(binding["source_id"], "binding.source_id")
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
        if reserved_receipts.intersection(source_receipts):
            raise ValueError("source receipts must be globally unique")
        reserved_receipts.update(source_receipts)
        key = (source_id, source_version)
        if key in bindings:
            raise ValueError("duplicate source binding")
        bindings[key] = {
            "source_id": source_id, "source_version": source_version, "source_kind": SOURCE_KIND,
            "schema_id": _id(binding["schema_id"], "binding.schema_id"),
            "schema_version": _id(binding["schema_version"], "binding.schema_version"),
            "authorization_receipt_id": source_receipts[0], "authorization_effective_at": auth_effective_text,
            "authorization_expires_at": auth_expires_text, "query_receipt_id": source_receipts[1],
            "page_receipt_id": source_receipts[2], "pseudonymization_receipt_id": source_receipts[3],
        }
    if not bindings:
        raise ValueError("at least one source binding is required")

    contracts: dict[str, dict[str, Any]] = {}
    contract_fields = {"integration_id", "contract_id", "contract_version", "contract_receipt_id", "lane_contracts"}
    lane_fields = {
        "lane_id", "lane_kind", "definition_receipt_id", "expected_recorded_state",
        "max_age_seconds", "reconciliation_rule",
    }
    for index, raw_contract in enumerate(_arr(row["integration_contracts"], "policy.integration_contracts")):
        contract = _obj(raw_contract, f"integration_contracts[{index}]")
        _keys(contract, contract_fields, f"integration_contracts[{index}]")
        integration_id = _integration_id(contract["integration_id"], "contract.integration_id")
        if integration_id in contracts:
            raise ValueError("duplicate integration contract")
        lane_map: dict[str, dict[str, Any]] = {}
        for lane_index, raw_lane in enumerate(_arr(contract["lane_contracts"], "contract.lane_contracts")):
            lane = _obj(raw_lane, f"lane_contracts[{lane_index}]")
            _keys(lane, lane_fields, f"lane_contracts[{lane_index}]")
            lane_kind = lane["lane_kind"]
            if lane_kind not in LANES or lane["lane_id"] != lane_kind:
                raise ValueError("lane ID and kind must be one exact required lane")
            if lane_kind in lane_map:
                raise ValueError("duplicate lane contract")
            expected = lane["expected_recorded_state"]
            max_age = lane["max_age_seconds"]
            rule = lane["reconciliation_rule"]
            if lane_kind in {"source-endpoint", "connector-job", "destination-endpoint"}:
                expected = _recorded_state(expected, "lane.expected_recorded_state")
                if max_age is not None or rule is not None:
                    raise ValueError("state lane contains incompatible contract values")
            elif lane_kind == "checkpoint":
                max_age = _integer(max_age, "lane.max_age_seconds", positive=True)
                if expected is not None or rule is not None:
                    raise ValueError("checkpoint lane contains incompatible contract values")
            else:
                if rule != "source-total-equals-target-total" or expected is not None or max_age is not None:
                    raise ValueError("reconciliation lane contract is invalid")
            lane_map[lane_kind] = {
                "lane_id": lane_kind, "lane_kind": lane_kind,
                "definition_receipt_id": _id(lane["definition_receipt_id"], "lane.definition_receipt_id"),
                "expected_recorded_state": expected, "max_age_seconds": max_age,
                "reconciliation_rule": rule,
            }
        if set(lane_map) != set(LANES):
            raise ValueError("integration contract must contain exactly five required lanes")
        definition_receipts = [lane_map[k]["definition_receipt_id"] for k in LANES]
        if len(definition_receipts) != len(set(definition_receipts)):
            raise ValueError("lane definition receipts must be unique")
        contract_receipt = _id(contract["contract_receipt_id"], "contract.contract_receipt_id")
        if contract_receipt in reserved_receipts or reserved_receipts.intersection(definition_receipts):
            raise ValueError("contract and lane receipts must be globally unique")
        reserved_receipts.add(contract_receipt)
        reserved_receipts.update(definition_receipts)
        contracts[integration_id] = {
            "integration_id": integration_id,
            "contract_id": _id(contract["contract_id"], "contract.contract_id"),
            "contract_version": _id(contract["contract_version"], "contract.contract_version"),
            "contract_receipt_id": contract_receipt,
            "lane_contracts": [lane_map[k] for k in LANES],
            "lane_map": lane_map,
        }
    if not contracts:
        raise ValueError("at least one integration contract is required")
    policy = {
        "policy_id": _id(row["policy_id"], "policy.policy_id"),
        "policy_version": _id(row["policy_version"], "policy.policy_version"),
        "effective_at": effective_text, "expires_at": expires_text, "cutoff_at": cutoff_text,
        "timezone": timezone_name, "approved_purpose": PURPOSE,
        "owner_role_id": _id(row["owner_role_id"], "policy.owner_role_id"),
        "human_reviewer_role_id": _id(row["human_reviewer_role_id"], "policy.human_reviewer_role_id"),
        **dict(zip(receipt_fields, governance_receipts)),
        "allowed_recipient_role_ids": sorted(recipients), "prohibited_uses": sorted(prohibited),
        "source_bindings": [bindings[key] for key in sorted(bindings)],
        "integration_contracts": [
            {k: v for k, v in contracts[key].items() if k != "lane_map"} for key in sorted(contracts)
        ],
    }
    return policy, bindings, contracts, reserved_receipts


def review_integration_evidence(document: Any) -> dict[str, Any]:
    root = _obj(document, "document")
    _keys(root, {"review_declaration", "policy", "source_populations", "observations"}, "document")
    declaration = _obj(root["review_declaration"], "review_declaration")
    _keys(declaration, {"review_id", "policy_id", "policy_version", "reviewed_at", "recipient_role_id", "integration_ids"}, "review_declaration")
    review_id = _id(declaration["review_id"], "declaration.review_id")
    reviewed_text, reviewed = _time(declaration["reviewed_at"], "declaration.reviewed_at")
    declared_integrations = _ids(declaration["integration_ids"], "declaration.integration_ids", integrations=True)
    if not declared_integrations:
        raise ValueError("declared integration population cannot be empty")
    policy, bindings, contracts, reserved_receipts = _policy(root["policy"])
    if declaration["policy_id"] != policy["policy_id"] or declaration["policy_version"] != policy["policy_version"]:
        raise ValueError("declaration conflicts with policy")
    cutoff = _time(policy["cutoff_at"], "policy.cutoff_at")[1]
    effective = _time(policy["effective_at"], "policy.effective_at")[1]
    expires = _optional_time(policy["expires_at"], "policy.expires_at")[1]
    if reviewed < cutoff or reviewed < effective or (expires is not None and reviewed > expires):
        raise ValueError("review time is outside policy window")
    recipient = _id(declaration["recipient_role_id"], "declaration.recipient_role_id")
    if recipient not in policy["allowed_recipient_role_ids"]:
        raise ValueError("recipient is not approved")
    if set(declared_integrations) != set(contracts):
        raise ValueError("declared integrations must exactly match policy contracts")

    population_fields = {"source_id", "source_version", "population_receipt_id", "complete", "observation_receipt_ids"}
    population_receipts: set[str] = set()
    allowed_observation_receipts: dict[tuple[str, str], set[str]] = {}
    for index, raw_population in enumerate(_arr(root["source_populations"], "source_populations")):
        population = _obj(raw_population, f"source_populations[{index}]")
        _keys(population, population_fields, f"source_populations[{index}]")
        key = (_source_id(population["source_id"], "population.source_id"), _id(population["source_version"], "population.source_version"))
        if key not in bindings or key in allowed_observation_receipts:
            raise ValueError("population source is unapproved or duplicated")
        if population["complete"] is not True:
            raise ValueError("source population must be complete")
        population_receipt = _id(population["population_receipt_id"], "population.population_receipt_id")
        if population_receipt in population_receipts or population_receipt in reserved_receipts:
            raise ValueError("population receipts must be globally unique")
        population_receipts.add(population_receipt)
        reserved_receipts.add(population_receipt)
        receipt_ids = set(_ids(population["observation_receipt_ids"], "population.observation_receipt_ids"))
        if not receipt_ids:
            raise ValueError("source population cannot be empty")
        allowed_observation_receipts[key] = receipt_ids
    population_observation_receipts = [receipt for receipts in allowed_observation_receipts.values() for receipt in receipts]
    if len(population_observation_receipts) != len(set(population_observation_receipts)):
        raise ValueError("observation receipts cannot appear in multiple source populations")
    if set(allowed_observation_receipts) != set(bindings):
        raise ValueError("every source binding requires one complete population")

    observation_fields = {
        "integration_id", "lane_id", "lane_kind", "source_id", "source_version",
        "evidence_receipt_id", "evidence_state", "observed_at", "captured_at",
        "recorded_state", "recorded_state_receipt_id", "checkpoint_at", "checkpoint_receipt_id",
        "source_total", "source_total_receipt_id", "target_total", "target_total_receipt_id",
    }
    observations: dict[tuple[str, str], dict[str, Any]] = {}
    seen_receipts: set[str] = set()
    for index, raw_observation in enumerate(_arr(root["observations"], "observations")):
        observation = _obj(raw_observation, f"observations[{index}]")
        _keys(observation, observation_fields, f"observations[{index}]")
        integration_id = _integration_id(observation["integration_id"], "observation.integration_id")
        if integration_id not in contracts:
            raise ValueError("observation integration is undeclared")
        lane_kind = observation["lane_kind"]
        if lane_kind not in LANES or observation["lane_id"] != lane_kind:
            raise ValueError("observation lane ID and kind conflict")
        key = (integration_id, lane_kind)
        if key in observations:
            raise ValueError("duplicate integration-lane observation")
        source_key = (_source_id(observation["source_id"], "observation.source_id"), _id(observation["source_version"], "observation.source_version"))
        if source_key not in bindings:
            raise ValueError("observation source is not approved")
        receipt_id = _id(observation["evidence_receipt_id"], "observation.evidence_receipt_id")
        if receipt_id in seen_receipts or receipt_id in reserved_receipts or receipt_id not in allowed_observation_receipts[source_key]:
            raise ValueError("observation receipt is duplicate or absent from its complete population")
        seen_receipts.add(receipt_id)
        observed_text, observed = _time(observation["observed_at"], "observation.observed_at")
        captured_text, captured = _time(observation["captured_at"], "observation.captured_at")
        if observed > captured or captured > cutoff:
            raise ValueError("observation time order is invalid")
        evidence_state = observation["evidence_state"]
        if evidence_state not in {"recorded", *UNRESOLVED}:
            raise ValueError("evidence state is not allowed")
        recorded_state = observation["recorded_state"]
        recorded_state_receipt = observation["recorded_state_receipt_id"]
        checkpoint_text = None
        checkpoint = None
        checkpoint_receipt = observation["checkpoint_receipt_id"]
        source_total = observation["source_total"]
        source_total_receipt = observation["source_total_receipt_id"]
        target_total = observation["target_total"]
        target_total_receipt = observation["target_total_receipt_id"]
        if evidence_state != "recorded":
            if any(value is not None for value in (
                recorded_state, recorded_state_receipt, observation["checkpoint_at"], checkpoint_receipt,
                source_total, source_total_receipt, target_total, target_total_receipt,
            )):
                raise ValueError("unresolved observation cannot contain recorded values")
        elif lane_kind in {"source-endpoint", "connector-job", "destination-endpoint"}:
            recorded_state = _recorded_state(recorded_state, "observation.recorded_state")
            recorded_state_receipt = _id(recorded_state_receipt, "observation.recorded_state_receipt_id")
            if any(value is not None for value in (observation["checkpoint_at"], checkpoint_receipt, source_total, source_total_receipt, target_total, target_total_receipt)):
                raise ValueError("state observation contains incompatible values")
        elif lane_kind == "checkpoint":
            checkpoint_text, checkpoint = _time(observation["checkpoint_at"], "observation.checkpoint_at")
            checkpoint_receipt = _id(checkpoint_receipt, "observation.checkpoint_receipt_id")
            if checkpoint > observed or any(value is not None for value in (recorded_state, recorded_state_receipt, source_total, source_total_receipt, target_total, target_total_receipt)):
                raise ValueError("checkpoint observation contains incompatible values")
        else:
            source_total = _integer(source_total, "observation.source_total")
            source_total_receipt = _id(source_total_receipt, "observation.source_total_receipt_id")
            target_total = _integer(target_total, "observation.target_total")
            target_total_receipt = _id(target_total_receipt, "observation.target_total_receipt_id")
            if any(value is not None for value in (recorded_state, recorded_state_receipt, observation["checkpoint_at"], checkpoint_receipt)):
                raise ValueError("reconciliation observation contains incompatible values")
        value_receipts = [value for value in (recorded_state_receipt, checkpoint_receipt, source_total_receipt, target_total_receipt) if value is not None]
        if len(value_receipts) != len(set(value_receipts)) or reserved_receipts.intersection(value_receipts) or seen_receipts.intersection(value_receipts):
            raise ValueError("value receipts must be globally unique")
        reserved_receipts.update(value_receipts)
        binding = bindings[source_key]
        auth_effective = _time(binding["authorization_effective_at"], "binding.authorization_effective_at")[1]
        auth_expires = _optional_time(binding["authorization_expires_at"], "binding.authorization_expires_at")[1]
        if captured < auth_effective or (auth_expires is not None and captured > auth_expires):
            raise ValueError("source authorization does not cover observation capture")
        observations[key] = {
            "integration_id": integration_id, "lane_id": lane_kind, "lane_kind": lane_kind,
            "source_id": source_key[0], "source_version": source_key[1], "evidence_receipt_id": receipt_id,
            "evidence_state": evidence_state, "observed_at": observed_text, "captured_at": captured_text,
            "recorded_state": recorded_state, "recorded_state_receipt_id": recorded_state_receipt,
            "checkpoint_at": checkpoint_text, "checkpoint_receipt_id": checkpoint_receipt,
            "source_total": source_total, "source_total_receipt_id": source_total_receipt,
            "target_total": target_total, "target_total_receipt_id": target_total_receipt,
        }
    expected_keys = {(integration_id, lane) for integration_id in contracts for lane in LANES}
    if set(observations) != expected_keys:
        raise ValueError("observations must contain exactly one row per declared integration lane")
    population_union = set().union(*allowed_observation_receipts.values())
    if seen_receipts != population_union:
        raise ValueError("complete source populations and observations do not reconcile")

    integration_results: list[dict[str, Any]] = []
    for integration_id in sorted(contracts):
        contract = contracts[integration_id]
        lane_results: list[dict[str, Any]] = []
        lane_states: list[str] = []
        for lane_kind in LANES:
            observation = observations[(integration_id, lane_kind)]
            lane_contract = contract["lane_map"][lane_kind]
            if observation["evidence_state"] in UNRESOLVED:
                state = UNRESOLVED[observation["evidence_state"]]
                values: dict[str, Any] = {}
            elif lane_kind in {"source-endpoint", "connector-job", "destination-endpoint"}:
                state = "CONTRACT_OBSERVATION_MATCHED" if observation["recorded_state"] == lane_contract["expected_recorded_state"] else "CONTRACT_OBSERVATION_NOT_MATCHED"
                values = {
                    "recorded_state": observation["recorded_state"],
                    "recorded_state_receipt_id": observation["recorded_state_receipt_id"],
                    "expected_recorded_state": lane_contract["expected_recorded_state"],
                }
            elif lane_kind == "checkpoint":
                checkpoint = _time(observation["checkpoint_at"], "observation.checkpoint_at")[1]
                age_seconds = int((cutoff - checkpoint).total_seconds())
                max_age_seconds = lane_contract["max_age_seconds"]
                state = "CONTRACT_OBSERVATION_MATCHED" if age_seconds <= max_age_seconds else "CONTRACT_OBSERVATION_NOT_MATCHED"
                values = {
                    "checkpoint_at": observation["checkpoint_at"],
                    "checkpoint_receipt_id": observation["checkpoint_receipt_id"],
                    "maximum_age_seconds": max_age_seconds,
                    "observed_age_seconds": age_seconds,
                }
            else:
                difference = observation["source_total"] - observation["target_total"]
                state = "CONTRACT_OBSERVATION_MATCHED" if difference == 0 else "CONTRACT_OBSERVATION_NOT_MATCHED"
                values = {
                    "reconciliation_rule": lane_contract["reconciliation_rule"],
                    "source_total": observation["source_total"],
                    "source_total_receipt_id": observation["source_total_receipt_id"],
                    "target_total": observation["target_total"],
                    "target_total_receipt_id": observation["target_total_receipt_id"],
                    "source_minus_target": difference,
                }
            lane_states.append(state)
            lane_results.append({
                "lane_id": lane_kind, "lane_kind": lane_kind, "evidence_state": state,
                "definition_receipt_id": lane_contract["definition_receipt_id"],
                "evidence_receipt_id": observation["evidence_receipt_id"],
                "source_id": observation["source_id"], "source_version": observation["source_version"],
                "observed_at": observation["observed_at"], "captured_at": observation["captured_at"],
                "values": values,
            })
        integration_state = "CONTRACT_OBSERVATION_MATCHED"
        for unresolved_key in UNRESOLVED_PRECEDENCE:
            unresolved_state = UNRESOLVED[unresolved_key]
            if unresolved_state in lane_states:
                integration_state = unresolved_state
                break
        else:
            if "CONTRACT_OBSERVATION_NOT_MATCHED" in lane_states:
                integration_state = "CONTRACT_OBSERVATION_NOT_MATCHED"
        integration_results.append({
            "integration_id": integration_id, "evidence_state": integration_state,
            "contract_id": contract["contract_id"], "contract_version": contract["contract_version"],
            "contract_receipt_id": contract["contract_receipt_id"], "lane_receipts": lane_results,
        })
    return {
        "review_id": review_id, "reviewed_at": reviewed_text, "recipient_role_id": recipient,
        "policy_receipt": {
            "policy_id": policy["policy_id"], "policy_version": policy["policy_version"],
            "cutoff_at": policy["cutoff_at"], "timezone": policy["timezone"],
            "operations_approval_receipt_id": policy["operations_approval_receipt_id"],
            "security_review_receipt_id": policy["security_review_receipt_id"],
            "privacy_review_receipt_id": policy["privacy_review_receipt_id"],
            "recipient_policy_receipt_id": policy["recipient_policy_receipt_id"],
            "retention_policy_receipt_id": policy["retention_policy_receipt_id"],
            "observation_policy_receipt_id": policy["observation_policy_receipt_id"],
        },
        "integration_reviews": integration_results,
        "interpretation_boundary": BOUNDARY,
        "action_authorization": {
            "alert_authorized": False, "escalation_authorized": False,
            "remediation_authorized": False, "system_action_authorized": False,
            "downstream_decision_authorized": False, "publication_authorized": False,
        },
    }


def render_review_output(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n\n"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: integration_evidence.py INPUT.json")
    document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sys.stdout.write(render_review_output(review_integration_evidence(document)))


if __name__ == "__main__":
    main()
