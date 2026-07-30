#!/usr/bin/env python3
"""Deterministic pseudonymous enrichment route-plan evidence review."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_enrichment_route_plan_evidence_review"
SOURCE_KIND = "customer-supplied-pseudonymous-enrichment-route-plan"
ELIGIBLE = "eligible"
UNRESOLVED = {"unauthorized": "UNAUTHORIZED", "suppressed": "SUPPRESSED", "conflicting": "EVIDENCE_CONFLICT", "missing": "EVIDENCE_MISSING"}
PRECEDENCE = ("unauthorized", "suppressed", "conflicting", "missing")
REQUIRED_PROHIBITIONS = {
    "accuracy-score", "alert", "candidate-value", "confidence-score", "crm-read", "crm-write",
    "direct-identifier", "downstream-decision", "enrichment-execution", "fallback-routing",
    "fuzzy-identity", "message-send", "personal-data", "profiling", "provider-call",
    "provider-ranking", "publication", "route-selection", "scheduling", "spend-authorization",
    "value-resolution",
}
BOUNDARY = "NO PROVIDER CHOICE, PERSONAL DATA, ENRICHMENT, VALUE RESOLUTION, SPEND, CRM, OUTREACH, OR DOWNSTREAM ACTION"
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_./:+-]*$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
MONEY_RE = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d{1,6})?$")


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


def _token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} must be a structured token")
    return value


def _time(value: Any, label: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        raise ValueError(f"{label} must be second-precision UTC ending in Z")
    return value, datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


def _optional_time(value: Any, label: str) -> tuple[str | None, datetime | None]:
    if value is None:
        return None, None
    return _time(value, label)


def _ids(values: Any, label: str, prefix: str | None = None) -> list[str]:
    result = [_id(value, f"{label}[]", prefix) for value in _arr(values, label)]
    if len(result) != len(set(result)):
        raise ValueError(f"{label} contains duplicates")
    return result


def _money(value: Any, label: str) -> tuple[str, Decimal]:
    if not isinstance(value, str) or not MONEY_RE.fullmatch(value):
        raise ValueError(f"{label} must be a non-negative decimal string with at most six places")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} is invalid") from exc
    return format(amount, "f"), amount


def _reserve(receipts: set[str], value: Any, label: str) -> str:
    receipt = _id(value, label, "receipt-")
    if receipt in receipts:
        raise ValueError("receipts must be globally unique")
    receipts.add(receipt)
    return receipt


def _policy(raw: Any) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]], set[str]]:
    row = _obj(raw, "policy")
    fields = {
        "policy_id", "policy_version", "effective_at", "expires_at", "cutoff_at", "timezone",
        "approved_purpose", "currency", "owner_role_id", "human_reviewer_role_id",
        "operations_approval_receipt_id", "security_review_receipt_id", "privacy_review_receipt_id",
        "legal_review_receipt_id", "lawful_basis_receipt_id", "notice_receipt_id",
        "objection_path_receipt_id", "suppression_policy_receipt_id", "correction_path_receipt_id",
        "recipient_policy_receipt_id", "retention_policy_receipt_id", "route_policy_receipt_id",
        "allowed_recipient_role_ids", "prohibited_uses", "source_bindings", "field_definitions",
        "provider_contracts",
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
    currency = _token(row["currency"], "policy.currency")
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("policy.currency must be an uppercase three-letter code")
    prohibited = _ids(row["prohibited_uses"], "policy.prohibited_uses")
    if not REQUIRED_PROHIBITIONS.issubset(prohibited):
        raise ValueError("policy.prohibited_uses is missing a required boundary")
    recipients = _ids(row["allowed_recipient_role_ids"], "policy.allowed_recipient_role_ids", "role-")
    if not recipients:
        raise ValueError("at least one recipient role is required")
    receipt_fields = (
        "operations_approval_receipt_id", "security_review_receipt_id", "privacy_review_receipt_id",
        "legal_review_receipt_id", "lawful_basis_receipt_id", "notice_receipt_id",
        "objection_path_receipt_id", "suppression_policy_receipt_id", "correction_path_receipt_id",
        "recipient_policy_receipt_id", "retention_policy_receipt_id", "route_policy_receipt_id",
    )
    receipts: set[str] = set()
    governance = [_reserve(receipts, row[field], f"policy.{field}") for field in receipt_fields]

    binding_fields = {
        "source_id", "source_version", "source_kind", "schema_id", "schema_version",
        "authorization_receipt_id", "authorization_effective_at", "authorization_expires_at",
        "query_receipt_id", "page_receipt_id", "pseudonymization_receipt_id",
    }
    bindings: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw_binding in enumerate(_arr(row["source_bindings"], "policy.source_bindings")):
        binding = _obj(raw_binding, f"source_bindings[{index}]")
        _keys(binding, binding_fields, f"source_bindings[{index}]")
        source_id = _id(binding["source_id"], "binding.source_id", "source-")
        source_version = _id(binding["source_version"], "binding.source_version")
        if binding["source_kind"] != SOURCE_KIND:
            raise ValueError("source kind is not allowed")
        auth_effective_text, auth_effective = _time(binding["authorization_effective_at"], "binding.authorization_effective_at")
        auth_expires_text, auth_expires = _optional_time(binding["authorization_expires_at"], "binding.authorization_expires_at")
        if auth_effective > cutoff or (auth_expires is not None and auth_expires < cutoff):
            raise ValueError("source authorization does not cover cutoff")
        key = (source_id, source_version)
        if key in bindings:
            raise ValueError("duplicate source binding")
        bindings[key] = {
            "source_id": source_id, "source_version": source_version, "source_kind": SOURCE_KIND,
            "schema_id": _id(binding["schema_id"], "binding.schema_id"),
            "schema_version": _id(binding["schema_version"], "binding.schema_version"),
            "authorization_receipt_id": _reserve(receipts, binding["authorization_receipt_id"], "binding.authorization_receipt_id"),
            "authorization_effective_at": auth_effective_text, "authorization_expires_at": auth_expires_text,
            "query_receipt_id": _reserve(receipts, binding["query_receipt_id"], "binding.query_receipt_id"),
            "page_receipt_id": _reserve(receipts, binding["page_receipt_id"], "binding.page_receipt_id"),
            "pseudonymization_receipt_id": _reserve(receipts, binding["pseudonymization_receipt_id"], "binding.pseudonymization_receipt_id"),
        }
    if not bindings:
        raise ValueError("at least one source binding is required")

    field_fields = {"field_id", "field_version", "definition_receipt_id", "purpose_receipt_id", "minimization_receipt_id", "field_policy_receipt_id"}
    field_defs: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw_field in enumerate(_arr(row["field_definitions"], "policy.field_definitions")):
        item = _obj(raw_field, f"field_definitions[{index}]")
        _keys(item, field_fields, f"field_definitions[{index}]")
        key = (_id(item["field_id"], "field.field_id", "field-"), _id(item["field_version"], "field.field_version"))
        if key in field_defs:
            raise ValueError("duplicate field definition")
        field_defs[key] = {
            "field_id": key[0], "field_version": key[1],
            "definition_receipt_id": _reserve(receipts, item["definition_receipt_id"], "field.definition_receipt_id"),
            "purpose_receipt_id": _reserve(receipts, item["purpose_receipt_id"], "field.purpose_receipt_id"),
            "minimization_receipt_id": _reserve(receipts, item["minimization_receipt_id"], "field.minimization_receipt_id"),
            "field_policy_receipt_id": _reserve(receipts, item["field_policy_receipt_id"], "field.field_policy_receipt_id"),
        }
    if not field_defs:
        raise ValueError("at least one field definition is required")

    provider_fields = {
        "provider_id", "contract_id", "contract_version", "authorization_effective_at", "authorization_expires_at",
        "contract_receipt_id", "authorization_receipt_id", "terms_receipt_id", "geography_receipt_id",
        "field_support_receipt_id", "price_receipt_id", "charge_unit", "currency", "unit_cost",
        "geography_scope_id", "supported_fields",
    }
    providers: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw_provider in enumerate(_arr(row["provider_contracts"], "policy.provider_contracts")):
        item = _obj(raw_provider, f"provider_contracts[{index}]")
        _keys(item, provider_fields, f"provider_contracts[{index}]")
        provider_id = _id(item["provider_id"], "provider.provider_id", "provider-")
        contract_version = _id(item["contract_version"], "provider.contract_version")
        key = (provider_id, contract_version)
        if key in providers:
            raise ValueError("duplicate provider contract")
        auth_effective_text, auth_effective = _time(item["authorization_effective_at"], "provider.authorization_effective_at")
        auth_expires_text, auth_expires = _optional_time(item["authorization_expires_at"], "provider.authorization_expires_at")
        if auth_effective > cutoff or (auth_expires is not None and auth_expires < cutoff):
            raise ValueError("provider authorization does not cover cutoff")
        if item["charge_unit"] != "per-route-assignment" or item["currency"] != currency:
            raise ValueError("provider charge basis conflicts with policy")
        unit_cost_text, unit_cost = _money(item["unit_cost"], "provider.unit_cost")
        supported = []
        for raw_support in _arr(item["supported_fields"], "provider.supported_fields"):
            support = _obj(raw_support, "provider.supported_fields[]")
            _keys(support, {"field_id", "field_version"}, "provider.supported_fields[]")
            field_key = (_id(support["field_id"], "support.field_id", "field-"), _id(support["field_version"], "support.field_version"))
            if field_key not in field_defs or field_key in supported:
                raise ValueError("provider field support is unapproved or duplicated")
            supported.append(field_key)
        if not supported:
            raise ValueError("provider must support at least one approved field")
        providers[key] = {
            "provider_id": provider_id, "contract_id": _id(item["contract_id"], "provider.contract_id", "contract-"),
            "contract_version": contract_version, "authorization_effective_at": auth_effective_text,
            "authorization_expires_at": auth_expires_text,
            "contract_receipt_id": _reserve(receipts, item["contract_receipt_id"], "provider.contract_receipt_id"),
            "authorization_receipt_id": _reserve(receipts, item["authorization_receipt_id"], "provider.authorization_receipt_id"),
            "terms_receipt_id": _reserve(receipts, item["terms_receipt_id"], "provider.terms_receipt_id"),
            "geography_receipt_id": _reserve(receipts, item["geography_receipt_id"], "provider.geography_receipt_id"),
            "geography_scope_id": _id(item["geography_scope_id"], "provider.geography_scope_id", "geography-"),
            "field_support_receipt_id": _reserve(receipts, item["field_support_receipt_id"], "provider.field_support_receipt_id"),
            "price_receipt_id": _reserve(receipts, item["price_receipt_id"], "provider.price_receipt_id"),
            "charge_unit": "per-route-assignment", "currency": currency, "unit_cost": unit_cost_text,
            "unit_cost_decimal": unit_cost, "supported_fields": sorted(supported),
        }
    if not providers:
        raise ValueError("at least one provider contract is required")
    policy = {
        "policy_id": _id(row["policy_id"], "policy.policy_id", "policy-"),
        "policy_version": _id(row["policy_version"], "policy.policy_version"),
        "effective_at": effective_text, "expires_at": expires_text, "cutoff_at": cutoff_text,
        "timezone": timezone_name, "approved_purpose": PURPOSE, "currency": currency,
        "owner_role_id": _id(row["owner_role_id"], "policy.owner_role_id", "role-"),
        "human_reviewer_role_id": _id(row["human_reviewer_role_id"], "policy.human_reviewer_role_id", "role-"),
        **dict(zip(receipt_fields, governance)), "allowed_recipient_role_ids": sorted(recipients),
        "prohibited_uses": sorted(prohibited),
    }
    return policy, bindings, field_defs, providers, receipts


def review_route_evidence(document: Any) -> dict[str, Any]:
    root = _obj(document, "document")
    _keys(root, {"review_declaration", "policy", "source_populations", "route_plan"}, "document")
    declaration = _obj(root["review_declaration"], "review_declaration")
    _keys(declaration, {"review_id", "policy_id", "policy_version", "reviewed_at", "recipient_role_id", "record_ids", "requested_fields"}, "review_declaration")
    review_id = _id(declaration["review_id"], "declaration.review_id", "review-")
    reviewed_text, reviewed = _time(declaration["reviewed_at"], "declaration.reviewed_at")
    record_ids = _ids(declaration["record_ids"], "declaration.record_ids", "record-")
    if not record_ids:
        raise ValueError("record population cannot be empty")
    policy, bindings, field_defs, providers, receipts = _policy(root["policy"])
    if declaration["policy_id"] != policy["policy_id"] or declaration["policy_version"] != policy["policy_version"]:
        raise ValueError("declaration conflicts with policy")
    cutoff = _time(policy["cutoff_at"], "policy.cutoff_at")[1]
    effective = _time(policy["effective_at"], "policy.effective_at")[1]
    expires = _optional_time(policy["expires_at"], "policy.expires_at")[1]
    if reviewed < cutoff or reviewed < effective or (expires is not None and reviewed > expires):
        raise ValueError("review time is outside policy window")
    recipient = _id(declaration["recipient_role_id"], "declaration.recipient_role_id", "role-")
    if recipient not in policy["allowed_recipient_role_ids"]:
        raise ValueError("recipient is not approved")
    requested: dict[str, list[tuple[str, str]]] = {}
    request_fields = {"record_id", "fields"}
    for index, raw_request in enumerate(_arr(declaration["requested_fields"], "declaration.requested_fields")):
        item = _obj(raw_request, f"requested_fields[{index}]")
        _keys(item, request_fields, f"requested_fields[{index}]")
        record_id = _id(item["record_id"], "request.record_id", "record-")
        if record_id not in record_ids or record_id in requested:
            raise ValueError("requested field record is undeclared or duplicated")
        fields = []
        for raw_field in _arr(item["fields"], "request.fields"):
            field = _obj(raw_field, "request.fields[]")
            _keys(field, {"field_id", "field_version"}, "request.fields[]")
            key = (_id(field["field_id"], "request.field_id", "field-"), _id(field["field_version"], "request.field_version"))
            if key not in field_defs or key in fields:
                raise ValueError("requested field is unapproved or duplicated")
            fields.append(key)
        if not fields:
            raise ValueError("each record needs at least one requested field")
        requested[record_id] = sorted(fields)
    if set(requested) != set(record_ids):
        raise ValueError("every declared record requires a requested field set")

    population_fields = {"source_id", "source_version", "population_receipt_id", "complete", "route_receipt_ids"}
    allowed_receipts: dict[tuple[str, str], set[str]] = {}
    for index, raw_population in enumerate(_arr(root["source_populations"], "source_populations")):
        item = _obj(raw_population, f"source_populations[{index}]")
        _keys(item, population_fields, f"source_populations[{index}]")
        source_key = (_id(item["source_id"], "population.source_id", "source-"), _id(item["source_version"], "population.source_version"))
        if source_key not in bindings or source_key in allowed_receipts or item["complete"] is not True:
            raise ValueError("population source is unapproved, duplicated, or incomplete")
        _reserve(receipts, item["population_receipt_id"], "population.population_receipt_id")
        route_receipts = set(_ids(item["route_receipt_ids"], "population.route_receipt_ids", "receipt-"))
        if not route_receipts:
            raise ValueError("source population cannot be empty")
        allowed_receipts[source_key] = route_receipts
    if set(allowed_receipts) != set(bindings):
        raise ValueError("every source binding requires one complete population")
    flattened = [receipt for group in allowed_receipts.values() for receipt in group]
    if len(flattened) != len(set(flattened)) or receipts.intersection(flattened):
        raise ValueError("route receipts must be globally unique")
    receipts.update(flattened)

    route_fields = {
        "record_id", "field_id", "field_version", "source_id", "source_version", "route_receipt_id",
        "request_state", "request_state_receipt_id", "provider_id", "provider_contract_version",
        "assignment_receipt_id", "geography_scope_id", "observed_at", "captured_at",
    }
    rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    seen_route_receipts: set[str] = set()
    for index, raw_route in enumerate(_arr(root["route_plan"], "route_plan")):
        item = _obj(raw_route, f"route_plan[{index}]")
        _keys(item, route_fields, f"route_plan[{index}]")
        record_id = _id(item["record_id"], "route.record_id", "record-")
        field_key = (_id(item["field_id"], "route.field_id", "field-"), _id(item["field_version"], "route.field_version"))
        key = (record_id, field_key[0], field_key[1])
        if record_id not in requested or field_key not in requested[record_id] or key in rows:
            raise ValueError("route pair is undeclared or duplicated")
        source_key = (_id(item["source_id"], "route.source_id", "source-"), _id(item["source_version"], "route.source_version"))
        if source_key not in bindings:
            raise ValueError("route source is not approved")
        route_receipt = _id(item["route_receipt_id"], "route.route_receipt_id", "receipt-")
        if route_receipt in seen_route_receipts or route_receipt not in allowed_receipts[source_key]:
            raise ValueError("route receipt is duplicate or absent from its population")
        seen_route_receipts.add(route_receipt)
        observed_text, observed = _time(item["observed_at"], "route.observed_at")
        captured_text, captured = _time(item["captured_at"], "route.captured_at")
        if observed > captured or captured > cutoff:
            raise ValueError("route time order is invalid")
        binding = bindings[source_key]
        auth_effective = _time(binding["authorization_effective_at"], "binding.authorization_effective_at")[1]
        auth_expires = _optional_time(binding["authorization_expires_at"], "binding.authorization_expires_at")[1]
        if captured < auth_effective or (auth_expires is not None and captured > auth_expires):
            raise ValueError("source authorization does not cover route capture")
        state = item["request_state"]
        if state not in {ELIGIBLE, *UNRESOLVED}:
            raise ValueError("request state is not allowed")
        request_state_receipt = _reserve(receipts, item["request_state_receipt_id"], "route.request_state_receipt_id")
        provider_key = None
        assignment_receipt = None
        geography_scope_id = None
        if state == ELIGIBLE:
            provider_key = (_id(item["provider_id"], "route.provider_id", "provider-"), _id(item["provider_contract_version"], "route.provider_contract_version"))
            assignment_receipt = _reserve(receipts, item["assignment_receipt_id"], "route.assignment_receipt_id")
            geography_scope_id = _id(item["geography_scope_id"], "route.geography_scope_id", "geography-")
        elif any(item[field] is not None for field in ("provider_id", "provider_contract_version", "assignment_receipt_id", "geography_scope_id")):
            raise ValueError("unresolved route cannot carry a provider assignment")
        rows[key] = {
            "record_id": record_id, "field_id": field_key[0], "field_version": field_key[1],
            "source_id": source_key[0], "source_version": source_key[1], "route_receipt_id": route_receipt,
            "request_state": state, "provider_key": provider_key, "observed_at": observed_text, "captured_at": captured_text,
            "request_state_receipt_id": request_state_receipt, "assignment_receipt_id": assignment_receipt,
            "geography_scope_id": geography_scope_id,
        }
    expected = {(record_id, field_id, field_version) for record_id, fields in requested.items() for field_id, field_version in fields}
    if set(rows) != expected or seen_route_receipts != set(flattened):
        raise ValueError("route plan and complete populations do not reconcile")

    route_results = []
    states = []
    total = Decimal("0")
    for key in sorted(rows):
        row = rows[key]
        if row["request_state"] in UNRESOLVED:
            state = UNRESOLVED[row["request_state"]]
            provider_receipt = None
            charge = None
        else:
            provider = providers.get(row["provider_key"])
            field_key = (row["field_id"], row["field_version"])
            if provider is None or field_key not in provider["supported_fields"] or row["geography_scope_id"] != provider["geography_scope_id"]:
                state = "CUSTOMER_ROUTE_EVIDENCE_NOT_MATCHED"
                provider_receipt = None if provider is None else {
                    "provider_id": provider["provider_id"], "contract_id": provider["contract_id"],
                    "contract_version": provider["contract_version"], "field_support_receipt_id": provider["field_support_receipt_id"],
                    "geography_scope_id": provider["geography_scope_id"], "geography_receipt_id": provider["geography_receipt_id"],
                }
                charge = None
            else:
                state = "CUSTOMER_ROUTE_EVIDENCE_MATCHED"
                provider_receipt = {
                    "provider_id": provider["provider_id"], "contract_id": provider["contract_id"],
                    "contract_version": provider["contract_version"], "contract_receipt_id": provider["contract_receipt_id"],
                    "authorization_receipt_id": provider["authorization_receipt_id"],
                    "terms_receipt_id": provider["terms_receipt_id"], "geography_receipt_id": provider["geography_receipt_id"],
                    "geography_scope_id": provider["geography_scope_id"],
                    "field_support_receipt_id": provider["field_support_receipt_id"], "price_receipt_id": provider["price_receipt_id"],
                }
                charge = {"charge_unit": provider["charge_unit"], "currency": provider["currency"], "included_in_aggregate": True}
                total += provider["unit_cost_decimal"]
        states.append(state)
        route_results.append({
            "record_id": row["record_id"], "field_id": row["field_id"], "field_version": row["field_version"],
            "evidence_state": state, "route_receipt_id": row["route_receipt_id"],
            "request_state_receipt_id": row["request_state_receipt_id"],
            "assignment_receipt_id": row["assignment_receipt_id"],
            "source_id": row["source_id"], "source_version": row["source_version"],
            "observed_at": row["observed_at"], "captured_at": row["captured_at"],
            "field_receipt": field_defs[(row["field_id"], row["field_version"])],
            "provider_receipt": provider_receipt, "planned_charge_basis_receipt": charge,
        })
    review_state = "CUSTOMER_ROUTE_EVIDENCE_MATCHED"
    for unresolved in PRECEDENCE:
        mapped = UNRESOLVED[unresolved]
        if mapped in states:
            review_state = mapped
            break
    else:
        if "CUSTOMER_ROUTE_EVIDENCE_NOT_MATCHED" in states:
            review_state = "CUSTOMER_ROUTE_EVIDENCE_NOT_MATCHED"
    return {
        "review_id": review_id, "reviewed_at": reviewed_text, "recipient_role_id": recipient,
        "evidence_state": review_state,
        "policy_receipt": {
            "policy_id": policy["policy_id"], "policy_version": policy["policy_version"],
            "cutoff_at": policy["cutoff_at"], "timezone": policy["timezone"], "currency": policy["currency"],
            "operations_approval_receipt_id": policy["operations_approval_receipt_id"],
            "security_review_receipt_id": policy["security_review_receipt_id"],
            "privacy_review_receipt_id": policy["privacy_review_receipt_id"],
            "legal_review_receipt_id": policy["legal_review_receipt_id"],
            "lawful_basis_receipt_id": policy["lawful_basis_receipt_id"], "notice_receipt_id": policy["notice_receipt_id"],
            "objection_path_receipt_id": policy["objection_path_receipt_id"],
            "suppression_policy_receipt_id": policy["suppression_policy_receipt_id"],
            "correction_path_receipt_id": policy["correction_path_receipt_id"],
            "recipient_policy_receipt_id": policy["recipient_policy_receipt_id"],
            "retention_policy_receipt_id": policy["retention_policy_receipt_id"],
            "route_policy_receipt_id": policy["route_policy_receipt_id"],
        },
        "route_reviews": route_results,
        "aggregate_planned_charge_receipt": {"currency": policy["currency"], "planned_charge": format(total, "f")},
        "interpretation_boundary": BOUNDARY,
        "action_authorization": {
            "enrichment_authorized": False, "spend_authorized": False, "provider_call_authorized": False,
            "crm_write_authorized": False, "outreach_authorized": False,
            "downstream_decision_authorized": False, "publication_authorized": False,
        },
    }


def render_review_output(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n\n"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: route_evidence.py INPUT.json")
    document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sys.stdout.write(render_review_output(review_route_evidence(document)))


if __name__ == "__main__":
    main()
