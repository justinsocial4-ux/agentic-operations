#!/usr/bin/env python3
"""Deterministic read-only QBR evidence-packet assembly."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_qbr_evidence_packet_assembly"
STATES = {"AVAILABLE", "EVIDENCE_MISSING", "EVIDENCE_CONFLICT", "SUPPRESSED", "UNAUTHORIZED"}
UNITS = {"CURRENCY", "COUNT", "DURATION", "PERCENT", "RATIO"}
AGGREGATIONS = {"AS_PROVIDED", "SUM"}
REQUIRED_PROHIBITIONS = {
    "account-ranking", "action-recommendation", "causal-narrative", "confidence-label",
    "customer-contact", "customer-diagnosis", "delivery", "direct-identifier",
    "expansion-inference", "health-inference", "live-system-read", "publication",
    "readiness-label", "renewal-inference", "risk-label", "root-cause-inference",
    "sentiment-inference", "system-write", "worker-action",
}
FORBIDDEN_KEY_PARTS = (
    "account_name", "company_name", "contact", "customer_name", "email", "feedback_text",
    "free_text", "message", "owner_name", "person", "phone", "recipient_address",
    "requester_name", "worker_name",
)
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$")


def _strict(value, fields, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    unknown = set(value) - set(fields)
    missing = set(fields) - set(value)
    if unknown or missing:
        raise ValueError(f"{label} fields mismatch: unknown={sorted(unknown)} missing={sorted(missing)}")
    return dict(value)


def _reject_forbidden(value, path="root"):
    if isinstance(value, dict):
        for key, item in value.items():
            folded = str(key).casefold()
            if any(part in folded for part in FORBIDDEN_KEY_PARTS):
                raise ValueError(f"prohibited field: {path}.{key}")
            _reject_forbidden(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_forbidden(item, f"{path}[{index}]")
    elif isinstance(value, str) and "@" in value:
        raise ValueError(f"email-like value prohibited: {path}")


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


def _identifier(value, label, prefix=None):
    value = _text(value, label)
    if not ID_RE.fullmatch(value):
        raise ValueError(f"{label} must be a lowercase hyphenated identifier")
    if prefix and not value.startswith(prefix):
        raise ValueError(f"{label} must begin {prefix}")
    return value


def _id_list(value, label, prefix=None, allow_empty=False):
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ValueError(f"{label} must be {'a list' if allow_empty else 'a non-empty list'}")
    items = [_identifier(item, label, prefix) for item in value]
    if len(items) != len(set(items)):
        raise ValueError(f"{label} must not contain duplicates")
    return sorted(items)


def _tokens(value, label):
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    items = [_text(item, label) for item in value]
    if any(not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", item) for item in items):
        raise ValueError(f"{label} must contain lowercase tokens")
    if len(items) != len(set(items)):
        raise ValueError(f"{label} must not contain duplicates")
    return sorted(items)


def _time(value, label):
    value = _text(value, label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include an offset")
    return parsed


def _timezone(value, label):
    value = _text(value, label)
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"{label} must be an IANA timezone") from exc
    return value


def _require_timezone_offset(parsed, timezone_name, label):
    expected = parsed.replace(tzinfo=None).replace(tzinfo=ZoneInfo(timezone_name)).utcoffset()
    if parsed.utcoffset() != expected:
        raise ValueError(f"{label} offset does not match reporting timezone")


def _decimal(value, label, count=False):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a Decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a Decimal string") from exc
    if not number.is_finite() or number.as_tuple().exponent < -6 or number.adjusted() > 18:
        raise ValueError(f"{label} exceeds supported precision")
    if count and (number < 0 or number != number.to_integral_value()):
        raise ValueError(f"{label} count must be a non-negative whole number")
    return number


def _decimal_text(value):
    rounded = value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    if rounded == 0:
        rounded = abs(rounded)
    return format(rounded, "f")


POLICY_FIELDS = {
    "policy_id", "policy_version", "approved_purpose", "effective_at", "expires_at", "cutoff_at",
    "reviewed_at", "audience_class_id", "confidentiality_class_id", "reviewer_role_id",
    "allowed_recipient_role_ids", "retention_rule_id", "authority_receipt_id", "privacy_receipt_id",
    "recipient_receipt_id", "retention_receipt_id", "publication_policy_receipt_id", "blueprint_id",
    "blueprint_version", "allowed_section_ids", "prohibited_uses",
}


def _validate_policy(raw):
    row = _strict(raw, POLICY_FIELDS, "policy")
    id_fields = POLICY_FIELDS - {
        "approved_purpose", "effective_at", "expires_at", "cutoff_at", "reviewed_at",
        "allowed_recipient_role_ids", "allowed_section_ids", "prohibited_uses",
    }
    for key in id_fields:
        row[key] = _identifier(row[key], f"policy.{key}")
    if row["approved_purpose"] != PURPOSE:
        raise ValueError("policy.approved_purpose mismatch")
    row["allowed_recipient_role_ids"] = _id_list(row["allowed_recipient_role_ids"], "policy.allowed_recipient_role_ids", "role-")
    row["allowed_section_ids"] = _id_list(row["allowed_section_ids"], "policy.allowed_section_ids", "section-")
    row["prohibited_uses"] = _tokens(row["prohibited_uses"], "policy.prohibited_uses")
    if not REQUIRED_PROHIBITIONS.issubset(row["prohibited_uses"]):
        raise ValueError("policy.prohibited_uses missing required boundaries")
    effective = _time(row["effective_at"], "policy.effective_at")
    expires = _time(row["expires_at"], "policy.expires_at")
    cutoff = _time(row["cutoff_at"], "policy.cutoff_at")
    reviewed = _time(row["reviewed_at"], "policy.reviewed_at")
    if not effective <= cutoff <= reviewed <= expires:
        raise ValueError("policy time order invalid")
    row["_cutoff"] = cutoff
    return row


BLUEPRINT_FIELDS = {"blueprint_id", "blueprint_version", "allowed_section_ids", "allowed_slot_ids", "approval_receipt_id"}


def _validate_blueprint(raw, policy):
    row = _strict(raw, BLUEPRINT_FIELDS, "blueprint")
    for key in BLUEPRINT_FIELDS - {"allowed_section_ids", "allowed_slot_ids"}:
        row[key] = _identifier(row[key], f"blueprint.{key}")
    row["allowed_section_ids"] = _id_list(row["allowed_section_ids"], "blueprint.allowed_section_ids", "section-")
    row["allowed_slot_ids"] = _id_list(row["allowed_slot_ids"], "blueprint.allowed_slot_ids", "slot-")
    if row["blueprint_id"] != policy["blueprint_id"] or row["blueprint_version"] != policy["blueprint_version"]:
        raise ValueError("blueprint identity mismatch")
    if row["allowed_section_ids"] != policy["allowed_section_ids"]:
        raise ValueError("blueprint section mismatch")
    return row


CONTRACT_FIELDS = {
    "contract_id", "metric_id", "section_id", "slot_id", "source_id", "source_version", "schema_id", "schema_version",
    "authorization_receipt_id", "authorization_effective_at", "authorization_expires_at", "query_receipt_id",
    "page_receipt_id", "population_receipt_id", "pseudonymization_receipt_id", "expected_record_ids",
    "reporting_timezone", "period_begin", "period_end", "freshness_observed_at", "unit", "currency",
    "amount_basis", "metric_definition_id", "aggregation_method", "aggregation_rule_receipt_id",
    "approval_receipt_id",
}


def _validate_contract(raw, cutoff, blueprint):
    row = _strict(raw, CONTRACT_FIELDS, "metric contract")
    non_id = {
        "authorization_effective_at", "authorization_expires_at", "expected_record_ids", "reporting_timezone",
        "period_begin", "period_end", "freshness_observed_at", "unit", "currency", "amount_basis",
        "aggregation_method",
    }
    for key in CONTRACT_FIELDS - non_id:
        row[key] = _identifier(row[key], f"contract.{key}")
    row["expected_record_ids"] = _id_list(row["expected_record_ids"], "contract.expected_record_ids", "record-")
    row["reporting_timezone"] = _timezone(row["reporting_timezone"], "contract.reporting_timezone")
    if row["unit"] not in UNITS or row["aggregation_method"] not in AGGREGATIONS:
        raise ValueError("metric contract unit or aggregation invalid")
    if row["section_id"] not in blueprint["allowed_section_ids"] or row["slot_id"] not in blueprint["allowed_slot_ids"]:
        raise ValueError("metric contract blueprint binding invalid")
    if row["unit"] == "CURRENCY":
        if not re.fullmatch(r"[A-Z]{3}", row["currency"]) or row["amount_basis"] == "not-applicable":
            raise ValueError("currency metric requires currency and amount basis")
        row["amount_basis"] = _identifier(row["amount_basis"], "contract.amount_basis")
    elif row["currency"] != "NONE" or row["amount_basis"] != "not-applicable":
        raise ValueError("non-currency metric rejects currency and amount basis")
    if row["aggregation_method"] == "AS_PROVIDED" and len(row["expected_record_ids"]) != 1:
        raise ValueError("AS_PROVIDED requires one record")
    auth_begin = _time(row["authorization_effective_at"], "contract.authorization_effective_at")
    auth_end = _time(row["authorization_expires_at"], "contract.authorization_expires_at")
    period_begin = _time(row["period_begin"], "contract.period_begin")
    period_end = _time(row["period_end"], "contract.period_end")
    freshness = _time(row["freshness_observed_at"], "contract.freshness_observed_at")
    _require_timezone_offset(period_begin, row["reporting_timezone"], "contract.period_begin")
    _require_timezone_offset(period_end, row["reporting_timezone"], "contract.period_end")
    if not auth_begin <= period_begin < period_end <= freshness <= cutoff <= auth_end:
        raise ValueError("metric contract time order invalid")
    row["_period_begin"] = period_begin
    row["_period_end"] = period_end
    return row


RECORD_FIELDS = {"record_id", "contract_id", "state", "value", "source_receipt_id"}


def _validate_record(raw):
    row = _strict(raw, RECORD_FIELDS, "metric record")
    row["record_id"] = _identifier(row["record_id"], "record.record_id", "record-")
    row["contract_id"] = _identifier(row["contract_id"], "record.contract_id", "contract-")
    row["source_receipt_id"] = _identifier(row["source_receipt_id"], "record.source_receipt_id", "receipt-")
    if row["state"] not in STATES:
        raise ValueError("record.state invalid")
    if row["state"] == "AVAILABLE" and row["value"] is None:
        raise ValueError("available record requires value")
    if row["state"] != "AVAILABLE" and row["value"] is not None:
        raise ValueError("unavailable record value must be null")
    return row


COMPARISON_FIELDS = {"comparison_id", "current_contract_id", "prior_contract_id", "comparison_basis_receipt_id", "approval_receipt_id"}
CLAIM_FIELDS = {"claim_id", "template_id", "evidence_contract_ids", "evidence_comparison_ids", "approval_receipt_id"}
SECTION_FIELDS = {"section_id", "metric_contract_ids", "comparison_ids", "claim_ids", "blueprint_slot_receipt_id"}


def _combined_state(states):
    unique = set(states)
    if unique == {"AVAILABLE"}:
        return "AVAILABLE"
    unresolved = unique - {"AVAILABLE"}
    if len(unresolved) == 1:
        return next(iter(unresolved))
    return "EVIDENCE_CONFLICT"


def _metric_receipt(contract, rows):
    state = _combined_state([row["state"] for row in rows])
    value = None
    if state == "AVAILABLE":
        numbers = [_decimal(row["value"], "record.value", contract["unit"] == "COUNT") for row in rows]
        value = numbers[0] if contract["aggregation_method"] == "AS_PROVIDED" else sum(numbers, Decimal("0"))
    return {
        "contract_id": contract["contract_id"], "metric_id": contract["metric_id"], "section_id": contract["section_id"], "slot_id": contract["slot_id"],
        "state": state, "value": None if value is None else _decimal_text(value), "unit": contract["unit"],
        "currency": contract["currency"], "amount_basis": contract["amount_basis"],
        "metric_definition_id": contract["metric_definition_id"], "aggregation_method": contract["aggregation_method"],
        "aggregation_rule_receipt_id": contract["aggregation_rule_receipt_id"], "source_id": contract["source_id"],
        "source_version": contract["source_version"], "schema_id": contract["schema_id"],
        "schema_version": contract["schema_version"], "query_receipt_id": contract["query_receipt_id"],
        "page_receipt_id": contract["page_receipt_id"], "population_receipt_id": contract["population_receipt_id"],
        "pseudonymization_receipt_id": contract["pseudonymization_receipt_id"],
        "authorization_receipt_id": contract["authorization_receipt_id"], "approval_receipt_id": contract["approval_receipt_id"],
        "record_receipts": [{"record_id": row["record_id"], "source_receipt_id": row["source_receipt_id"], "state": row["state"]} for row in rows],
    }


def assemble_qbr_packet(document):
    _reject_forbidden(document)
    doc = _strict(document, {"policy", "blueprint", "metric_contracts", "records", "comparisons", "claims", "sections"}, "document")
    policy = _validate_policy(doc["policy"])
    blueprint = _validate_blueprint(doc["blueprint"], policy)
    if not isinstance(doc["metric_contracts"], list) or not doc["metric_contracts"]:
        raise ValueError("metric_contracts must be non-empty")
    contracts = [_validate_contract(row, policy["_cutoff"], blueprint) for row in doc["metric_contracts"]]
    contract_map = {row["contract_id"]: row for row in contracts}
    if len(contract_map) != len(contracts):
        raise ValueError("duplicate metric contract")
    records = [_validate_record(row) for row in doc["records"]] if isinstance(doc["records"], list) else []
    if len({row["record_id"] for row in records}) != len(records):
        raise ValueError("duplicate record")
    if len({row["source_receipt_id"] for row in records}) != len(records):
        raise ValueError("record source receipts must be unique")
    expected = {(contract["contract_id"], record_id) for contract in contracts for record_id in contract["expected_record_ids"]}
    actual = {(row["contract_id"], row["record_id"]) for row in records}
    if expected != actual:
        raise ValueError("record population mismatch")
    grouped = {contract_id: [] for contract_id in contract_map}
    for row in records:
        if row["contract_id"] not in contract_map:
            raise ValueError("record references unknown contract")
        grouped[row["contract_id"]].append(row)
    metric_receipts = [_metric_receipt(contract, sorted(grouped[contract["contract_id"]], key=lambda row: row["record_id"])) for contract in sorted(contracts, key=lambda row: row["contract_id"])]
    metric_map = {row["contract_id"]: row for row in metric_receipts}

    comparisons = []
    comparison_ids = set()
    if not isinstance(doc["comparisons"], list):
        raise ValueError("comparisons must be a list")
    for raw in doc["comparisons"]:
        row = _strict(raw, COMPARISON_FIELDS, "comparison")
        for key in COMPARISON_FIELDS:
            row[key] = _identifier(row[key], f"comparison.{key}")
        if row["comparison_id"] in comparison_ids:
            raise ValueError("duplicate comparison")
        comparison_ids.add(row["comparison_id"])
        if row["current_contract_id"] == row["prior_contract_id"] or row["current_contract_id"] not in contract_map or row["prior_contract_id"] not in contract_map:
            raise ValueError("comparison contract reference invalid")
        current = contract_map[row["current_contract_id"]]
        prior = contract_map[row["prior_contract_id"]]
        basis = ("unit", "currency", "amount_basis", "metric_definition_id", "aggregation_method", "aggregation_rule_receipt_id", "reporting_timezone")
        if any(current[key] != prior[key] for key in basis) or prior["_period_end"] > current["_period_begin"]:
            raise ValueError("comparison basis mismatch")
        current_receipt = metric_map[current["contract_id"]]
        prior_receipt = metric_map[prior["contract_id"]]
        state = _combined_state([current_receipt["state"], prior_receipt["state"]])
        delta = percent = None
        if state == "AVAILABLE":
            current_value = Decimal(current_receipt["value"])
            prior_value = Decimal(prior_receipt["value"])
            delta = _decimal_text(current_value - prior_value)
            percent = None if prior_value == 0 else _decimal_text((current_value - prior_value) / abs(prior_value) * Decimal("100"))
        comparisons.append({
            "comparison_id": row["comparison_id"], "current_contract_id": current["contract_id"],
            "prior_contract_id": prior["contract_id"], "state": state, "delta": delta,
            "percent_change": percent, "comparison_basis_receipt_id": row["comparison_basis_receipt_id"],
            "approval_receipt_id": row["approval_receipt_id"],
        })
    comparisons.sort(key=lambda row: row["comparison_id"])
    comparison_map = {row["comparison_id"]: row for row in comparisons}

    claims = []
    claim_ids = set()
    if not isinstance(doc["claims"], list):
        raise ValueError("claims must be a list")
    for raw in doc["claims"]:
        row = _strict(raw, CLAIM_FIELDS, "claim")
        for key in {"claim_id", "template_id", "approval_receipt_id"}:
            row[key] = _identifier(row[key], f"claim.{key}")
        row["evidence_contract_ids"] = _id_list(row["evidence_contract_ids"], "claim.evidence_contract_ids", "contract-", allow_empty=True)
        row["evidence_comparison_ids"] = _id_list(row["evidence_comparison_ids"], "claim.evidence_comparison_ids", "comparison-", allow_empty=True)
        if not row["evidence_contract_ids"] and not row["evidence_comparison_ids"]:
            raise ValueError("claim requires evidence")
        if row["claim_id"] in claim_ids or not set(row["evidence_contract_ids"]).issubset(contract_map) or not set(row["evidence_comparison_ids"]).issubset(comparison_map):
            raise ValueError("claim identity or evidence invalid")
        claim_ids.add(row["claim_id"])
        states = [metric_map[item]["state"] for item in row["evidence_contract_ids"]] + [comparison_map[item]["state"] for item in row["evidence_comparison_ids"]]
        claims.append({**row, "state": _combined_state(states)})
    claims.sort(key=lambda row: row["claim_id"])
    claim_map = {row["claim_id"]: row for row in claims}

    if not isinstance(doc["sections"], list) or not doc["sections"]:
        raise ValueError("sections must be non-empty")
    sections = []
    for raw in doc["sections"]:
        row = _strict(raw, SECTION_FIELDS, "section")
        row["section_id"] = _identifier(row["section_id"], "section.section_id", "section-")
        row["blueprint_slot_receipt_id"] = _identifier(row["blueprint_slot_receipt_id"], "section.blueprint_slot_receipt_id", "receipt-")
        row["metric_contract_ids"] = _id_list(row["metric_contract_ids"], "section.metric_contract_ids", "contract-", allow_empty=True)
        row["comparison_ids"] = _id_list(row["comparison_ids"], "section.comparison_ids", "comparison-", allow_empty=True)
        row["claim_ids"] = _id_list(row["claim_ids"], "section.claim_ids", "claim-", allow_empty=True)
        if not row["metric_contract_ids"] and not row["comparison_ids"] and not row["claim_ids"]:
            raise ValueError("section must not be empty")
        if not set(row["metric_contract_ids"]).issubset(contract_map) or not set(row["comparison_ids"]).issubset(comparison_map) or not set(row["claim_ids"]).issubset(claim_map):
            raise ValueError("section evidence reference invalid")
        if any(contract_map[item]["section_id"] != row["section_id"] for item in row["metric_contract_ids"]):
            raise ValueError("metric contract assigned outside approved section")
        for comparison_id in row["comparison_ids"]:
            comparison = comparison_map[comparison_id]
            if comparison["current_contract_id"] not in row["metric_contract_ids"] or comparison["prior_contract_id"] not in row["metric_contract_ids"]:
                raise ValueError("comparison contracts must share its section")
        for claim_id in row["claim_ids"]:
            claim = claim_map[claim_id]
            if not set(claim["evidence_contract_ids"]).issubset(row["metric_contract_ids"]) or not set(claim["evidence_comparison_ids"]).issubset(row["comparison_ids"]):
                raise ValueError("claim evidence must be assigned to its section")
        sections.append(row)
    if len({row["section_id"] for row in sections}) != len(sections) or sorted(row["section_id"] for row in sections) != blueprint["allowed_section_ids"]:
        raise ValueError("section population mismatch")
    for key, universe in (("metric_contract_ids", set(contract_map)), ("comparison_ids", set(comparison_map)), ("claim_ids", set(claim_map))):
        assigned = [item for row in sections for item in row[key]]
        if len(assigned) != len(set(assigned)) or set(assigned) != universe:
            raise ValueError(f"{key} assignment mismatch")
    sections.sort(key=lambda row: row["section_id"])

    unresolved = [{"contract_id": row["contract_id"], "state": row["state"]} for row in metric_receipts if row["state"] != "AVAILABLE"]
    return {
        "review_state": "HUMAN_REVIEW_REQUIRED",
        "policy_receipt": {
            "policy_id": policy["policy_id"], "policy_version": policy["policy_version"],
            "approved_purpose": policy["approved_purpose"], "audience_class_id": policy["audience_class_id"],
            "confidentiality_class_id": policy["confidentiality_class_id"], "reviewer_role_id": policy["reviewer_role_id"],
            "allowed_recipient_role_ids": policy["allowed_recipient_role_ids"], "retention_rule_id": policy["retention_rule_id"],
            "authority_receipt_id": policy["authority_receipt_id"], "privacy_receipt_id": policy["privacy_receipt_id"],
            "recipient_receipt_id": policy["recipient_receipt_id"], "retention_receipt_id": policy["retention_receipt_id"],
            "publication_policy_receipt_id": policy["publication_policy_receipt_id"], "prohibited_uses": policy["prohibited_uses"],
        },
        "blueprint_receipt": blueprint,
        "metric_receipts": metric_receipts,
        "comparison_receipts": comparisons,
        "claim_ledger": claims,
        "section_blocks": sections,
        "unresolved_evidence": unresolved,
        "narrative_authorized": False,
        "action_authorized": False,
        "delivery_authorized": False,
        "publication_authorized": False,
    }


def render_qbr_output(result):
    return json.dumps(result, indent=2, ensure_ascii=True, separators=(",", ": ")) + "\n\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) > 1:
        raise SystemExit("usage: qbr_packet.py [input.json]")
    raw = Path(argv[0]).read_text(encoding="utf-8") if argv else sys.stdin.read()
    sys.stdout.write(render_qbr_output(assemble_qbr_packet(json.loads(raw))))


if __name__ == "__main__":
    main()
