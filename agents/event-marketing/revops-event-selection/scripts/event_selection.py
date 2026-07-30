#!/usr/bin/env python3
"""Build an exact, read-only event criteria selection preview."""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path


POLICY_STATES = {"APPROVED", "PENDING", "NOT_APPROVED", "UNKNOWN"}
APPROVAL_FIELDS = (
    "identity_policy_status", "criteria_policy_status", "cost_policy_status",
    "privacy_policy_status", "downstream_use_status",
)
POPULATION_STATES = {"COMPLETE", "INCOMPLETE", "UNKNOWN"}
IDENTITY_STATES = {"RESOLVED", "AMBIGUOUS", "CONFLICT", "UNKNOWN"}
MEMBERSHIP_STATES = {"VERIFIED_MEMBER", "NOT_MEMBER", "CONFLICT", "UNKNOWN"}
EVIDENCE_STATES = {"COMPLETE", "INCOMPLETE", "CONFLICT", "UNKNOWN"}
COST_STATES = {"APPROVED_ACTUAL", "APPROVED_QUOTE", "UNAVAILABLE", "CONFLICT", "UNKNOWN"}
CRITERION_STATES = {"MATCHED", "NOT_MATCHED", "UNKNOWN", "CONFLICT"}
ACTION_STATES = {"APPROVED", "NOT_APPROVED", "UNKNOWN"}
PURPOSES = {"EVENT_CRITERIA_COMPARISON"}
BOUNDARY = "NO SPONSORSHIP OR BUDGET ACTION / NO CRM, LIST, CAMPAIGN, OUTREACH, SCHEDULE, OR ORCHESTRATION ACTION"
FORBIDDEN_KEYS = {
    "attendee_name", "attendee_email", "email", "phone", "job_title", "linkedin_url",
    "social_url", "free_text", "predicted_pipeline", "predicted_revenue", "roi",
    "win_probability", "confidence_score", "recommendation",
}
ADEQUACY_PATTERN = re.compile(r"\b(small|large|enough|limited|insufficient|good|poor|high|low)\b", re.I)


def _exact_fields(raw, allowed, field):
    if not isinstance(raw, dict):
        raise ValueError(f"{field} must be an object")
    extra = sorted(set(raw) - set(allowed))
    if extra:
        raise ValueError(f"{field} contains unsupported fields: " + ", ".join(extra))


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _enum(value, allowed, field):
    result = _text(value, field)
    if result not in allowed:
        raise ValueError(f"{field} has an invalid state")
    return result


def _integer(value, field, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")
    return value


def _decimal(value, field):
    if isinstance(value, bool) or isinstance(value, float) or not isinstance(value, (str, int, Decimal)):
        raise ValueError(f"{field} must be an integer or decimal string")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{field} must be an exact decimal") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{field} must be a finite non-negative decimal")
    return result


def _timestamp(value, field):
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must use UTC")
    return text, parsed


def _date(value, field):
    text = _text(value, field)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO 8601 date") from exc
    return text, parsed


def _pseudonymous(value, field):
    result = _text(value, field)
    if "@" in result or re.search(r"https?://|www\.", result, re.I) or len(result) > 80:
        raise ValueError(f"{field} must be a stable pseudonymous ID")
    return result


def _criterion_definition(value, field):
    result = _text(value, field)
    if ADEQUACY_PATTERN.search(result):
        raise ValueError(f"{field} contains an unapproved adequacy label")
    return result


def _reject_forbidden(value, path="document"):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise ValueError(f"{path}.{key} is prohibited")
            _reject_forbidden(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_forbidden(item, f"{path}[{index}]")


def _policy(raw):
    fields = (
        "policy_id", "version", "owner", "reviewer", "effective_date", "cutoff", "purpose",
        "candidate_population_id", "candidate_population_receipt_id", "candidate_population_status",
        "candidate_count", "source_id", "source_version", "schema_id", "schema_version",
        "currency", "cost_basis", "accepted_cost_statuses", "capacity", "tie_rule", "action_approval_status",
        "proposed_use", "records_system", "correction_path", "prohibited_uses", "criteria",
        *APPROVAL_FIELDS,
    )
    _exact_fields(raw, fields, "policy")
    missing = [field for field in fields if field not in raw]
    if missing:
        raise ValueError("policy missing: " + ", ".join(missing))
    text_fields = {
        "policy_id", "version", "owner", "reviewer", "purpose", "candidate_population_id",
        "candidate_population_receipt_id", "source_id", "source_version", "schema_id",
        "schema_version", "currency", "cost_basis", "tie_rule", "action_approval_status", "proposed_use",
        "records_system", "correction_path", *APPROVAL_FIELDS,
    }
    policy = {field: _text(raw[field], f"policy.{field}") for field in text_fields}
    policy["effective_date"], policy["effective_date_value"] = _date(raw["effective_date"], "policy.effective_date")
    policy["cutoff"], policy["cutoff_dt"] = _timestamp(raw["cutoff"], "policy.cutoff")
    if policy["effective_date_value"] > policy["cutoff_dt"].date():
        raise ValueError("policy cannot become effective after cutoff")
    policy["candidate_population_status"] = _enum(raw["candidate_population_status"], POPULATION_STATES, "policy.candidate_population_status")
    policy["candidate_count"] = _integer(raw["candidate_count"], "policy.candidate_count")
    policy["capacity"] = _integer(raw["capacity"], "policy.capacity")
    if policy["purpose"] not in PURPOSES or policy["tie_rule"] != "NO_AUTOMATIC_TIE_BREAK":
        raise ValueError("policy purpose or tie rule is invalid")
    if policy["action_approval_status"] not in ACTION_STATES:
        raise ValueError("policy.action_approval_status is invalid")
    if any(policy[field] not in POLICY_STATES for field in APPROVAL_FIELDS):
        raise ValueError("policy contains an invalid approval state")
    if not isinstance(raw["accepted_cost_statuses"], list) or not raw["accepted_cost_statuses"]:
        raise ValueError("policy.accepted_cost_statuses must be a non-empty list")
    accepted_cost_statuses = [_enum(item, COST_STATES, "policy.accepted_cost_statuses") for item in raw["accepted_cost_statuses"]]
    if len(accepted_cost_statuses) != len(set(accepted_cost_statuses)):
        raise ValueError("policy.accepted_cost_statuses contains duplicates")
    policy["accepted_cost_statuses"] = sorted(accepted_cost_statuses)
    if any(item not in {"APPROVED_ACTUAL", "APPROVED_QUOTE"} for item in policy["accepted_cost_statuses"]):
        raise ValueError("accepted cost statuses must be approved evidence states")
    if not isinstance(raw["prohibited_uses"], list) or not raw["prohibited_uses"]:
        raise ValueError("policy.prohibited_uses must be a non-empty list")
    policy["prohibited_uses"] = sorted({_text(item, "policy.prohibited_uses") for item in raw["prohibited_uses"]})
    if not isinstance(raw["criteria"], list) or not raw["criteria"]:
        raise ValueError("policy.criteria must be a non-empty list")
    criteria = []
    seen = set()
    total = Decimal("0")
    for index, item in enumerate(raw["criteria"]):
        fields = ("criterion_id", "definition", "evidence_rule_id", "required", "weight")
        _exact_fields(item, fields, f"policy.criteria[{index}]")
        if set(item) != set(fields):
            raise ValueError(f"policy.criteria[{index}] has missing fields")
        criterion_id = _text(item["criterion_id"], f"policy.criteria[{index}].criterion_id")
        if criterion_id in seen:
            raise ValueError(f"duplicate criterion_id: {criterion_id}")
        seen.add(criterion_id)
        if not isinstance(item["required"], bool):
            raise ValueError(f"{criterion_id}.required must be boolean")
        weight = _decimal(item["weight"], f"{criterion_id}.weight")
        total += weight
        criteria.append({
            "criterion_id": criterion_id,
            "definition": _criterion_definition(item["definition"], f"{criterion_id}.definition"),
            "evidence_rule_id": _text(item["evidence_rule_id"], f"{criterion_id}.evidence_rule_id"),
            "required": item["required"],
            "weight": str(weight),
            "weight_decimal": weight,
        })
    if total != Decimal("100"):
        raise ValueError("criterion weights must total exactly 100")
    policy["criteria"] = sorted(criteria, key=lambda item: item["criterion_id"])
    return policy


def _policy_receipt(policy):
    excluded = {"cutoff_dt", "effective_date_value"}
    result = {key: value for key, value in policy.items() if key not in excluded and key != "criteria"}
    result["criteria"] = [{key: value for key, value in item.items() if key != "weight_decimal"} for item in policy["criteria"]]
    return result


def _base_result(policy, gate, status, events=None):
    result = {
        "gate": gate,
        "status": status,
        "policy_receipt": _policy_receipt(policy),
        "event_receipts": events or [],
        "capacity_receipt": {
            "capacity": policy["capacity"], "rankable_count": 0, "filled_slots": 0,
            "unfilled_slots": policy["capacity"], "tie_unresolved_slots": 0,
            "presentation_order": "POLICY_SCORE_DESC; EVENT_ID_ASC_WITHIN_EQUAL_SCORE_FOR_DISPLAY_ONLY",
        },
        "selection_event_ids": [],
        "provisional_above_boundary": [],
        "review_event_ids": [],
        "artifact_paths": {
            "policy_and_population": "policy_receipt",
            "event_identity_source_cost_and_criteria": "event_receipts",
            "capacity_and_ties": "capacity_receipt",
            "selection_preview": "selection_event_ids,provisional_above_boundary,review_event_ids",
            "human_review": "policy_receipt.owner,policy_receipt.reviewer,policy_receipt.proposed_use",
        },
        "interpretation": "APPROVED_POLICY_ARITHMETIC_ONLY",
        "prohibited_conclusions": [
            "BUYER_INTENT", "CAUSALITY", "CONFIDENCE", "CONVERSION", "EVENT_QUALITY",
            "EXPECTED_PIPELINE", "FORECAST", "REVENUE", "ROI", "SPONSORSHIP_RECOMMENDATION",
        ],
        "action_state": policy["action_approval_status"],
        "action_authorized": False,
        "boundary": BOUNDARY,
    }
    return result


def build_selection(document):
    _reject_forbidden(document)
    _exact_fields(document, ("policy", "events"), "document")
    if not isinstance(document.get("policy"), dict) or not isinstance(document.get("events"), list):
        raise ValueError("document must contain policy and events")
    policy = _policy(document["policy"])
    if any(policy[field] != "APPROVED" for field in APPROVAL_FIELDS):
        return _base_result(policy, "POLICY_REQUIRED", "POLICY_APPROVAL_REQUIRED")
    if policy["candidate_population_status"] != "COMPLETE" or policy["candidate_count"] != len(document["events"]):
        return _base_result(policy, "POPULATION_INCOMPLETE", "CANDIDATE_POPULATION_RECONCILIATION_FAILED")

    criterion_map = {item["criterion_id"]: item for item in policy["criteria"]}
    seen = set()
    receipts = []
    rankable = []
    unresolved = []
    for index, raw in enumerate(document["events"]):
        fields = (
            "event_id", "population_membership_status", "population_membership_receipt_id",
            "identity_status", "identity_receipt_id", "source_id", "source_version", "schema_id",
            "schema_version", "extraction_id", "evidence_cutoff", "evidence_population_status",
            "evidence_population_receipt_id", "event_begin_date", "event_end_date", "cost_status",
            "cost_amount", "currency", "cost_basis", "cost_receipt_id", "evidence_organization_count",
            "organization_receipts", "criterion_evidence",
        )
        _exact_fields(raw, fields, f"events[{index}]")
        missing = [field for field in fields if field not in raw]
        if missing:
            raise ValueError(f"events[{index}] missing: " + ", ".join(missing))
        event_id = _text(raw["event_id"], f"events[{index}].event_id")
        if event_id in seen:
            raise ValueError(f"duplicate event_id: {event_id}")
        seen.add(event_id)
        membership = _enum(raw["population_membership_status"], MEMBERSHIP_STATES, f"{event_id}.population_membership_status")
        identity = _enum(raw["identity_status"], IDENTITY_STATES, f"{event_id}.identity_status")
        evidence_population = _enum(raw["evidence_population_status"], EVIDENCE_STATES, f"{event_id}.evidence_population_status")
        cost_status = _enum(raw["cost_status"], COST_STATES, f"{event_id}.cost_status")
        cutoff_text, cutoff_dt = _timestamp(raw["evidence_cutoff"], f"{event_id}.evidence_cutoff")
        begin_text, begin_value = _date(raw["event_begin_date"], f"{event_id}.event_begin_date")
        end_text, end_value = _date(raw["event_end_date"], f"{event_id}.event_end_date")
        if end_value < begin_value:
            raise ValueError(f"{event_id} event end precedes begin")
        cost = _decimal(raw["cost_amount"], f"{event_id}.cost_amount") if cost_status in {"APPROVED_ACTUAL", "APPROVED_QUOTE"} else None
        if cost is None and raw["cost_amount"] is not None:
            raise ValueError(f"{event_id} unresolved cost must be null")
        organization_count = _integer(raw["evidence_organization_count"], f"{event_id}.evidence_organization_count")
        if not isinstance(raw["organization_receipts"], list):
            raise ValueError(f"{event_id}.organization_receipts must be a list")
        organizations = []
        organization_receipts = []
        for organization_index, item in enumerate(raw["organization_receipts"]):
            organization_fields = ("organization_id", "identity_status", "identity_receipt_id")
            _exact_fields(item, organization_fields, f"{event_id}.organization_receipts[{organization_index}]")
            if set(item) != set(organization_fields):
                raise ValueError(f"{event_id} organization receipt has missing fields")
            organization_id = _pseudonymous(item["organization_id"], f"{event_id}.organization_id")
            organization_identity = _enum(item["identity_status"], IDENTITY_STATES, f"{event_id}.{organization_id}.identity_status")
            organizations.append(organization_id)
            organization_receipts.append({
                "organization_id": organization_id,
                "identity_status": organization_identity,
                "identity_receipt_id": _text(item["identity_receipt_id"], f"{event_id}.{organization_id}.identity_receipt_id"),
            })
        if organization_count != len(organization_receipts):
            raise ValueError(f"{event_id} evidence organization count does not reconcile")
        if len(organizations) != len(set(organizations)):
            raise ValueError(f"{event_id} has duplicate organization IDs")
        organization_identity_unresolved = any(item["identity_status"] != "RESOLVED" for item in organization_receipts)
        if not isinstance(raw["criterion_evidence"], list):
            raise ValueError(f"{event_id}.criterion_evidence must be a list")
        criterion_receipts = []
        criterion_seen = set()
        score = Decimal("0")
        criterion_unresolved = False
        required_not_matched = False
        for evidence_index, item in enumerate(raw["criterion_evidence"]):
            evidence_fields = ("criterion_id", "state", "evidence_receipt_id", "evidence_rule_id")
            _exact_fields(item, evidence_fields, f"{event_id}.criterion_evidence[{evidence_index}]")
            if set(item) != set(evidence_fields):
                raise ValueError(f"{event_id} criterion evidence has missing fields")
            criterion_id = _text(item["criterion_id"], f"{event_id}.criterion_id")
            if criterion_id in criterion_seen or criterion_id not in criterion_map:
                raise ValueError(f"{event_id} has duplicate or unknown criterion: {criterion_id}")
            criterion_seen.add(criterion_id)
            definition = criterion_map[criterion_id]
            evidence_rule_id = _text(item["evidence_rule_id"], f"{event_id}.{criterion_id}.evidence_rule_id")
            if evidence_rule_id != definition["evidence_rule_id"]:
                raise ValueError(f"{event_id}.{criterion_id} evidence rule conflicts with policy")
            state = _enum(item["state"], CRITERION_STATES, f"{event_id}.{criterion_id}.state")
            if state == "MATCHED":
                score += definition["weight_decimal"]
            if state in {"UNKNOWN", "CONFLICT"}:
                criterion_unresolved = True
            if definition["required"] and state == "NOT_MATCHED":
                required_not_matched = True
            criterion_receipts.append({
                "criterion_id": criterion_id, "state": state,
                "evidence_receipt_id": _text(item["evidence_receipt_id"], f"{event_id}.{criterion_id}.evidence_receipt_id"),
                "evidence_rule_id": evidence_rule_id,
            })
        if criterion_seen != set(criterion_map):
            raise ValueError(f"{event_id} must provide every policy criterion exactly once")

        disposition = "RANKABLE"
        if membership != "VERIFIED_MEMBER":
            disposition = "POPULATION_MEMBERSHIP_REVIEW"
        elif identity != "RESOLVED":
            disposition = "IDENTITY_REVIEW"
        elif raw["source_id"] != policy["source_id"] or raw["source_version"] != policy["source_version"]:
            disposition = "SOURCE_CONFLICT"
        elif raw["schema_id"] != policy["schema_id"] or raw["schema_version"] != policy["schema_version"]:
            disposition = "SCHEMA_CONFLICT"
        elif cutoff_dt.date() < policy["effective_date_value"] or cutoff_dt > policy["cutoff_dt"]:
            disposition = "EVIDENCE_CUTOFF_REVIEW"
        elif evidence_population != "COMPLETE":
            disposition = "EVIDENCE_POPULATION_REVIEW"
        elif organization_identity_unresolved:
            disposition = "ORGANIZATION_IDENTITY_REVIEW"
        elif cost_status not in policy["accepted_cost_statuses"]:
            disposition = "COST_REVIEW"
        elif raw["currency"] != policy["currency"]:
            disposition = "CURRENCY_CONFLICT"
        elif raw["cost_basis"] != policy["cost_basis"]:
            disposition = "COST_BASIS_CONFLICT"
        elif criterion_unresolved:
            disposition = "CRITERION_EVIDENCE_REVIEW"
        elif required_not_matched:
            disposition = "REQUIRED_CRITERION_NOT_MATCHED"

        receipt = {
            "event_id": event_id,
            "population_membership_status": membership,
            "population_membership_receipt_id": _text(raw["population_membership_receipt_id"], f"{event_id}.population_membership_receipt_id"),
            "identity_status": identity,
            "identity_receipt_id": _text(raw["identity_receipt_id"], f"{event_id}.identity_receipt_id"),
            "source_id": _text(raw["source_id"], f"{event_id}.source_id"),
            "source_version": _text(raw["source_version"], f"{event_id}.source_version"),
            "schema_id": _text(raw["schema_id"], f"{event_id}.schema_id"),
            "schema_version": _text(raw["schema_version"], f"{event_id}.schema_version"),
            "extraction_id": _text(raw["extraction_id"], f"{event_id}.extraction_id"),
            "evidence_cutoff": cutoff_text,
            "evidence_population_status": evidence_population,
            "evidence_population_receipt_id": _text(raw["evidence_population_receipt_id"], f"{event_id}.evidence_population_receipt_id"),
            "event_begin_date": begin_text,
            "event_end_date": end_text,
            "cost_status": cost_status,
            "cost_amount": str(cost) if cost is not None else None,
            "currency": _text(raw["currency"], f"{event_id}.currency"),
            "cost_basis": _text(raw["cost_basis"], f"{event_id}.cost_basis"),
            "cost_receipt_id": _text(raw["cost_receipt_id"], f"{event_id}.cost_receipt_id"),
            "evidence_organization_count": organization_count,
            "organization_receipts": sorted(organization_receipts, key=lambda item: item["organization_id"]),
            "criterion_receipts": sorted(criterion_receipts, key=lambda item: item["criterion_id"]),
            "policy_score": str(score),
            "disposition": disposition,
        }
        receipts.append(receipt)
        if disposition == "RANKABLE":
            rankable.append((event_id, score))
        elif disposition != "REQUIRED_CRITERION_NOT_MATCHED":
            unresolved.append(event_id)

    receipts.sort(key=lambda item: item["event_id"])
    if unresolved:
        result = _base_result(policy, "EVIDENCE_REVIEW", "FINAL_SELECTION_UNAVAILABLE", receipts)
        result["review_event_ids"] = sorted(unresolved)
        result["capacity_receipt"]["rankable_count"] = len(rankable)
        return result

    ordered = sorted(rankable, key=lambda item: (-item[1], item[0]))
    result = _base_result(policy, "READY_FOR_HUMAN_REVIEW", "SELECTION_PREVIEW_AVAILABLE", receipts)
    capacity = policy["capacity"]
    cap = result["capacity_receipt"]
    cap["rankable_count"] = len(ordered)
    if len(ordered) <= capacity:
        result["selection_event_ids"] = [item[0] for item in ordered]
        cap["filled_slots"] = len(ordered)
        cap["unfilled_slots"] = capacity - len(ordered)
        return result
    if capacity == 0:
        cap["unfilled_slots"] = 0
        return result
    boundary_score = ordered[capacity - 1][1]
    next_score = ordered[capacity][1]
    if boundary_score == next_score:
        above = [item[0] for item in ordered if item[1] > boundary_score]
        tied = [item[0] for item in ordered if item[1] == boundary_score]
        result["gate"] = "BOUNDARY_TIE_REVIEW"
        result["status"] = "FINAL_SELECTION_UNAVAILABLE"
        result["provisional_above_boundary"] = above
        result["review_event_ids"] = tied
        cap["filled_slots"] = len(above)
        cap["unfilled_slots"] = 0
        cap["tie_unresolved_slots"] = capacity - len(above)
        return result
    result["selection_event_ids"] = [item[0] for item in ordered[:capacity]]
    cap["filled_slots"] = capacity
    cap["unfilled_slots"] = 0
    return result


def render_selection_output(result):
    return "```json\n" + json.dumps(result, indent=2, sort_keys=True) + "\n```\n" + result["boundary"]


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        raise SystemExit("usage: event_selection.py [input.json]")
    raw = Path(args[0]).read_text(encoding="utf-8") if args else sys.stdin.read()
    result = build_selection(json.loads(raw))
    sys.stdout.write(render_selection_output(result))


if __name__ == "__main__":
    main()
