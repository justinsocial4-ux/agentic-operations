#!/usr/bin/env python3
"""Deterministic, read-only market-size scenario evidence review."""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys


BOUNDARY = "NO MARKET SELECTION / NO FORECAST / NO BUDGET, QUOTA, CRM, LIST, OR CAMPAIGN ACTION"
COUNT_STATES = {"AVAILABLE", "SUPPRESSED", "UNAVAILABLE", "CONFLICT"}
SCENARIO_STATES = {"AVAILABLE", "NOT_SUPPLIED", "CONFLICT"}
APPROVAL_STATES = {"APPROVAL_REQUIRED", "REVIEW_REQUIRED", "APPROVED_FOR_REVIEW"}
PROHIBITED_FIELDS = {"name", "email", "phone", "contact", "message", "content", "home_address", "protected_traits", "employee_performance", "quota_attainment"}


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _integer(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _decimal(value, field, maximum=None):
    if isinstance(value, bool) or isinstance(value, float) or not isinstance(value, (str, int, Decimal)):
        raise ValueError(f"{field} must be an exact decimal-compatible value")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{field} must be an exact decimal-compatible value") from error
    if not result.is_finite() or result < 0 or maximum is not None and result > maximum:
        raise ValueError(f"{field} is outside its allowed range")
    return result


def _instant(value, field):
    value = _text(value, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field} must be ISO 8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include an offset")
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
            if folded in PROHIBITED_FIELDS or folded.startswith("person_") or folded.startswith("rep_"):
                raise ValueError(f"prohibited field: {path}.{key}")
            reject_sensitive_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_sensitive_fields(child, f"{path}[{index}]")


def validate_policy(raw):
    fields = {"policy_id", "version", "purpose", "cutoff", "target_count_unit", "coverage_definition", "taxonomy_id", "taxonomy_version", "geography_scheme_id", "currency", "price_period", "price_basis", "freshness_policy_id", "max_age_days", "aggregation_policy_id", "disjoint_aggregation_status", "disjoint_receipt_id", "disjoint_evidence_id", "serviceability_policy_id", "obtainability_policy_id", "owner_role", "reviewer_role", "approver_role", "correction_path", "prohibited_uses"}
    _required(raw, fields, "policy")
    extras = sorted(set(raw) - fields)
    if extras:
        raise ValueError(f"policy contains unsupported fields: {', '.join(extras)}")
    reject_sensitive_fields(raw)
    clean = {field: _text(raw[field], field) for field in fields - {"cutoff", "max_age_days", "prohibited_uses", "disjoint_receipt_id", "disjoint_evidence_id"}}
    clean["cutoff"] = _format(_instant(raw["cutoff"], "cutoff"))
    clean["cutoff_dt"] = _instant(raw["cutoff"], "cutoff")
    clean["max_age_days"] = _integer(raw["max_age_days"], "max_age_days")
    if not isinstance(raw["prohibited_uses"], list) or not raw["prohibited_uses"]:
        raise ValueError("prohibited_uses must be a non-empty list")
    clean["prohibited_uses"] = sorted({_text(value, "prohibited_use") for value in raw["prohibited_uses"]})
    status = clean["disjoint_aggregation_status"].upper()
    if status not in {"VERIFIED_DISJOINT", "NOT_VERIFIED"}:
        raise ValueError("invalid disjoint_aggregation_status")
    clean["disjoint_aggregation_status"] = status
    receipt = raw["disjoint_receipt_id"]
    if status == "VERIFIED_DISJOINT":
        clean["disjoint_receipt_id"] = _text(receipt, "disjoint_receipt_id")
        clean["disjoint_evidence_id"] = _text(raw["disjoint_evidence_id"], "disjoint_evidence_id")
    elif receipt is not None or raw["disjoint_evidence_id"] is not None:
        raise ValueError("disjoint receipt and evidence IDs must be null when disjointness is not verified")
    else:
        clean["disjoint_receipt_id"] = None
        clean["disjoint_evidence_id"] = None
    return clean


def validate_evidence(rows, cutoff_dt):
    fields = {"evidence_id", "source_id", "source_version", "dataset_year", "as_of", "extracted_at", "access_scope", "policy_id"}
    if not isinstance(rows, list) or not rows:
        raise ValueError("evidence_rows must be a non-empty list")
    result = {}
    for row in rows:
        _required(row, fields, "evidence row")
        extras = sorted(set(row) - fields)
        if extras:
            raise ValueError(f"evidence row contains unsupported fields: {', '.join(extras)}")
        reject_sensitive_fields(row)
        clean = {field: _text(row[field], field) for field in fields}
        as_of = _instant(clean["as_of"], "as_of")
        extracted = _instant(clean["extracted_at"], "extracted_at")
        if extracted < as_of:
            raise ValueError("evidence extraction cannot precede its as-of time")
        if clean["evidence_id"] in result:
            raise ValueError("evidence IDs must be unique")
        clean["as_of"] = _format(as_of)
        clean["extracted_at"] = _format(extracted)
        clean["as_of_dt"] = as_of
        clean["future"] = as_of > cutoff_dt
        result[clean["evidence_id"]] = clean
    return result


def _rows_by_segment(rows, fields, label):
    if not isinstance(rows, list):
        raise ValueError(f"{label} must be a list")
    result = {}
    for row in rows:
        _required(row, fields, label[:-1] if label.endswith("s") else label)
        extras = sorted(set(row) - set(fields))
        if extras:
            raise ValueError(f"{label} contains unsupported fields: {', '.join(extras)}")
        reject_sensitive_fields(row)
        segment_id = _text(row["segment_id"], "segment_id")
        if segment_id in result:
            raise ValueError(f"{label} must use unique segment IDs")
        result[segment_id] = row
    return result


def _evidence_state(evidence_id, evidence, policy):
    if evidence_id not in evidence:
        return "SOURCE_REQUIRED"
    row = evidence[evidence_id]
    if row["future"]:
        return "CONFLICTING"
    age_days = (policy["cutoff_dt"] - row["as_of_dt"]).total_seconds() / 86400
    if age_days > policy["max_age_days"]:
        return "STALE"
    return "VALID"


def _public_evidence(evidence):
    return [{key: value for key, value in row.items() if key not in {"as_of_dt", "future"}} for _, row in sorted(evidence.items())]


def review_market(*, review_id, policy, evidence_rows, universe_rows, price_rows, serviceability_rows=None, obtainability_rows=None, approval_state="APPROVAL_REQUIRED"):
    review_id = _text(review_id, "review_id")
    policy = validate_policy(deepcopy(policy))
    evidence = validate_evidence(deepcopy(evidence_rows), policy["cutoff_dt"])
    universe_fields = {"segment_id", "label", "geography_id", "taxonomy_code", "count_state", "total_count", "count_unit", "coverage_definition", "taxonomy_id", "taxonomy_version", "geography_scheme_id", "evidence_id"}
    price_fields = {"segment_id", "price_state", "price_per_unit", "currency", "period", "basis", "evidence_id"}
    service_fields = {"segment_id", "state", "serviceable_count", "policy_id", "receipt_id", "evidence_id"}
    obtain_fields = {"segment_id", "state", "fraction", "horizon", "policy_id", "receipt_id", "evidence_id"}
    universes = _rows_by_segment(deepcopy(universe_rows), universe_fields, "universe_rows")
    if not universes:
        raise ValueError("universe_rows must not be empty")
    prices = _rows_by_segment(deepcopy(price_rows), price_fields, "price_rows")
    services = _rows_by_segment(deepcopy(serviceability_rows or []), service_fields, "serviceability_rows")
    obtains = _rows_by_segment(deepcopy(obtainability_rows or []), obtain_fields, "obtainability_rows")
    unknown = sorted((set(prices) | set(services) | set(obtains)) - set(universes))
    if unknown:
        raise ValueError("scenario rows reference unknown segments")

    results = []
    exceptions = []
    for segment_id in sorted(universes):
        raw = universes[segment_id]
        count_state = _text(raw["count_state"], "count_state").upper()
        if count_state not in COUNT_STATES:
            raise ValueError("invalid count_state")
        count = raw["total_count"]
        if count_state == "AVAILABLE":
            count = _integer(count, "total_count")
        elif count is not None:
            raise ValueError("non-available total_count must be null")
        universe = {field: (_text(raw[field], field) if field not in {"total_count"} else count) for field in universe_fields}
        universe["count_state"] = count_state
        mismatches = [
            name for name, actual, expected in (
                ("count_unit", universe["count_unit"], policy["target_count_unit"]),
                ("coverage_definition", universe["coverage_definition"], policy["coverage_definition"]),
                ("taxonomy_id", universe["taxonomy_id"], policy["taxonomy_id"]),
                ("taxonomy_version", universe["taxonomy_version"], policy["taxonomy_version"]),
                ("geography_scheme_id", universe["geography_scheme_id"], policy["geography_scheme_id"]),
            ) if actual != expected
        ]
        source_state = _evidence_state(universe["evidence_id"], evidence, policy)
        state = "CALCULATED"
        reason = None
        if mismatches:
            state, reason = "POLICY_REQUIRED", "UNIVERSE_POLICY_MISMATCH"
        elif source_state != "VALID":
            state, reason = source_state, "UNIVERSE_EVIDENCE_INVALID"
        elif count_state != "AVAILABLE":
            state, reason = count_state, "UNIVERSE_COUNT_NOT_AVAILABLE"

        price = None
        total_value = None
        raw_price = prices.get(segment_id)
        if state == "CALCULATED" and raw_price is None:
            state, reason = "SOURCE_REQUIRED", "PRICE_REQUIRED"
        elif raw_price is not None:
            price_state = _text(raw_price["price_state"], "price_state").upper()
            if price_state not in COUNT_STATES:
                raise ValueError("invalid price_state")
            price_value = raw_price["price_per_unit"]
            if price_state == "AVAILABLE":
                price_value = _decimal(price_value, "price_per_unit")
            elif price_value is not None:
                raise ValueError("non-available price_per_unit must be null")
            price = {field: (_text(raw_price[field], field) if field not in {"price_per_unit"} else price_value) for field in price_fields}
            price["price_state"] = price_state
            price_mismatch = price["currency"] != policy["currency"] or price["period"] != policy["price_period"] or price["basis"] != policy["price_basis"]
            price_source_state = _evidence_state(price["evidence_id"], evidence, policy)
            if state == "CALCULATED" and price_mismatch:
                state, reason = "POLICY_REQUIRED", "PRICE_POLICY_MISMATCH"
            elif state == "CALCULATED" and price_source_state != "VALID":
                state, reason = price_source_state, "PRICE_EVIDENCE_INVALID"
            elif state == "CALCULATED" and price_state != "AVAILABLE":
                state, reason = price_state, "PRICE_NOT_AVAILABLE"
            if state == "CALCULATED":
                total_value = Decimal(count) * price_value

        service = None
        serviceable_value = None
        service_result_state = "NOT_SUPPLIED"
        service_reason = None
        raw_service = services.get(segment_id)
        if raw_service is not None:
            receipt_state = _text(raw_service["state"], "serviceability state").upper()
            if receipt_state not in SCENARIO_STATES:
                raise ValueError("invalid serviceability state")
            service_count = raw_service["serviceable_count"]
            if receipt_state == "AVAILABLE":
                service_count = _integer(service_count, "serviceable_count")
            elif service_count is not None:
                raise ValueError("non-available serviceable_count must be null")
            service = {field: (_text(raw_service[field], field) if field not in {"serviceable_count"} else service_count) for field in service_fields}
            service["state"] = receipt_state
            if state != "CALCULATED":
                service_result_state, service_reason = "BLOCKED_BY_TOTAL_LANE", "TOTAL_LANE_REQUIRED"
            elif receipt_state == "NOT_SUPPLIED":
                service_result_state = "NOT_SUPPLIED"
            elif receipt_state == "CONFLICT":
                service_result_state, service_reason = "CONFLICTING", "SERVICEABILITY_RECEIPT_CONFLICT"
            else:
                if service["policy_id"] != policy["serviceability_policy_id"]:
                    service_result_state, service_reason = "POLICY_REQUIRED", "SERVICEABILITY_POLICY_MISMATCH"
                elif _evidence_state(service["evidence_id"], evidence, policy) != "VALID":
                    service_result_state = _evidence_state(service["evidence_id"], evidence, policy)
                    service_reason = "SERVICEABILITY_EVIDENCE_INVALID"
                elif service_count > count:
                    service_result_state, service_reason = "CONFLICTING", "SERVICEABLE_COUNT_EXCEEDS_TOTAL"
                else:
                    serviceable_value = Decimal(service_count) * price["price_per_unit"]
                    service_result_state = "CALCULATED"

        obtain = None
        obtainable_value = None
        obtain_result_state = "NOT_SUPPLIED"
        obtain_reason = None
        raw_obtain = obtains.get(segment_id)
        if raw_obtain is not None:
            receipt_state = _text(raw_obtain["state"], "obtainability state").upper()
            if receipt_state not in SCENARIO_STATES:
                raise ValueError("invalid obtainability state")
            fraction = raw_obtain["fraction"]
            if receipt_state == "AVAILABLE":
                fraction = _decimal(fraction, "fraction", Decimal("1"))
            elif fraction is not None:
                raise ValueError("non-available fraction must be null")
            obtain = {field: (_text(raw_obtain[field], field) if field not in {"fraction"} else fraction) for field in obtain_fields}
            obtain["state"] = receipt_state
            if state != "CALCULATED":
                obtain_result_state, obtain_reason = "BLOCKED_BY_TOTAL_LANE", "TOTAL_LANE_REQUIRED"
            elif receipt_state == "NOT_SUPPLIED":
                obtain_result_state = "NOT_SUPPLIED"
            elif receipt_state == "CONFLICT":
                obtain_result_state, obtain_reason = "CONFLICTING", "OBTAINABILITY_RECEIPT_CONFLICT"
            elif service_result_state != "CALCULATED":
                obtain_result_state, obtain_reason = "POLICY_REQUIRED", "SERVICEABLE_VALUE_REQUIRED_FOR_OBTAINABLE"
            else:
                if serviceable_value is None:
                    obtain_result_state, obtain_reason = "POLICY_REQUIRED", "SERVICEABLE_VALUE_REQUIRED_FOR_OBTAINABLE"
                elif obtain["policy_id"] != policy["obtainability_policy_id"]:
                    obtain_result_state, obtain_reason = "POLICY_REQUIRED", "OBTAINABILITY_POLICY_MISMATCH"
                elif _evidence_state(obtain["evidence_id"], evidence, policy) != "VALID":
                    obtain_result_state = _evidence_state(obtain["evidence_id"], evidence, policy)
                    obtain_reason = "OBTAINABILITY_EVIDENCE_INVALID"
                else:
                    obtainable_value = serviceable_value * fraction
                    obtain_result_state = "CALCULATED"

        if state != "CALCULATED":
            exceptions.append({"segment_id": segment_id, "state": state, "reason_code": reason, "mismatched_fields": sorted(mismatches)})
        if service_result_state not in {"CALCULATED", "NOT_SUPPLIED", "BLOCKED_BY_TOTAL_LANE"}:
            exceptions.append({"segment_id": segment_id, "lane": "SERVICEABILITY", "state": service_result_state, "reason_code": service_reason, "mismatched_fields": []})
        if obtain_result_state not in {"CALCULATED", "NOT_SUPPLIED", "BLOCKED_BY_TOTAL_LANE"}:
            exceptions.append({"segment_id": segment_id, "lane": "OBTAINABILITY", "state": obtain_result_state, "reason_code": obtain_reason, "mismatched_fields": []})
        results.append({
            "segment_id": segment_id,
            "label": universe["label"],
            "state": state,
            "reason_code": reason,
            "universe_receipt": universe,
            "price_receipt": price,
            "total_addressable_scenario_value": total_value,
            "serviceability_receipt": service,
            "serviceability_result_state": service_result_state,
            "serviceability_reason_code": service_reason,
            "serviceable_addressable_scenario_value": serviceable_value,
            "obtainability_receipt": obtain,
            "obtainability_result_state": obtain_result_state,
            "obtainability_reason_code": obtain_reason,
            "obtainable_scenario_value": obtainable_value,
            "obtainable_interpretation": "SCENARIO_NOT_FORECAST" if obtainable_value is not None else None,
        })

    if len(results) == 1:
        aggregation = {"state": "SINGLE_SEGMENT_NOT_REPRINTED", "total_addressable_value": None, "serviceable_addressable_value": None, "obtainable_value": None}
    elif policy["disjoint_aggregation_status"] != "VERIFIED_DISJOINT":
        aggregation = {"state": "AGGREGATION_UNAVAILABLE", "reason_code": "DISJOINTNESS_NOT_VERIFIED", "total_addressable_value": None, "serviceable_addressable_value": None, "obtainable_value": None}
    elif _evidence_state(policy["disjoint_evidence_id"], evidence, policy) != "VALID":
        aggregation = {"state": "AGGREGATION_UNAVAILABLE", "reason_code": "DISJOINTNESS_EVIDENCE_INVALID", "total_addressable_value": None, "serviceable_addressable_value": None, "obtainable_value": None}
    else:
        total_complete = all(row["state"] == "CALCULATED" for row in results)
        service_complete = all(row["serviceability_result_state"] == "CALCULATED" for row in results)
        obtain_complete = all(row["obtainability_result_state"] == "CALCULATED" for row in results)
        aggregation = {
            "state": "VERIFIED_DISJOINT_AGGREGATION" if total_complete else "AGGREGATION_UNAVAILABLE",
            "reason_code": None if total_complete else "TOTAL_LANE_UNRESOLVED",
            "receipt_id": policy["disjoint_receipt_id"],
            "evidence_id": policy["disjoint_evidence_id"],
            "total_addressable_value": sum((row["total_addressable_scenario_value"] for row in results), Decimal("0")) if total_complete else None,
            "serviceable_addressable_value": sum((row["serviceable_addressable_scenario_value"] for row in results), Decimal("0")) if service_complete else None,
            "obtainable_value": sum((row["obtainable_scenario_value"] for row in results), Decimal("0")) if obtain_complete else None,
            "serviceability_aggregation_state": "CALCULATED" if service_complete else "AGGREGATION_UNAVAILABLE",
            "obtainability_aggregation_state": "CALCULATED" if obtain_complete else "AGGREGATION_UNAVAILABLE",
            "obtainable_interpretation": "SCENARIO_NOT_FORECAST" if obtain_complete else None,
        }
    approval_state = _text(approval_state, "approval_state").upper()
    if approval_state not in APPROVAL_STATES:
        raise ValueError("unsupported approval_state")
    public_policy = {key: value for key, value in policy.items() if key != "cutoff_dt"}
    return {
        "review_id": review_id,
        "policy": public_policy,
        "evidence": _public_evidence(evidence),
        "segment_results": results,
        "exception_queue": exceptions,
        "aggregation": aggregation,
        "ranked": False,
        "market_selected": False,
        "forecast_authorized": False,
        "action_authorized": False,
        "approval_state": approval_state,
        "boundary": BOUNDARY,
    }


def render_review_output(review):
    if not isinstance(review, dict):
        raise ValueError("review must be an object")

    def convert(value):
        if isinstance(value, Decimal):
            return format(value, "f")
        if isinstance(value, dict):
            return {key: convert(child) for key, child in value.items()}
        if isinstance(value, list):
            return [convert(child) for child in value]
        return value

    return "```json\n" + json.dumps(convert(review), ensure_ascii=False, indent=2, sort_keys=True) + "\n```\n\n" + BOUNDARY


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) > 1:
        raise SystemExit("usage: market_sizing_evidence.py [input.json]")
    document = json.loads(Path(argv[0]).read_text() if argv else sys.stdin.read())
    print(render_review_output(review_market(**document)))


if __name__ == "__main__":
    main()
