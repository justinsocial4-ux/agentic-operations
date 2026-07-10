#!/usr/bin/env python3
"""Build an exact, read-only ABM selection preview under an approved policy."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path


APPROVAL_FIELDS = (
    "identity_policy_status",
    "eligibility_policy_status",
    "selection_policy_status",
    "privacy_scope_status",
    "downstream_use_status",
)
PURPOSES = {"NEW_ADDITIONS_PREVIEW", "FULL_REFRESH_PREVIEW"}
IDENTITY_STATES = {"RESOLVED", "AMBIGUOUS", "CONFLICT", "UNKNOWN"}
ELIGIBILITY_STATES = {"VERIFIED_ELIGIBLE", "VERIFIED_INELIGIBLE", "CONFLICT", "UNKNOWN"}
SCORE_STATES = {"AVAILABLE", "UNAVAILABLE", "CONFLICT", "UNKNOWN"}
SEGMENT_STATES = {"VERIFIED", "CONFLICT", "UNKNOWN"}
ACTION_STATES = {"APPROVED", "NOT_APPROVED", "UNKNOWN"}
POLICY_STATES = {"APPROVED", "PENDING", "NOT_APPROVED", "UNKNOWN"}
POPULATION_STATES = {"COMPLETE", "INCOMPLETE", "UNKNOWN"}
MEMBERSHIP_STATES = {"VERIFIED_MEMBER", "NOT_MEMBER", "CONFLICT", "UNKNOWN"}
BOUNDARY = "NO CRM WRITE / NO TARGET PROPERTY CHANGE / NO LIST / NO CAMPAIGN OR OUTREACH ACTION"
VALIDATION_STATES = {"PRESENT", "NOT_PRESENT", "UNKNOWN"}
VALIDATION_FIELDS = (
    "model_card_status", "construct_validation_status", "mature_outcome_cohort_status",
    "calibration_status", "uncertainty_analysis_status", "prospective_evaluation_status",
    "treatment_design_status", "causal_evidence_status", "predictive_approval_status",
)


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


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
    if not result.is_finite() or result < 0 or result > 100:
        raise ValueError(f"{field} must be finite and between 0 and 100")
    return result


def _timestamp(value, field):
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    if parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must use UTC")
    return text, parsed


def _date(value, field):
    text = _text(value, field)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO 8601 date") from exc
    return text, parsed


def _policy(raw):
    required = (
        "policy_id", "version", "owner", "effective_date", "candidate_population_id",
        "candidate_population_receipt_id", "candidate_population_status", "candidate_count",
        "cutoff", "purpose", "entity_level", "capacity", "reviewer",
        "action_approval_status", "proposed_use", "records_system", "reversal_path",
        "score_policy_id", "score_policy_version",
        *VALIDATION_FIELDS,
        *APPROVAL_FIELDS,
    )
    missing = [field for field in required if field not in raw]
    if missing:
        raise ValueError("policy missing: " + ", ".join(missing))
    numeric_or_time = {"capacity", "candidate_count", "cutoff", "effective_date"}
    policy = {field: _text(raw[field], f"policy.{field}") for field in required if field not in numeric_or_time}
    policy["capacity"] = _integer(raw["capacity"], "policy.capacity")
    policy["candidate_count"] = _integer(raw["candidate_count"], "policy.candidate_count")
    policy["cutoff"], policy["cutoff_dt"] = _timestamp(raw["cutoff"], "policy.cutoff")
    policy["effective_date"], policy["effective_date_value"] = _date(raw["effective_date"], "policy.effective_date")
    if policy["effective_date_value"] > policy["cutoff_dt"].date():
        raise ValueError("policy cannot become effective after the cutoff")
    if policy["purpose"] not in PURPOSES:
        raise ValueError("policy.purpose is not an allowed preview purpose")
    if policy["entity_level"] != "legal_account":
        raise ValueError("policy.entity_level must be legal_account")
    if policy["action_approval_status"] not in ACTION_STATES:
        raise ValueError("policy.action_approval_status is invalid")
    if policy["candidate_population_status"] not in POPULATION_STATES:
        raise ValueError("policy.candidate_population_status is invalid")
    if any(policy[field] not in POLICY_STATES for field in APPROVAL_FIELDS):
        raise ValueError("policy contains an invalid approval state")
    if any(policy[field] not in VALIDATION_STATES for field in VALIDATION_FIELDS):
        raise ValueError("policy contains an invalid validation state")

    segment_field = raw.get("segment_field")
    segment_slots = raw.get("segment_slots")
    if (segment_field is None) != (segment_slots is None):
        raise ValueError("segment_field and segment_slots must be supplied together")
    if segment_slots is not None:
        policy["segment_field"] = _text(segment_field, "policy.segment_field")
        if not isinstance(segment_slots, dict) or not segment_slots:
            raise ValueError("policy.segment_slots must be a non-empty object")
        normalized = {}
        for name, slots in segment_slots.items():
            key = _text(name, "policy.segment_slots key")
            if key in normalized:
                raise ValueError("duplicate normalized segment slot")
            normalized[key] = _integer(slots, f"policy.segment_slots.{key}")
        if sum(normalized.values()) != policy["capacity"]:
            raise ValueError("segment slots must sum exactly to capacity")
        policy["segment_slots"] = normalized
    else:
        policy["segment_field"] = None
        policy["segment_slots"] = None
    return policy


def _policy_receipt(policy):
    excluded = {"cutoff_dt", "effective_date_value", "segment_slots", *VALIDATION_FIELDS}
    receipt = {key: value for key, value in policy.items() if key not in excluded}
    receipt["segment_slots_source"] = "capacity_receipts"
    receipt["validation_source"] = "validation_receipt"
    return receipt


def _finalize_result(result, policy):
    result.setdefault("candidate_receipts", [])
    result.setdefault("selection_account_ids", [])
    result.setdefault("provisional_above_boundary", [])
    result.setdefault("review_account_ids", [])
    result.setdefault("capacity_receipts", [])
    result["artifact_paths"] = {
        "policy_and_scope_receipt": "policy_receipt",
        "candidate_population_identity_and_eligibility": "candidate_receipts",
        "score_evidence": "candidate_receipts",
        "capacity_and_segment_slots": "capacity_receipts",
        "selection_preview": "gate,status,selection_account_ids,provisional_above_boundary,review_account_ids",
        "validation_and_prohibited_conclusions": "validation_receipt",
        "human_decision_preview": "policy_receipt.owner,policy_receipt.reviewer,policy_receipt.proposed_use,policy_receipt.action_approval_status,policy_receipt.records_system,policy_receipt.reversal_path",
    }
    result["validation_receipt"] = {field: policy[field] for field in VALIDATION_FIELDS}
    result["validation_receipt"].update({
        "interpretation": "POLICY_ARITHMETIC_ONLY",
        "prohibited_conclusions": [
            "BUYING_INTENT", "CAUSAL_LIFT", "EXPECTED_PIPELINE", "FORECAST", "PRIORITY_TRUTH",
            "PROPENSITY", "QUALIFICATION", "QUALITY", "REVENUE", "ROI",
        ],
    })
    result["action_authorized"] = False
    return result


def _bucket(rankable, slots, bucket):
    ordered = sorted(rankable, key=lambda item: (-item["score_decimal"], item["account_id"]))
    receipt = {
        "bucket": bucket,
        "slots": slots,
        "rankable_count": len(ordered),
        "filled_slots": 0,
        "unfilled_slots": 0,
        "provisional_above_boundary": [],
        "boundary_tie_accounts": [],
        "not_selected_accounts": [],
        "tie_unresolved_slots": 0,
        "presentation_order": "SCORE_DESC; ACCOUNT_ID_ASC_WITHIN_EQUAL_SCORE_FOR_DISPLAY_ONLY",
    }
    if slots == 0:
        receipt["not_selected_accounts"] = [item["account_id"] for item in ordered]
        return receipt
    if len(ordered) <= slots:
        receipt["provisional_above_boundary"] = [item["account_id"] for item in ordered]
        receipt["filled_slots"] = len(ordered)
        receipt["unfilled_slots"] = slots - len(ordered)
        return receipt

    boundary_score = ordered[slots - 1]["score_decimal"]
    next_score = ordered[slots]["score_decimal"]
    if boundary_score == next_score:
        above = [item for item in ordered if item["score_decimal"] > boundary_score]
        tied = [item for item in ordered if item["score_decimal"] == boundary_score]
        below = [item for item in ordered if item["score_decimal"] < boundary_score]
        receipt["provisional_above_boundary"] = [item["account_id"] for item in above]
        receipt["boundary_tie_accounts"] = [item["account_id"] for item in tied]
        receipt["not_selected_accounts"] = [item["account_id"] for item in below]
        receipt["filled_slots"] = len(above)
        receipt["tie_unresolved_slots"] = slots - len(above)
        return receipt

    receipt["provisional_above_boundary"] = [item["account_id"] for item in ordered[:slots]]
    receipt["not_selected_accounts"] = [item["account_id"] for item in ordered[slots:]]
    receipt["filled_slots"] = slots
    return receipt


def build_preview(document):
    if not isinstance(document, dict) or not isinstance(document.get("policy"), dict):
        raise ValueError("document must contain a policy object")
    if not isinstance(document.get("candidates"), list):
        raise ValueError("document must contain a candidates list")
    policy = _policy(document["policy"])
    if any(policy[field] != "APPROVED" for field in APPROVAL_FIELDS):
        return _finalize_result({
            "gate": "POLICY_APPROVAL_REQUIRED",
            "status": "POLICY_APPROVAL_REQUIRED",
            "policy_receipt": _policy_receipt(policy),
            "candidate_receipts": [],
            "selection_account_ids": [],
            "action_state": policy["action_approval_status"],
            "execution_state": "OUT_OF_SCOPE",
            "boundary": BOUNDARY,
        }, policy)
    if policy["candidate_population_status"] != "COMPLETE":
        return _finalize_result({
            "gate": "CANDIDATE_POPULATION_INCOMPLETE",
            "status": "CANDIDATE_POPULATION_INCOMPLETE",
            "policy_receipt": _policy_receipt(policy),
            "candidate_receipts": [],
            "selection_account_ids": [],
            "action_state": policy["action_approval_status"],
            "execution_state": "OUT_OF_SCOPE",
            "boundary": BOUNDARY,
        }, policy)
    if policy["candidate_count"] != len(document["candidates"]):
        return _finalize_result({
            "gate": "CANDIDATE_POPULATION_INCOMPLETE",
            "status": "CANDIDATE_POPULATION_COUNT_MISMATCH",
            "policy_receipt": _policy_receipt(policy),
            "candidate_receipts": [],
            "selection_account_ids": [],
            "action_state": policy["action_approval_status"],
            "execution_state": "OUT_OF_SCOPE",
            "boundary": BOUNDARY,
        }, policy)

    seen = set()
    receipts = []
    unresolved = []
    rankable = []
    for index, raw in enumerate(document["candidates"]):
        if not isinstance(raw, dict):
            raise ValueError(f"candidates[{index}] must be an object")
        required = (
            "account_id", "population_membership_status", "population_membership_receipt_id",
            "identity_status", "identity_receipt_id", "eligibility_status",
            "eligibility_receipt_id", "score_status", "score", "score_receipt_id",
            "score_policy_id", "score_policy_version", "evidence_cutoff",
        )
        missing = [field for field in required if field not in raw]
        if missing:
            raise ValueError(f"candidates[{index}] missing: " + ", ".join(missing))
        account_id = _text(raw["account_id"], f"candidates[{index}].account_id")
        if account_id in seen:
            raise ValueError(f"duplicate account_id: {account_id}")
        seen.add(account_id)
        membership = _text(raw["population_membership_status"], f"{account_id}.population_membership_status")
        membership_receipt_id = _text(raw["population_membership_receipt_id"], f"{account_id}.population_membership_receipt_id")
        identity = _text(raw["identity_status"], f"{account_id}.identity_status")
        identity_receipt_id = _text(raw["identity_receipt_id"], f"{account_id}.identity_receipt_id")
        eligibility = _text(raw["eligibility_status"], f"{account_id}.eligibility_status")
        eligibility_receipt_id = _text(raw["eligibility_receipt_id"], f"{account_id}.eligibility_receipt_id")
        score_status = _text(raw["score_status"], f"{account_id}.score_status")
        score_receipt_id = _text(raw["score_receipt_id"], f"{account_id}.score_receipt_id")
        if membership not in MEMBERSHIP_STATES or identity not in IDENTITY_STATES or eligibility not in ELIGIBILITY_STATES or score_status not in SCORE_STATES:
            raise ValueError(f"{account_id} has an invalid evidence state")
        score_policy_id = _text(raw["score_policy_id"], f"{account_id}.score_policy_id")
        score_policy_version = _text(raw["score_policy_version"], f"{account_id}.score_policy_version")
        cutoff_text, cutoff_dt = _timestamp(raw["evidence_cutoff"], f"{account_id}.evidence_cutoff")
        score_decimal = None
        if score_status == "AVAILABLE":
            if raw["score"] is None:
                raise ValueError(f"{account_id} AVAILABLE score cannot be null")
            score_decimal = _decimal(raw["score"], f"{account_id}.score")
        elif raw["score"] is not None:
            raise ValueError(f"{account_id} non-available score must be null")

        receipt = {
            "account_id": account_id,
            "population_membership_status": membership,
            "population_membership_receipt_id": membership_receipt_id,
            "identity_status": identity,
            "identity_receipt_id": identity_receipt_id,
            "eligibility_status": eligibility,
            "eligibility_receipt_id": eligibility_receipt_id,
            "score_status": score_status,
            "score_receipt_id": score_receipt_id,
            "score": str(score_decimal) if score_decimal is not None else None,
            "score_policy_id": score_policy_id,
            "score_policy_version": score_policy_version,
            "evidence_cutoff": cutoff_text,
            "segment_status": None,
            "segment": None,
            "disposition": None,
        }

        if membership != "VERIFIED_MEMBER":
            receipt["disposition"] = "POPULATION_MEMBERSHIP_REVIEW_REQUIRED"
        elif identity != "RESOLVED":
            receipt["disposition"] = "IDENTITY_REVIEW_REQUIRED"
        elif cutoff_dt.date() < policy["effective_date_value"]:
            receipt["disposition"] = "EVIDENCE_BEFORE_POLICY_EFFECTIVE"
        elif cutoff_dt > policy["cutoff_dt"]:
            receipt["disposition"] = "EVIDENCE_AFTER_CUTOFF"
        elif eligibility in {"UNKNOWN", "CONFLICT"}:
            receipt["disposition"] = "ELIGIBILITY_REVIEW_REQUIRED"
        elif eligibility == "VERIFIED_INELIGIBLE":
            receipt["disposition"] = "VERIFIED_INELIGIBLE"
        elif score_policy_id != policy["score_policy_id"] or score_policy_version != policy["score_policy_version"]:
            receipt["disposition"] = "SCORE_POLICY_CONFLICT"
        elif score_status != "AVAILABLE":
            receipt["disposition"] = "SCORE_EVIDENCE_REVIEW_REQUIRED"
        else:
            receipt["disposition"] = "RANKABLE"

        if policy["segment_slots"] is not None:
            if "segment_status" not in raw or "segment" not in raw or "segment_receipt_id" not in raw:
                raise ValueError(f"{account_id} requires segment_status, segment, and segment_receipt_id")
            segment_status = _text(raw["segment_status"], f"{account_id}.segment_status")
            segment_receipt_id = _text(raw["segment_receipt_id"], f"{account_id}.segment_receipt_id")
            if segment_status not in SEGMENT_STATES:
                raise ValueError(f"{account_id}.segment_status is invalid")
            segment = None if raw["segment"] is None else _text(raw["segment"], f"{account_id}.segment")
            receipt["segment_status"] = segment_status
            receipt["segment"] = segment
            receipt["segment_receipt_id"] = segment_receipt_id
            if receipt["disposition"] == "RANKABLE":
                if segment_status != "VERIFIED" or segment is None:
                    receipt["disposition"] = "SEGMENT_REVIEW_REQUIRED"
                elif segment not in policy["segment_slots"]:
                    receipt["disposition"] = "SEGMENT_POLICY_CONFLICT"

        receipt["score_decimal"] = score_decimal
        receipts.append(receipt)
        if receipt["disposition"] == "RANKABLE":
            rankable.append(receipt)
        elif receipt["disposition"] != "VERIFIED_INELIGIBLE":
            unresolved.append(account_id)

    public_receipts = [{key: value for key, value in item.items() if key != "score_decimal"} for item in receipts]
    if unresolved:
        return _finalize_result({
            "gate": "POLICY_EVIDENCE_PRESENT",
            "status": "CANDIDATE_EVIDENCE_REVIEW_REQUIRED",
            "policy_receipt": _policy_receipt(policy),
            "candidate_receipts": public_receipts,
            "selection_account_ids": [],
            "provisional_above_boundary": [],
            "review_account_ids": unresolved,
            "capacity_receipts": [],
            "action_state": policy["action_approval_status"],
            "execution_state": "OUT_OF_SCOPE",
            "boundary": BOUNDARY,
        }, policy)

    buckets = []
    if policy["segment_slots"] is None:
        buckets.append(_bucket(rankable, policy["capacity"], "ALL"))
    else:
        for segment in sorted(policy["segment_slots"]):
            slots = policy["segment_slots"][segment]
            members = [item for item in rankable if item["segment"] == segment]
            buckets.append(_bucket(members, slots, segment))

    tie_accounts = [account for bucket in buckets for account in bucket["boundary_tie_accounts"]]
    provisional = [account for bucket in buckets for account in bucket["provisional_above_boundary"]]
    unfilled = sum(bucket["unfilled_slots"] for bucket in buckets)
    if tie_accounts:
        status = "BOUNDARY_TIE_REVIEW_REQUIRED"
        final_ids = []
    elif unfilled:
        status = "SELECTION_PREVIEW_AVAILABLE_CAPACITY_UNFILLED"
        final_ids = provisional
    else:
        status = "SELECTION_PREVIEW_AVAILABLE"
        final_ids = provisional

    tie_set = set(tie_accounts)
    provisional_set = set(provisional)
    not_selected_set = {account for bucket in buckets for account in bucket["not_selected_accounts"]}
    for receipt in receipts:
        if receipt["disposition"] != "RANKABLE":
            continue
        account_id = receipt["account_id"]
        if account_id in tie_set:
            receipt["disposition"] = "BOUNDARY_TIE_REVIEW"
        elif account_id in provisional_set:
            receipt["disposition"] = "PROVISIONAL_ABOVE_BOUNDARY" if tie_accounts else "SELECTED_PREVIEW"
        elif account_id in not_selected_set:
            receipt["disposition"] = "NOT_SELECTED_CAPACITY"
    public_receipts = [{key: value for key, value in item.items() if key != "score_decimal"} for item in receipts]

    result = {
        "gate": "POLICY_EVIDENCE_PRESENT",
        "status": status,
        "policy_receipt": _policy_receipt(policy),
        "candidate_receipts": public_receipts,
        "selection_account_ids": sorted(final_ids),
        "provisional_above_boundary": sorted(provisional),
        "review_account_ids": sorted(tie_accounts),
        "capacity_receipts": buckets,
        "membership_list_order": "ACCOUNT_ID_ASC_FOR_DISPLAY_ONLY",
        "action_state": policy["action_approval_status"],
        "execution_state": "OUT_OF_SCOPE",
        "boundary": BOUNDARY,
    }
    return _finalize_result(result, policy)


def render_preview_output(preview):
    if not isinstance(preview, dict):
        raise ValueError("preview must be an object")
    return "```json\n" + json.dumps(preview, indent=2, sort_keys=True) + "\n```\n\n" + BOUNDARY


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) > 1:
        raise SystemExit("usage: selection_preview.py [input.json]")
    data = json.loads(Path(argv[0]).read_text() if argv else sys.stdin.read())
    print(render_preview_output(build_preview(data)))


if __name__ == "__main__":
    main()
