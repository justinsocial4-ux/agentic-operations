#!/usr/bin/env python3
"""Deterministic, read-only segment outcome evidence review."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


BOUNDARY = "NO SEGMENT RANKING / NO FORECAST / NO ALERT / NO CRM, LIST, BUDGET, CAMPAIGN, OR WORKFORCE ACTION"
SENSITIVE_PARTS = ("contact", "email", "phone", "person", "rep_", "owner_id", "employee", "activity_content", "message")


def _strict(row, fields, label):
    if not isinstance(row, dict):
        raise ValueError(f"{label} must be an object")
    unknown = set(row) - set(fields)
    missing = set(fields) - set(row)
    if unknown or missing:
        raise ValueError(f"{label} fields mismatch: unknown={sorted(unknown)} missing={sorted(missing)}")
    return dict(row)


def reject_sensitive_fields(value, path="root"):
    if isinstance(value, dict):
        for key, item in value.items():
            folded = str(key).casefold()
            if any(part in folded for part in SENSITIVE_PARTS):
                raise ValueError(f"sensitive field prohibited: {path}.{key}")
            reject_sensitive_fields(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_sensitive_fields(item, f"{path}[{index}]")


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


def _time(value, label):
    value = _text(value, label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include an offset")
    return parsed.astimezone(timezone.utc)


def _decimal(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a Decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a Decimal string") from exc
    if not number.is_finite() or number < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    return number


def _decimal_text(value):
    return format(value, "f")


def validate_policy(row):
    fields = {
        "policy_id", "version", "purpose", "cutoff", "max_age_days", "source_evidence_policy_id", "source_schema_id",
        "source_schema_version", "outcome_mapping_id", "outcome_event_rule",
        "opportunity_identity_rule", "segment_definition_id", "segment_definition_version",
        "membership_mode", "period_timezone", "current_period_id", "comparison_period_id",
        "currency", "amount_basis", "duration_begin_event", "duration_stop_event",
        "comparison_policy_id", "rate_decimal_places", "workforce_policy_id", "owner_role",
        "reviewer_role", "approver_role", "correction_path", "prohibited_uses",
    }
    clean = _strict(row, fields, "policy")
    for key in fields - {"max_age_days", "rate_decimal_places", "prohibited_uses"}:
        clean[key] = _text(clean[key], f"policy.{key}")
    if not isinstance(clean["max_age_days"], int) or isinstance(clean["max_age_days"], bool) or clean["max_age_days"] < 0:
        raise ValueError("policy.max_age_days must be a non-negative integer")
    if not isinstance(clean["rate_decimal_places"], int) or isinstance(clean["rate_decimal_places"], bool) or not 0 <= clean["rate_decimal_places"] <= 6:
        raise ValueError("policy.rate_decimal_places must be an integer from 0 through 6")
    if clean["membership_mode"] not in {"EXCLUSIVE", "OVERLAPPING"}:
        raise ValueError("policy.membership_mode must be EXCLUSIVE or OVERLAPPING")
    if not isinstance(clean["prohibited_uses"], list) or not clean["prohibited_uses"]:
        raise ValueError("policy.prohibited_uses must be a non-empty list")
    clean["prohibited_uses"] = sorted({_text(item, "prohibited use") for item in clean["prohibited_uses"]})
    _time(clean["cutoff"], "policy.cutoff")
    return clean


def _validate_periods(rows, policy):
    fields = {"period_id", "label", "begin", "end", "evidence_id"}
    periods = {}
    for raw in rows:
        row = _strict(raw, fields, "period")
        row["period_id"] = _text(row["period_id"], "period.period_id")
        if row["period_id"] in periods:
            raise ValueError("duplicate period_id")
        row["label"] = _text(row["label"], "period.label")
        row["evidence_id"] = _text(row["evidence_id"], "period.evidence_id")
        begin, end = _time(row["begin"], "period.begin"), _time(row["end"], "period.end")
        if end <= begin:
            raise ValueError("period end must be after begin")
        row["duration_seconds"] = int((end - begin).total_seconds())
        row["_begin"], row["_end"] = begin, end
        periods[row["period_id"]] = row
    wanted = {policy["current_period_id"], policy["comparison_period_id"]}
    if set(periods) != wanted or len(wanted) != 2:
        raise ValueError("periods must contain exactly the distinct current and comparison period IDs")
    current, previous = periods[policy["current_period_id"]], periods[policy["comparison_period_id"]]
    if current["_begin"] < previous["_end"] and previous["_begin"] < current["_end"]:
        raise ValueError("comparison periods must not overlap")
    if current["_begin"] < previous["_end"]:
        raise ValueError("current period must follow comparison period")
    if any(period["_end"] > _time(policy["cutoff"], "policy.cutoff") for period in periods.values()):
        raise ValueError("period cannot extend beyond cutoff")
    return periods


def _validate_evidence(rows, policy):
    fields = {"evidence_id", "source_id", "source_version", "schema_id", "schema_version", "as_of", "extracted_at", "access_scope", "policy_id"}
    cutoff = _time(policy["cutoff"], "policy.cutoff")
    evidence = {}
    states = {}
    for raw in rows:
        row = _strict(raw, fields, "evidence")
        for key in fields:
            row[key] = _text(row[key], f"evidence.{key}")
        key = row["evidence_id"]
        if key in evidence:
            raise ValueError("duplicate evidence_id")
        as_of, extracted = _time(row["as_of"], "evidence.as_of"), _time(row["extracted_at"], "evidence.extracted_at")
        if extracted < as_of:
            raise ValueError("evidence extraction cannot precede as_of")
        state = "AVAILABLE"
        if as_of > cutoff or extracted > cutoff:
            state = "CONFLICTING"
        elif (cutoff - as_of).total_seconds() > policy["max_age_days"] * 86400:
            state = "STALE"
        elif row["policy_id"] != policy["source_evidence_policy_id"] or row["schema_id"] != policy["source_schema_id"] or row["schema_version"] != policy["source_schema_version"]:
            state = "POLICY_REQUIRED"
        evidence[key], states[key] = row, state
    return evidence, states


def _validate_segments(rows):
    fields = {"segment_id", "label", "definition_receipt_id", "evidence_id"}
    segments = {}
    for raw in rows:
        row = _strict(raw, fields, "segment")
        for key in fields:
            row[key] = _text(row[key], f"segment.{key}")
        if row["segment_id"] in segments:
            raise ValueError("duplicate segment_id")
        segments[row["segment_id"]] = row
    if not segments:
        raise ValueError("at least one segment is required")
    return segments


def _record_structural(raw):
    fields = {
        "opportunity_id", "revision_id", "period_id", "record_state", "outcome", "outcome_at",
        "segment_ids", "membership_evidence_id", "evidence_id", "amount_state", "amount",
        "currency", "amount_basis", "duration_state", "duration_begin_at", "duration_stop_at",
    }
    row = _strict(raw, fields, "opportunity")
    for key in ("opportunity_id", "revision_id", "period_id", "record_state", "membership_evidence_id", "evidence_id", "amount_state", "duration_state"):
        row[key] = _text(row[key], f"opportunity.{key}")
    if not isinstance(row["segment_ids"], list):
        raise ValueError("opportunity.segment_ids must be a list")
    row["segment_ids"] = sorted({_text(item, "segment_id") for item in row["segment_ids"]})
    if row["record_state"] not in {"AVAILABLE", "UNKNOWN", "CONFLICTING"}:
        raise ValueError("invalid record_state")
    if row["amount_state"] not in {"AVAILABLE", "UNAVAILABLE", "CONFLICTING"}:
        raise ValueError("invalid amount_state")
    if row["duration_state"] not in {"AVAILABLE", "UNAVAILABLE", "CONFLICTING"}:
        raise ValueError("invalid duration_state")
    if row["outcome"] is not None and row["outcome"] not in {"WON", "LOST"}:
        raise ValueError("invalid outcome")
    return row


def _exception(queue, opportunity_id, lane, state, reason_code):
    queue.append({"opportunity_id": opportunity_id, "lane": lane, "state": state, "reason_code": reason_code})


def _median_decimal(values):
    ordered = sorted(values)
    size = len(ordered)
    if size % 2:
        return ordered[size // 2]
    return (ordered[size // 2 - 1] + ordered[size // 2]) / Decimal("2")


def review_segments(*, review_id, policy, evidence_rows, period_rows, segment_rows, opportunity_rows, approval_state="APPROVAL_REQUIRED"):
    reject_sensitive_fields({"policy": policy, "evidence_rows": evidence_rows, "period_rows": period_rows, "segment_rows": segment_rows, "opportunity_rows": opportunity_rows})
    review_id = _text(review_id, "review_id")
    if approval_state not in {"APPROVAL_REQUIRED", "REVIEWED_NOT_APPROVED", "APPROVED_FOR_REVIEW_ONLY"}:
        raise ValueError("invalid approval_state")
    policy = validate_policy(policy)
    periods = _validate_periods(period_rows, policy)
    evidence, evidence_states = _validate_evidence(evidence_rows, policy)
    segments = _validate_segments(segment_rows)
    for period in periods.values():
        if evidence_states.get(period["evidence_id"]) != "AVAILABLE":
            raise ValueError("period definition evidence is not available")
    for segment in segments.values():
        if evidence_states.get(segment["evidence_id"]) != "AVAILABLE":
            raise ValueError("segment definition evidence is not available")
    exceptions = []
    structurally_valid = [_record_structural(row) for row in opportunity_rows]
    duplicate_ids = {key for key in {row["opportunity_id"] for row in structurally_valid} if sum(item["opportunity_id"] == key for item in structurally_valid) > 1}
    included = {(segment_id, period_id): [] for segment_id in segments for period_id in periods}
    included_opportunity_ids = set()

    for row in sorted(structurally_valid, key=lambda item: (item["opportunity_id"], item["revision_id"])):
        oid = row["opportunity_id"]
        if oid in duplicate_ids:
            _exception(exceptions, oid, "POPULATION", "CONFLICTING", "DUPLICATE_OPPORTUNITY_ID")
            continue
        if row["record_state"] != "AVAILABLE":
            _exception(exceptions, oid, "POPULATION", row["record_state"], "RECORD_NOT_AVAILABLE")
            continue
        if row["outcome"] not in {"WON", "LOST"} or row["outcome_at"] is None:
            _exception(exceptions, oid, "POPULATION", "SOURCE_REQUIRED", "OUTCOME_REQUIRED")
            continue
        if row["period_id"] not in periods:
            _exception(exceptions, oid, "POPULATION", "POLICY_REQUIRED", "UNKNOWN_PERIOD")
            continue
        source_state = evidence_states.get(row["evidence_id"], "SOURCE_REQUIRED")
        member_state = evidence_states.get(row["membership_evidence_id"], "SOURCE_REQUIRED")
        if source_state != "AVAILABLE" or member_state != "AVAILABLE":
            state = source_state if source_state != "AVAILABLE" else member_state
            _exception(exceptions, oid, "POPULATION", state, "EVIDENCE_NOT_AVAILABLE")
            continue
        unknown_segments = sorted(set(row["segment_ids"]) - set(segments))
        if unknown_segments or not row["segment_ids"]:
            _exception(exceptions, oid, "MEMBERSHIP", "POLICY_REQUIRED", "SEGMENT_MEMBERSHIP_INVALID")
            continue
        if policy["membership_mode"] == "EXCLUSIVE" and len(row["segment_ids"]) != 1:
            _exception(exceptions, oid, "MEMBERSHIP", "CONFLICTING", "EXCLUSIVE_MEMBERSHIP_VIOLATION")
            continue
        outcome_at = _time(row["outcome_at"], "opportunity.outcome_at")
        period = periods[row["period_id"]]
        if not period["_begin"] <= outcome_at < period["_end"]:
            _exception(exceptions, oid, "POPULATION", "CONFLICTING", "OUTCOME_OUTSIDE_PERIOD")
            continue

        row["_amount"] = None
        if row["amount_state"] == "AVAILABLE":
            if row["amount"] is None or row["currency"] != policy["currency"] or row["amount_basis"] != policy["amount_basis"]:
                row["amount_state"] = "CONFLICTING"
            else:
                row["_amount"] = _decimal(row["amount"], "opportunity.amount")
        elif any(value is not None for value in (row["amount"], row["currency"], row["amount_basis"])):
            raise ValueError("non-available amount lane cannot contain values")
        if row["outcome"] == "WON" and row["amount_state"] != "AVAILABLE":
            _exception(exceptions, oid, "MONEY", "SOURCE_REQUIRED" if row["amount_state"] == "UNAVAILABLE" else "CONFLICTING", "WON_AMOUNT_REQUIRED")

        row["_duration_seconds"] = None
        if row["duration_state"] == "AVAILABLE":
            if row["duration_begin_at"] is None or row["duration_stop_at"] is None:
                row["duration_state"] = "CONFLICTING"
            else:
                begin = _time(row["duration_begin_at"], "opportunity.duration_begin_at")
                end = _time(row["duration_stop_at"], "opportunity.duration_stop_at")
                if end < begin:
                    row["duration_state"] = "CONFLICTING"
                else:
                    row["_duration_seconds"] = int((end - begin).total_seconds())
        elif row["duration_begin_at"] is not None or row["duration_stop_at"] is not None:
            raise ValueError("non-available duration lane cannot contain values")
        if row["duration_state"] != "AVAILABLE":
            _exception(exceptions, oid, "DURATION", "SOURCE_REQUIRED" if row["duration_state"] == "UNAVAILABLE" else "CONFLICTING", "DURATION_EVIDENCE_REQUIRED")
        included_opportunity_ids.add(oid)
        for segment_id in row["segment_ids"]:
            included[(segment_id, row["period_id"])].append(row)

    metrics = []
    by_key = {}
    quantum = Decimal(1).scaleb(-policy["rate_decimal_places"])
    for segment_id in sorted(segments):
        for period_id in sorted(periods):
            rows = included[(segment_id, period_id)]
            won = [row for row in rows if row["outcome"] == "WON"]
            lost = [row for row in rows if row["outcome"] == "LOST"]
            denominator = len(won) + len(lost)
            rate = None if denominator == 0 else _decimal_text((Decimal(len(won)) * 100 / Decimal(denominator)).quantize(quantum, rounding=ROUND_HALF_UP))

            missing_money = [row for row in won if row["amount_state"] != "AVAILABLE"]
            amounts = [row["_amount"] for row in won if row["_amount"] is not None]
            money_state = "SOURCE_REQUIRED" if missing_money else "CALCULATED"
            money_reason = "WON_AMOUNT_REQUIRED" if missing_money else ("NO_WON_RECORDS" if not won else None)
            amount_total = None if missing_money else _decimal_text(sum(amounts, Decimal("0")))
            amount_median = None if missing_money or not amounts else _decimal_text(_median_decimal(amounts))

            missing_duration = [row for row in rows if row["duration_state"] != "AVAILABLE"]
            durations = [row["_duration_seconds"] for row in rows if row["_duration_seconds"] is not None]
            duration_state = "SOURCE_REQUIRED" if missing_duration else "CALCULATED"
            duration_reason = "DURATION_EVIDENCE_REQUIRED" if missing_duration else ("ZERO_DENOMINATOR" if not rows else None)
            duration_median = None if missing_duration or not durations else _decimal_text(_median_decimal([Decimal(value) for value in durations]))

            result = {
                "segment_id": segment_id,
                "period_id": period_id,
                "population_state": "CALCULATED",
                "closed_outcome_count": denominator,
                "won_count": len(won),
                "lost_count": len(lost),
                "win_rate_pct": rate,
                "population_reason_code": "ZERO_DENOMINATOR" if denominator == 0 else None,
                "money_state": money_state,
                "won_amount_record_count": len(amounts),
                "won_amount_total": amount_total,
                "won_amount_median": amount_median,
                "money_reason_code": money_reason,
                "duration_state": duration_state,
                "duration_record_count": len(durations),
                "median_duration_seconds": duration_median,
                "duration_reason_code": duration_reason,
            }
            metrics.append(result)
            by_key[(segment_id, period_id)] = result

    comparisons = []
    equal_periods = periods[policy["current_period_id"]]["duration_seconds"] == periods[policy["comparison_period_id"]]["duration_seconds"]
    for segment_id in sorted(segments):
        current = by_key[(segment_id, policy["current_period_id"])]
        previous = by_key[(segment_id, policy["comparison_period_id"])]
        rate_delta = None
        if current["win_rate_pct"] is not None and previous["win_rate_pct"] is not None:
            rate_delta = _decimal_text(Decimal(current["win_rate_pct"]) - Decimal(previous["win_rate_pct"]))
        money_available = current["money_state"] == previous["money_state"] == "CALCULATED"
        duration_available = current["duration_state"] == previous["duration_state"] == "CALCULATED" and current["median_duration_seconds"] is not None and previous["median_duration_seconds"] is not None
        comparisons.append({
            "segment_id": segment_id,
            "comparison_state": "CALCULATED" if equal_periods else "COMPARISON_UNAVAILABLE",
            "comparison_reason_code": None if equal_periods else "PERIOD_LENGTH_MISMATCH",
            "closed_outcome_count_delta": current["closed_outcome_count"] - previous["closed_outcome_count"] if equal_periods else None,
            "won_count_delta": current["won_count"] - previous["won_count"] if equal_periods else None,
            "lost_count_delta": current["lost_count"] - previous["lost_count"] if equal_periods else None,
            "win_rate_delta_pp": rate_delta if equal_periods else None,
            "money_comparison_state": "CALCULATED" if equal_periods and money_available else "COMPARISON_UNAVAILABLE",
            "won_amount_total_delta": _decimal_text(Decimal(current["won_amount_total"]) - Decimal(previous["won_amount_total"])) if equal_periods and money_available else None,
            "duration_comparison_state": "CALCULATED" if equal_periods and duration_available else "COMPARISON_UNAVAILABLE",
            "median_duration_seconds_delta": _decimal_text(Decimal(current["median_duration_seconds"]) - Decimal(previous["median_duration_seconds"])) if equal_periods and duration_available else None,
        })

    public_periods = [{key: value for key, value in periods[period_id].items() if key[:1] != "_"} for period_id in sorted(periods)]
    result = {
        "review_id": review_id,
        "policy": policy,
        "evidence": [evidence[key] for key in sorted(evidence)],
        "periods": public_periods,
        "segments": [segments[key] for key in sorted(segments)],
        "membership_interpretation": "PER_SEGMENT_ONLY_NO_CROSS_SEGMENT_TOTALS" if policy["membership_mode"] == "OVERLAPPING" else "EXCLUSIVE_MEMBERSHIP",
        "population_reconciliation": {
            "submitted_record_count": len(structurally_valid),
            "included_unique_opportunity_count": len(included_opportunity_ids),
            "exception_opportunity_count": len({item["opportunity_id"] for item in exceptions}),
        },
        "metric_results": metrics,
        "comparisons": comparisons,
        "exception_queue": sorted(exceptions, key=lambda item: (item["opportunity_id"], item["lane"], item["reason_code"])),
        "approval_state": approval_state,
        "ranked": False,
        "segment_selected": False,
        "forecast_authorized": False,
        "alert_authorized": False,
        "action_authorized": False,
        "boundary": BOUNDARY,
    }
    return result


def render_review_output(review):
    if not isinstance(review, dict):
        raise ValueError("review must be an object")
    return "```json\n" + json.dumps(review, indent=2, sort_keys=True) + "\n```\n\n" + BOUNDARY


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    document = json.loads(Path(argv[0]).read_text() if argv else sys.stdin.read())
    print(render_review_output(review_segments(**document)))


if __name__ == "__main__":
    main()
