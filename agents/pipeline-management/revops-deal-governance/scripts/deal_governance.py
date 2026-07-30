#!/usr/bin/env python3
"""Deterministic, read-only deal-governance evidence review."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any


BOUNDARY = "NO APPROVAL OR CRM ACTION / NO LEGAL OR WORKFORCE DETERMINATION"
PURPOSE = "deal_governance_evidence_review"
OBSERVATION_STATES = {"OBSERVED", "NOT_OBSERVED", "CONFLICT", "UNRESOLVED"}
OPERATORS = {"lt", "le", "eq", "ge", "gt"}
RULE_TYPES = {"numeric", "document", "process"}
DISPOSITIONS = {"HUMAN_REVIEW", "RECORD_ONLY"}
R1_WORDS = {"small", "large", "enough", "limited", "insufficient", "good", "poor", "high", "low"}
FORBIDDEN_KEYS = {
    "name", "email", "phone", "title", "notes", "free_text", "contract_text",
    "message", "call_content", "protected_trait", "disability", "accommodation",
    "home_location", "rep_seniority", "historical_performance", "compensation",
    "quota", "manager_ranking", "coaching", "sentiment", "risk_score",
    "compliance_score", "confidence", "severity", "probability", "forecast",
}
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,79}$")
DECIMAL_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _keys(obj: dict[str, Any], required: set[str], optional: set[str], label: str) -> None:
    missing = required - set(obj)
    unknown = set(obj) - required - optional
    if missing:
        raise ValueError(f"{label} missing fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"{label} has unsupported fields: {sorted(unknown)}")


def _scan_forbidden(value: Any, path: str = "document") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise ValueError(f"{path}.{key} is prohibited")
            _scan_forbidden(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden(child, f"{path}[{index}]")
    elif isinstance(value, str) and "@" in value:
        raise ValueError(f"{path} contains a direct contact identifier")


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be a stable pseudonymous identifier")
    if R1_WORDS.intersection(part.lower() for part in re.split(r"[_.:-]+", value)):
        raise ValueError(f"{label} contains an unapproved adequacy token")
    return value


def _token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 120 or "@" in value:
        raise ValueError(f"{label} must be a non-contact token")
    if R1_WORDS.intersection(part.lower() for part in re.split(r"[ _./:-]+", value)):
        raise ValueError(f"{label} contains an unapproved adequacy token")
    return value


def _timestamp(value: Any, label: str) -> tuple[str, datetime]:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO-8601 timestamp")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a UTC offset")
    utc_value = parsed.astimezone(timezone.utc)
    return utc_value.isoformat().replace("+00:00", "Z"), utc_value


def _decimal(value: Any, label: str, *, positive: bool = False) -> Decimal:
    if not isinstance(value, str) or not DECIMAL_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be a non-negative plain Decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} is not a Decimal") from exc
    if not number.is_finite() or number < 0 or (positive and number <= 0):
        raise ValueError(f"{label} has an invalid numeric value")
    return number


def _source_binding(policy: dict[str, Any]) -> dict[str, str]:
    bindings: dict[str, str] = {}
    rows = _require_list(policy["source_bindings"], "policy.source_bindings")
    if not rows:
        raise ValueError("policy.source_bindings must not be empty")
    for index, raw in enumerate(rows):
        row = _require_object(raw, f"policy.source_bindings[{index}]")
        _keys(row, {"source_id", "schema_version"}, set(), f"policy.source_bindings[{index}]")
        source_id = _identifier(row["source_id"], "source_id")
        schema = _token(row["schema_version"], "schema_version")
        if source_id in bindings:
            raise ValueError("duplicate policy source binding")
        bindings[source_id] = schema
    return bindings


def _check_source(row: dict[str, Any], bindings: dict[str, str], label: str) -> None:
    source_id = _identifier(row["source_id"], f"{label}.source_id")
    schema = _token(row["schema_version"], f"{label}.schema_version")
    if bindings.get(source_id) != schema:
        raise ValueError(f"{label} does not match an approved source/schema binding")


def _normal_decimal(number: Decimal) -> str:
    rendered = format(number, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def _compare(actual: Decimal, operator: str, threshold: Decimal) -> bool:
    return {
        "lt": actual < threshold,
        "le": actual <= threshold,
        "eq": actual == threshold,
        "ge": actual >= threshold,
        "gt": actual > threshold,
    }[operator]


def _validate_policy(raw: Any) -> tuple[dict[str, Any], dict[str, str], list[dict[str, Any]], datetime]:
    policy = _require_object(raw, "policy")
    _keys(
        policy,
        {
            "policy_id", "policy_version", "owner_id", "human_reviewer_role_id",
            "effective_at", "expires_at", "cutoff_at", "timezone", "approved_purpose",
            "prohibited_uses", "correction_path", "source_bindings", "rules",
        },
        set(),
        "policy",
    )
    for field in ("policy_id", "owner_id", "human_reviewer_role_id"):
        _identifier(policy[field], f"policy.{field}")
    _token(policy["policy_version"], "policy.policy_version")
    _token(policy["timezone"], "policy.timezone")
    _token(policy["correction_path"], "policy.correction_path")
    if policy["approved_purpose"] != PURPOSE:
        raise ValueError("policy.approved_purpose is not authorized for this review")
    prohibited = _require_list(policy["prohibited_uses"], "policy.prohibited_uses")
    if not prohibited or not all(isinstance(item, str) and item for item in prohibited):
        raise ValueError("policy.prohibited_uses must contain tokens")
    effective_text, effective = _timestamp(policy["effective_at"], "policy.effective_at")
    cutoff_text, cutoff = _timestamp(policy["cutoff_at"], "policy.cutoff_at")
    expires_text = None
    if policy["expires_at"] is not None:
        expires_text, expires = _timestamp(policy["expires_at"], "policy.expires_at")
        if cutoff >= expires:
            raise ValueError("policy is expired at cutoff")
    if effective > cutoff:
        raise ValueError("policy is not effective at cutoff")
    policy["effective_at"] = effective_text
    policy["cutoff_at"] = cutoff_text
    policy["expires_at"] = expires_text
    bindings = _source_binding(policy)

    rules: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_rule in enumerate(_require_list(policy["rules"], "policy.rules")):
        rule = _require_object(raw_rule, f"policy.rules[{index}]")
        common = {
            "rule_id", "rule_type", "applies_to_tags", "disposition",
            "human_review_role_id", "precedence",
        }
        rule_type = rule.get("rule_type")
        if rule_type == "numeric":
            specific = {"fact_kind", "operator", "threshold", "unit", "basis", "currency"}
        elif rule_type in {"document", "process"}:
            specific = {"observation_key", "expected_state"}
        else:
            raise ValueError(f"policy.rules[{index}].rule_type is unsupported")
        _keys(rule, common | specific, set(), f"policy.rules[{index}]")
        rule_id = _identifier(rule["rule_id"], "rule_id")
        if rule_id in seen:
            raise ValueError("duplicate rule_id")
        seen.add(rule_id)
        if rule_type not in RULE_TYPES:
            raise ValueError("unsupported rule type")
        tags = _require_list(rule["applies_to_tags"], "applies_to_tags")
        if len(tags) != len(set(tags)) or not all(isinstance(tag, str) and tag for tag in tags):
            raise ValueError("applies_to_tags must contain unique tokens")
        if rule["disposition"] not in DISPOSITIONS:
            raise ValueError("disposition must be HUMAN_REVIEW or RECORD_ONLY")
        _identifier(rule["human_review_role_id"], "human_review_role_id")
        if not isinstance(rule["precedence"], int) or isinstance(rule["precedence"], bool) or rule["precedence"] < 0:
            raise ValueError("precedence must be a non-negative integer")
        if rule_type == "numeric":
            _token(rule["fact_kind"], "fact_kind")
            if rule["operator"] not in OPERATORS:
                raise ValueError("unsupported numeric operator")
            _decimal(rule["threshold"], "threshold")
            _token(rule["unit"], "unit")
            _token(rule["basis"], "basis")
            if rule["currency"] is not None:
                _token(rule["currency"], "currency")
        else:
            _token(rule["observation_key"], "observation_key")
            if rule["expected_state"] not in {"OBSERVED", "NOT_OBSERVED"}:
                raise ValueError("expected_state must be OBSERVED or NOT_OBSERVED")
        rules.append(rule)
    if not rules:
        raise ValueError("policy.rules must not be empty")
    return policy, bindings, rules, cutoff


def review_governance(document: dict[str, Any]) -> dict[str, Any]:
    """Validate evidence and return one deterministic governance review receipt."""
    root = _require_object(document, "document")
    _scan_forbidden(root)
    _keys(
        root,
        {"policy", "declaration", "deals", "numeric_facts", "document_observations", "process_observations"},
        set(),
        "document",
    )
    policy, bindings, rules, cutoff = _validate_policy(root["policy"])

    declaration = _require_object(root["declaration"], "declaration")
    _keys(declaration, {"declared_deal_count", "deal_ids"}, set(), "declaration")
    declared_count = declaration["declared_deal_count"]
    if not isinstance(declared_count, int) or isinstance(declared_count, bool) or declared_count < 0:
        raise ValueError("declared_deal_count must be a non-negative integer")
    declared_ids = [_identifier(value, "declaration.deal_id") for value in _require_list(declaration["deal_ids"], "declaration.deal_ids")]
    if len(declared_ids) != declared_count or len(set(declared_ids)) != len(declared_ids):
        raise ValueError("declared population does not reconcile")

    deals: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_require_list(root["deals"], "deals")):
        row = _require_object(raw, f"deals[{index}]")
        _keys(row, {"deal_id", "account_id", "owner_id", "source_id", "schema_version", "observed_at", "scope_tags"}, set(), f"deals[{index}]")
        deal_id = _identifier(row["deal_id"], "deal_id")
        if deal_id in deals:
            raise ValueError("duplicate deal_id")
        _identifier(row["account_id"], "account_id")
        _identifier(row["owner_id"], "owner_id")
        _check_source(row, bindings, f"deals[{index}]")
        _, observed = _timestamp(row["observed_at"], "deal.observed_at")
        if observed > cutoff:
            raise ValueError("deal observation occurs after cutoff")
        tags = _require_list(row["scope_tags"], "scope_tags")
        if len(tags) != len(set(tags)) or not all(isinstance(tag, str) and tag for tag in tags):
            raise ValueError("scope_tags must contain unique tokens")
        deals[deal_id] = row
    if sorted(deals) != sorted(declared_ids):
        raise ValueError("supplied deal rows do not match declared population")

    facts_by_deal: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    numeric_receipts: list[dict[str, Any]] = []
    seen_fact_ids: set[str] = set()
    for index, raw in enumerate(_require_list(root["numeric_facts"], "numeric_facts")):
        row = _require_object(raw, f"numeric_facts[{index}]")
        _keys(row, {"fact_id", "deal_id", "kind", "value", "unit", "basis", "currency", "source_id", "schema_version", "observed_at"}, set(), f"numeric_facts[{index}]")
        fact_id = _identifier(row["fact_id"], "fact_id")
        deal_id = _identifier(row["deal_id"], "fact.deal_id")
        if fact_id in seen_fact_ids or deal_id not in deals:
            raise ValueError("numeric fact identity is invalid")
        seen_fact_ids.add(fact_id)
        kind = _token(row["kind"], "kind")
        value = _decimal(row["value"], "value")
        unit = _token(row["unit"], "unit")
        basis = _token(row["basis"], "basis")
        currency = row["currency"]
        if currency is not None:
            currency = _token(currency, "currency")
        _check_source(row, bindings, f"numeric_facts[{index}]")
        observed_text, observed = _timestamp(row["observed_at"], "fact.observed_at")
        if observed > cutoff:
            raise ValueError("numeric fact occurs after cutoff")
        normalized = dict(row)
        normalized["value_decimal"] = value
        facts_by_deal[deal_id][kind].append(normalized)
        numeric_receipts.append({
            "fact_id": fact_id, "deal_id": deal_id, "kind": kind,
            "value": _normal_decimal(value), "unit": unit, "basis": basis,
            "currency": currency, "source_id": row["source_id"],
            "schema_version": row["schema_version"], "observed_at": observed_text,
        })

    derived_by_deal: dict[str, dict[str, Any]] = {}
    derivation_conflicts: dict[str, list[str]] = {}
    for deal_id in sorted(deals):
        list_rows = facts_by_deal[deal_id].get("list_amount", [])
        quote_rows = facts_by_deal[deal_id].get("quoted_amount", [])
        if list_rows or quote_rows:
            if len(list_rows) != 1 or len(quote_rows) != 1:
                derivation_conflicts[deal_id] = sorted(row["fact_id"] for row in list_rows + quote_rows)
                continue
            listed, quoted = list_rows[0], quote_rows[0]
            if listed["currency"] != quoted["currency"] or listed["basis"] != quoted["basis"]:
                derivation_conflicts[deal_id] = sorted([listed["fact_id"], quoted["fact_id"]])
                continue
            list_value = _decimal(listed["value"], "list_amount", positive=True)
            quote_value = _decimal(quoted["value"], "quoted_amount")
            with localcontext() as context:
                context.prec = 40
                derived = ((list_value - quote_value) / list_value) * Decimal("100")
            if derived < 0:
                derivation_conflicts[deal_id] = sorted([listed["fact_id"], quoted["fact_id"]])
                continue
            fact_id = f"derived-discount-{deal_id}"
            derived_row = {
                "fact_id": fact_id, "deal_id": deal_id, "kind": "discount_pct",
                "value_decimal": derived, "unit": "percent", "basis": listed["basis"],
                "currency": listed["currency"],
            }
            derived_by_deal[deal_id] = derived_row
            numeric_receipts.append({
                "fact_id": fact_id, "deal_id": deal_id, "kind": "derived_discount_pct",
                "value": _normal_decimal(derived), "unit": "percent",
                "basis": listed["basis"], "currency": listed["currency"],
                "source_fact_ids": [listed["fact_id"], quoted["fact_id"]],
            })

    document_by_deal: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    document_receipts: list[dict[str, Any]] = []
    seen_observations: set[str] = set()
    for index, raw in enumerate(_require_list(root["document_observations"], "document_observations")):
        row = _require_object(raw, f"document_observations[{index}]")
        _keys(row, {"observation_id", "deal_id", "observation_key", "state", "document_id", "document_version", "document_sha256", "locator", "method", "complete_document", "amendments_complete", "precedence_complete", "source_id", "schema_version", "observed_at"}, set(), f"document_observations[{index}]")
        observation_id = _identifier(row["observation_id"], "observation_id")
        deal_id = _identifier(row["deal_id"], "document.deal_id")
        if observation_id in seen_observations or deal_id not in deals:
            raise ValueError("document observation identity is invalid")
        seen_observations.add(observation_id)
        key = _token(row["observation_key"], "observation_key")
        if row["state"] not in OBSERVATION_STATES:
            raise ValueError("unsupported document observation state")
        _identifier(row["document_id"], "document_id")
        _token(row["document_version"], "document_version")
        if not isinstance(row["document_sha256"], str) or not SHA256_PATTERN.fullmatch(row["document_sha256"]):
            raise ValueError("document_sha256 must be lowercase SHA-256")
        _token(row["locator"], "locator")
        _token(row["method"], "method")
        if not all(isinstance(row[field], bool) for field in ("complete_document", "amendments_complete", "precedence_complete")):
            raise ValueError("document completeness receipts must be boolean")
        _check_source(row, bindings, f"document_observations[{index}]")
        observed_text, observed = _timestamp(row["observed_at"], "document.observed_at")
        if observed > cutoff:
            raise ValueError("document observation occurs after cutoff")
        normalized = dict(row)
        normalized["observed_at"] = observed_text
        document_by_deal[deal_id][key].append(normalized)
        document_receipts.append(normalized)

    process_by_deal: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    process_receipts: list[dict[str, Any]] = []
    seen_process: set[str] = set()
    for index, raw in enumerate(_require_list(root["process_observations"], "process_observations")):
        row = _require_object(raw, f"process_observations[{index}]")
        _keys(row, {"process_observation_id", "deal_id", "observation_key", "state", "process_id", "process_version", "permissions_receipt_id", "side_effects_receipt_id", "source_id", "schema_version", "observed_at"}, set(), f"process_observations[{index}]")
        observation_id = _identifier(row["process_observation_id"], "process_observation_id")
        deal_id = _identifier(row["deal_id"], "process.deal_id")
        if observation_id in seen_process or deal_id not in deals:
            raise ValueError("process observation identity is invalid")
        seen_process.add(observation_id)
        key = _token(row["observation_key"], "observation_key")
        if row["state"] not in OBSERVATION_STATES:
            raise ValueError("unsupported process observation state")
        for field in ("process_id", "permissions_receipt_id", "side_effects_receipt_id"):
            _identifier(row[field], field)
        _token(row["process_version"], "process_version")
        _check_source(row, bindings, f"process_observations[{index}]")
        observed_text, observed = _timestamp(row["observed_at"], "process.observed_at")
        if observed > cutoff:
            raise ValueError("process observation occurs after cutoff")
        normalized = dict(row)
        normalized["observed_at"] = observed_text
        process_by_deal[deal_id][key].append(normalized)
        process_receipts.append(normalized)

    threshold_receipts = []
    for rule in sorted((rule for rule in rules if rule["rule_type"] == "numeric"), key=lambda item: item["rule_id"]):
        threshold_receipts.append({
            "threshold_receipt_id": f"threshold-{rule['rule_id']}",
            "rule_id": rule["rule_id"], "value": _normal_decimal(_decimal(rule["threshold"], "threshold")),
            "unit": rule["unit"], "basis": rule["basis"], "currency": rule["currency"],
        })

    deal_reviews = []
    for deal_id in sorted(deals):
        tags = set(deals[deal_id]["scope_tags"])
        applicable = [rule for rule in rules if set(rule["applies_to_tags"]).issubset(tags)]
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for rule in applicable:
            target = rule["fact_kind"] if rule["rule_type"] == "numeric" else rule["observation_key"]
            grouped[(rule["rule_type"], target)].append(rule)
        results = []
        unresolved = [] if applicable else ["POLICY_REQUIRED"]
        for (rule_type, target), group in sorted(grouped.items()):
            top = max(rule["precedence"] for rule in group)
            selected = [rule for rule in group if rule["precedence"] == top]
            if len(selected) != 1:
                results.append({"target_type": rule_type, "target": target, "state": "POLICY_CONFLICT"})
                unresolved.append("POLICY_CONFLICT")
                continue
            rule = selected[0]
            result = {
                "rule_id": rule["rule_id"], "target_type": rule_type, "target": target,
                "disposition": rule["disposition"], "human_review_role_id": rule["human_review_role_id"],
            }
            if rule_type == "numeric":
                rows = list(facts_by_deal[deal_id].get(target, []))
                if target == "discount_pct" and deal_id in derived_by_deal:
                    rows.append(derived_by_deal[deal_id])
                if target == "discount_pct" and deal_id in derivation_conflicts:
                    result["state"] = "EVIDENCE_CONFLICT"
                    result["fact_ids"] = derivation_conflicts[deal_id]
                    unresolved.append("EVIDENCE_CONFLICT")
                elif not rows:
                    result["state"] = "NOT_EVALUABLE"
                    unresolved.append("SOURCE_REQUIRED")
                elif len(rows) > 1 and any(row["value_decimal"] != rows[0]["value_decimal"] for row in rows[1:]):
                    result["state"] = "EVIDENCE_CONFLICT"
                    result["fact_ids"] = sorted(row["fact_id"] for row in rows)
                    unresolved.append("EVIDENCE_CONFLICT")
                else:
                    row = rows[0]
                    if row["unit"] != rule["unit"] or row["basis"] != rule["basis"] or row["currency"] != rule["currency"]:
                        result["state"] = "NOT_EVALUABLE"
                        result["fact_id"] = row["fact_id"]
                        unresolved.append("SOURCE_REQUIRED")
                    else:
                        matched = _compare(row["value_decimal"], rule["operator"], _decimal(rule["threshold"], "threshold"))
                        result["state"] = "RULE_MATCHED" if matched else "RULE_NOT_MATCHED"
                        result["fact_id"] = row["fact_id"]
                        result["threshold_receipt_id"] = f"threshold-{rule['rule_id']}"
            else:
                rows = (document_by_deal if rule_type == "document" else process_by_deal)[deal_id].get(target, [])
                id_field = "observation_id" if rule_type == "document" else "process_observation_id"
                if not rows:
                    result["state"] = "DOCUMENT_REVIEW_REQUIRED" if rule_type == "document" else "NOT_EVALUABLE"
                    unresolved.append(result["state"])
                elif len(rows) != 1 or rows[0]["state"] in {"CONFLICT", "UNRESOLVED"}:
                    result["state"] = "EVIDENCE_CONFLICT"
                    result["observation_ids"] = sorted(row[id_field] for row in rows)
                    unresolved.append("EVIDENCE_CONFLICT")
                elif rule_type == "document" and not all(rows[0][field] for field in ("complete_document", "amendments_complete", "precedence_complete")):
                    result["state"] = "DOCUMENT_REVIEW_REQUIRED"
                    result["observation_id"] = rows[0][id_field]
                    unresolved.append("DOCUMENT_REVIEW_REQUIRED")
                else:
                    result["state"] = "RULE_MATCHED" if rows[0]["state"] == rule["expected_state"] else "RULE_NOT_MATCHED"
                    result["observation_id"] = rows[0][id_field]
            results.append(result)
        deal_reviews.append({
            "deal_id": deal_id,
            "rule_results": sorted(results, key=lambda item: (item.get("rule_id", ""), item["target_type"], item["target"])),
            "unresolved_states": sorted(set(unresolved)),
        })

    return {
        "review_type": "DEAL_GOVERNANCE_EVIDENCE_REVIEW",
        "review_state": "HUMAN_APPROVAL_REQUIRED",
        "policy_receipt": {
            "policy_id": policy["policy_id"], "policy_version": policy["policy_version"],
            "owner_id": policy["owner_id"], "human_reviewer_role_id": policy["human_reviewer_role_id"],
            "effective_at": policy["effective_at"], "expires_at": policy["expires_at"],
            "cutoff_at": policy["cutoff_at"], "timezone": policy["timezone"],
            "approved_purpose": policy["approved_purpose"], "correction_path": policy["correction_path"],
            "prohibited_uses": sorted(policy["prohibited_uses"]),
            "source_bindings": [
                {"source_id": source_id, "schema_version": schema}
                for source_id, schema in sorted(bindings.items())
            ],
        },
        "population_receipt": {"declared_deal_count": declared_count, "deal_ids": sorted(declared_ids)},
        "policy_numeric_receipts": threshold_receipts,
        "numeric_receipts": sorted(numeric_receipts, key=lambda item: item["fact_id"]),
        "document_observation_receipts": sorted(document_receipts, key=lambda item: item["observation_id"]),
        "process_observation_receipts": sorted(process_receipts, key=lambda item: item["process_observation_id"]),
        "deal_reviews": deal_reviews,
        "boundary": BOUNDARY,
    }


def render_review_output(result: dict[str, Any]) -> str:
    """Render the complete response exactly once."""
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    raw = Path(sys.argv[1]).read_text(encoding="utf-8") if len(sys.argv) > 1 else sys.stdin.read()
    document = json.loads(raw)
    sys.stdout.write(render_review_output(review_governance(document)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
