#!/usr/bin/env python3
"""Deterministic pseudonymous event follow-up-plan evidence review."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_event_followup_plan_evidence_review"
SOURCE_KIND = "customer-supplied-pseudonymous-event-followup-plan"
ELIGIBLE = "eligible"
UNRESOLVED = {
    "unauthorized": "UNAUTHORIZED",
    "suppressed": "SUPPRESSED",
    "conflicting": "EVIDENCE_CONFLICT",
    "missing": "EVIDENCE_MISSING",
}
PRECEDENCE = ("unauthorized", "suppressed", "conflicting", "missing")
REQUIRED_PROHIBITIONS = {
    "alert", "behavioral-profiling", "buying-stage", "candidate-contact-detail",
    "confidence-score", "contact-execution", "conversion-prediction", "crm-read",
    "crm-write", "direct-identifier", "downstream-decision", "enrichment-execution",
    "fallback-routing", "firmographic-scoring", "fuzzy-identity", "intent-inference",
    "interest-score", "message-send", "personal-data", "priority-ranking", "publication",
    "route-selection", "scheduling", "tier-assignment", "workflow-enrollment",
}
BOUNDARY = "NO IDENTITY, PROFILING, PRIORITY, ROUTE CHOICE, CONTACT, CRM, WORKFLOW, OR DOWNSTREAM ACTION"
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
        "approved_purpose", "owner_role_id", "human_reviewer_role_id",
        "operations_approval_receipt_id", "security_review_receipt_id", "privacy_review_receipt_id",
        "legal_review_receipt_id", "lawful_basis_receipt_id", "collection_notice_receipt_id",
        "direct_marketing_notice_receipt_id", "objection_path_receipt_id",
        "suppression_policy_receipt_id", "correction_access_path_receipt_id",
        "recipient_policy_receipt_id", "retention_policy_receipt_id", "followup_policy_receipt_id",
        "allowed_recipient_role_ids", "prohibited_uses", "source_bindings", "event_contracts",
        "route_contracts",
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
    recipients = _ids(row["allowed_recipient_role_ids"], "policy.allowed_recipient_role_ids", "role-")
    if not recipients:
        raise ValueError("at least one recipient role is required")
    owner_role_id = _id(row["owner_role_id"], "policy.owner_role_id", "role-")
    human_reviewer_role_id = _id(row["human_reviewer_role_id"], "policy.human_reviewer_role_id", "role-")
    if human_reviewer_role_id not in recipients:
        raise ValueError("human reviewer must be an allowed recipient")
    receipt_fields = (
        "operations_approval_receipt_id", "security_review_receipt_id", "privacy_review_receipt_id",
        "legal_review_receipt_id", "lawful_basis_receipt_id", "collection_notice_receipt_id",
        "direct_marketing_notice_receipt_id", "objection_path_receipt_id",
        "suppression_policy_receipt_id", "correction_access_path_receipt_id",
        "recipient_policy_receipt_id", "retention_policy_receipt_id", "followup_policy_receipt_id",
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
        item = _obj(raw_binding, f"source_bindings[{index}]")
        _keys(item, binding_fields, f"source_bindings[{index}]")
        source_id = _id(item["source_id"], "binding.source_id", "source-")
        source_version = _id(item["source_version"], "binding.source_version")
        if item["source_kind"] != SOURCE_KIND:
            raise ValueError("source kind is not allowed")
        auth_effective_text, auth_effective = _time(item["authorization_effective_at"], "binding.authorization_effective_at")
        auth_expires_text, auth_expires = _optional_time(item["authorization_expires_at"], "binding.authorization_expires_at")
        if auth_effective > cutoff or (auth_expires is not None and auth_expires < cutoff):
            raise ValueError("source authorization does not cover cutoff")
        key = (source_id, source_version)
        if key in bindings:
            raise ValueError("duplicate source binding")
        bindings[key] = {
            "source_id": source_id, "source_version": source_version, "source_kind": SOURCE_KIND,
            "schema_id": _id(item["schema_id"], "binding.schema_id"),
            "schema_version": _id(item["schema_version"], "binding.schema_version"),
            "authorization_receipt_id": _reserve(receipts, item["authorization_receipt_id"], "binding.authorization_receipt_id"),
            "authorization_effective_at": auth_effective_text, "authorization_expires_at": auth_expires_text,
            "query_receipt_id": _reserve(receipts, item["query_receipt_id"], "binding.query_receipt_id"),
            "page_receipt_id": _reserve(receipts, item["page_receipt_id"], "binding.page_receipt_id"),
            "pseudonymization_receipt_id": _reserve(receipts, item["pseudonymization_receipt_id"], "binding.pseudonymization_receipt_id"),
        }
    if not bindings:
        raise ValueError("at least one source binding is required")

    event_fields = {
        "event_id", "event_version", "source_id", "source_version", "starts_at", "ends_at",
        "event_receipt_id", "participation_definition_receipt_id", "capture_policy_receipt_id",
    }
    events: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw_event in enumerate(_arr(row["event_contracts"], "policy.event_contracts")):
        item = _obj(raw_event, f"event_contracts[{index}]")
        _keys(item, event_fields, f"event_contracts[{index}]")
        source_key = (_id(item["source_id"], "event.source_id", "source-"), _id(item["source_version"], "event.source_version"))
        if source_key not in bindings:
            raise ValueError("event source is not approved")
        key = (_id(item["event_id"], "event.event_id", "event-"), _id(item["event_version"], "event.event_version"))
        if key in events:
            raise ValueError("duplicate event contract")
        starts_text, starts = _time(item["starts_at"], "event.starts_at")
        ends_text, ends = _time(item["ends_at"], "event.ends_at")
        if starts < effective or starts > ends or ends > cutoff:
            raise ValueError("event window is outside the evidence policy")
        events[key] = {
            "event_id": key[0], "event_version": key[1], "source_key": source_key,
            "starts_at": starts_text, "ends_at": ends_text,
            "event_receipt_id": _reserve(receipts, item["event_receipt_id"], "event.event_receipt_id"),
            "participation_definition_receipt_id": _reserve(receipts, item["participation_definition_receipt_id"], "event.participation_definition_receipt_id"),
            "capture_policy_receipt_id": _reserve(receipts, item["capture_policy_receipt_id"], "event.capture_policy_receipt_id"),
        }
    if not events:
        raise ValueError("at least one event contract is required")

    route_fields = {
        "route_id", "route_version", "event_id", "event_version", "owner_role_id", "channel_id",
        "authorization_effective_at", "authorization_expires_at", "window_opens_at", "window_closes_at",
        "route_receipt_id", "authorization_receipt_id", "channel_policy_receipt_id",
        "owner_policy_receipt_id", "timing_policy_receipt_id",
    }
    routes: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw_route in enumerate(_arr(row["route_contracts"], "policy.route_contracts")):
        item = _obj(raw_route, f"route_contracts[{index}]")
        _keys(item, route_fields, f"route_contracts[{index}]")
        key = (_id(item["route_id"], "route.route_id", "route-"), _id(item["route_version"], "route.route_version"))
        if key in routes:
            raise ValueError("duplicate route contract")
        event_key = (_id(item["event_id"], "route.event_id", "event-"), _id(item["event_version"], "route.event_version"))
        if event_key not in events:
            raise ValueError("route event is not approved")
        owner_role_id = _id(item["owner_role_id"], "route.owner_role_id", "role-")
        if owner_role_id not in recipients:
            raise ValueError("route owner is not an allowed recipient")
        auth_effective_text, auth_effective = _time(item["authorization_effective_at"], "route.authorization_effective_at")
        auth_expires_text, auth_expires = _optional_time(item["authorization_expires_at"], "route.authorization_expires_at")
        opens_text, opens = _time(item["window_opens_at"], "route.window_opens_at")
        closes_text, closes = _time(item["window_closes_at"], "route.window_closes_at")
        if auth_effective > opens or opens < cutoff or opens > closes:
            raise ValueError("route timing is outside the policy evidence window")
        if auth_expires is not None and auth_expires < closes:
            raise ValueError("route authorization does not cover its window")
        if expires is not None and closes > expires:
            raise ValueError("route window exceeds policy expiry")
        routes[key] = {
            "route_id": key[0], "route_version": key[1], "event_key": event_key,
            "owner_role_id": owner_role_id, "channel_id": _id(item["channel_id"], "route.channel_id", "channel-"),
            "authorization_effective_at": auth_effective_text, "authorization_expires_at": auth_expires_text,
            "window_opens_at": opens_text, "window_closes_at": closes_text,
            "route_receipt_id": _reserve(receipts, item["route_receipt_id"], "route.route_receipt_id"),
            "authorization_receipt_id": _reserve(receipts, item["authorization_receipt_id"], "route.authorization_receipt_id"),
            "channel_policy_receipt_id": _reserve(receipts, item["channel_policy_receipt_id"], "route.channel_policy_receipt_id"),
            "owner_policy_receipt_id": _reserve(receipts, item["owner_policy_receipt_id"], "route.owner_policy_receipt_id"),
            "timing_policy_receipt_id": _reserve(receipts, item["timing_policy_receipt_id"], "route.timing_policy_receipt_id"),
        }
    if not routes:
        raise ValueError("at least one route contract is required")
    policy = {
        "policy_id": _id(row["policy_id"], "policy.policy_id", "policy-"),
        "policy_version": _id(row["policy_version"], "policy.policy_version"),
        "effective_at": effective_text, "expires_at": expires_text, "cutoff_at": cutoff_text,
        "timezone": timezone_name, "approved_purpose": PURPOSE,
        "owner_role_id": owner_role_id, "human_reviewer_role_id": human_reviewer_role_id,
        **dict(zip(receipt_fields, governance)), "allowed_recipient_role_ids": sorted(recipients),
        "prohibited_uses": sorted(prohibited),
    }
    return policy, bindings, events, routes, receipts


def review_event_plan_evidence(document: Any) -> dict[str, Any]:
    root = _obj(document, "document")
    _keys(root, {"review_declaration", "policy", "source_populations", "followup_plan"}, "document")
    declaration = _obj(root["review_declaration"], "review_declaration")
    declaration_fields = {
        "review_id", "policy_id", "policy_version", "event_id", "event_version",
        "reviewed_at", "recipient_role_id", "review_authorization_receipt_id", "participant_ids",
    }
    _keys(declaration, declaration_fields, "review_declaration")
    review_id = _id(declaration["review_id"], "declaration.review_id", "review-")
    reviewed_text, reviewed = _time(declaration["reviewed_at"], "declaration.reviewed_at")
    participants = _ids(declaration["participant_ids"], "declaration.participant_ids", "participant-")
    if not participants:
        raise ValueError("participant population cannot be empty")
    policy, bindings, events, routes, receipts = _policy(root["policy"])
    if declaration["policy_id"] != policy["policy_id"] or declaration["policy_version"] != policy["policy_version"]:
        raise ValueError("declaration conflicts with policy")
    cutoff = _time(policy["cutoff_at"], "policy.cutoff_at")[1]
    effective = _time(policy["effective_at"], "policy.effective_at")[1]
    expires = _optional_time(policy["expires_at"], "policy.expires_at")[1]
    if reviewed < cutoff or reviewed < effective or (expires is not None and reviewed > expires):
        raise ValueError("review time is outside policy window")
    recipient = _id(declaration["recipient_role_id"], "declaration.recipient_role_id", "role-")
    if recipient not in policy["allowed_recipient_role_ids"] or recipient != policy["human_reviewer_role_id"]:
        raise ValueError("recipient is not the approved human reviewer")
    review_authorization_receipt = _reserve(receipts, declaration["review_authorization_receipt_id"], "declaration.review_authorization_receipt_id")
    event_key = (_id(declaration["event_id"], "declaration.event_id", "event-"), _id(declaration["event_version"], "declaration.event_version"))
    if event_key not in events:
        raise ValueError("declaration event is not approved")
    event = events[event_key]

    population_fields = {"source_id", "source_version", "population_receipt_id", "complete", "plan_receipt_ids"}
    allowed_receipts: dict[tuple[str, str], set[str]] = {}
    for index, raw_population in enumerate(_arr(root["source_populations"], "source_populations")):
        item = _obj(raw_population, f"source_populations[{index}]")
        _keys(item, population_fields, f"source_populations[{index}]")
        source_key = (_id(item["source_id"], "population.source_id", "source-"), _id(item["source_version"], "population.source_version"))
        if source_key not in bindings or source_key in allowed_receipts or item["complete"] is not True:
            raise ValueError("population source is unapproved, duplicated, or incomplete")
        _reserve(receipts, item["population_receipt_id"], "population.population_receipt_id")
        plan_receipts = set(_ids(item["plan_receipt_ids"], "population.plan_receipt_ids", "receipt-"))
        if not plan_receipts:
            raise ValueError("source population cannot be empty")
        allowed_receipts[source_key] = plan_receipts
    required_sources = {event["source_key"]}
    if set(allowed_receipts) != required_sources:
        raise ValueError("source populations must exactly match the declared event source")
    flattened = [receipt for group in allowed_receipts.values() for receipt in group]
    if len(flattened) != len(set(flattened)) or receipts.intersection(flattened):
        raise ValueError("plan receipts must be globally unique")
    receipts.update(flattened)

    plan_fields = {
        "participant_id", "source_id", "source_version", "plan_receipt_id", "participation_state",
        "participation_state_receipt_id", "route_id", "route_version", "owner_role_id", "channel_id",
        "assignment_receipt_id", "planned_at", "observed_at", "captured_at",
    }
    rows: dict[str, dict[str, Any]] = {}
    seen_plan_receipts: set[str] = set()
    event_starts = _time(event["starts_at"], "event.starts_at")[1]
    event_ends = _time(event["ends_at"], "event.ends_at")[1]
    for index, raw_plan in enumerate(_arr(root["followup_plan"], "followup_plan")):
        item = _obj(raw_plan, f"followup_plan[{index}]")
        _keys(item, plan_fields, f"followup_plan[{index}]")
        participant_id = _id(item["participant_id"], "plan.participant_id", "participant-")
        if participant_id not in participants or participant_id in rows:
            raise ValueError("plan participant is undeclared or duplicated")
        source_key = (_id(item["source_id"], "plan.source_id", "source-"), _id(item["source_version"], "plan.source_version"))
        if source_key != event["source_key"]:
            raise ValueError("plan source conflicts with event source")
        plan_receipt = _id(item["plan_receipt_id"], "plan.plan_receipt_id", "receipt-")
        if plan_receipt in seen_plan_receipts or plan_receipt not in allowed_receipts[source_key]:
            raise ValueError("plan receipt is duplicate or absent from its population")
        seen_plan_receipts.add(plan_receipt)
        observed_text, observed = _time(item["observed_at"], "plan.observed_at")
        captured_text, captured = _time(item["captured_at"], "plan.captured_at")
        if observed < event_starts or observed > event_ends or observed > captured or captured > cutoff:
            raise ValueError("plan observation time is outside the event evidence window")
        binding = bindings[source_key]
        auth_effective = _time(binding["authorization_effective_at"], "binding.authorization_effective_at")[1]
        auth_expires = _optional_time(binding["authorization_expires_at"], "binding.authorization_expires_at")[1]
        if captured < auth_effective or (auth_expires is not None and captured > auth_expires):
            raise ValueError("source authorization does not cover plan capture")
        state = item["participation_state"]
        if state not in {ELIGIBLE, *UNRESOLVED}:
            raise ValueError("participation state is not allowed")
        state_receipt = _reserve(receipts, item["participation_state_receipt_id"], "plan.participation_state_receipt_id")
        route_key = None
        owner_role_id = None
        channel_id = None
        assignment_receipt = None
        planned_text = None
        planned = None
        if state == ELIGIBLE:
            route_key = (_id(item["route_id"], "plan.route_id", "route-"), _id(item["route_version"], "plan.route_version"))
            owner_role_id = _id(item["owner_role_id"], "plan.owner_role_id", "role-")
            channel_id = _id(item["channel_id"], "plan.channel_id", "channel-")
            assignment_receipt = _reserve(receipts, item["assignment_receipt_id"], "plan.assignment_receipt_id")
            planned_text, planned = _time(item["planned_at"], "plan.planned_at")
            if planned < reviewed or planned < captured:
                raise ValueError("planned time precedes review or capture")
        elif any(item[field] is not None for field in ("route_id", "route_version", "owner_role_id", "channel_id", "assignment_receipt_id", "planned_at")):
            raise ValueError("unresolved plan cannot carry a route assignment")
        rows[participant_id] = {
            "participant_id": participant_id, "source_id": source_key[0], "source_version": source_key[1],
            "plan_receipt_id": plan_receipt, "participation_state": state,
            "participation_state_receipt_id": state_receipt, "route_key": route_key,
            "owner_role_id": owner_role_id, "channel_id": channel_id,
            "assignment_receipt_id": assignment_receipt, "planned_at": planned_text,
            "planned_time": planned, "observed_at": observed_text, "captured_at": captured_text,
        }
    if set(rows) != set(participants) or seen_plan_receipts != set(flattened):
        raise ValueError("follow-up plan and complete population do not reconcile")

    results = []
    states = []
    for participant_id in sorted(rows):
        row = rows[participant_id]
        if row["participation_state"] in UNRESOLVED:
            state = UNRESOLVED[row["participation_state"]]
            route_receipt = None
        else:
            route = routes.get(row["route_key"])
            matched = route is not None
            if route is not None:
                auth_effective = _time(route["authorization_effective_at"], "route.authorization_effective_at")[1]
                auth_expires = _optional_time(route["authorization_expires_at"], "route.authorization_expires_at")[1]
                opens = _time(route["window_opens_at"], "route.window_opens_at")[1]
                closes = _time(route["window_closes_at"], "route.window_closes_at")[1]
                matched = matched and route["event_key"] == event_key
                matched = matched and route["owner_role_id"] == row["owner_role_id"]
                matched = matched and route["channel_id"] == row["channel_id"]
                matched = matched and auth_effective <= row["planned_time"] <= closes
                matched = matched and opens <= row["planned_time"]
                matched = matched and (auth_expires is None or row["planned_time"] <= auth_expires)
            state = "CUSTOMER_EVENT_PLAN_EVIDENCE_MATCHED" if matched else "CUSTOMER_EVENT_PLAN_EVIDENCE_NOT_MATCHED"
            route_receipt = None if route is None else {
                "route_id": route["route_id"], "route_version": route["route_version"],
                "owner_role_id": route["owner_role_id"], "channel_id": route["channel_id"],
                "authorization_effective_at": route["authorization_effective_at"],
                "authorization_expires_at": route["authorization_expires_at"],
                "window_opens_at": route["window_opens_at"], "window_closes_at": route["window_closes_at"],
                "route_receipt_id": route["route_receipt_id"],
                "authorization_receipt_id": route["authorization_receipt_id"],
                "channel_policy_receipt_id": route["channel_policy_receipt_id"],
                "owner_policy_receipt_id": route["owner_policy_receipt_id"],
                "timing_policy_receipt_id": route["timing_policy_receipt_id"],
            }
        states.append(state)
        results.append({
            "participant_id": row["participant_id"], "evidence_state": state,
            "plan_receipt_id": row["plan_receipt_id"],
            "participation_state_receipt_id": row["participation_state_receipt_id"],
            "source_id": row["source_id"], "source_version": row["source_version"],
            "observed_at": row["observed_at"], "captured_at": row["captured_at"],
            "assignment_receipt_id": row["assignment_receipt_id"], "planned_at": row["planned_at"],
            "route_receipt": route_receipt,
        })
    review_state = "CUSTOMER_EVENT_PLAN_EVIDENCE_MATCHED"
    for unresolved in PRECEDENCE:
        mapped = UNRESOLVED[unresolved]
        if mapped in states:
            review_state = mapped
            break
    else:
        if "CUSTOMER_EVENT_PLAN_EVIDENCE_NOT_MATCHED" in states:
            review_state = "CUSTOMER_EVENT_PLAN_EVIDENCE_NOT_MATCHED"
    return {
        "review_id": review_id, "reviewed_at": reviewed_text, "recipient_role_id": recipient,
        "review_authorization_receipt_id": review_authorization_receipt,
        "evidence_state": review_state,
        "policy_receipt": {
            "policy_id": policy["policy_id"], "policy_version": policy["policy_version"],
            "cutoff_at": policy["cutoff_at"], "timezone": policy["timezone"],
            "operations_approval_receipt_id": policy["operations_approval_receipt_id"],
            "security_review_receipt_id": policy["security_review_receipt_id"],
            "privacy_review_receipt_id": policy["privacy_review_receipt_id"],
            "legal_review_receipt_id": policy["legal_review_receipt_id"],
            "lawful_basis_receipt_id": policy["lawful_basis_receipt_id"],
            "collection_notice_receipt_id": policy["collection_notice_receipt_id"],
            "direct_marketing_notice_receipt_id": policy["direct_marketing_notice_receipt_id"],
            "objection_path_receipt_id": policy["objection_path_receipt_id"],
            "suppression_policy_receipt_id": policy["suppression_policy_receipt_id"],
            "correction_access_path_receipt_id": policy["correction_access_path_receipt_id"],
            "recipient_policy_receipt_id": policy["recipient_policy_receipt_id"],
            "retention_policy_receipt_id": policy["retention_policy_receipt_id"],
            "followup_policy_receipt_id": policy["followup_policy_receipt_id"],
        },
        "event_receipt": {
            "event_id": event["event_id"], "event_version": event["event_version"],
            "starts_at": event["starts_at"], "ends_at": event["ends_at"],
            "event_receipt_id": event["event_receipt_id"],
            "participation_definition_receipt_id": event["participation_definition_receipt_id"],
            "capture_policy_receipt_id": event["capture_policy_receipt_id"],
        },
        "participant_plan_reviews": results,
        "interpretation_boundary": BOUNDARY,
        "action_authorization": {
            "contact_authorized": False, "outreach_authorized": False,
            "message_authorized": False, "route_selection_authorized": False,
            "crm_write_authorized": False, "workflow_enrollment_authorized": False,
            "enrichment_authorized": False, "scoring_authorized": False,
            "ranking_authorized": False, "alert_authorized": False,
            "scheduling_authorized": False, "publication_authorized": False,
            "downstream_decision_authorized": False,
        },
    }


def render_review_output(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n\n"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: event_plan_evidence.py INPUT.json")
    document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sys.stdout.write(render_review_output(review_event_plan_evidence(document)))


if __name__ == "__main__":
    main()
