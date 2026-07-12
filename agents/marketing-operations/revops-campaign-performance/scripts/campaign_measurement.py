#!/usr/bin/env python3
"""Deterministic read-only campaign measurement evidence review."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "pseudonymous_campaign_measurement_evidence_review"
EVIDENCE_STATES = {
    "AVAILABLE",
    "EVIDENCE_MISSING",
    "EVIDENCE_CONFLICT",
    "SUPPRESSED",
    "UNAUTHORIZED",
}
REQUIRED_PROHIBITIONS = {
    "alert",
    "attribution-claim",
    "budget-change",
    "campaign-ranking",
    "causal-claim",
    "crm-read",
    "crm-write",
    "direct-identifier",
    "forecast",
    "fuzzy-campaign-match",
    "message-send",
    "optimization-recommendation",
    "performance-label",
    "platform-read",
    "platform-write",
    "silent-deduplication",
    "silent-fx-conversion",
    "worker-monitoring",
}
FORBIDDEN_KEY_PARTS = (
    "account_name",
    "campaign_name",
    "creative",
    "email",
    "campaign_owner",
    "audience",
    "demographic",
    "contact",
    "lead",
    "opportunity",
    "person",
    "search_term",
    "url",
    "free_text",
    "message",
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


def _decimal(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a Decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a Decimal string") from exc
    if not number.is_finite() or number < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    if number.as_tuple().exponent < -6 or number.adjusted() > 18:
        raise ValueError(f"{label} exceeds supported precision")
    return number


def _count_decimal(value, label):
    number = _decimal(value, label)
    if number != number.to_integral_value():
        raise ValueError(f"{label} must be a whole-number Decimal string")
    return number


def _decimal_text(value):
    return format(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP), "f")


def _ratio_text(numerator, denominator):
    if denominator == 0:
        return None
    return _decimal_text(numerator / denominator)


def _sorted_unique_texts(value, label, prefix=None):
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    items = [_identifier(item, label, prefix) for item in value]
    if len(items) != len(set(items)):
        raise ValueError(f"{label} must not contain duplicates")
    return sorted(items)


def _sorted_unique_tokens(value, label):
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    items = [_text(item, label) for item in value]
    if any(not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", item) for item in items):
        raise ValueError(f"{label} must contain lowercase tokens")
    if len(items) != len(set(items)):
        raise ValueError(f"{label} must not contain duplicates")
    return sorted(items)


def _validate_policy(raw):
    fields = {
        "policy_id",
        "policy_version",
        "approved_purpose",
        "effective_at",
        "expires_at",
        "cutoff_at",
        "reviewed_at",
        "owner_role_id",
        "human_reviewer_role_id",
        "source_policy_receipt_id",
        "measurement_policy_receipt_id",
        "equivalence_policy_receipt_id",
        "recipient_policy_receipt_id",
        "retention_policy_receipt_id",
        "retention_rule_id",
        "allowed_recipient_role_ids",
        "approved_comparison_groups",
        "prohibited_uses",
    }
    row = _strict(raw, fields, "policy")
    for key in fields - {"approved_purpose", "allowed_recipient_role_ids", "approved_comparison_groups", "prohibited_uses", "effective_at", "expires_at", "cutoff_at", "reviewed_at"}:
        row[key] = _identifier(row[key], f"policy.{key}")
    if row["approved_purpose"] != PURPOSE:
        raise ValueError("policy.approved_purpose mismatch")
    row["allowed_recipient_role_ids"] = _sorted_unique_texts(
        row["allowed_recipient_role_ids"], "policy.allowed_recipient_role_ids", "role-"
    )
    row["prohibited_uses"] = _sorted_unique_tokens(row["prohibited_uses"], "policy.prohibited_uses")
    if not REQUIRED_PROHIBITIONS.issubset(row["prohibited_uses"]):
        raise ValueError("policy.prohibited_uses missing required boundaries")
    effective = _time(row["effective_at"], "policy.effective_at")
    expires = _time(row["expires_at"], "policy.expires_at")
    cutoff = _time(row["cutoff_at"], "policy.cutoff_at")
    reviewed = _time(row["reviewed_at"], "policy.reviewed_at")
    if not effective <= cutoff <= reviewed <= expires:
        raise ValueError("policy time order invalid")
    if not isinstance(row["approved_comparison_groups"], list) or not row["approved_comparison_groups"]:
        raise ValueError("policy.approved_comparison_groups must be a non-empty list")
    approved = []
    for raw_group in row["approved_comparison_groups"]:
        group = _strict(raw_group, {"group_id", "contract_ids", "equivalence_receipt_id"}, "approved comparison group")
        group["group_id"] = _identifier(group["group_id"], "approved_comparison_group.group_id", "group-")
        group["contract_ids"] = _sorted_unique_texts(
            group["contract_ids"], "approved_comparison_group.contract_ids", "contract-"
        )
        group["equivalence_receipt_id"] = _identifier(
            group["equivalence_receipt_id"], "approved_comparison_group.equivalence_receipt_id", "receipt-"
        )
        approved.append(group)
    if len({item["group_id"] for item in approved}) != len(approved):
        raise ValueError("duplicate approved comparison group")
    row["approved_comparison_groups"] = sorted(approved, key=lambda item: item["group_id"])
    return row, cutoff


CONTRACT_FIELDS = {
    "contract_id",
    "source_id",
    "source_version",
    "schema_id",
    "schema_version",
    "authorization_receipt_id",
    "authorization_effective_at",
    "authorization_expires_at",
    "query_receipt_id",
    "complete_page_receipt_id",
    "reporting_level",
    "reporting_timezone",
    "period_start_local",
    "period_end_local",
    "freshness_observed_at",
    "currency",
    "amount_basis",
    "spend_definition_id",
    "impression_definition_id",
    "click_definition_id",
    "conversion_definition_id",
    "conversion_action_id",
    "conversion_action_category",
    "counting_mode",
    "attribution_model",
    "attribution_window",
    "date_basis",
}

COMPARABILITY_FIELDS = (
    "reporting_level",
    "reporting_timezone",
    "period_start_local",
    "period_end_local",
    "currency",
    "amount_basis",
    "spend_definition_id",
    "impression_definition_id",
    "click_definition_id",
    "conversion_definition_id",
    "conversion_action_category",
    "counting_mode",
    "attribution_model",
    "attribution_window",
    "date_basis",
)


def _validate_contracts(raw_rows, policy, cutoff):
    if not isinstance(raw_rows, list) or not raw_rows:
        raise ValueError("contracts must be a non-empty list")
    contracts = {}
    unique_receipts = {"query_receipt_id": set(), "complete_page_receipt_id": set()}
    for raw in raw_rows:
        row = _strict(raw, CONTRACT_FIELDS, "contract")
        for key in CONTRACT_FIELDS - {
            "authorization_effective_at",
            "authorization_expires_at",
            "period_start_local",
            "period_end_local",
            "freshness_observed_at",
            "reporting_timezone",
            "currency",
        }:
            row[key] = _identifier(row[key], f"contract.{key}")
        row["reporting_timezone"] = _timezone(row["reporting_timezone"], "contract.reporting_timezone")
        row["currency"] = _text(row["currency"], "contract.currency").upper()
        if not re.fullmatch(r"[A-Z]{3}", row["currency"]):
            raise ValueError("contract.currency must be ISO-style three-letter code")
        contract_id = row["contract_id"]
        if contract_id in contracts:
            raise ValueError("duplicate contract_id")
        auth_start = _time(row["authorization_effective_at"], "contract.authorization_effective_at")
        auth_end = _time(row["authorization_expires_at"], "contract.authorization_expires_at")
        if not auth_start <= cutoff <= auth_end:
            raise ValueError("contract authorization does not cover cutoff")
        period_start = _time(row["period_start_local"], "contract.period_start_local")
        period_end = _time(row["period_end_local"], "contract.period_end_local")
        zone = ZoneInfo(row["reporting_timezone"])
        if period_start.astimezone(zone).utcoffset() != period_start.utcoffset():
            raise ValueError("contract.period_start_local offset conflicts with reporting_timezone")
        if period_end.astimezone(zone).utcoffset() != period_end.utcoffset():
            raise ValueError("contract.period_end_local offset conflicts with reporting_timezone")
        freshness = _time(row["freshness_observed_at"], "contract.freshness_observed_at")
        if period_start >= period_end or period_end > freshness or freshness > cutoff:
            raise ValueError("contract period/freshness time order invalid")
        for receipt_field, seen in unique_receipts.items():
            if row[receipt_field] in seen:
                raise ValueError(f"duplicate {receipt_field}")
            seen.add(row[receipt_field])
        contracts[contract_id] = row
    return contracts


def _validate_populations(raw_rows, contracts, cutoff):
    fields = {"population_receipt_id", "contract_id", "complete", "row_ids", "observed_at"}
    if not isinstance(raw_rows, list) or len(raw_rows) != len(contracts):
        raise ValueError("one population receipt is required per contract")
    populations = {}
    by_contract = {}
    all_row_ids = set()
    for raw in raw_rows:
        row = _strict(raw, fields, "population")
        row["population_receipt_id"] = _identifier(row["population_receipt_id"], "population.population_receipt_id")
        row["contract_id"] = _identifier(row["contract_id"], "population.contract_id", "contract-")
        if row["complete"] is not True:
            raise ValueError("population.complete must be true")
        row["row_ids"] = _sorted_unique_texts(row["row_ids"], "population.row_ids", "row-")
        if _time(row["observed_at"], "population.observed_at") != cutoff:
            raise ValueError("population.observed_at must equal policy cutoff")
        if row["population_receipt_id"] in populations or row["contract_id"] in by_contract:
            raise ValueError("duplicate population or contract population")
        if row["contract_id"] not in contracts:
            raise ValueError("population references unknown contract")
        if all_row_ids.intersection(row["row_ids"]):
            raise ValueError("row_id appears in multiple populations")
        all_row_ids.update(row["row_ids"])
        populations[row["population_receipt_id"]] = row
        by_contract[row["contract_id"]] = row
    if set(by_contract) != set(contracts):
        raise ValueError("population contract coverage mismatch")
    return populations, by_contract, all_row_ids


def _validate_rows(raw_rows, contracts, populations, declared_row_ids):
    fields = {
        "row_id",
        "anonymous_campaign_id",
        "contract_id",
        "population_receipt_id",
        "evidence_state",
        "spend",
        "impressions",
        "clicks",
        "conversions",
    }
    if not isinstance(raw_rows, list):
        raise ValueError("measurement_rows must be a list")
    rows = {}
    for raw in raw_rows:
        row = _strict(raw, fields, "measurement row")
        row["row_id"] = _identifier(row["row_id"], "measurement_row.row_id", "row-")
        row["anonymous_campaign_id"] = _identifier(
            row["anonymous_campaign_id"], "measurement_row.anonymous_campaign_id", "anonymous-campaign-"
        )
        row["contract_id"] = _identifier(row["contract_id"], "measurement_row.contract_id", "contract-")
        row["population_receipt_id"] = _identifier(
            row["population_receipt_id"], "measurement_row.population_receipt_id", "population-"
        )
        row["evidence_state"] = _text(row["evidence_state"], "measurement_row.evidence_state")
        if row["evidence_state"] not in EVIDENCE_STATES:
            raise ValueError("invalid evidence_state")
        if row["row_id"] in rows:
            raise ValueError("duplicate row_id")
        if row["contract_id"] not in contracts or row["population_receipt_id"] not in populations:
            raise ValueError("measurement row references unknown contract or population")
        population = populations[row["population_receipt_id"]]
        if population["contract_id"] != row["contract_id"] or row["row_id"] not in population["row_ids"]:
            raise ValueError("measurement row population binding mismatch")
        metric_fields = ("spend", "impressions", "clicks", "conversions")
        if row["evidence_state"] == "AVAILABLE":
            row["_numbers"] = {
                "spend": _decimal(row["spend"], "measurement_row.spend"),
                "impressions": _count_decimal(row["impressions"], "measurement_row.impressions"),
                "clicks": _count_decimal(row["clicks"], "measurement_row.clicks"),
                "conversions": _decimal(row["conversions"], "measurement_row.conversions"),
            }
        else:
            if any(row[key] is not None for key in metric_fields):
                raise ValueError("unresolved measurement row metrics must be null")
            row["_numbers"] = None
        rows[row["row_id"]] = row
    if set(rows) != declared_row_ids:
        raise ValueError("measurement rows do not equal declared populations")
    return rows


def _validate_groups(raw_groups, contracts, rows, policy):
    fields = {"group_id", "contract_ids", "row_ids", "equivalence_receipt_id"}
    if not isinstance(raw_groups, list) or not raw_groups:
        raise ValueError("comparison_groups must be a non-empty list")
    groups = []
    used_contracts = set()
    used_rows = set()
    for raw in raw_groups:
        group = _strict(raw, fields, "comparison group")
        group["group_id"] = _identifier(group["group_id"], "comparison_group.group_id", "group-")
        group["equivalence_receipt_id"] = _identifier(
            group["equivalence_receipt_id"], "comparison_group.equivalence_receipt_id", "receipt-"
        )
        group["contract_ids"] = _sorted_unique_texts(group["contract_ids"], "comparison_group.contract_ids", "contract-")
        group["row_ids"] = _sorted_unique_texts(group["row_ids"], "comparison_group.row_ids", "row-")
        if used_contracts.intersection(group["contract_ids"]) or used_rows.intersection(group["row_ids"]):
            raise ValueError("contract or row appears in multiple comparison groups")
        if any(item not in contracts for item in group["contract_ids"]) or any(item not in rows for item in group["row_ids"]):
            raise ValueError("comparison group references unknown contract or row")
        expected_rows = {row_id for row_id, row in rows.items() if row["contract_id"] in group["contract_ids"]}
        if set(group["row_ids"]) != expected_rows:
            raise ValueError("comparison group row coverage mismatch")
        anchor = contracts[group["contract_ids"][0]]
        for contract_id in group["contract_ids"][1:]:
            candidate = contracts[contract_id]
            mismatches = [key for key in COMPARABILITY_FIELDS if candidate[key] != anchor[key]]
            if mismatches:
                raise ValueError(f"incomparable contracts: {mismatches}")
        used_contracts.update(group["contract_ids"])
        used_rows.update(group["row_ids"])
        groups.append(group)
    if used_contracts != set(contracts) or used_rows != set(rows):
        raise ValueError("comparison groups must cover every contract and row exactly once")
    if len({group["group_id"] for group in groups}) != len(groups):
        raise ValueError("duplicate group_id")
    if len({group["equivalence_receipt_id"] for group in groups}) != len(groups):
        raise ValueError("duplicate equivalence_receipt_id")
    groups = sorted(groups, key=lambda item: item["group_id"])
    actual_approval_shape = [
        {
            "group_id": group["group_id"],
            "contract_ids": group["contract_ids"],
            "equivalence_receipt_id": group["equivalence_receipt_id"],
        }
        for group in groups
    ]
    if actual_approval_shape != policy["approved_comparison_groups"]:
        raise ValueError("comparison groups do not match approved policy groups")
    return groups


def _public_contract(contract):
    return {key: contract[key] for key in sorted(CONTRACT_FIELDS)}


def review_campaign_measurements(document):
    """Validate one complete document and return a deterministic review object."""
    _reject_forbidden(document)
    fields = {"review_id", "policy", "contracts", "population_receipts", "measurement_rows", "comparison_groups"}
    clean = _strict(document, fields, "document")
    review_id = _identifier(clean["review_id"], "review_id", "review-")
    policy, cutoff = _validate_policy(clean["policy"])
    contracts = _validate_contracts(clean["contracts"], policy, cutoff)
    populations, _, declared_row_ids = _validate_populations(clean["population_receipts"], contracts, cutoff)
    rows = _validate_rows(clean["measurement_rows"], contracts, populations, declared_row_ids)
    groups = _validate_groups(clean["comparison_groups"], contracts, rows, policy)

    evidence_rows = []
    for row_id in sorted(rows):
        row = rows[row_id]
        evidence_rows.append(
            {
                "anonymous_campaign_id": row["anonymous_campaign_id"],
                "contract_id": row["contract_id"],
                "evidence_state": row["evidence_state"],
                "population_receipt_id": row["population_receipt_id"],
                "row_id": row_id,
            }
        )

    group_receipts = []
    for group in groups:
        available = [rows[row_id] for row_id in group["row_ids"] if rows[row_id]["evidence_state"] == "AVAILABLE"]
        totals = {key: sum((row["_numbers"][key] for row in available), Decimal("0")) for key in ("spend", "impressions", "clicks", "conversions")}
        group_receipts.append(
            {
                "contract_ids": group["contract_ids"],
                "cost_per_conversion": _ratio_text(totals["spend"], totals["conversions"]),
                "cpc": _ratio_text(totals["spend"], totals["clicks"]),
                "ctr": _ratio_text(totals["clicks"], totals["impressions"]),
                "currency": contracts[group["contract_ids"][0]]["currency"],
                "equivalence_receipt_id": group["equivalence_receipt_id"],
                "group_id": group["group_id"],
                "included_row_count": len(available),
                "row_ids": group["row_ids"],
                "total_clicks": _decimal_text(totals["clicks"]),
                "total_conversions": _decimal_text(totals["conversions"]),
                "total_impressions": _decimal_text(totals["impressions"]),
                "total_spend": _decimal_text(totals["spend"]),
            }
        )

    return {
        "action_authorized": False,
        "attribution_authorized": False,
        "contracts": [_public_contract(contracts[key]) for key in sorted(contracts)],
        "limitations": [
            "descriptive-same-basis-measurement-only",
            "no-platform-or-crm-access",
            "no-fuzzy-match-or-silent-deduplication",
            "no-performance-ranking-or-label",
            "no-budget-alert-write-or-monitoring-action",
            "no-attribution-forecast-causal-or-financial-claim",
        ],
        "measurement_groups": group_receipts,
        "policy_receipt": policy,
        "population_receipts": [populations[key] for key in sorted(populations)],
        "purpose": PURPOSE,
        "ranking_authorized": False,
        "review_id": review_id,
        "review_status": "HUMAN_REVIEW_REQUIRED",
        "row_evidence": evidence_rows,
    }


def render_review_output(result):
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        raise SystemExit("usage: campaign_measurement.py INPUT.json")
    document = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    sys.stdout.write(render_review_output(review_campaign_measurements(document)))


if __name__ == "__main__":
    main()
