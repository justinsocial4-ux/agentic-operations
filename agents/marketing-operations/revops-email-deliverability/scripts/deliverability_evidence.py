#!/usr/bin/env python3
"""Deterministic source-bound email deliverability observation review."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_email_deliverability_observation_evidence_review"
SOURCE_KIND = "customer-supplied-pseudonymous-deliverability-observation"
LANE_KINDS = {
    "authentication-ratio", "blocklist-state", "bounce-ratio", "complaint-ratio",
    "delivery-error-ratio", "placement-test-ratio", "reputation-code",
    "sender-requirement-state",
}
VALUE_KINDS = {"boolean", "code", "count", "percentage", "ratio"}
LANE_VALUE_KINDS = {
    "authentication-ratio": {"percentage", "ratio"},
    "blocklist-state": {"boolean"},
    "bounce-ratio": {"percentage", "ratio"},
    "complaint-ratio": {"percentage", "ratio"},
    "delivery-error-ratio": {"percentage", "ratio"},
    "placement-test-ratio": {"percentage", "ratio"},
    "reputation-code": {"code"},
    "sender-requirement-state": {"boolean"},
}
UNRESOLVED = {
    "unauthorized": "UNAUTHORIZED", "suppressed": "SUPPRESSED",
    "conflicting": "EVIDENCE_CONFLICT", "missing": "EVIDENCE_MISSING",
}
PRECEDENCE = ("unauthorized", "suppressed", "conflicting", "missing")
REQUIRED_PROHIBITIONS = {
    "alert", "benchmark-substitution", "composite-score", "confidence-score",
    "content-diagnosis", "cross-provider-comparison", "delisting-action",
    "dns-change", "downstream-decision", "health-label", "identity-data",
    "legal-conclusion", "message-content", "message-send", "personal-data",
    "publication", "remediation", "reputation-inference", "revenue-inference",
    "root-cause", "scheduling", "send-change", "system-write", "workflow-action",
}
BOUNDARY = "NO SCORE, COMPARISON, CAUSE, REMEDIATION, CONFIGURATION, SEND, ALERT, WRITE, OR DOWNSTREAM ACTION"
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_./:+-]*$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
DEC_RE = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?$")
FORBIDDEN_VALUE_CODES = {
    "bad", "critical", "excellent", "fair", "good", "healthy", "high", "low",
    "medium", "normal", "poor", "safe", "severe", "unhealthy", "urgent",
}


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


def _value(value: Any, kind: str, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    if kind in {"count", "percentage", "ratio"}:
        if not DEC_RE.fullmatch(value):
            raise ValueError(f"{label} must be a nonnegative canonical decimal string")
        integer_part, separator, fractional_part = value.partition(".")
        if len(integer_part) > 18 or (separator and (not fractional_part or len(fractional_part) > 9)):
            raise ValueError(f"{label} exceeds numeric precision bounds")
        try:
            number = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"{label} is not decimal") from exc
        if kind == "count" and number != number.to_integral_value():
            raise ValueError(f"{label} count must be integral")
        if kind in {"percentage", "ratio"} and number > Decimal("100"):
            raise ValueError(f"{label} exceeds its bounded scale")
        return value
    token = _token(value, label)
    if token.lower() in FORBIDDEN_VALUE_CODES:
        raise ValueError(f"{label} uses a forbidden interpretive code")
    if kind == "boolean" and token not in {"true", "false"}:
        raise ValueError(f"{label} boolean must be true or false")
    if kind == "code" and not token.startswith("source-code-"):
        raise ValueError(f"{label} code must be pseudonymous and source-bound")
    return token


def _policy(raw: Any) -> tuple[dict[str, Any], dict[str, dict[str, Any]], set[str], datetime]:
    row = _obj(raw, "policy")
    fields = {
        "policy_id", "policy_version", "effective_at", "expires_at", "cutoff_at", "timezone",
        "approved_purpose", "owner_role_id", "human_reviewer_role_id", "actual_recipient_role_id",
        "review_authorization_effective_at", "review_authorization_expires_at",
        "operations_approval_receipt_id", "security_review_receipt_id", "privacy_review_receipt_id",
        "legal_review_receipt_id", "collection_policy_receipt_id", "recipient_policy_receipt_id",
        "retention_policy_receipt_id", "review_authorization_receipt_id",
        "pseudonymization_policy_receipt_id", "source_separation_policy_receipt_id",
        "allowed_recipient_role_ids", "prohibited_uses", "lane_contracts",
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
    owner = _id(row["owner_role_id"], "policy.owner_role_id", "role-")
    reviewer = _id(row["human_reviewer_role_id"], "policy.human_reviewer_role_id", "role-")
    actual = _id(row["actual_recipient_role_id"], "policy.actual_recipient_role_id", "role-")
    if reviewer not in recipients or actual != reviewer:
        raise ValueError("actual recipient must equal an allowed human reviewer")
    receipts: set[str] = set()
    receipt_fields = (
        "operations_approval_receipt_id", "security_review_receipt_id", "privacy_review_receipt_id",
        "legal_review_receipt_id", "collection_policy_receipt_id", "recipient_policy_receipt_id",
        "retention_policy_receipt_id", "review_authorization_receipt_id",
        "pseudonymization_policy_receipt_id", "source_separation_policy_receipt_id",
    )
    governance = {field: _reserve(receipts, row[field], f"policy.{field}") for field in receipt_fields}
    lane_fields = {
        "lane_id", "lane_kind", "provider_id", "source_id", "source_version", "source_kind",
        "schema_id", "schema_version", "metric_definition_id", "value_kind", "unit_id",
        "denominator_definition_id", "window_starts_at", "window_ends_at",
        "authorization_effective_at", "authorization_expires_at", "declared_observation_ids",
        "source_authorization_receipt_id", "metric_definition_receipt_id", "denominator_definition_receipt_id",
        "population_receipt_id", "completeness_receipt_id", "privacy_receipt_id", "source_documentation_receipt_id",
    }
    lanes: dict[str, dict[str, Any]] = {}
    lane_signatures: set[tuple[str, ...]] = set()
    claimed_observations: set[str] = set()
    for index, raw_lane in enumerate(_arr(row["lane_contracts"], "policy.lane_contracts")):
        item = _obj(raw_lane, f"lane_contracts[{index}]")
        _keys(item, lane_fields, f"lane_contracts[{index}]")
        lane_id = _id(item["lane_id"], "lane.lane_id", "lane-")
        if lane_id in lanes:
            raise ValueError("duplicate lane contract")
        lane_kind = _id(item["lane_kind"], "lane.lane_kind")
        if lane_kind not in LANE_KINDS:
            raise ValueError("lane kind is not allowed")
        if item["source_kind"] != SOURCE_KIND:
            raise ValueError("source kind is not allowed")
        provider_id = _id(item["provider_id"], "lane.provider_id", "provider-")
        source_id = _id(item["source_id"], "lane.source_id", "source-")
        source_version = _id(item["source_version"], "lane.source_version")
        schema_id = _id(item["schema_id"], "lane.schema_id", "schema-")
        schema_version = _id(item["schema_version"], "lane.schema_version")
        metric_definition_id = _id(item["metric_definition_id"], "lane.metric_definition_id", "definition-")
        value_kind = _id(item["value_kind"], "lane.value_kind")
        if value_kind not in VALUE_KINDS:
            raise ValueError("value kind is not allowed")
        if value_kind not in LANE_VALUE_KINDS[lane_kind]:
            raise ValueError("value kind is incompatible with lane kind")
        denominator = item["denominator_definition_id"]
        if value_kind in {"percentage", "ratio"}:
            denominator = _id(denominator, "lane.denominator_definition_id", "definition-")
        elif denominator is not None:
            raise ValueError("denominator is allowed only for percentage or ratio")
        starts_text, starts = _time(item["window_starts_at"], "lane.window_starts_at")
        ends_text, ends = _time(item["window_ends_at"], "lane.window_ends_at")
        auth_effective_text, auth_effective = _time(item["authorization_effective_at"], "lane.authorization_effective_at")
        auth_expires_text, auth_expires = _optional_time(item["authorization_expires_at"], "lane.authorization_expires_at")
        if starts > ends or ends > cutoff or auth_effective > starts or (auth_expires is not None and auth_expires < ends):
            raise ValueError("lane window or authorization is invalid")
        observation_ids = _ids(item["declared_observation_ids"], "lane.declared_observation_ids", "observation-")
        if not observation_ids or claimed_observations.intersection(observation_ids):
            raise ValueError("lane observation populations must be nonempty and disjoint")
        claimed_observations.update(observation_ids)
        signature = (
            provider_id, source_id, source_version, schema_id, schema_version,
            metric_definition_id, starts_text, ends_text,
        )
        if signature in lane_signatures:
            raise ValueError("duplicate provider/source/definition/window lane contract")
        lane_signatures.add(signature)
        lane_receipt_fields = (
            "source_authorization_receipt_id", "metric_definition_receipt_id", "denominator_definition_receipt_id",
            "population_receipt_id", "completeness_receipt_id", "privacy_receipt_id", "source_documentation_receipt_id",
        )
        lane_receipts = {field: _reserve(receipts, item[field], f"lane.{field}") for field in lane_receipt_fields}
        lanes[lane_id] = {
            "lane_id": lane_id, "lane_kind": lane_kind,
            "provider_id": provider_id, "source_id": source_id, "source_version": source_version,
            "schema_id": schema_id, "schema_version": schema_version,
            "metric_definition_id": metric_definition_id,
            "value_kind": value_kind, "unit_id": _id(item["unit_id"], "lane.unit_id", "unit-"),
            "denominator_definition_id": denominator, "window_starts_at": starts_text,
            "window_ends_at": ends_text, "window_starts_dt": starts, "window_ends_dt": ends,
            "authorization_effective_at": auth_effective_text, "authorization_expires_at": auth_expires_text,
            "declared_observation_ids": sorted(observation_ids), **lane_receipts,
        }
    if not lanes:
        raise ValueError("at least one lane contract is required")
    policy = {
        "policy_id": _id(row["policy_id"], "policy.policy_id", "policy-"),
        "policy_version": _id(row["policy_version"], "policy.policy_version"),
        "effective_at": effective_text, "expires_at": expires_text, "cutoff_at": cutoff_text,
        "timezone": timezone_name, "approved_purpose": PURPOSE, "owner_role_id": owner,
        "human_reviewer_role_id": reviewer, "actual_recipient_role_id": actual,
        "review_authorization_effective_at": review_effective_text,
        "review_authorization_expires_at": review_expires_text,
        **governance, "allowed_recipient_role_ids": sorted(recipients), "prohibited_uses": sorted(prohibited),
    }
    return policy, lanes, receipts, cutoff


def review_deliverability_evidence(document: Any) -> dict[str, Any]:
    root = _obj(document, "document")
    _keys(root, {"review_id", "review_version", "policy", "declared_observation_ids", "observations", "packet_receipt_id"}, "document")
    policy, lanes, receipts, cutoff = _policy(root["policy"])
    packet_receipt = _reserve(receipts, root["packet_receipt_id"], "document.packet_receipt_id")
    declared = _ids(root["declared_observation_ids"], "document.declared_observation_ids", "observation-")
    lane_declared = sorted(value for lane in lanes.values() for value in lane["declared_observation_ids"])
    if sorted(declared) != lane_declared:
        raise ValueError("document and lane observation populations differ")
    observation_fields = {
        "observation_id", "lane_id", "provider_id", "source_id", "source_version", "schema_id",
        "schema_version", "metric_definition_id", "value_kind", "unit_id", "denominator_definition_id",
        "observed_at", "evidence_state", "source_value", "capture_authorization_receipt_id",
        "observation_receipt_id", "state_receipt_id",
    }
    raw_observations = _arr(root["observations"], "document.observations")
    observations: dict[str, dict[str, Any]] = {}
    for index, raw_observation in enumerate(raw_observations):
        row = _obj(raw_observation, f"observations[{index}]")
        _keys(row, observation_fields, f"observations[{index}]")
        observation_id = _id(row["observation_id"], "observation.observation_id", "observation-")
        if observation_id in observations:
            raise ValueError("duplicate observation")
        lane_id = _id(row["lane_id"], "observation.lane_id", "lane-")
        if lane_id not in lanes:
            raise ValueError("observation lane is not approved")
        lane = lanes[lane_id]
        observed_text, observed = _time(row["observed_at"], "observation.observed_at")
        if observed > cutoff or observed < lane["window_starts_dt"] or observed > lane["window_ends_dt"]:
            raise ValueError("observation timestamp is outside its frozen window")
        state = _id(row["evidence_state"], "observation.evidence_state")
        if state not in {"observed", *UNRESOLVED}:
            raise ValueError("observation evidence state is not allowed")
        source_value = row["source_value"]
        if state == "observed":
            source_value = _value(source_value, lane["value_kind"], "observation.source_value")
        elif source_value is not None:
            raise ValueError("unresolved observation cannot carry a value")
        capture_receipt = _reserve(receipts, row["capture_authorization_receipt_id"], "observation.capture_authorization_receipt_id")
        observation_receipt = _reserve(receipts, row["observation_receipt_id"], "observation.observation_receipt_id")
        state_receipt = _reserve(receipts, row["state_receipt_id"], "observation.state_receipt_id")
        bindings = {
            "provider_id": _id(row["provider_id"], "observation.provider_id", "provider-"),
            "source_id": _id(row["source_id"], "observation.source_id", "source-"),
            "source_version": _id(row["source_version"], "observation.source_version"),
            "schema_id": _id(row["schema_id"], "observation.schema_id", "schema-"),
            "schema_version": _id(row["schema_version"], "observation.schema_version"),
            "metric_definition_id": _id(row["metric_definition_id"], "observation.metric_definition_id", "definition-"),
            "value_kind": _id(row["value_kind"], "observation.value_kind"),
            "unit_id": _id(row["unit_id"], "observation.unit_id", "unit-"),
            "denominator_definition_id": row["denominator_definition_id"],
        }
        if bindings["denominator_definition_id"] is not None:
            bindings["denominator_definition_id"] = _id(bindings["denominator_definition_id"], "observation.denominator_definition_id", "definition-")
        expected = {key: lane[key] for key in bindings}
        exact_match = bindings == expected and observation_id in lane["declared_observation_ids"]
        if state in UNRESOLVED:
            status = UNRESOLVED[state]
        elif exact_match:
            status = "SOURCE_OBSERVATION_EVIDENCE_PRESENT"
        else:
            status = "SOURCE_OBSERVATION_EVIDENCE_NOT_MATCHED"
            source_value = None
        observations[observation_id] = {
            "observation_id": observation_id, "lane_id": lane_id, **bindings,
            "observed_at": observed_text, "evidence_status": status, "source_value": source_value,
            "capture_authorization_receipt_id": capture_receipt,
            "observation_receipt_id": observation_receipt, "state_receipt_id": state_receipt,
            "source_authorization_receipt_id": lane["source_authorization_receipt_id"],
            "metric_definition_receipt_id": lane["metric_definition_receipt_id"],
            "denominator_definition_receipt_id": lane["denominator_definition_receipt_id"],
            "population_receipt_id": lane["population_receipt_id"],
            "completeness_receipt_id": lane["completeness_receipt_id"],
            "privacy_receipt_id": lane["privacy_receipt_id"],
            "source_documentation_receipt_id": lane["source_documentation_receipt_id"],
        }
    if sorted(observations) != sorted(declared):
        raise ValueError("observation packet is not the complete declared population")
    statuses = [observations[key]["evidence_status"] for key in sorted(observations)]
    review_status = "SOURCE_OBSERVATION_EVIDENCE_PRESENT"
    for unresolved in PRECEDENCE:
        token = UNRESOLVED[unresolved]
        if token in statuses:
            review_status = token
            break
    else:
        if "SOURCE_OBSERVATION_EVIDENCE_NOT_MATCHED" in statuses:
            review_status = "SOURCE_OBSERVATION_EVIDENCE_NOT_MATCHED"
    return {
        "review_receipt": {
            "review_id": _id(root["review_id"], "document.review_id", "review-"),
            "review_version": _id(root["review_version"], "document.review_version"),
            "policy_id": policy["policy_id"], "policy_version": policy["policy_version"],
            "cutoff_at": policy["cutoff_at"], "actual_recipient_role_id": policy["actual_recipient_role_id"],
            "review_status": review_status, "packet_receipt_id": packet_receipt,
            "review_authorization_receipt_id": policy["review_authorization_receipt_id"],
            "source_separation_policy_receipt_id": policy["source_separation_policy_receipt_id"],
        },
        "observation_receipts": [observations[key] for key in sorted(observations)],
        "action_boundary": {
            "alert_authorized": False, "cross_provider_comparison_authorized": False,
            "delisting_authorized": False, "diagnosis_authorized": False,
            "dns_change_authorized": False, "message_authorized": False,
            "publication_authorized": False, "remediation_authorized": False,
            "schedule_authorized": False, "score_authorized": False,
            "send_change_authorized": False, "system_write_authorized": False,
            "workflow_authorized": False, "downstream_decision_authorized": False,
            "boundary": BOUNDARY,
        },
    }


def render_review_output(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: deliverability_evidence.py INPUT.json")
    document = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    sys.stdout.write(render_review_output(review_deliverability_evidence(document)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
