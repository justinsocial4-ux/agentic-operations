#!/usr/bin/env python3
"""Validate and render anonymous aggregate sales evidence."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class EvidenceError(ValueError):
    """Raised when evidence cannot be reviewed without invention."""


APPROVED_PURPOSE = "anonymous_aggregate_descriptive_review"
APPROVED_METRICS = {
    "calls_logged": "count",
    "emails_logged": "count",
    "meetings_occurred": "count",
    "active_pipeline_amount": "money",
    "active_opportunity_count": "count",
    "closed_won_count": "count",
    "closed_lost_count": "count",
}
REQUIRED_PROHIBITED_USES = {
    "causal_or_predictive_claim",
    "coaching_recommendation",
    "compensation_action",
    "crm_write",
    "customer_action",
    "employment_action",
    "individual_worker_analysis",
    "message_or_alert",
    "quota_action",
    "territory_action",
    "worker_ranking",
    "worker_scoring",
}
FORBIDDEN_KEY_PARTS = {
    "account_id",
    "address",
    "attainment",
    "compensation",
    "contact_id",
    "customer_id",
    "deal_id",
    "disability",
    "email_address",
    "employee",
    "first_name",
    "gender",
    "health",
    "individual_activity",
    "job_title",
    "last_name",
    "leave",
    "name",
    "note",
    "owner_id",
    "performance_score",
    "phone",
    "protected_trait",
    "pseudonym",
    "quota",
    "race",
    "rank",
    "recording",
    "rep_id",
    "salary",
    "text",
    "transcript",
    "url",
    "user_id",
    "worker_id",
}
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,79}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
URL_RE = re.compile(r"(?i)^(?:https?://|www\.)")


def _require_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{location} must be an object")
    return value


def _require_list(value: Any, location: str) -> list[Any]:
    if not isinstance(value, list):
        raise EvidenceError(f"{location} must be a list")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], location: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise EvidenceError(f"{location} keys mismatch; missing={missing}; extra={extra}")


def _identifier(value: Any, location: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise EvidenceError(f"{location} must be a stable identifier")
    if EMAIL_RE.fullmatch(value) or URL_RE.search(value):
        raise EvidenceError(f"{location} cannot contain contact or URL data")
    return value


def _identifier_list(value: Any, location: str, *, allow_empty: bool = False) -> list[str]:
    items = _require_list(value, location)
    if not allow_empty and not items:
        raise EvidenceError(f"{location} cannot be empty")
    normalized = [_identifier(item, f"{location}[{index}]") for index, item in enumerate(items)]
    if len(normalized) != len(set(normalized)):
        raise EvidenceError(f"{location} contains duplicate identifiers")
    return normalized


def _utc(value: Any, location: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise EvidenceError(f"{location} must be an ISO 8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise EvidenceError(f"{location} is not a valid timestamp") from exc
    if parsed.tzinfo != timezone.utc:
        raise EvidenceError(f"{location} must use UTC")
    return parsed


def _positive_integer(value: Any, location: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise EvidenceError(f"{location} must be a positive integer")
    return value


def _decimal(value: Any, location: str, unit: str) -> Decimal:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise EvidenceError(f"{location} must be a canonical decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise EvidenceError(f"{location} must be a decimal string") from exc
    if not parsed.is_finite() or parsed < 0:
        raise EvidenceError(f"{location} must be finite and non-negative")
    if unit == "count" and parsed != parsed.to_integral_value():
        raise EvidenceError(f"{location} must be a whole-number count")
    return parsed


def _decimal_text(value: Decimal) -> str:
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def _scan_forbidden(value: Any, location: str = "document") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                raise EvidenceError(f"{location}.{key} is a forbidden individual or sensitive field")
            _scan_forbidden(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_forbidden(item, f"{location}[{index}]")
    elif isinstance(value, str):
        if EMAIL_RE.fullmatch(value) or URL_RE.search(value):
            raise EvidenceError(f"{location} contains contact or URL data")


def _index_records(
    records: Any,
    declared_ids: list[str],
    id_key: str,
    location: str,
) -> dict[str, dict[str, Any]]:
    rows = _require_list(records, location)
    indexed: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(rows):
        row = _require_object(raw, f"{location}[{index}]")
        record_id = _identifier(row.get(id_key), f"{location}[{index}].{id_key}")
        if record_id in indexed:
            raise EvidenceError(f"{location} contains duplicate {record_id}")
        indexed[record_id] = row
    if set(indexed) != set(declared_ids):
        raise EvidenceError(f"{location} does not match its declared population")
    return indexed


def review_aggregate_evidence(document: dict[str, Any]) -> dict[str, Any]:
    """Validate one document and return a complete exact review receipt."""

    document = _require_object(document, "document")
    _scan_forbidden(document)
    _exact_keys(
        document,
        {
            "review_id",
            "policy",
            "declared_source_ids",
            "sources",
            "declared_cohort_ids",
            "cohorts",
            "declared_period_ids",
            "periods",
            "declared_cell_ids",
            "cells",
            "declared_comparison_ids",
            "comparisons",
        },
        "document",
    )

    review_id = _identifier(document["review_id"], "review_id")
    declared_source_ids = _identifier_list(document["declared_source_ids"], "declared_source_ids")
    declared_cohort_ids = _identifier_list(document["declared_cohort_ids"], "declared_cohort_ids")
    declared_period_ids = _identifier_list(document["declared_period_ids"], "declared_period_ids")
    declared_cell_ids = _identifier_list(document["declared_cell_ids"], "declared_cell_ids")
    declared_comparison_ids = _identifier_list(
        document["declared_comparison_ids"], "declared_comparison_ids", allow_empty=True
    )

    policy = _require_object(document["policy"], "policy")
    _exact_keys(
        policy,
        {
            "policy_id",
            "version",
            "policy_authority_id",
            "human_reviewer_id",
            "privacy_approval_id",
            "workforce_approval_id",
            "notice_receipt_id",
            "approved_purpose",
            "approved_cohort_dimension",
            "allowed_metric_codes",
            "allowed_aggregation_rule_ids",
            "minimum_group_size",
            "cutoff_at",
            "effective_from",
            "effective_to",
            "authorized_recipient_ids",
            "retention_rule_id",
            "correction_path_id",
            "prohibited_uses",
        },
        "policy",
    )
    policy_id = _identifier(policy["policy_id"], "policy.policy_id")
    policy_version = _identifier(policy["version"], "policy.version")
    policy_authority_id = _identifier(policy["policy_authority_id"], "policy.policy_authority_id")
    human_reviewer_id = _identifier(policy["human_reviewer_id"], "policy.human_reviewer_id")
    privacy_approval_id = _identifier(policy["privacy_approval_id"], "policy.privacy_approval_id")
    workforce_approval_id = _identifier(policy["workforce_approval_id"], "policy.workforce_approval_id")
    notice_receipt_id = _identifier(policy["notice_receipt_id"], "policy.notice_receipt_id")
    if policy["approved_purpose"] != APPROVED_PURPOSE:
        raise EvidenceError("policy.approved_purpose is not permitted")
    cohort_dimension = _identifier(policy["approved_cohort_dimension"], "policy.approved_cohort_dimension")
    allowed_metrics = _identifier_list(policy["allowed_metric_codes"], "policy.allowed_metric_codes")
    if not set(allowed_metrics).issubset(APPROVED_METRICS):
        raise EvidenceError("policy.allowed_metric_codes contains an unsupported metric")
    allowed_aggregation_rules = _identifier_list(
        policy["allowed_aggregation_rule_ids"], "policy.allowed_aggregation_rule_ids"
    )
    minimum_group_size = _positive_integer(policy["minimum_group_size"], "policy.minimum_group_size")
    cutoff = _utc(policy["cutoff_at"], "policy.cutoff_at")
    effective_from = _utc(policy["effective_from"], "policy.effective_from")
    effective_to = _utc(policy["effective_to"], "policy.effective_to")
    if not effective_from <= cutoff <= effective_to:
        raise EvidenceError("policy is not effective at cutoff_at")
    recipient_ids = _identifier_list(policy["authorized_recipient_ids"], "policy.authorized_recipient_ids")
    retention_rule_id = _identifier(policy["retention_rule_id"], "policy.retention_rule_id")
    correction_path_id = _identifier(policy["correction_path_id"], "policy.correction_path_id")
    prohibited_uses = _identifier_list(policy["prohibited_uses"], "policy.prohibited_uses")
    if set(prohibited_uses) != REQUIRED_PROHIBITED_USES:
        raise EvidenceError("policy.prohibited_uses must match the complete required prohibition set")

    sources = _index_records(document["sources"], declared_source_ids, "source_id", "sources")
    source_receipts: list[dict[str, Any]] = []
    normalized_sources: dict[str, dict[str, Any]] = {}
    for source_id in sorted(sources):
        source = sources[source_id]
        _exact_keys(
            source,
            {
                "source_id",
                "system_code",
                "schema_version",
                "authorization_id",
                "population_receipt_id",
                "observed_at",
                "captured_at",
                "declared_cell_ids",
            },
            f"sources.{source_id}",
        )
        system_code = _identifier(source["system_code"], f"sources.{source_id}.system_code")
        schema_version = _identifier(source["schema_version"], f"sources.{source_id}.schema_version")
        authorization_id = _identifier(source["authorization_id"], f"sources.{source_id}.authorization_id")
        population_receipt_id = _identifier(
            source["population_receipt_id"], f"sources.{source_id}.population_receipt_id"
        )
        observed_at = _utc(source["observed_at"], f"sources.{source_id}.observed_at")
        captured_at = _utc(source["captured_at"], f"sources.{source_id}.captured_at")
        if observed_at > captured_at or captured_at > cutoff:
            raise EvidenceError(f"sources.{source_id} has invalid observation/capture timing")
        source_cell_ids = _identifier_list(
            source["declared_cell_ids"], f"sources.{source_id}.declared_cell_ids"
        )
        normalized_sources[source_id] = {
            "system_code": system_code,
            "schema_version": schema_version,
            "authorization_id": authorization_id,
            "declared_cell_ids": source_cell_ids,
            "observed_at": observed_at,
        }
        source_receipts.append(
            {
                "authorization_id": authorization_id,
                "captured_at": source["captured_at"],
                "declared_cell_ids": sorted(source_cell_ids),
                "observed_at": source["observed_at"],
                "population_receipt_id": population_receipt_id,
                "schema_version": schema_version,
                "source_id": source_id,
                "system_code": system_code,
            }
        )

    cohorts = _index_records(document["cohorts"], declared_cohort_ids, "cohort_id", "cohorts")
    cohort_receipts: list[dict[str, Any]] = []
    suppressed_cohorts: set[str] = set()
    for cohort_id in sorted(cohorts):
        cohort = cohorts[cohort_id]
        _exact_keys(
            cohort,
            {
                "cohort_id",
                "dimension_code",
                "member_count",
                "population_receipt_id",
                "anonymity_receipt_id",
            },
            f"cohorts.{cohort_id}",
        )
        dimension_code = _identifier(cohort["dimension_code"], f"cohorts.{cohort_id}.dimension_code")
        if dimension_code != cohort_dimension:
            raise EvidenceError(f"cohorts.{cohort_id} uses an unapproved dimension")
        member_count = _positive_integer(cohort["member_count"], f"cohorts.{cohort_id}.member_count")
        population_receipt_id = _identifier(
            cohort["population_receipt_id"], f"cohorts.{cohort_id}.population_receipt_id"
        )
        anonymity_receipt_id = _identifier(
            cohort["anonymity_receipt_id"], f"cohorts.{cohort_id}.anonymity_receipt_id"
        )
        status = "SUPPRESSED" if member_count < minimum_group_size else "REVIEWABLE"
        if status == "SUPPRESSED":
            suppressed_cohorts.add(cohort_id)
        cohort_receipts.append(
            {
                "cohort_id": cohort_id,
                "dimension_code": dimension_code,
                "member_count": member_count,
                "population_receipt_id": population_receipt_id,
                "anonymity_receipt_id": anonymity_receipt_id,
                "status": status,
            }
        )

    periods = _index_records(document["periods"], declared_period_ids, "period_id", "periods")
    period_receipts: list[dict[str, Any]] = []
    normalized_periods: dict[str, tuple[datetime, datetime]] = {}
    for period_id in sorted(periods):
        period = periods[period_id]
        _exact_keys(period, {"period_id", "begin_at", "end_at"}, f"periods.{period_id}")
        begin = _utc(period["begin_at"], f"periods.{period_id}.begin_at")
        end = _utc(period["end_at"], f"periods.{period_id}.end_at")
        if begin >= end or end > cutoff:
            raise EvidenceError(f"periods.{period_id} has invalid bounds")
        normalized_periods[period_id] = (begin, end)
        period_receipts.append(
            {"begin_at": period["begin_at"], "end_at": period["end_at"], "period_id": period_id}
        )

    cells = _index_records(document["cells"], declared_cell_ids, "cell_id", "cells")
    observed_cells_by_source: dict[str, set[str]] = {source_id: set() for source_id in sources}
    normalized_cells: dict[str, dict[str, Any]] = {}
    cell_receipts: list[dict[str, Any]] = []
    for cell_id in sorted(cells):
        cell = cells[cell_id]
        _exact_keys(
            cell,
            {
                "cell_id",
                "source_id",
                "cohort_id",
                "period_id",
                "metric_code",
                "value",
                "unit",
                "currency",
                "amount_basis",
                "aggregation_rule_id",
            },
            f"cells.{cell_id}",
        )
        source_id = _identifier(cell["source_id"], f"cells.{cell_id}.source_id")
        cohort_id = _identifier(cell["cohort_id"], f"cells.{cell_id}.cohort_id")
        period_id = _identifier(cell["period_id"], f"cells.{cell_id}.period_id")
        metric_code = _identifier(cell["metric_code"], f"cells.{cell_id}.metric_code")
        aggregation_rule_id = _identifier(
            cell["aggregation_rule_id"], f"cells.{cell_id}.aggregation_rule_id"
        )
        if source_id not in sources or cohort_id not in cohorts or period_id not in periods:
            raise EvidenceError(f"cells.{cell_id} references an unknown record")
        if metric_code not in allowed_metrics:
            raise EvidenceError(f"cells.{cell_id} uses a metric not allowed by policy")
        if aggregation_rule_id not in allowed_aggregation_rules:
            raise EvidenceError(f"cells.{cell_id} uses an aggregation rule not allowed by policy")
        expected_unit = APPROVED_METRICS[metric_code]
        if cell["unit"] != expected_unit:
            raise EvidenceError(f"cells.{cell_id}.unit does not match metric semantics")
        value = _decimal(cell["value"], f"cells.{cell_id}.value", expected_unit)
        if expected_unit == "money":
            currency = _identifier(cell["currency"], f"cells.{cell_id}.currency")
            amount_basis = _identifier(cell["amount_basis"], f"cells.{cell_id}.amount_basis")
        else:
            if cell["currency"] is not None or cell["amount_basis"] is not None:
                raise EvidenceError(f"cells.{cell_id} count metric cannot carry money basis")
            currency = None
            amount_basis = None
        observed_cells_by_source[source_id].add(cell_id)
        normalized_cells[cell_id] = {
            "source_id": source_id,
            "cohort_id": cohort_id,
            "period_id": period_id,
            "metric_code": metric_code,
            "unit": expected_unit,
            "currency": currency,
            "amount_basis": amount_basis,
            "value": value,
            "aggregation_rule_id": aggregation_rule_id,
        }
        receipt: dict[str, Any] = {
            "amount_basis": amount_basis,
            "aggregation_rule_id": aggregation_rule_id,
            "cell_id": cell_id,
            "cohort_id": cohort_id,
            "currency": currency,
            "metric_code": metric_code,
            "period_id": period_id,
            "source_id": source_id,
            "status": "SUPPRESSED" if cohort_id in suppressed_cohorts else "REVIEWABLE",
            "unit": expected_unit,
        }
        if cohort_id not in suppressed_cohorts:
            receipt["value"] = _decimal_text(value)
        cell_receipts.append(receipt)

    for source_id, source in normalized_sources.items():
        if set(source["declared_cell_ids"]) != observed_cells_by_source[source_id]:
            raise EvidenceError(f"sources.{source_id}.declared_cell_ids does not match observed cells")
        for cell_id in observed_cells_by_source[source_id]:
            period_id = normalized_cells[cell_id]["period_id"]
            if normalized_periods[period_id][1] > source["observed_at"]:
                raise EvidenceError(f"sources.{source_id} was observed before a declared period ended")

    comparisons = _index_records(
        document["comparisons"], declared_comparison_ids, "comparison_id", "comparisons"
    )
    comparison_receipts: list[dict[str, Any]] = []
    for comparison_id in sorted(comparisons):
        comparison = comparisons[comparison_id]
        _exact_keys(
            comparison,
            {"comparison_id", "current_cell_id", "previous_cell_id"},
            f"comparisons.{comparison_id}",
        )
        current_id = _identifier(
            comparison["current_cell_id"], f"comparisons.{comparison_id}.current_cell_id"
        )
        previous_id = _identifier(
            comparison["previous_cell_id"], f"comparisons.{comparison_id}.previous_cell_id"
        )
        if current_id == previous_id or current_id not in normalized_cells or previous_id not in normalized_cells:
            raise EvidenceError(f"comparisons.{comparison_id} has invalid cell references")
        current = normalized_cells[current_id]
        previous = normalized_cells[previous_id]
        comparison_fields = (
            "source_id",
            "cohort_id",
            "metric_code",
            "unit",
            "currency",
            "amount_basis",
        )
        if any(current[field] != previous[field] for field in comparison_fields):
            raise EvidenceError(f"comparisons.{comparison_id} mixes incompatible cells")
        current_source = normalized_sources[current["source_id"]]
        previous_source = normalized_sources[previous["source_id"]]
        if current_source["schema_version"] != previous_source["schema_version"]:
            raise EvidenceError(f"comparisons.{comparison_id} mixes schema versions")
        if current_source["authorization_id"] != previous_source["authorization_id"]:
            raise EvidenceError(f"comparisons.{comparison_id} mixes authorization receipts")
        current_begin, current_end = normalized_periods[current["period_id"]]
        previous_begin, previous_end = normalized_periods[previous["period_id"]]
        if current_end - current_begin != previous_end - previous_begin:
            raise EvidenceError(f"comparisons.{comparison_id} mixes unequal period durations")
        if previous_end > current_begin:
            raise EvidenceError(f"comparisons.{comparison_id} periods overlap or are reversed")
        receipt = {
            "comparison_id": comparison_id,
            "current_cell_id": current_id,
            "previous_cell_id": previous_id,
        }
        if current["cohort_id"] in suppressed_cohorts:
            receipt["status"] = "SUPPRESSED"
        else:
            receipt["signed_delta"] = _decimal_text(current["value"] - previous["value"])
            receipt["status"] = "REVIEWABLE"
        comparison_receipts.append(receipt)

    return {
        "action_boundary": {
            "action_authorized": False,
            "decision_status": "HUMAN_REVIEW_REQUIRED",
            "permitted_use": "AUTHORIZED_ANONYMOUS_DESCRIPTIVE_REVIEW_ONLY",
            "prohibited_result_types": sorted(REQUIRED_PROHIBITED_USES),
        },
        "cell_receipts": cell_receipts,
        "cohort_receipts": cohort_receipts,
        "comparison_receipts": comparison_receipts,
        "limitations": [
            "AGGREGATE_EVIDENCE_IS_NOT_INDIVIDUAL_PERFORMANCE_EVIDENCE",
            "NO_CAUSAL_ATTRIBUTION_OR_FORECAST",
            "NO_WORKFORCE_CUSTOMER_OR_SYSTEM_ACTION",
        ],
        "period_receipts": period_receipts,
        "policy_receipt": {
            "approved_cohort_dimension": cohort_dimension,
            "approved_purpose": APPROVED_PURPOSE,
            "authorized_recipient_ids": sorted(recipient_ids),
            "correction_path_id": correction_path_id,
            "cutoff_at": policy["cutoff_at"],
            "human_reviewer_id": human_reviewer_id,
            "notice_receipt_id": notice_receipt_id,
            "privacy_approval_id": privacy_approval_id,
            "workforce_approval_id": workforce_approval_id,
            "allowed_aggregation_rule_ids": sorted(allowed_aggregation_rules),
            "minimum_group_size": minimum_group_size,
            "policy_authority_id": policy_authority_id,
            "policy_id": policy_id,
            "prohibited_uses": sorted(prohibited_uses),
            "retention_rule_id": retention_rule_id,
            "version": policy_version,
        },
        "population_receipt": {
            "cohort_ids": sorted(declared_cohort_ids),
            "comparison_ids": sorted(declared_comparison_ids),
            "cell_ids": sorted(declared_cell_ids),
            "period_ids": sorted(declared_period_ids),
            "source_ids": sorted(declared_source_ids),
        },
        "review_id": review_id,
        "source_receipts": source_receipts,
        "status": "HUMAN_REVIEW_REQUIRED",
    }


def render_review_output(result: dict[str, Any]) -> str:
    """Return one canonical JSON response with a final newline."""

    return json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) > 1:
        print("usage: aggregate_evidence.py [document.json]", file=sys.stderr)
        return 2
    try:
        raw = Path(arguments[0]).read_text(encoding="utf-8") if arguments else sys.stdin.read()
        document = json.loads(raw)
        sys.stdout.write(render_review_output(review_aggregate_evidence(document)))
    except (OSError, json.JSONDecodeError, EvidenceError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
