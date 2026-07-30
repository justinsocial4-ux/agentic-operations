#!/usr/bin/env python3
"""Deterministic read-only board-packet evidence assembly."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_board_packet_evidence_assembly"
STATES = {"AVAILABLE", "EVIDENCE_MISSING", "EVIDENCE_CONFLICT", "SUPPRESSED", "UNAUTHORIZED"}
UNITS = {"CURRENCY", "COUNT", "DURATION", "PERCENT", "RATIO"}
AGGREGATIONS = {"AS_PROVIDED", "SUM"}
FINANCIAL_BASES = {"GAAP", "NON_GAAP", "OPERATING"}
REQUIRED_PROHIBITIONS = {
    "causal-narrative",
    "confidence-label",
    "crm-read",
    "crm-write",
    "deck-export",
    "direct-identifier",
    "distribution",
    "executive-recommendation",
    "forecast-invention",
    "fuzzy-mapping",
    "named-deal-analysis",
    "named-worker-analysis",
    "performance-label",
    "publication",
    "readiness-label",
    "risk-label",
    "system-read",
    "system-write",
}
FORBIDDEN_KEY_PARTS = (
    "account_name",
    "customer_name",
    "deal_name",
    "email",
    "employee",
    "free_text",
    "message",
    "opportunity_name",
    "owner_name",
    "person",
    "recipient_address",
    "rep_name",
    "requester_name",
    "worker_name",
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
    return format(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP), "f")


POLICY_FIELDS = {
    "policy_id", "policy_version", "approved_purpose", "effective_at", "expires_at", "cutoff_at",
    "reviewed_at", "audience_class_id", "confidentiality_class_id", "reviewer_role_id",
    "allowed_recipient_role_ids", "retention_rule_id", "authority_receipt_id", "privacy_receipt_id", "recipient_receipt_id",
    "retention_receipt_id", "blueprint_id", "blueprint_version", "blueprint_receipt_id",
    "allowed_slide_ids", "prohibited_uses",
}


def _validate_policy(raw):
    row = _strict(raw, POLICY_FIELDS, "policy")
    for key in POLICY_FIELDS - {"approved_purpose", "effective_at", "expires_at", "cutoff_at", "reviewed_at", "allowed_recipient_role_ids", "allowed_slide_ids", "prohibited_uses"}:
        row[key] = _identifier(row[key], f"policy.{key}")
    if row["approved_purpose"] != PURPOSE:
        raise ValueError("policy.approved_purpose mismatch")
    row["allowed_recipient_role_ids"] = _id_list(row["allowed_recipient_role_ids"], "policy.allowed_recipient_role_ids", "role-")
    row["allowed_slide_ids"] = _id_list(row["allowed_slide_ids"], "policy.allowed_slide_ids", "slide-")
    row["prohibited_uses"] = _tokens(row["prohibited_uses"], "policy.prohibited_uses")
    if not REQUIRED_PROHIBITIONS.issubset(row["prohibited_uses"]):
        raise ValueError("policy.prohibited_uses missing required boundaries")
    effective = _time(row["effective_at"], "policy.effective_at")
    expires = _time(row["expires_at"], "policy.expires_at")
    cutoff = _time(row["cutoff_at"], "policy.cutoff_at")
    reviewed = _time(row["reviewed_at"], "policy.reviewed_at")
    if not effective <= cutoff <= reviewed <= expires:
        raise ValueError("policy time order invalid")
    return row, cutoff


CONTRACT_FIELDS = {
    "contract_id", "metric_id", "display_label_id", "source_id", "source_version", "schema_id", "schema_version",
    "authorization_receipt_id", "authorization_effective_at", "authorization_expires_at",
    "query_receipt_id", "page_receipt_id", "population_receipt_id", "pseudonymization_receipt_id", "expected_record_ids",
    "reporting_timezone", "period_start", "period_end", "freshness_observed_at", "unit", "currency",
    "amount_basis", "metric_definition_id", "aggregation_method", "financial_basis",
    "non_gaap_label_id", "comparable_gaap_contract_id", "reconciliation_receipt_id",
    "period_consistency_receipt_id", "approval_receipt_id",
}


def _validate_contract(raw, cutoff):
    row = _strict(raw, CONTRACT_FIELDS, "metric contract")
    enum_keys = {"unit", "currency", "aggregation_method", "financial_basis"}
    time_keys = {"authorization_effective_at", "authorization_expires_at", "period_start", "period_end", "freshness_observed_at", "reporting_timezone"}
    list_keys = {"expected_record_ids"}
    for key in CONTRACT_FIELDS - enum_keys - time_keys - list_keys:
        prefix = "contract-" if key in {"contract_id", "comparable_gaap_contract_id"} and row[key] != "not-applicable" else None
        row[key] = _identifier(row[key], f"metric_contract.{key}", prefix)
    row["expected_record_ids"] = _id_list(row["expected_record_ids"], "metric_contract.expected_record_ids", "record-")
    if row["unit"] not in UNITS or row["aggregation_method"] not in AGGREGATIONS or row["financial_basis"] not in FINANCIAL_BASES:
        raise ValueError("metric contract enum invalid")
    if row["unit"] == "CURRENCY":
        if not re.fullmatch(r"[A-Z]{3}", row["currency"]):
            raise ValueError("currency metric requires ISO currency")
        if row["amount_basis"] == "not-applicable":
            raise ValueError("currency metric requires amount basis")
    elif row["currency"] != "NONE" or row["amount_basis"] != "not-applicable":
        raise ValueError("non-currency metric must use NONE and not-applicable")
    auth_start = _time(row["authorization_effective_at"], "metric_contract.authorization_effective_at")
    auth_end = _time(row["authorization_expires_at"], "metric_contract.authorization_expires_at")
    period_start = _time(row["period_start"], "metric_contract.period_start")
    period_end = _time(row["period_end"], "metric_contract.period_end")
    freshness = _time(row["freshness_observed_at"], "metric_contract.freshness_observed_at")
    row["reporting_timezone"] = _timezone(row["reporting_timezone"], "metric_contract.reporting_timezone")
    _require_timezone_offset(period_start, row["reporting_timezone"], "metric_contract.period_start")
    _require_timezone_offset(period_end, row["reporting_timezone"], "metric_contract.period_end")
    if not auth_start <= period_start < period_end <= freshness <= cutoff <= auth_end:
        raise ValueError("metric contract time order invalid")
    optional = ("non_gaap_label_id", "comparable_gaap_contract_id", "reconciliation_receipt_id", "period_consistency_receipt_id")
    if row["financial_basis"] == "NON_GAAP":
        if any(row[key] == "not-applicable" for key in optional):
            raise ValueError("non-GAAP contract missing required receipts")
    elif any(row[key] != "not-applicable" for key in optional):
        raise ValueError("non-GAAP fields must be not-applicable")
    if row["aggregation_method"] == "AS_PROVIDED" and len(row["expected_record_ids"]) != 1:
        raise ValueError("AS_PROVIDED requires exactly one record")
    row["_period_start"] = period_start
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
    if row["state"] == "AVAILABLE":
        if row["value"] is None:
            raise ValueError("available record requires value")
    elif row["value"] is not None:
        raise ValueError("unavailable record value must be null")
    return row


COMPARISON_FIELDS = {"comparison_id", "current_contract_id", "prior_contract_id", "comparison_basis_receipt_id", "approval_receipt_id"}


def _validate_comparison(raw):
    row = _strict(raw, COMPARISON_FIELDS, "comparison")
    row["comparison_id"] = _identifier(row["comparison_id"], "comparison.comparison_id", "comparison-")
    row["current_contract_id"] = _identifier(row["current_contract_id"], "comparison.current_contract_id", "contract-")
    row["prior_contract_id"] = _identifier(row["prior_contract_id"], "comparison.prior_contract_id", "contract-")
    row["comparison_basis_receipt_id"] = _identifier(row["comparison_basis_receipt_id"], "comparison.comparison_basis_receipt_id", "receipt-")
    row["approval_receipt_id"] = _identifier(row["approval_receipt_id"], "comparison.approval_receipt_id", "receipt-")
    if row["current_contract_id"] == row["prior_contract_id"]:
        raise ValueError("comparison contracts must differ")
    return row


CLAIM_FIELDS = {"claim_id", "template_id", "evidence_metric_contract_ids", "evidence_comparison_ids", "approval_receipt_id"}


def _validate_claim(raw):
    row = _strict(raw, CLAIM_FIELDS, "claim")
    row["claim_id"] = _identifier(row["claim_id"], "claim.claim_id", "claim-")
    row["template_id"] = _identifier(row["template_id"], "claim.template_id", "template-")
    row["evidence_metric_contract_ids"] = _id_list(row["evidence_metric_contract_ids"], "claim.evidence_metric_contract_ids", "contract-", True)
    row["evidence_comparison_ids"] = _id_list(row["evidence_comparison_ids"], "claim.evidence_comparison_ids", "comparison-", True)
    row["approval_receipt_id"] = _identifier(row["approval_receipt_id"], "claim.approval_receipt_id", "receipt-")
    if not row["evidence_metric_contract_ids"] and not row["evidence_comparison_ids"]:
        raise ValueError("claim requires evidence")
    return row


SLIDE_FIELDS = {"slide_id", "metric_contract_ids", "comparison_ids", "claim_ids", "blueprint_slot_receipt_id"}


def _validate_slide(raw):
    row = _strict(raw, SLIDE_FIELDS, "slide")
    row["slide_id"] = _identifier(row["slide_id"], "slide.slide_id", "slide-")
    row["metric_contract_ids"] = _id_list(row["metric_contract_ids"], "slide.metric_contract_ids", "contract-", True)
    row["comparison_ids"] = _id_list(row["comparison_ids"], "slide.comparison_ids", "comparison-", True)
    row["claim_ids"] = _id_list(row["claim_ids"], "slide.claim_ids", "claim-", True)
    row["blueprint_slot_receipt_id"] = _identifier(row["blueprint_slot_receipt_id"], "slide.blueprint_slot_receipt_id", "receipt-")
    if not row["metric_contract_ids"] and not row["comparison_ids"] and not row["claim_ids"]:
        raise ValueError("slide must contain at least one slot")
    return row


def _unique(rows, key, label):
    values = [row[key] for row in rows]
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label}")


def _clean_contract(row):
    return {key: value for key, value in row.items() if not key.startswith("_")}


def assemble_board_packet(document):
    fields = {"policy", "metric_contracts", "records", "comparisons", "claims", "slides"}
    document = _strict(document, fields, "document")
    _reject_forbidden(document)
    policy, cutoff = _validate_policy(document["policy"])
    if not all(isinstance(document[key], list) and document[key] for key in ("metric_contracts", "records", "slides")):
        raise ValueError("metric_contracts, records, and slides must be non-empty lists")
    if not isinstance(document["comparisons"], list) or not isinstance(document["claims"], list):
        raise ValueError("comparisons and claims must be lists")

    contracts = [_validate_contract(row, cutoff) for row in document["metric_contracts"]]
    records = [_validate_record(row) for row in document["records"]]
    comparisons = [_validate_comparison(row) for row in document["comparisons"]]
    claims = [_validate_claim(row) for row in document["claims"]]
    slides = [_validate_slide(row) for row in document["slides"]]
    for rows, key, label in ((contracts, "contract_id", "contract"), (contracts, "metric_id", "metric"), (records, "record_id", "record"), (comparisons, "comparison_id", "comparison"), (claims, "claim_id", "claim"), (slides, "slide_id", "slide")):
        _unique(rows, key, label)

    contract_map = {row["contract_id"]: row for row in contracts}
    record_map = {row["record_id"]: row for row in records}
    if set(policy["allowed_slide_ids"]) != {row["slide_id"] for row in slides}:
        raise ValueError("slides do not match policy blueprint")

    metric_receipts = []
    totals = {}
    unresolved = []
    for contract in sorted(contracts, key=lambda row: row["contract_id"]):
        expected = set(contract["expected_record_ids"])
        actual = {row["record_id"] for row in records if row["contract_id"] == contract["contract_id"]}
        if expected != actual:
            raise ValueError(f"record population mismatch for {contract['contract_id']}")
        rows = [record_map[record_id] for record_id in sorted(expected)]
        receipt_base = {
            "metric_receipt_id": f"metric-receipt-{contract['contract_id'].removeprefix('contract-')}",
            "contract_id": contract["contract_id"],
            "metric_id": contract["metric_id"],
            "display_label_id": contract["display_label_id"],
            "source_id": contract["source_id"],
            "source_version": contract["source_version"],
            "schema_id": contract["schema_id"],
            "schema_version": contract["schema_version"],
            "authorization_receipt_id": contract["authorization_receipt_id"],
            "query_receipt_id": contract["query_receipt_id"],
            "page_receipt_id": contract["page_receipt_id"],
            "population_receipt_id": contract["population_receipt_id"],
            "pseudonymization_receipt_id": contract["pseudonymization_receipt_id"],
            "source_record_receipt_ids": sorted(row["source_receipt_id"] for row in rows),
            "metric_definition_id": contract["metric_definition_id"],
            "reporting_timezone": contract["reporting_timezone"],
            "period_start": contract["period_start"],
            "period_end": contract["period_end"],
            "amount_basis": contract["amount_basis"],
            "aggregation_method": contract["aggregation_method"],
            "financial_basis": contract["financial_basis"],
            "approval_receipt_id": contract["approval_receipt_id"],
            "non_gaap_label_id": contract["non_gaap_label_id"],
            "comparable_gaap_contract_id": contract["comparable_gaap_contract_id"],
            "reconciliation_receipt_id": contract["reconciliation_receipt_id"],
            "period_consistency_receipt_id": contract["period_consistency_receipt_id"],
        }
        states = sorted({row["state"] for row in rows})
        if states != ["AVAILABLE"]:
            state = states[0] if len(states) == 1 else "EVIDENCE_CONFLICT"
            metric_receipts.append({**receipt_base, "state": state, "value": None, "unit": contract["unit"], "currency": contract["currency"]})
            unresolved.append({"contract_id": contract["contract_id"], "record_states": [{"record_id": row["record_id"], "state": row["state"]} for row in rows if row["state"] != "AVAILABLE"]})
            continue
        numbers = [_decimal(row["value"], f"record {row['record_id']} value", contract["unit"] == "COUNT") for row in rows]
        value = numbers[0] if contract["aggregation_method"] == "AS_PROVIDED" else sum(numbers, Decimal("0"))
        totals[contract["contract_id"]] = value
        metric_receipts.append({**receipt_base, "state": "AVAILABLE", "value": _decimal_text(value), "unit": contract["unit"], "currency": contract["currency"]})

    for contract in contracts:
        if contract["financial_basis"] == "NON_GAAP":
            comparable = contract_map.get(contract["comparable_gaap_contract_id"])
            if comparable is None or comparable["financial_basis"] != "GAAP":
                raise ValueError("non-GAAP comparable contract must exist and be GAAP")
            same = ("unit", "currency", "amount_basis", "period_start", "period_end", "reporting_timezone")
            if any(contract[key] != comparable[key] for key in same):
                raise ValueError("non-GAAP comparable contract basis mismatch")

    comparison_receipts = []
    comparison_ids = set()
    comparison_map = {row["comparison_id"]: row for row in comparisons}
    for comparison in sorted(comparisons, key=lambda row: row["comparison_id"]):
        current = contract_map.get(comparison["current_contract_id"])
        prior = contract_map.get(comparison["prior_contract_id"])
        if current is None or prior is None:
            raise ValueError("comparison references unknown contract")
        same = ("unit", "currency", "amount_basis", "metric_definition_id", "aggregation_method", "reporting_timezone", "financial_basis", "non_gaap_label_id")
        if any(current[key] != prior[key] for key in same):
            raise ValueError("comparison basis mismatch")
        if prior["_period_end"] > current["_period_start"]:
            raise ValueError("comparison periods overlap or reverse")
        comparison_ids.add(comparison["comparison_id"])
        if current["contract_id"] not in totals or prior["contract_id"] not in totals:
            comparison_receipts.append({"comparison_receipt_id": f"comparison-receipt-{comparison['comparison_id'].removeprefix('comparison-')}", "comparison_id": comparison["comparison_id"], "comparison_basis_receipt_id": comparison["comparison_basis_receipt_id"], "approval_receipt_id": comparison["approval_receipt_id"], "current_metric_receipt_id": f"metric-receipt-{current['contract_id'].removeprefix('contract-')}", "prior_metric_receipt_id": f"metric-receipt-{prior['contract_id'].removeprefix('contract-')}", "state": "EVIDENCE_MISSING", "delta": None, "percent_change": None, "unit": current["unit"], "currency": current["currency"]})
            continue
        delta = totals[current["contract_id"]] - totals[prior["contract_id"]]
        percent = None if totals[prior["contract_id"]] == 0 else _decimal_text((delta / totals[prior["contract_id"]]) * Decimal("100"))
        comparison_receipts.append({"comparison_receipt_id": f"comparison-receipt-{comparison['comparison_id'].removeprefix('comparison-')}", "comparison_id": comparison["comparison_id"], "comparison_basis_receipt_id": comparison["comparison_basis_receipt_id"], "approval_receipt_id": comparison["approval_receipt_id"], "current_metric_receipt_id": f"metric-receipt-{current['contract_id'].removeprefix('contract-')}", "prior_metric_receipt_id": f"metric-receipt-{prior['contract_id'].removeprefix('contract-')}", "state": "AVAILABLE", "delta": _decimal_text(delta), "percent_change": percent, "unit": current["unit"], "currency": current["currency"]})

    claim_ids = {row["claim_id"] for row in claims}
    metric_state = {row["contract_id"]: row["state"] for row in metric_receipts}
    comparison_state = {row["comparison_id"]: row["state"] for row in comparison_receipts}
    for claim in claims:
        if not set(claim["evidence_metric_contract_ids"]).issubset(contract_map) or not set(claim["evidence_comparison_ids"]).issubset(comparison_ids):
            raise ValueError("claim references unknown evidence")

    slide_blocks = []
    assigned_metrics = set()
    assigned_comparisons = set()
    assigned_claims = set()
    for slide in sorted(slides, key=lambda row: row["slide_id"]):
        if not set(slide["metric_contract_ids"]).issubset(contract_map) or not set(slide["comparison_ids"]).issubset(comparison_ids) or not set(slide["claim_ids"]).issubset(claim_ids):
            raise ValueError("slide references unknown slot")
        for claim_id in slide["claim_ids"]:
            claim = next(item for item in claims if item["claim_id"] == claim_id)
            if not set(claim["evidence_metric_contract_ids"]).issubset(slide["metric_contract_ids"]) or not set(claim["evidence_comparison_ids"]).issubset(slide["comparison_ids"]):
                raise ValueError("claim evidence must be present on its slide")
        assigned_metrics.update(slide["metric_contract_ids"])
        assigned_comparisons.update(slide["comparison_ids"])
        assigned_claims.update(slide["claim_ids"])
        slide_blocks.append({
            "slide_id": slide["slide_id"],
            "metric_receipt_ids": [f"metric-receipt-{item.removeprefix('contract-')}" for item in slide["metric_contract_ids"]],
            "comparison_receipt_ids": [f"comparison-receipt-{item.removeprefix('comparison-')}" for item in slide["comparison_ids"]],
            "claim_ids": slide["claim_ids"],
            "blueprint_slot_receipt_id": slide["blueprint_slot_receipt_id"],
        })
    if assigned_metrics != set(contract_map) or assigned_comparisons != comparison_ids or assigned_claims != claim_ids:
        raise ValueError("all evidence must be assigned by the approved slide blueprint")

    return {
        "review_state": "HUMAN_REVIEW_REQUIRED",
        "policy_receipt": {
            "policy_id": policy["policy_id"], "policy_version": policy["policy_version"],
            "audience_class_id": policy["audience_class_id"], "confidentiality_class_id": policy["confidentiality_class_id"],
            "blueprint_id": policy["blueprint_id"], "blueprint_version": policy["blueprint_version"],
            "reviewer_role_id": policy["reviewer_role_id"], "allowed_recipient_role_ids": policy["allowed_recipient_role_ids"],
            "retention_rule_id": policy["retention_rule_id"], "authority_receipt_id": policy["authority_receipt_id"],
            "privacy_receipt_id": policy["privacy_receipt_id"], "recipient_receipt_id": policy["recipient_receipt_id"],
            "retention_receipt_id": policy["retention_receipt_id"], "blueprint_receipt_id": policy["blueprint_receipt_id"],
        },
        "metric_receipts": metric_receipts,
        "comparison_receipts": comparison_receipts,
        "claim_ledger": [{"claim_id": row["claim_id"], "template_id": row["template_id"], "evidence_metric_contract_ids": row["evidence_metric_contract_ids"], "evidence_comparison_ids": row["evidence_comparison_ids"], "approval_receipt_id": row["approval_receipt_id"], "state": "AVAILABLE" if all(metric_state[item] == "AVAILABLE" for item in row["evidence_metric_contract_ids"]) and all(comparison_state[item] == "AVAILABLE" for item in row["evidence_comparison_ids"]) else "EVIDENCE_MISSING"} for row in sorted(claims, key=lambda item: item["claim_id"])],
        "slide_blocks": slide_blocks,
        "unresolved_evidence": unresolved,
        "narrative_authorized": False,
        "action_authorized": False,
        "publication_authorized": False,
    }


def render_packet_output(result):
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n\n"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: board_packet.py INPUT.json")
    document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sys.stdout.write(render_packet_output(assemble_board_packet(document)))


if __name__ == "__main__":
    main()
