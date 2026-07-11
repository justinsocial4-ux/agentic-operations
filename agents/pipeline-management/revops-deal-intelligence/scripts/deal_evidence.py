#!/usr/bin/env python3
"""Build an exact, read-only deal evidence review."""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path


POLICY_STATES = {"APPROVED", "PENDING", "NOT_APPROVED", "UNKNOWN"}
POPULATION_STATES = {"COMPLETE", "INCOMPLETE", "UNKNOWN"}
MEMBERSHIP_STATES = {"VERIFIED_MEMBER", "NOT_MEMBER", "CONFLICT", "UNKNOWN"}
LANE_STATES = {"AVAILABLE", "UNAVAILABLE", "CONFLICT"}
ACTIVITY_STATES = {"AVAILABLE", "NO_QUALIFYING_ACTIVITY_RECORDED", "EVIDENCE_UNAVAILABLE", "CONFLICT"}
ACTIVITY_POPULATION_STATES = {"COMPLETE", "INCOMPLETE", "CONFLICT", "UNKNOWN"}
ACTION_STATES = {"APPROVED", "NOT_APPROVED", "UNKNOWN"}
BOUNDARY = "NO FORECAST OR DEAL VERDICT / NO CRM, OWNER, COACHING, TASK, MESSAGE, ALERT, SCHEDULE, OR WORKFORCE ACTION"
FORBIDDEN_KEYS = {
    "account_name", "deal_name", "owner_name", "manager_name", "email", "phone", "title",
    "message", "note", "transcript", "sentiment", "free_text", "probability", "confidence",
    "risk_score", "forecast", "recommendation",
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


def _reject_forbidden(value, path="document"):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise ValueError(f"{path}.{key} is prohibited")
            _reject_forbidden(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_forbidden(item, f"{path}[{index}]")


def _unique_text_list(value, field):
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    result = [_text(item, field) for item in value]
    if len(result) != len(set(result)):
        raise ValueError(f"{field} contains duplicates")
    return sorted(result)


def _policy(raw):
    fields = (
        "policy_id", "version", "purpose", "owner", "reviewer", "effective_date", "cutoff",
        "timezone", "population_policy_id", "source_id", "source_version", "schema_id",
        "schema_version", "stage_history_source_id", "stage_history_source_version",
        "activity_source_id", "activity_source_version", "pipeline_id", "open_stage_ids",
        "terminal_stage_ids", "stage_threshold_days", "activity_threshold_days",
        "qualifying_activity_types", "activity_occurrence_rule_id", "activity_association_rule_id",
        "amount_basis", "currency", "identity_policy_status", "stage_policy_status",
        "activity_policy_status", "amount_policy_status", "privacy_policy_status",
        "workforce_policy_status", "downstream_use_status", "action_approval_status",
        "correction_path", "prohibited_uses",
    )
    _exact_fields(raw, fields, "policy")
    missing = [field for field in fields if field not in raw]
    if missing:
        raise ValueError("policy missing: " + ", ".join(missing))
    numeric_or_date = {"activity_threshold_days", "stage_threshold_days", "effective_date", "cutoff", "open_stage_ids", "terminal_stage_ids", "qualifying_activity_types", "prohibited_uses"}
    policy = {field: _text(raw[field], f"policy.{field}") for field in fields if field not in numeric_or_date}
    if policy["purpose"] != "DEAL_EVIDENCE_REVIEW" or policy["timezone"] != "UTC":
        raise ValueError("policy purpose or timezone is invalid")
    policy["effective_date"], policy["effective_date_value"] = _date(raw["effective_date"], "policy.effective_date")
    policy["cutoff"], policy["cutoff_dt"] = _timestamp(raw["cutoff"], "policy.cutoff")
    if policy["effective_date_value"] > policy["cutoff_dt"].date():
        raise ValueError("policy cannot become effective after cutoff")
    policy["open_stage_ids"] = _unique_text_list(raw["open_stage_ids"], "policy.open_stage_ids")
    policy["terminal_stage_ids"] = _unique_text_list(raw["terminal_stage_ids"], "policy.terminal_stage_ids")
    if set(policy["open_stage_ids"]) & set(policy["terminal_stage_ids"]):
        raise ValueError("active and terminal stage IDs must be disjoint")
    if not isinstance(raw["stage_threshold_days"], dict):
        raise ValueError("policy.stage_threshold_days must be an object")
    if set(raw["stage_threshold_days"]) != set(policy["open_stage_ids"]):
        raise ValueError("stage thresholds must cover every active stage exactly")
    policy["stage_threshold_days"] = {
        _text(stage_id, "policy.stage_threshold_days key"): _integer(days, f"policy.stage_threshold_days.{stage_id}", 1)
        for stage_id, days in raw["stage_threshold_days"].items()
    }
    policy["activity_threshold_days"] = _integer(raw["activity_threshold_days"], "policy.activity_threshold_days", 1)
    policy["qualifying_activity_types"] = _unique_text_list(raw["qualifying_activity_types"], "policy.qualifying_activity_types")
    policy["prohibited_uses"] = _unique_text_list(raw["prohibited_uses"], "policy.prohibited_uses")
    approval_fields = (
        "identity_policy_status", "stage_policy_status", "activity_policy_status", "amount_policy_status",
        "privacy_policy_status", "workforce_policy_status", "downstream_use_status",
    )
    if any(policy[field] not in POLICY_STATES for field in approval_fields):
        raise ValueError("policy contains an invalid approval state")
    if policy["action_approval_status"] not in ACTION_STATES:
        raise ValueError("policy.action_approval_status is invalid")
    policy["approval_fields"] = approval_fields
    return policy


def _policy_receipt(policy):
    excluded = {"cutoff_dt", "effective_date_value", "approval_fields"}
    return {key: value for key, value in policy.items() if key not in excluded}


def _base_result(policy, population, gate, status, deals=None):
    return {
        "gate": gate,
        "status": status,
        "policy_receipt": _policy_receipt(policy),
        "population_receipt": population,
        "deal_receipts": deals or [],
        "review_deal_ids": [],
        "artifact_paths": {
            "policy_and_population": "policy_receipt,population_receipt",
            "current_stage_close_activity_and_amount": "deal_receipts",
            "unranked_review_set": "review_deal_ids,deal_receipts.review_reasons",
            "human_review": "policy_receipt.owner,policy_receipt.reviewer,policy_receipt.correction_path",
        },
        "interpretation": "RECORDED_DEAL_EVIDENCE_ONLY",
        "prohibited_conclusions": [
            "BUYER_INTENT", "CAUSE", "CLOSE_PROBABILITY", "COACHING_NEED", "CONFIDENCE",
            "DEAL_HEALTH", "DEAL_RISK", "FORECAST", "REVENUE_AT_RISK", "SELLER_PERFORMANCE",
        ],
        "action_state": policy["action_approval_status"],
        "action_authorized": False,
        "boundary": BOUNDARY,
    }


def review_deals(document):
    _reject_forbidden(document)
    _exact_fields(document, ("review_id", "policy", "population_receipt", "deals"), "document")
    if not isinstance(document.get("policy"), dict) or not isinstance(document.get("population_receipt"), dict) or not isinstance(document.get("deals"), list):
        raise ValueError("document must contain policy, population_receipt, and deals")
    review_id = _text(document.get("review_id"), "review_id")
    policy = _policy(document["policy"])
    population_fields = ("receipt_id", "policy_id", "population_status", "declared_deal_count", "source_id", "source_version", "schema_id", "schema_version", "extraction_id")
    population_raw = document["population_receipt"]
    _exact_fields(population_raw, population_fields, "population_receipt")
    if set(population_raw) != set(population_fields):
        raise ValueError("population_receipt has missing fields")
    population = {
        "review_id": review_id,
        "receipt_id": _text(population_raw["receipt_id"], "population_receipt.receipt_id"),
        "policy_id": _text(population_raw["policy_id"], "population_receipt.policy_id"),
        "population_status": _enum(population_raw["population_status"], POPULATION_STATES, "population_receipt.population_status"),
        "declared_deal_count": _integer(population_raw["declared_deal_count"], "population_receipt.declared_deal_count"),
        "source_id": _text(population_raw["source_id"], "population_receipt.source_id"),
        "source_version": _text(population_raw["source_version"], "population_receipt.source_version"),
        "schema_id": _text(population_raw["schema_id"], "population_receipt.schema_id"),
        "schema_version": _text(population_raw["schema_version"], "population_receipt.schema_version"),
        "extraction_id": _text(population_raw["extraction_id"], "population_receipt.extraction_id"),
    }
    if any(policy[field] != "APPROVED" for field in policy["approval_fields"]):
        return _base_result(policy, population, "POLICY_REQUIRED", "POLICY_APPROVAL_REQUIRED")
    population_binding = (
        population["policy_id"] == policy["population_policy_id"]
        and population["source_id"] == policy["source_id"]
        and population["source_version"] == policy["source_version"]
        and population["schema_id"] == policy["schema_id"]
        and population["schema_version"] == policy["schema_version"]
    )
    if population["population_status"] != "COMPLETE" or population["declared_deal_count"] != len(document["deals"]) or not population_binding:
        return _base_result(policy, population, "POPULATION_INCOMPLETE", "DEAL_POPULATION_RECONCILIATION_FAILED")

    fields = (
        "deal_id", "account_id", "owner_id", "population_membership_status", "population_membership_receipt_id",
        "source_id", "source_version", "schema_id", "schema_version", "extraction_id", "evidence_cutoff",
        "pipeline_id", "current_stage_id", "current_state_receipt_id", "stage_entry_state",
        "current_stage_entered_at", "stage_history_source_id", "stage_history_source_version",
        "stage_history_receipt_id", "close_date_state", "close_date", "close_date_receipt_id",
        "activity_population_state", "activity_population_receipt_id", "activity_state", "last_activity_at",
        "last_activity_type", "activity_source_id", "activity_source_version", "activity_occurrence_rule_id",
        "activity_association_rule_id", "activity_receipt_id",
        "amount_state", "amount", "currency", "amount_basis", "amount_receipt_id",
    )
    seen = set()
    receipts = []
    review_ids = []
    for index, raw in enumerate(document["deals"]):
        _exact_fields(raw, fields, f"deals[{index}]")
        missing = [field for field in fields if field not in raw]
        if missing:
            raise ValueError(f"deals[{index}] missing: " + ", ".join(missing))
        deal_id = _pseudonymous(raw["deal_id"], f"deals[{index}].deal_id")
        if deal_id in seen:
            raise ValueError(f"duplicate deal_id: {deal_id}")
        seen.add(deal_id)
        account_id = _pseudonymous(raw["account_id"], f"{deal_id}.account_id")
        owner_id = _pseudonymous(raw["owner_id"], f"{deal_id}.owner_id")
        membership = _enum(raw["population_membership_status"], MEMBERSHIP_STATES, f"{deal_id}.population_membership_status")
        cutoff_text, cutoff_dt = _timestamp(raw["evidence_cutoff"], f"{deal_id}.evidence_cutoff")
        current_stage_id = _text(raw["current_stage_id"], f"{deal_id}.current_stage_id")
        stage_entry_state = _enum(raw["stage_entry_state"], LANE_STATES, f"{deal_id}.stage_entry_state")
        close_date_state = _enum(raw["close_date_state"], LANE_STATES, f"{deal_id}.close_date_state")
        activity_population_state = _enum(raw["activity_population_state"], ACTIVITY_POPULATION_STATES, f"{deal_id}.activity_population_state")
        activity_state = _enum(raw["activity_state"], ACTIVITY_STATES, f"{deal_id}.activity_state")
        amount_state = _enum(raw["amount_state"], LANE_STATES, f"{deal_id}.amount_state")
        binding_conflict = any((
            raw["source_id"] != policy["source_id"], raw["source_version"] != policy["source_version"],
            raw["schema_id"] != policy["schema_id"], raw["schema_version"] != policy["schema_version"],
            raw["pipeline_id"] != policy["pipeline_id"], cutoff_dt > policy["cutoff_dt"],
            cutoff_dt.date() < policy["effective_date_value"],
        ))
        current_binding_ok = not binding_conflict
        stage_source_ok = raw["stage_history_source_id"] == policy["stage_history_source_id"] and raw["stage_history_source_version"] == policy["stage_history_source_version"]
        activity_source_ok = (
            raw["activity_source_id"] == policy["activity_source_id"]
            and raw["activity_source_version"] == policy["activity_source_version"]
            and raw["activity_occurrence_rule_id"] == policy["activity_occurrence_rule_id"]
            and raw["activity_association_rule_id"] == policy["activity_association_rule_id"]
        )
        review_reasons = []
        if membership != "VERIFIED_MEMBER":
            review_reasons.append("POPULATION_MEMBERSHIP_REVIEW")
        if binding_conflict:
            review_reasons.append("SOURCE_POLICY_CONFLICT")
        if current_stage_id not in policy["open_stage_ids"]:
            review_reasons.append("CURRENT_STAGE_NOT_OPEN")

        stage_entered_text = None
        stage_elapsed_days = None
        stage_threshold = policy["stage_threshold_days"].get(current_stage_id)
        stage_result = "STAGE_ENTRY_UNAVAILABLE"
        if stage_entry_state == "CONFLICT":
            if raw["current_stage_entered_at"] is not None:
                raise ValueError(f"{deal_id} conflicting stage entry must have null timestamp")
            stage_result = "STAGE_HISTORY_CONFLICT"
            review_reasons.append(stage_result)
        elif stage_entry_state == "UNAVAILABLE":
            if raw["current_stage_entered_at"] is not None:
                raise ValueError(f"{deal_id} unavailable stage entry must have null timestamp")
            review_reasons.append(stage_result)
        else:
            stage_entered_text, stage_entered_dt = _timestamp(raw["current_stage_entered_at"], f"{deal_id}.current_stage_entered_at")
            if stage_entered_dt > cutoff_dt:
                raise ValueError(f"{deal_id} stage entry is after evidence cutoff")
            if not stage_source_ok:
                stage_result = "STAGE_HISTORY_SOURCE_CONFLICT"
                review_reasons.append(stage_result)
            elif not current_binding_ok:
                stage_result = "CURRENT_STATE_SOURCE_CONFLICT"
                review_reasons.append(stage_result)
            elif stage_threshold is None:
                stage_result = "STAGE_THRESHOLD_UNAVAILABLE"
                review_reasons.append(stage_result)
            else:
                stage_elapsed_days = (cutoff_dt - stage_entered_dt).days
                if stage_elapsed_days > stage_threshold:
                    stage_result = "THRESHOLD_EXCEEDED"
                    review_reasons.append("STAGE_THRESHOLD_EXCEEDED")
                else:
                    stage_result = "WITHIN_THRESHOLD"

        close_date_text = None
        close_result = "DATE_UNAVAILABLE"
        if close_date_state == "CONFLICT":
            if raw["close_date"] is not None:
                raise ValueError(f"{deal_id} conflicting close date must be null")
            close_result = "DATE_CONFLICT"
            review_reasons.append(close_result)
        elif close_date_state == "UNAVAILABLE":
            if raw["close_date"] is not None:
                raise ValueError(f"{deal_id} unavailable close date must be null")
            review_reasons.append(close_result)
        else:
            close_date_text, close_value = _date(raw["close_date"], f"{deal_id}.close_date")
            if not current_binding_ok:
                close_result = "CURRENT_STATE_SOURCE_CONFLICT"
                review_reasons.append(close_result)
            else:
                close_result = "DATE_BEFORE_CUTOFF" if close_value < cutoff_dt.date() else "DATE_ON_OR_AFTER_CUTOFF"
                if close_result == "DATE_BEFORE_CUTOFF":
                    review_reasons.append(close_result)

        activity_text = None
        activity_elapsed_days = None
        activity_type = None
        activity_result = activity_state
        if activity_population_state != "COMPLETE":
            activity_result = "ACTIVITY_EVIDENCE_UNAVAILABLE"
            review_reasons.append(activity_result)
            if raw["last_activity_at"] is not None or raw["last_activity_type"] is not None:
                raise ValueError(f"{deal_id} incomplete activity population cannot provide last activity")
        elif activity_state == "AVAILABLE":
            activity_text, activity_dt = _timestamp(raw["last_activity_at"], f"{deal_id}.last_activity_at")
            activity_type = _text(raw["last_activity_type"], f"{deal_id}.last_activity_type")
            if activity_type not in policy["qualifying_activity_types"]:
                raise ValueError(f"{deal_id} activity type is not policy-qualified")
            if activity_dt > cutoff_dt:
                raise ValueError(f"{deal_id} activity occurs after evidence cutoff")
            if not activity_source_ok:
                activity_result = "ACTIVITY_SOURCE_CONFLICT"
                review_reasons.append(activity_result)
            else:
                activity_elapsed_days = (cutoff_dt - activity_dt).days
                if activity_elapsed_days > policy["activity_threshold_days"]:
                    activity_result = "THRESHOLD_EXCEEDED"
                    review_reasons.append("ACTIVITY_THRESHOLD_EXCEEDED")
                else:
                    activity_result = "WITHIN_THRESHOLD"
        else:
            if raw["last_activity_at"] is not None or raw["last_activity_type"] is not None:
                raise ValueError(f"{deal_id} non-available activity must have null occurrence fields")
            if activity_state in {"EVIDENCE_UNAVAILABLE", "CONFLICT"}:
                review_reasons.append("ACTIVITY_EVIDENCE_UNAVAILABLE" if activity_state == "EVIDENCE_UNAVAILABLE" else "ACTIVITY_CONFLICT")
            else:
                review_reasons.append("NO_QUALIFYING_ACTIVITY_RECORDED")

        amount_value = None
        amount_result = amount_state
        if amount_state == "AVAILABLE":
            amount_value = _decimal(raw["amount"], f"{deal_id}.amount")
            if not current_binding_ok:
                amount_result = "CURRENT_STATE_SOURCE_CONFLICT"
                review_reasons.append(amount_result)
            elif raw["currency"] != policy["currency"]:
                amount_result = "CURRENCY_CONFLICT"
                review_reasons.append(amount_result)
            elif raw["amount_basis"] != policy["amount_basis"]:
                amount_result = "AMOUNT_BASIS_CONFLICT"
                review_reasons.append(amount_result)
        else:
            if raw["amount"] is not None:
                raise ValueError(f"{deal_id} non-available amount must be null")
            amount_result = "AMOUNT_CONFLICT" if amount_state == "CONFLICT" else "AMOUNT_UNAVAILABLE"
            review_reasons.append(amount_result)

        receipt = {
            "deal_id": deal_id,
            "account_id": account_id,
            "owner_id": owner_id,
            "population_membership_status": membership,
            "population_membership_receipt_id": _text(raw["population_membership_receipt_id"], f"{deal_id}.population_membership_receipt_id"),
            "source_receipt": {
                "source_id": _text(raw["source_id"], f"{deal_id}.source_id"), "source_version": _text(raw["source_version"], f"{deal_id}.source_version"),
                "schema_id": _text(raw["schema_id"], f"{deal_id}.schema_id"), "schema_version": _text(raw["schema_version"], f"{deal_id}.schema_version"),
                "extraction_id": _text(raw["extraction_id"], f"{deal_id}.extraction_id"), "evidence_cutoff": cutoff_text,
            },
            "current_state_lane": {"pipeline_id": _text(raw["pipeline_id"], f"{deal_id}.pipeline_id"), "current_stage_id": current_stage_id, "receipt_id": _text(raw["current_state_receipt_id"], f"{deal_id}.current_state_receipt_id")},
            "stage_lane": {
                "state": stage_entry_state, "current_stage_entered_at": stage_entered_text,
                "elapsed_days": stage_elapsed_days, "threshold_days": stage_threshold, "result": stage_result,
                "source_id": _text(raw["stage_history_source_id"], f"{deal_id}.stage_history_source_id"),
                "source_version": _text(raw["stage_history_source_version"], f"{deal_id}.stage_history_source_version"),
                "receipt_id": _text(raw["stage_history_receipt_id"], f"{deal_id}.stage_history_receipt_id"),
            },
            "close_date_lane": {"state": close_date_state, "close_date": close_date_text, "result": close_result, "receipt_id": _text(raw["close_date_receipt_id"], f"{deal_id}.close_date_receipt_id")},
            "activity_lane": {
                "population_state": activity_population_state,
                "population_receipt_id": _text(raw["activity_population_receipt_id"], f"{deal_id}.activity_population_receipt_id"),
                "state": activity_state, "last_activity_at": activity_text, "activity_type": activity_type,
                "elapsed_days": activity_elapsed_days, "threshold_days": policy["activity_threshold_days"], "result": activity_result,
                "source_id": _text(raw["activity_source_id"], f"{deal_id}.activity_source_id"),
                "source_version": _text(raw["activity_source_version"], f"{deal_id}.activity_source_version"),
                "occurrence_rule_id": _text(raw["activity_occurrence_rule_id"], f"{deal_id}.activity_occurrence_rule_id"),
                "association_rule_id": _text(raw["activity_association_rule_id"], f"{deal_id}.activity_association_rule_id"),
                "receipt_id": _text(raw["activity_receipt_id"], f"{deal_id}.activity_receipt_id"),
            },
            "amount_lane": {
                "state": amount_state, "amount": str(amount_value) if amount_value is not None else None,
                "currency": _text(raw["currency"], f"{deal_id}.currency"), "amount_basis": _text(raw["amount_basis"], f"{deal_id}.amount_basis"),
                "result": amount_result, "receipt_id": _text(raw["amount_receipt_id"], f"{deal_id}.amount_receipt_id"),
            },
            "review_reasons": sorted(set(review_reasons)),
        }
        receipts.append(receipt)
        if receipt["review_reasons"]:
            review_ids.append(deal_id)

    receipts.sort(key=lambda item: item["deal_id"])
    result = _base_result(policy, population, "READY_FOR_HUMAN_REVIEW", "DEAL_EVIDENCE_REVIEW_AVAILABLE", receipts)
    result["review_deal_ids"] = sorted(review_ids)
    return result


def render_review_output(result):
    return "```json\n" + json.dumps(result, indent=2, sort_keys=True) + "\n```\n" + result["boundary"]


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        raise SystemExit("usage: deal_evidence.py [input.json]")
    raw = Path(args[0]).read_text(encoding="utf-8") if args else sys.stdin.read()
    sys.stdout.write(render_review_output(review_deals(json.loads(raw))))


if __name__ == "__main__":
    main()
