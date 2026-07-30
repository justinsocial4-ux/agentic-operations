#!/usr/bin/env python3
"""Deterministic read-only attribution-credit allocation evidence review."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_attribution_credit_allocation_evidence_review"
STATES = {"AVAILABLE", "EVIDENCE_MISSING", "EVIDENCE_CONFLICT", "SUPPRESSED", "UNAUTHORIZED"}
REMAINDER_RULE = "lexicographic-first-touchpoint"
REQUIRED_PROHIBITIONS = {
    "budget-action", "causal-claim", "confidence-label", "direct-identifier", "downstream-decision",
    "engagement-inference", "export", "forecast-use", "gtm-action", "identity-inference",
    "incrementality-claim", "message-send", "model-choice", "model-tuning", "partial-data",
    "performance-label", "profiling", "ranking", "roi-claim", "system-read", "system-write",
}
FORBIDDEN_KEY_PARTS = (
    "account_id", "account_name", "campaign_name", "contact_id", "contact_name", "deal_id",
    "email", "free_text", "lead_id", "message", "opportunity_name", "person", "phone", "url", "utm",
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
    elif isinstance(value, str) and ("@" in value or "://" in value):
        raise ValueError(f"direct or URL-like value prohibited: {path}")


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
    if not isinstance(value, list) or (not value and not allow_empty) or len(value) > 1000:
        raise ValueError(f"{label} must be a bounded {'list' if allow_empty else 'non-empty list'}")
    items = [_identifier(item, label, prefix) for item in value]
    if len(items) != len(set(items)):
        raise ValueError(f"{label} must not contain duplicates")
    return sorted(items)


def _tokens(value, label):
    if not isinstance(value, list) or not value or len(value) > 100:
        raise ValueError(f"{label} must be a bounded non-empty list")
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


def _decimal(value, label, allow_zero=True):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a Decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a Decimal string") from exc
    if not number.is_finite() or number < 0 or number.as_tuple().exponent < -6 or number.adjusted() > 18:
        raise ValueError(f"{label} exceeds supported non-negative precision")
    if not allow_zero and number == 0:
        raise ValueError(f"{label} must be greater than zero")
    return Decimal("0") if number == 0 else number


def _decimal_text(value):
    return format(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP), "f")


def _unique(rows, key, label):
    values = [row[key] for row in rows]
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label}")


POLICY_FIELDS = {
    "policy_id", "policy_version", "approved_purpose", "effective_at", "expires_at", "cutoff_at",
    "reviewed_at", "reviewer_role_id", "privacy_receipt_id", "lawful_basis_receipt_id",
    "recipient_policy_receipt_id", "retention_policy_receipt_id", "retention_rule_id",
    "allowed_recipient_role_ids", "prohibited_uses",
}


def _validate_policy(raw):
    row = _strict(raw, POLICY_FIELDS, "policy")
    special = {"approved_purpose", "effective_at", "expires_at", "cutoff_at", "reviewed_at", "allowed_recipient_role_ids", "prohibited_uses"}
    for key in POLICY_FIELDS - special:
        row[key] = _identifier(row[key], f"policy.{key}")
    if row["approved_purpose"] != PURPOSE:
        raise ValueError("policy.approved_purpose mismatch")
    row["allowed_recipient_role_ids"] = _id_list(row["allowed_recipient_role_ids"], "policy.allowed_recipient_role_ids", "role-")
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
    "contract_id", "model_id", "model_version", "model_definition_receipt_id", "model_approval_receipt_id",
    "remainder_rule", "remainder_rule_receipt_id", "source_id", "source_version", "schema_id", "schema_version",
    "authorization_receipt_id", "authorization_effective_at", "authorization_expires_at", "query_receipt_id",
    "page_receipt_id", "opportunity_population_receipt_id", "expected_opportunity_ids", "freshness_observed_at",
    "reporting_timezone", "reporting_period_start", "reporting_period_end", "touchpoint_window_start",
    "touchpoint_window_end", "currency", "amount_basis", "measure_definition_id", "finance_approval_receipt_id",
    "pseudonymization_receipt_id", "identity_linkage_policy_receipt_id", "event_definition_policy_receipt_id",
    "eligibility_policy_receipt_id", "deduplication_policy_receipt_id", "ordering_policy_receipt_id",
    "exclusion_policy_receipt_id", "bucket_policy_receipt_id", "allowed_bucket_ids",
}


def _validate_contract(raw, cutoff):
    row = _strict(raw, CONTRACT_FIELDS, "allocation contract")
    special = {
        "remainder_rule", "authorization_effective_at", "authorization_expires_at", "expected_opportunity_ids",
        "freshness_observed_at", "reporting_timezone", "reporting_period_start", "reporting_period_end",
        "touchpoint_window_start", "touchpoint_window_end", "currency", "allowed_bucket_ids",
    }
    for key in CONTRACT_FIELDS - special:
        prefix = "contract-" if key == "contract_id" else None
        row[key] = _identifier(row[key], f"allocation_contract.{key}", prefix)
    if row["remainder_rule"] != REMAINDER_RULE:
        raise ValueError("allocation_contract.remainder_rule mismatch")
    if not re.fullmatch(r"[A-Z]{3}", row["currency"]):
        raise ValueError("allocation_contract.currency must be ISO currency")
    row["expected_opportunity_ids"] = _id_list(row["expected_opportunity_ids"], "allocation_contract.expected_opportunity_ids", "anonymous-opportunity-")
    row["allowed_bucket_ids"] = _id_list(row["allowed_bucket_ids"], "allocation_contract.allowed_bucket_ids", "anonymous-bucket-")
    row["reporting_timezone"] = _timezone(row["reporting_timezone"], "allocation_contract.reporting_timezone")
    auth_start = _time(row["authorization_effective_at"], "allocation_contract.authorization_effective_at")
    auth_end = _time(row["authorization_expires_at"], "allocation_contract.authorization_expires_at")
    report_start = _time(row["reporting_period_start"], "allocation_contract.reporting_period_start")
    report_end = _time(row["reporting_period_end"], "allocation_contract.reporting_period_end")
    window_start = _time(row["touchpoint_window_start"], "allocation_contract.touchpoint_window_start")
    window_end = _time(row["touchpoint_window_end"], "allocation_contract.touchpoint_window_end")
    freshness = _time(row["freshness_observed_at"], "allocation_contract.freshness_observed_at")
    for parsed, label in ((report_start, "reporting_period_start"), (report_end, "reporting_period_end"), (window_start, "touchpoint_window_start"), (window_end, "touchpoint_window_end")):
        _require_timezone_offset(parsed, row["reporting_timezone"], f"allocation_contract.{label}")
    if not auth_start <= window_start < window_end <= freshness <= cutoff <= auth_end:
        raise ValueError("allocation contract authorization/window order invalid")
    if not auth_start <= report_start < report_end <= freshness:
        raise ValueError("allocation contract reporting period order invalid")
    row["_window_start"] = window_start
    row["_window_end"] = window_end
    return row


OPPORTUNITY_FIELDS = {
    "opportunity_id", "state", "approved_amount", "amount_source_receipt_id",
    "touchpoint_population_receipt_id", "expected_touchpoint_ids",
}


def _validate_opportunity(raw):
    row = _strict(raw, OPPORTUNITY_FIELDS, "opportunity")
    row["opportunity_id"] = _identifier(row["opportunity_id"], "opportunity.opportunity_id", "anonymous-opportunity-")
    row["amount_source_receipt_id"] = _identifier(row["amount_source_receipt_id"], "opportunity.amount_source_receipt_id", "receipt-")
    row["touchpoint_population_receipt_id"] = _identifier(row["touchpoint_population_receipt_id"], "opportunity.touchpoint_population_receipt_id", "receipt-")
    row["expected_touchpoint_ids"] = _id_list(row["expected_touchpoint_ids"], "opportunity.expected_touchpoint_ids", "anonymous-touchpoint-", True)
    if row["state"] not in STATES:
        raise ValueError("opportunity.state invalid")
    if row["state"] == "AVAILABLE":
        row["_amount"] = _decimal(row["approved_amount"], "opportunity.approved_amount")
    elif row["approved_amount"] is not None:
        raise ValueError("unavailable opportunity amount must be null")
    return row


TOUCHPOINT_FIELDS = {
    "touchpoint_id", "opportunity_id", "state", "bucket_id", "event_type_id", "event_at", "sequence_index",
    "source_receipt_id", "linkage_receipt_id", "eligibility_receipt_id", "bucket_mapping_receipt_id",
}


def _validate_touchpoint(raw, contract):
    row = _strict(raw, TOUCHPOINT_FIELDS, "touchpoint")
    row["touchpoint_id"] = _identifier(row["touchpoint_id"], "touchpoint.touchpoint_id", "anonymous-touchpoint-")
    row["opportunity_id"] = _identifier(row["opportunity_id"], "touchpoint.opportunity_id", "anonymous-opportunity-")
    for key in ("source_receipt_id", "linkage_receipt_id", "eligibility_receipt_id", "bucket_mapping_receipt_id"):
        row[key] = _identifier(row[key], f"touchpoint.{key}")
    if row["state"] not in STATES:
        raise ValueError("touchpoint.state invalid")
    if row["state"] == "AVAILABLE":
        row["bucket_id"] = _identifier(row["bucket_id"], "touchpoint.bucket_id", "anonymous-bucket-")
        row["event_type_id"] = _identifier(row["event_type_id"], "touchpoint.event_type_id")
        event_at = _time(row["event_at"], "touchpoint.event_at")
        _require_timezone_offset(event_at, contract["reporting_timezone"], "touchpoint.event_at")
        if not contract["_window_start"] <= event_at <= contract["_window_end"]:
            raise ValueError("touchpoint.event_at outside approved window")
        row["_event_at"] = event_at
        if isinstance(row["sequence_index"], bool) or not isinstance(row["sequence_index"], int) or row["sequence_index"] < 1 or row["sequence_index"] > 1000:
            raise ValueError("touchpoint.sequence_index invalid")
    elif any(row[key] is not None for key in ("bucket_id", "event_type_id", "event_at", "sequence_index")):
        raise ValueError("unavailable touchpoint evidence fields must be null")
    return row


WEIGHT_FIELDS = {"touchpoint_id", "state", "raw_weight", "weight_receipt_id"}


def _validate_weight(raw):
    row = _strict(raw, WEIGHT_FIELDS, "model weight")
    row["touchpoint_id"] = _identifier(row["touchpoint_id"], "weight.touchpoint_id", "anonymous-touchpoint-")
    row["weight_receipt_id"] = _identifier(row["weight_receipt_id"], "weight.weight_receipt_id", "receipt-")
    if row["state"] not in STATES:
        raise ValueError("weight.state invalid")
    if row["state"] == "AVAILABLE":
        row["_weight"] = _decimal(row["raw_weight"], "weight.raw_weight")
    elif row["raw_weight"] is not None:
        raise ValueError("unavailable raw_weight must be null")
    return row


def _derived_state(states):
    unresolved = sorted(set(state for state in states if state != "AVAILABLE"))
    if not unresolved:
        return "AVAILABLE"
    return unresolved[0] if len(unresolved) == 1 else "EVIDENCE_CONFLICT"


def review_attribution_credit(document):
    document = _strict(document, {"policy", "allocation_contract", "opportunities", "touchpoints", "weights"}, "document")
    _reject_forbidden(document)
    policy, cutoff = _validate_policy(document["policy"])
    contract = _validate_contract(document["allocation_contract"], cutoff)
    if not isinstance(document["opportunities"], list) or not document["opportunities"] or len(document["opportunities"]) > 1000:
        raise ValueError("opportunities must be a bounded non-empty list")
    if not isinstance(document["touchpoints"], list) or len(document["touchpoints"]) > 1000:
        raise ValueError("touchpoints must be a bounded list")
    if not isinstance(document["weights"], list) or len(document["weights"]) > 1000:
        raise ValueError("weights must be a bounded list")
    opportunities = [_validate_opportunity(row) for row in document["opportunities"]]
    touchpoints = [_validate_touchpoint(row, contract) for row in document["touchpoints"]]
    weights = [_validate_weight(row) for row in document["weights"]]
    _unique(opportunities, "opportunity_id", "opportunity")
    _unique(touchpoints, "touchpoint_id", "touchpoint")
    _unique(weights, "touchpoint_id", "weight")
    _unique(opportunities, "amount_source_receipt_id", "amount source receipt")
    _unique(opportunities, "touchpoint_population_receipt_id", "touchpoint population receipt")
    _unique(weights, "weight_receipt_id", "weight receipt")
    for receipt_key in ("source_receipt_id", "linkage_receipt_id", "eligibility_receipt_id", "bucket_mapping_receipt_id"):
        _unique(touchpoints, receipt_key, receipt_key.replace("_", " "))
    if {row["opportunity_id"] for row in opportunities} != set(contract["expected_opportunity_ids"]):
        raise ValueError("opportunity population mismatch")
    expected_touchpoints = set()
    for opportunity in opportunities:
        for touchpoint_id in opportunity["expected_touchpoint_ids"]:
            if touchpoint_id in expected_touchpoints:
                raise ValueError("touchpoint declared by multiple opportunities")
            expected_touchpoints.add(touchpoint_id)
    if expected_touchpoints != {row["touchpoint_id"] for row in touchpoints} or expected_touchpoints != {row["touchpoint_id"] for row in weights}:
        raise ValueError("touchpoint or weight population mismatch")
    opportunity_map = {row["opportunity_id"]: row for row in opportunities}
    touchpoint_map = {row["touchpoint_id"]: row for row in touchpoints}
    weight_map = {row["touchpoint_id"]: row for row in weights}
    for touchpoint in touchpoints:
        if touchpoint["opportunity_id"] not in opportunity_map:
            raise ValueError("touchpoint references unknown opportunity")
        if touchpoint["touchpoint_id"] not in opportunity_map[touchpoint["opportunity_id"]]["expected_touchpoint_ids"]:
            raise ValueError("touchpoint opportunity binding mismatch")
        if touchpoint["state"] == "AVAILABLE" and touchpoint["bucket_id"] not in contract["allowed_bucket_ids"]:
            raise ValueError("touchpoint bucket not allowed")

    bucket_totals = {bucket_id: Decimal("0") for bucket_id in contract["allowed_bucket_ids"]}
    opportunity_receipts = []
    unresolved_evidence = []
    any_allocation = False
    for opportunity in sorted(opportunities, key=lambda row: row["opportunity_id"]):
        ids = opportunity["expected_touchpoint_ids"]
        rows = [touchpoint_map[item] for item in ids]
        weight_rows = [weight_map[item] for item in ids]
        states = [opportunity["state"]] + [row["state"] for row in rows] + [row["state"] for row in weight_rows]
        state = _derived_state(states)
        if not ids and opportunity["state"] == "AVAILABLE":
            state = "EVIDENCE_MISSING"
        base_receipt = {
            "opportunity_id": opportunity["opportunity_id"],
            "amount_source_receipt_id": opportunity["amount_source_receipt_id"],
            "touchpoint_population_receipt_id": opportunity["touchpoint_population_receipt_id"],
            "touchpoint_ids": ids,
            "weight_receipt_ids": sorted(row["weight_receipt_id"] for row in weight_rows),
            "touchpoint_evidence_receipts": [
                {
                    "touchpoint_id": row["touchpoint_id"], "source_receipt_id": row["source_receipt_id"],
                    "linkage_receipt_id": row["linkage_receipt_id"], "eligibility_receipt_id": row["eligibility_receipt_id"],
                    "bucket_mapping_receipt_id": row["bucket_mapping_receipt_id"],
                }
                for row in sorted(rows, key=lambda item: item["touchpoint_id"])
            ],
        }
        if state != "AVAILABLE":
            opportunity_receipts.append({**base_receipt, "state": state, "conservation_state": "NOT_APPLICABLE"})
            unresolved_evidence.append({
                "opportunity_id": opportunity["opportunity_id"], "state": state,
                "touchpoint_states": [{"touchpoint_id": row["touchpoint_id"], "state": row["state"], "weight_state": weight_map[row["touchpoint_id"]]["state"]} for row in rows if row["state"] != "AVAILABLE" or weight_map[row["touchpoint_id"]]["state"] != "AVAILABLE"],
            })
            continue
        sequence = sorted(row["sequence_index"] for row in rows)
        if sequence != list(range(1, len(rows) + 1)):
            raise ValueError("touchpoint sequence must be contiguous per opportunity")
        ordered_rows = sorted(rows, key=lambda row: row["sequence_index"])
        if [row["_event_at"] for row in ordered_rows] != sorted(row["_event_at"] for row in ordered_rows):
            raise ValueError("touchpoint sequence conflicts with event chronology")
        total_weight = sum((row["_weight"] for row in weight_rows), Decimal("0"))
        if total_weight <= 0:
            raise ValueError("opportunity raw weight total must be positive")
        amount = opportunity["_amount"].quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        with localcontext() as context:
            context.prec = 50
            allocated = {
                touchpoint_id: (amount * weight_map[touchpoint_id]["_weight"] / total_weight).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
                for touchpoint_id in ids
            }
        residual = amount - sum(allocated.values(), Decimal("0"))
        allocated[min(ids)] += residual
        if sum(allocated.values(), Decimal("0")) != amount:
            raise ValueError("allocation conservation failure")
        for touchpoint_id, credit in allocated.items():
            bucket_totals[touchpoint_map[touchpoint_id]["bucket_id"]] += credit
        any_allocation = True
        opportunity_receipts.append({**base_receipt, "state": "AVAILABLE", "conservation_state": "CONSERVED"})

    bucket_receipts = []
    for bucket_id in sorted(contract["allowed_bucket_ids"]):
        bucket_receipts.append({
            "bucket_id": bucket_id,
            "state": "AVAILABLE" if any_allocation else "EVIDENCE_MISSING",
            "measure_kind": "POLICY_ALLOCATED_CREDIT",
            "policy_allocated_credit": _decimal_text(bucket_totals[bucket_id]) if any_allocation else None,
            "currency": contract["currency"],
        })
    return {
        "review_state": "HUMAN_REVIEW_REQUIRED",
        "policy_receipt": {
            "policy_id": policy["policy_id"], "policy_version": policy["policy_version"],
            "reviewer_role_id": policy["reviewer_role_id"], "privacy_receipt_id": policy["privacy_receipt_id"],
            "lawful_basis_receipt_id": policy["lawful_basis_receipt_id"],
            "recipient_policy_receipt_id": policy["recipient_policy_receipt_id"],
            "retention_policy_receipt_id": policy["retention_policy_receipt_id"],
            "retention_rule_id": policy["retention_rule_id"],
            "allowed_recipient_role_ids": policy["allowed_recipient_role_ids"],
        },
        "allocation_contract_receipt": {
            "contract_id": contract["contract_id"], "model_id": contract["model_id"],
            "model_version": contract["model_version"], "model_definition_receipt_id": contract["model_definition_receipt_id"],
            "model_approval_receipt_id": contract["model_approval_receipt_id"],
            "remainder_rule": contract["remainder_rule"], "remainder_rule_receipt_id": contract["remainder_rule_receipt_id"],
            "source_id": contract["source_id"], "source_version": contract["source_version"],
            "schema_id": contract["schema_id"], "schema_version": contract["schema_version"],
            "authorization_receipt_id": contract["authorization_receipt_id"], "query_receipt_id": contract["query_receipt_id"],
            "page_receipt_id": contract["page_receipt_id"], "opportunity_population_receipt_id": contract["opportunity_population_receipt_id"],
            "reporting_timezone": contract["reporting_timezone"], "reporting_period_start": contract["reporting_period_start"],
            "reporting_period_end": contract["reporting_period_end"], "touchpoint_window_start": contract["touchpoint_window_start"],
            "touchpoint_window_end": contract["touchpoint_window_end"], "currency": contract["currency"],
            "amount_basis": contract["amount_basis"], "measure_definition_id": contract["measure_definition_id"],
            "finance_approval_receipt_id": contract["finance_approval_receipt_id"],
            "pseudonymization_receipt_id": contract["pseudonymization_receipt_id"],
            "identity_linkage_policy_receipt_id": contract["identity_linkage_policy_receipt_id"],
            "event_definition_policy_receipt_id": contract["event_definition_policy_receipt_id"],
            "eligibility_policy_receipt_id": contract["eligibility_policy_receipt_id"],
            "deduplication_policy_receipt_id": contract["deduplication_policy_receipt_id"],
            "ordering_policy_receipt_id": contract["ordering_policy_receipt_id"],
            "exclusion_policy_receipt_id": contract["exclusion_policy_receipt_id"],
            "bucket_policy_receipt_id": contract["bucket_policy_receipt_id"],
        },
        "bucket_credit_receipts": bucket_receipts,
        "opportunity_evidence_receipts": opportunity_receipts,
        "unresolved_evidence": unresolved_evidence,
        "causal_attribution_authorized": False,
        "ranking_authorized": False,
        "downstream_decision_authorized": False,
        "action_authorized": False,
    }


def render_allocation_output(result):
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n\n"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: attribution_credit.py INPUT.json")
    document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sys.stdout.write(render_allocation_output(review_attribution_credit(document)))


if __name__ == "__main__":
    main()
