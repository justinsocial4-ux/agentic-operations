#!/usr/bin/env python3
"""Deterministic, read-only SLA evidence evaluation."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json


BOUNDARY = "NO ALERT / NO ESCALATION / NO CRM OR WORKFORCE ACTION"
PROHIBITED_FIELDS = {"name", "email", "content", "body", "home_address", "home_coordinates", "protected_traits", "manager_narrative", "quota", "discipline", "performance"}


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _ids(values, name, allow_empty=False):
    if not isinstance(values, list) or (not values and not allow_empty):
        raise ValueError(f"{name} must be a list")
    clean = [_text(value, name) for value in values]
    if len(clean) != len(set(clean)):
        raise ValueError(f"{name} must contain unique values")
    return clean


def _instant(value, name):
    value = _text(value, name)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO 8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must include an offset")
    return parsed.astimezone(timezone.utc)


def _format(moment):
    return moment.isoformat().replace("+00:00", "Z")


def _required(row, fields, label):
    if not isinstance(row, dict):
        raise ValueError(f"each {label} must be an object")
    missing = sorted(field for field in fields if field not in row)
    if missing:
        raise ValueError(f"{label} missing fields: {', '.join(missing)}")


def reject_sensitive_fields(value, path="root"):
    if isinstance(value, dict):
        for key, child in value.items():
            folded = _text(key, "field name").casefold()
            if folded in PROHIBITED_FIELDS or folded.startswith("rep_") and folded.removeprefix("rep_") in PROHIBITED_FIELDS:
                raise ValueError(f"prohibited field: {path}.{key}")
            reject_sensitive_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_sensitive_fields(child, f"{path}[{index}]")
    return {"state": "VALID"}


def validate_policy(policy):
    required = {"policy_id", "version", "purpose", "start_event_type", "qualifying_event_types", "clock_type", "target_seconds", "timezone", "exclusion_policy_id", "denominator_policy_id", "workforce_policy_id", "owner", "reviewer", "approver", "correction_path", "prohibited_uses"}
    _required(policy, required, "policy")
    reject_sensitive_fields(policy)
    clean = {field: _text(policy[field], field) for field in required - {"qualifying_event_types", "target_seconds", "prohibited_uses"}}
    clean["qualifying_event_types"] = sorted(_ids(policy["qualifying_event_types"], "qualifying_event_types"))
    clean["target_seconds"] = _integer(policy["target_seconds"], "target_seconds")
    clean["prohibited_uses"] = sorted(_ids(policy["prohibited_uses"], "prohibited_uses"))
    clean["clock_type"] = clean["clock_type"].upper()
    if clean["clock_type"] not in {"CONTINUOUS", "SUPPLIED_CALENDAR"}:
        raise ValueError("clock_type must be CONTINUOUS or SUPPLIED_CALENDAR")
    if clean["clock_type"] == "CONTINUOUS" and clean["timezone"].upper() != "UTC":
        raise ValueError("continuous clocks must use UTC")
    return {field: clean[field] for field in sorted(clean)}


def validate_evidence(rows):
    required = {"evidence_id", "source_id", "source_version", "extracted_at", "as_of", "policy_id", "access_scope"}
    if not isinstance(rows, list) or not rows:
        raise ValueError("evidence rows must be a non-empty list")
    seen = set()
    clean = []
    for row in rows:
        _required(row, required, "evidence row")
        reject_sensitive_fields(row)
        normalized = {field: _text(row[field], field) for field in required}
        _instant(normalized["extracted_at"], "extracted_at")
        _instant(normalized["as_of"], "as_of")
        if normalized["evidence_id"] in seen:
            raise ValueError("evidence IDs must be unique")
        seen.add(normalized["evidence_id"])
        clean.append(normalized)
    return sorted(clean, key=lambda row: row["evidence_id"])


def _calendar_due_receipts(rows):
    if not isinstance(rows, list):
        raise ValueError("calendar_due_receipts must be a list")
    required = {"record_id", "due_at", "calendar_id", "calendar_version", "calculator_id", "computed_at", "evidence_id"}
    result = {}
    for row in rows:
        _required(row, required, "calendar due receipt")
        reject_sensitive_fields(row)
        record_id = _text(row["record_id"], "record_id")
        if record_id in result:
            raise ValueError("calendar due receipts must use unique record IDs")
        clean = {field: _text(row[field], field) for field in required}
        _instant(clean["due_at"], "due_at")
        _instant(clean["computed_at"], "computed_at")
        result[record_id] = clean
    return result


def evaluate(*, review_id, cutoff, policy, evidence_rows, record_rows, event_rows, excluded_rows=None, calendar_due_receipts=None, approval_state="APPROVAL_REQUIRED"):
    review_id = _text(review_id, "review_id")
    cutoff_dt = _instant(cutoff, "cutoff")
    policy = validate_policy(policy)
    evidence = validate_evidence(evidence_rows)
    evidence_ids = {row["evidence_id"] for row in evidence}
    evidence_by_id = {row["evidence_id"]: row for row in evidence}
    if not isinstance(record_rows, list) or not record_rows:
        raise ValueError("record_rows must be a non-empty list")
    if not isinstance(event_rows, list):
        raise ValueError("event_rows must be a list")
    if excluded_rows is not None and not isinstance(excluded_rows, list):
        raise ValueError("excluded_rows must be a list")
    exclusions = {}
    for row in excluded_rows or []:
        _required(row, {"record_id", "reason_code", "evidence_id", "policy_id"}, "exclusion row")
        reject_sensitive_fields(row)
        record_id = _text(row["record_id"], "record_id")
        if record_id in exclusions:
            raise ValueError("exclusions must use unique record IDs")
        exclusions[record_id] = {field: _text(row[field], field) for field in ("record_id", "reason_code", "evidence_id", "policy_id")}
    due_receipts = _calendar_due_receipts(calendar_due_receipts or [])
    records = {}
    for row in record_rows:
        _required(row, {"record_id", "start_at", "start_event_type", "owner_id", "evidence_ids"}, "record row")
        reject_sensitive_fields(row)
        record_id = _text(row["record_id"], "record_id")
        if record_id in records:
            raise ValueError("record IDs must be unique")
        row_evidence = sorted(_ids(row["evidence_ids"], "record evidence_ids"))
        records[record_id] = {"record_id": record_id, "start_at": row["start_at"], "start_event_type": _text(row["start_event_type"], "start_event_type"), "owner_id": _text(row["owner_id"], "owner_id"), "evidence_ids": row_evidence}
    unknown_exclusions = sorted(set(exclusions) - set(records))
    if unknown_exclusions:
        raise ValueError("exclusions reference unknown records")
    events_by_record = defaultdict(list)
    seen_events = set()
    required_event = {"event_id", "record_id", "event_type", "occurred_at", "created_at", "association_evidence_id", "source_id", "source_version", "evidence_id"}
    unknown_event_records = set()
    for row in event_rows:
        _required(row, required_event, "event row")
        reject_sensitive_fields(row)
        event_id = _text(row["event_id"], "event_id")
        if event_id in seen_events:
            raise ValueError("event IDs must be unique")
        seen_events.add(event_id)
        clean = {field: _text(row[field], field) for field in required_event}
        clean["occurred_at_dt"] = _instant(clean["occurred_at"], "occurred_at")
        _instant(clean["created_at"], "created_at")
        if clean["record_id"] not in records:
            unknown_event_records.add(clean["record_id"])
        events_by_record[clean["record_id"]].append(clean)
    results = []
    conflict_queue = []
    for record_id in sorted(records):
        record = records[record_id]
        if record_id in exclusions:
            exclusion = exclusions[record_id]
            if exclusion["evidence_id"] not in evidence_ids:
                results.append({"record_id": record_id, "state": "SOURCE_REQUIRED", "reason_code": "EXCLUSION_EVIDENCE_NOT_REGISTERED"})
            elif exclusion["policy_id"] != policy["exclusion_policy_id"]:
                results.append({"record_id": record_id, "state": "POLICY_REQUIRED", "reason_code": "EXCLUSION_POLICY_MISMATCH"})
            else:
                results.append({"record_id": record_id, "state": "EXCLUDED", "exclusion": exclusion})
            continue
        if any(item not in evidence_ids for item in record["evidence_ids"]):
            results.append({"record_id": record_id, "state": "SOURCE_REQUIRED", "reason_code": "RECORD_EVIDENCE_NOT_REGISTERED"})
            continue
        if record["start_event_type"] != policy["start_event_type"]:
            results.append({"record_id": record_id, "state": "POLICY_REQUIRED", "reason_code": "START_EVENT_TYPE_MISMATCH"})
            continue
        try:
            start_dt = _instant(record["start_at"], "start_at")
        except (ValueError, TypeError):
            results.append({"record_id": record_id, "state": "SOURCE_REQUIRED", "reason_code": "START_TIME_REQUIRED"})
            continue
        if start_dt > cutoff_dt:
            results.append({"record_id": record_id, "state": "CONFLICTING", "reason_code": "START_AFTER_CUTOFF"})
            continue
        if policy["clock_type"] == "CONTINUOUS":
            due_dt = start_dt + timedelta(seconds=policy["target_seconds"])
            due_receipt = None
        else:
            due_receipt = due_receipts.get(record_id)
            if due_receipt is None or due_receipt["evidence_id"] not in evidence_ids:
                results.append({"record_id": record_id, "state": "POLICY_REQUIRED", "reason_code": "CALENDAR_DUE_RECEIPT_REQUIRED"})
                continue
            due_dt = _instant(due_receipt["due_at"], "due_at")
            if due_dt < start_dt:
                results.append({"record_id": record_id, "state": "CONFLICTING", "reason_code": "CALENDAR_DUE_BEFORE_START"})
                continue
        candidates = []
        for event in events_by_record.get(record_id, []):
            if event["event_type"] not in policy["qualifying_event_types"]:
                continue
            if event["evidence_id"] not in evidence_ids or event["association_evidence_id"] not in evidence_ids:
                conflict_queue.append({"event_id": event["event_id"], "record_id": record_id, "reason_code": "EVENT_EVIDENCE_NOT_REGISTERED"})
                continue
            event_evidence = evidence_by_id[event["evidence_id"]]
            if event["source_id"] != event_evidence["source_id"] or event["source_version"] != event_evidence["source_version"]:
                conflict_queue.append({"event_id": event["event_id"], "record_id": record_id, "reason_code": "EVENT_SOURCE_MISMATCH"})
                continue
            if event["occurred_at_dt"] < start_dt:
                conflict_queue.append({"event_id": event["event_id"], "record_id": record_id, "reason_code": "EVENT_BEFORE_START"})
                continue
            if event["occurred_at_dt"] > cutoff_dt:
                conflict_queue.append({"event_id": event["event_id"], "record_id": record_id, "reason_code": "EVENT_AFTER_CUTOFF"})
                continue
            if _instant(event["created_at"], "created_at") > cutoff_dt:
                conflict_queue.append({"event_id": event["event_id"], "record_id": record_id, "reason_code": "EVENT_CREATED_AFTER_CUTOFF"})
                continue
            candidates.append(event)
        candidates.sort(key=lambda row: (row["occurred_at_dt"], row["event_id"]))
        first = candidates[0] if candidates else None
        if first is not None:
            state = "MET" if first["occurred_at_dt"] <= due_dt else "BREACHED"
            stop_event = {field: first[field] for field in ("event_id", "event_type", "occurred_at", "created_at", "association_evidence_id", "source_id", "source_version", "evidence_id")}
        else:
            state = "BREACHED" if cutoff_dt > due_dt else "PENDING"
            stop_event = None
        result = {"record_id": record_id, "state": state, "start_at": _format(start_dt), "due_at": _format(due_dt), "stop_event": stop_event, "owner_id": record["owner_id"], "evidence_ids": record["evidence_ids"]}
        if due_receipt is not None:
            result["calendar_due_receipt"] = due_receipt
        results.append(result)
    counts = Counter(row["state"] for row in results)
    denominator = counts["MET"] + counts["BREACHED"]
    rate = None if denominator == 0 else Decimal(counts["MET"]) / Decimal(denominator)
    approval_state = _text(approval_state, "approval_state").upper()
    if approval_state not in {"APPROVAL_REQUIRED", "REVIEW_REQUIRED", "APPROVED_FOR_REVIEW"}:
        raise ValueError("unsupported approval_state")
    return {
        "review_id": review_id,
        "cutoff": _format(cutoff_dt),
        "policy": policy,
        "evidence": evidence,
        "population": {"record_count": len(records), "event_count": len(event_rows), "exclusion_count": len(exclusions)},
        "results": results,
        "summary": {"met_count": counts["MET"], "breached_count": counts["BREACHED"], "pending_count": counts["PENDING"], "excluded_count": counts["EXCLUDED"], "policy_required_count": counts["POLICY_REQUIRED"], "source_required_count": counts["SOURCE_REQUIRED"], "conflicting_count": counts["CONFLICTING"], "resolved_denominator": denominator, "met_rate": rate},
        "conflict_queue": sorted(conflict_queue, key=lambda row: (row["record_id"], row["event_id"])),
        "unknown_event_record_ids": sorted(unknown_event_records),
        "approval_state": approval_state,
        "ranked": False,
        "action_authorized": False,
        "boundary": BOUNDARY,
    }


def render_report_json(report):
    if not isinstance(report, dict):
        raise ValueError("report must be an object")

    def convert(value):
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, dict):
            return {key: convert(child) for key, child in value.items()}
        if isinstance(value, list):
            return [convert(child) for child in value]
        return value

    return json.dumps(convert(report), ensure_ascii=False, indent=2, sort_keys=True)
