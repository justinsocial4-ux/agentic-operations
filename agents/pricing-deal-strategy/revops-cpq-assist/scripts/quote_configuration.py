#!/usr/bin/env python3
"""Deterministic, read-only quote-configuration evidence review."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
from pathlib import Path
from typing import Any


BOUNDARY = "NO PRODUCT OR PRICE RECOMMENDATION / NO APPROVAL, CUSTOMER SEND, CRM, LEGAL, FINANCE, OR WORKFORCE ACTION"
PURPOSE = "quote_configuration_evidence_review"
REQUIRED_PROHIBITED = {"product-recommendation", "price-recommendation", "approval-action", "customer-send", "crm-write", "legal-determination", "finance-determination", "workforce-action"}
OPERATORS = {"lt", "le", "eq", "ge", "gt"}
RECORD_TYPES = {"catalog", "quote", "approval"}
RULE_TYPES = {"numeric", "requires_item", "excludes_item", "quantity", "approval_observation"}
APPROVAL_MODES = {"ALL", "ANY", "SEQUENTIAL", "PARALLEL"}
APPROVAL_STATES = {"OBSERVED", "NOT_OBSERVED", "CONFLICT", "UNRESOLVED"}
R1_WORDS = {"small", "large", "enough", "limited", "insufficient", "good", "poor", "high", "low"}
ACTION_LABEL_WORDS = {"approve", "reject", "submit", "route", "escalate", "notify", "send", "write", "create", "assign", "contact", "recommend", "rank", "coach"}
FORBIDDEN_KEY_PARTS = {"name", "email", "phone", "address", "contact", "message", "text", "activity", "attendee", "title", "trait", "disability", "accommodation", "performance", "quota", "compensation", "coaching", "ranking", "committee", "sentiment", "probability", "confidence", "forecast", "margin", "recommendation"}
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,95}$")
DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
ROUNDING = {"ROUND_DOWN": ROUND_DOWN, "ROUND_HALF_EVEN": ROUND_HALF_EVEN, "ROUND_HALF_UP": ROUND_HALF_UP}


def _obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict): raise ValueError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list): raise ValueError(f"{label} must be a list")
    return value


def _keys(obj: dict[str, Any], required: set[str], optional: set[str], label: str) -> None:
    missing = required - set(obj); unknown = set(obj) - required - optional
    if missing: raise ValueError(f"{label} missing fields: {sorted(missing)}")
    if unknown: raise ValueError(f"{label} has unsupported fields: {sorted(unknown)}")


def _scan(value: Any, path: str = "document") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            parts = {p for p in re.split(r"[^a-z0-9]+", key.lower()) if p}
            if parts & FORBIDDEN_KEY_PARTS: raise ValueError(f"{path}.{key} is prohibited")
            _scan(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value): _scan(child, f"{path}[{index}]")
    elif isinstance(value, str) and "@" in value:
        raise ValueError(f"{path} contains a direct contact identifier")


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value): raise ValueError(f"{label} must be a stable pseudonymous identifier")
    if {p.lower() for p in re.split(r"[_.:-]+", value)} & R1_WORDS: raise ValueError(f"{label} contains an unapproved adequacy token")
    return value


def _token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 160 or "@" in value: raise ValueError(f"{label} must be a non-contact token")
    if {p.lower() for p in re.split(r"[ _./:-]+", value)} & R1_WORDS: raise ValueError(f"{label} contains an unapproved adequacy token")
    return value


def _ts(value: Any, label: str) -> tuple[str, datetime]:
    if not isinstance(value, str): raise ValueError(f"{label} must be ISO-8601")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try: parsed = datetime.fromisoformat(text)
    except ValueError as exc: raise ValueError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None: raise ValueError(f"{label} must include a UTC offset")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _dec(value: Any, label: str, positive: bool = False) -> Decimal:
    if not isinstance(value, str) or not DECIMAL_PATTERN.fullmatch(value): raise ValueError(f"{label} must be a plain Decimal string")
    try: number = Decimal(value)
    except InvalidOperation as exc: raise ValueError(f"{label} is not Decimal") from exc
    if not number.is_finite() or len(number.as_tuple().digits) > 40 or (positive and number <= 0): raise ValueError(f"{label} has an invalid value")
    return number


def _norm(number: Decimal) -> str:
    text = format(number, "f")
    if "." in text: text = text.rstrip("0").rstrip(".")
    return text or "0"


def _compare(actual: Decimal, op: str, threshold: Decimal) -> bool:
    return {"lt": actual < threshold, "le": actual <= threshold, "eq": actual == threshold, "ge": actual >= threshold, "gt": actual > threshold}[op]


def _decimal_places(number: Decimal) -> int:
    return max(0, -number.as_tuple().exponent)


def _binding_map(rows: Any) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for index, raw in enumerate(_list(rows, "policy.source_bindings")):
        row = _obj(raw, f"source_bindings[{index}]"); _keys(row, {"record_type", "source_id", "schema_version"}, set(), f"source_bindings[{index}]")
        if row["record_type"] not in RECORD_TYPES: raise ValueError("unsupported record_type")
        _id(row["source_id"], "source_id"); _token(row["schema_version"], "schema_version")
        key = (row["record_type"], row["source_id"])
        if key in result: raise ValueError("duplicate source binding")
        result[key] = row["schema_version"]
    if not result: raise ValueError("source bindings must not be empty")
    return result


def _check_source(row: dict[str, Any], record_type: str, bindings: dict[tuple[str, str], str], label: str) -> None:
    _id(row["source_id"], f"{label}.source_id"); _token(row["schema_version"], f"{label}.schema_version")
    if bindings.get((record_type, row["source_id"])) != row["schema_version"]: raise ValueError(f"{label} does not match source/schema binding")


def _validate_policy(raw: Any) -> tuple[dict[str, Any], dict[tuple[str, str], str], list[dict[str, Any]], datetime]:
    policy = _obj(raw, "policy")
    _keys(policy, {"policy_id", "policy_version", "owner_id", "human_reviewer_role_id", "effective_at", "expires_at", "cutoff_at", "timezone", "approved_purpose", "prohibited_uses", "correction_path", "catalog_binding", "calculation_policy", "source_bindings", "rules"}, set(), "policy")
    for field in ("policy_id", "owner_id", "human_reviewer_role_id"): _id(policy[field], f"policy.{field}")
    for field in ("policy_version", "timezone", "correction_path"): _token(policy[field], f"policy.{field}")
    if policy["approved_purpose"] != PURPOSE: raise ValueError("policy purpose is unauthorized")
    prohibited = _list(policy["prohibited_uses"], "policy.prohibited_uses")
    if not REQUIRED_PROHIBITED.issubset(set(prohibited)): raise ValueError("fixed prohibited uses are missing")
    for value in prohibited: _token(value, "prohibited use")
    effective_text, effective = _ts(policy["effective_at"], "policy.effective_at"); cutoff_text, cutoff = _ts(policy["cutoff_at"], "policy.cutoff_at")
    if effective > cutoff: raise ValueError("policy not effective at cutoff")
    expires_text = None
    if policy["expires_at"] is not None:
        expires_text, expires = _ts(policy["expires_at"], "policy.expires_at")
        if cutoff >= expires: raise ValueError("policy expired at cutoff")
    policy.update(effective_at=effective_text, expires_at=expires_text, cutoff_at=cutoff_text)
    binding = _obj(policy["catalog_binding"], "policy.catalog_binding")
    _keys(binding, {"catalog_id", "catalog_version", "pricebook_id", "pricebook_version"}, set(), "policy.catalog_binding")
    for field in ("catalog_id", "pricebook_id"): _id(binding[field], field)
    for field in ("catalog_version", "pricebook_version"): _token(binding[field], field)
    calculation = _obj(policy["calculation_policy"], "policy.calculation_policy")
    _keys(calculation, {"discount_scale", "discount_rounding"}, set(), "policy.calculation_policy")
    if not isinstance(calculation["discount_scale"], str) or not calculation["discount_scale"].isdigit() or int(calculation["discount_scale"]) > 9: raise ValueError("discount_scale must be a digit string from zero through nine")
    if calculation["discount_rounding"] not in ROUNDING: raise ValueError("unsupported discount_rounding")
    bindings = _binding_map(policy["source_bindings"])

    rules: list[dict[str, Any]] = []; seen: set[str] = set()
    for index, raw_rule in enumerate(_list(policy["rules"], "policy.rules")):
        rule = _obj(raw_rule, f"rules[{index}]"); common = {"rule_id", "rule_type", "precedence", "observation_label", "human_review_role_id"}
        rtype = rule.get("rule_type")
        if rtype == "numeric": specific = {"fact_id", "operator", "threshold", "unit", "basis", "currency", "billing_period"}
        elif rtype in {"requires_item", "excludes_item"}: specific = {"left_item_id", "right_item_id"}
        elif rtype == "quantity": specific = {"item_id", "operator", "threshold", "unit"}
        elif rtype == "approval_observation": specific = {"process_id", "expected_state"}
        else: raise ValueError("unsupported rule_type")
        _keys(rule, common | specific, set(), f"rules[{index}]")
        rid = _id(rule["rule_id"], "rule_id")
        if rid in seen: raise ValueError("duplicate rule_id")
        seen.add(rid); _id(rule["human_review_role_id"], "human_review_role_id")
        _token(rule["observation_label"], "observation_label")
        if not rule["observation_label"].startswith(("review-observation-", "record-observation-")): raise ValueError("observation label must be neutral")
        if {p.lower() for p in re.split(r"[_.:-]+", rule["observation_label"])} & ACTION_LABEL_WORDS: raise ValueError("observation label contains an action token")
        if not isinstance(rule["precedence"], int) or isinstance(rule["precedence"], bool) or rule["precedence"] < 0: raise ValueError("precedence must be non-negative integer")
        if rtype == "numeric":
            _id(rule["fact_id"], "fact_id")
            if rule["operator"] not in OPERATORS: raise ValueError("unsupported operator")
            rule["threshold"] = _norm(_dec(rule["threshold"], "threshold"))
            for field in ("unit", "basis", "billing_period"): _token(rule[field], field)
            if rule["currency"] is not None: _token(rule["currency"], "currency")
        elif rtype in {"requires_item", "excludes_item"}:
            _id(rule["left_item_id"], "left_item_id"); _id(rule["right_item_id"], "right_item_id")
            if rule["left_item_id"] == rule["right_item_id"]: raise ValueError("configuration rule items must differ")
        elif rtype == "quantity":
            _id(rule["item_id"], "item_id")
            if rule["operator"] not in OPERATORS: raise ValueError("unsupported operator")
            rule["threshold"] = _norm(_dec(rule["threshold"], "threshold")); _token(rule["unit"], "unit")
        else:
            _id(rule["process_id"], "process_id")
            if rule["expected_state"] not in APPROVAL_STATES: raise ValueError("unsupported approval state")
        rules.append(rule)
    if not rules: raise ValueError("policy.rules must not be empty")
    return policy, bindings, rules, cutoff


def review_quote_configuration(document: dict[str, Any]) -> dict[str, Any]:
    root = _obj(document, "document"); _scan(root)
    _keys(root, {"policy", "declaration", "catalog_items", "quote_lines", "approval_processes"}, set(), "document")
    policy, bindings, rules, cutoff = _validate_policy(root["policy"]); cb = policy["catalog_binding"]
    declaration = _obj(root["declaration"], "declaration")
    _keys(declaration, {"quote_id", "account_id", "declared_line_count", "line_ids"}, set(), "declaration")
    _id(declaration["quote_id"], "quote_id"); _id(declaration["account_id"], "account_id")
    line_ids = [_id(v, "line_id") for v in _list(declaration["line_ids"], "line_ids")]
    if len(line_ids) != len(set(line_ids)): raise ValueError("duplicate declared line ID")
    if not isinstance(declaration["declared_line_count"], int) or isinstance(declaration["declared_line_count"], bool) or declaration["declared_line_count"] != len(line_ids): raise ValueError("declared line count does not reconcile")
    declared = set(line_ids)

    facts: list[dict[str, Any]] = []; fact_values: dict[str, tuple[Decimal, str, str, str | None, str]] = {}
    def add_fact(fid: str, kind: str, value: Decimal, unit: str, basis: str, currency: str | None, period: str, source: str) -> None:
        if fid in fact_values: raise ValueError("duplicate fact ID")
        fact_values[fid] = (value, unit, basis, currency, period)
        facts.append({"fact_id": fid, "kind": kind, "value": _norm(value), "unit": unit, "basis": basis, "currency": currency, "billing_period": period, "source_receipt_id": source})

    items: dict[str, dict[str, Any]] = {}; catalog_receipts: list[dict[str, Any]] = []
    for index, raw in enumerate(_list(root["catalog_items"], "catalog_items")):
        row = _obj(raw, f"catalog_items[{index}]")
        _keys(row, {"item_id", "catalog_id", "catalog_version", "pricebook_id", "pricebook_version", "pricebook_entry_id", "item_type", "unit", "quantity_scale", "currency", "price_basis", "billing_period", "effective_at", "expires_at", "list_unit_price", "active", "source_id", "schema_version", "observed_at"}, set(), f"catalog_items[{index}]")
        for field in ("item_id", "catalog_id", "pricebook_id", "pricebook_entry_id"): _id(row[field], field)
        if row["item_id"] in items: raise ValueError("duplicate catalog item")
        for field in ("catalog_version", "pricebook_version", "item_type", "unit", "currency", "price_basis", "billing_period", "schema_version"): _token(row[field], field)
        if any(row[field] != cb[field] for field in ("catalog_id", "catalog_version", "pricebook_id", "pricebook_version")): raise ValueError("catalog item binding mismatch")
        if not isinstance(row["active"], bool) or not row["active"]: raise ValueError("catalog item must be active")
        if not isinstance(row["quantity_scale"], str) or not row["quantity_scale"].isdigit(): raise ValueError("quantity_scale must be a digit string")
        scale = int(row["quantity_scale"])
        if scale > 9: raise ValueError("quantity_scale unsupported")
        effective_text, effective = _ts(row["effective_at"], "effective_at"); observed_text, observed = _ts(row["observed_at"], "observed_at")
        if effective > cutoff or observed > cutoff: raise ValueError("catalog evidence after cutoff")
        expires_text = None
        if row["expires_at"] is not None:
            expires_text, expires = _ts(row["expires_at"], "expires_at")
            if cutoff >= expires: raise ValueError("catalog item expired at cutoff")
        _check_source(row, "catalog", bindings, "catalog item")
        price = _dec(row["list_unit_price"], "list_unit_price", positive=True)
        fid = f"fact:{row['item_id']}:list-unit-price"; add_fact(fid, "list_unit_price", price, row["unit"], row["price_basis"], row["currency"], row["billing_period"], row["pricebook_entry_id"])
        receipt = {k: row[k] for k in row if k not in {"list_unit_price"}}
        receipt.update(effective_at=effective_text, expires_at=expires_text, observed_at=observed_text, list_unit_price_fact_id=fid)
        items[row["item_id"]] = {**row, "effective_at": effective_text, "expires_at": expires_text, "observed_at": observed_text, "scale": scale, "list_price": price}
        catalog_receipts.append(receipt)

    for rule in rules:
        if rule["rule_type"] in {"requires_item", "excludes_item"} and ({rule["left_item_id"], rule["right_item_id"]} - set(items)):
            raise ValueError("configuration rule references an unknown catalog item")
        if rule["rule_type"] == "quantity" and rule["item_id"] not in items:
            raise ValueError("quantity rule references an unknown catalog item")

    line_receipts: list[dict[str, Any]] = []; item_lines: dict[str, list[str]] = defaultdict(list); line_quantities: dict[str, Decimal] = {}; line_states: dict[str, str] = {}
    groups: dict[tuple[str, str, str, str], list[tuple[str, Decimal, Decimal]]] = defaultdict(list)
    blocked_price_facts: dict[str, str] = {}
    for index, raw in enumerate(_list(root["quote_lines"], "quote_lines")):
        row = _obj(raw, f"quote_lines[{index}]")
        _keys(row, {"line_id", "quote_id", "account_id", "item_id", "catalog_id", "catalog_version", "pricebook_id", "pricebook_version", "pricebook_entry_id", "quantity", "quoted_unit_price", "provided_discount_percent", "unit", "currency", "price_basis", "billing_period", "tax_present", "fee_present", "shipping_present", "ramp_present", "usage_present", "indefinite_term", "source_id", "schema_version", "observed_at"}, set(), f"quote_lines[{index}]")
        for field in ("line_id", "quote_id", "account_id", "item_id", "catalog_id", "pricebook_id", "pricebook_entry_id"): _id(row[field], field)
        if row["line_id"] not in declared: raise ValueError("quote line is undeclared")
        if row["quote_id"] != declaration["quote_id"] or row["account_id"] != declaration["account_id"]: raise ValueError("quote line declaration mismatch")
        item = items.get(row["item_id"])
        if item is None: raise ValueError("quote line item missing from catalog")
        for field in ("catalog_version", "pricebook_version", "unit", "currency", "price_basis", "billing_period", "schema_version"): _token(row[field], field)
        for field in ("catalog_id", "catalog_version", "pricebook_id", "pricebook_version", "pricebook_entry_id", "unit", "currency", "price_basis", "billing_period"):
            if row[field] != item[field]: raise ValueError(f"quote line {field} mismatch")
        for field in ("tax_present", "fee_present", "shipping_present", "ramp_present", "usage_present", "indefinite_term"):
            if not isinstance(row[field], bool): raise ValueError(f"{field} must be boolean")
        _check_source(row, "quote", bindings, "quote line")
        observed_text, observed = _ts(row["observed_at"], "observed_at")
        if observed > cutoff: raise ValueError("quote line after cutoff")
        quantity = _dec(row["quantity"], "quantity", positive=True); quoted = _dec(row["quoted_unit_price"], "quoted_unit_price")
        if quoted < 0: raise ValueError("quoted unit price must not be negative")
        if _decimal_places(quantity) > item["scale"]: raise ValueError("quantity exceeds catalog precision")
        qfid = f"fact:{row['line_id']}:quantity"; pfid = f"fact:{row['line_id']}:quoted-unit-price"
        add_fact(qfid, "quantity", quantity, row["unit"], "quantity", None, row["billing_period"], row["line_id"])
        add_fact(pfid, "quoted_unit_price", quoted, row["unit"], row["price_basis"], row["currency"], row["billing_period"], row["line_id"])
        provided_fid = None; provided = None
        if row["provided_discount_percent"] is not None:
            provided = _dec(row["provided_discount_percent"], "provided_discount_percent")
            provided_fid = f"fact:{row['line_id']}:provided-discount-percent"
            add_fact(provided_fid, "provided_discount_percent", provided, "percent", row["price_basis"], row["currency"], row["billing_period"], row["line_id"])
        adjustment = any(row[field] for field in ("tax_present", "fee_present", "shipping_present", "ramp_present", "usage_present", "indefinite_term"))
        derived_ids: list[str] = []; state = "NOT_COMPARABLE" if adjustment else "OBSERVED"
        if not adjustment:
            with localcontext() as ctx:
                ctx.prec = 80
                list_amount = item["list_price"] * quantity; quote_amount = quoted * quantity; discount_amount = list_amount - quote_amount
                raw_percent = discount_amount / list_amount * Decimal("100")
                quantum = Decimal("1").scaleb(-int(policy["calculation_policy"]["discount_scale"]))
                discount_percent = raw_percent.quantize(quantum, rounding=ROUNDING[policy["calculation_policy"]["discount_rounding"]])
            for suffix, kind, value, unit in (("list-amount", "line_list_amount", list_amount, "money"), ("quoted-amount", "line_quoted_amount", quote_amount, "money"), ("discount-amount", "discount_amount", discount_amount, "money"), ("discount-percent", "derived_discount_percent", discount_percent, "percent")):
                fid = f"fact:{row['line_id']}:{suffix}"; add_fact(fid, kind, value, unit, row["price_basis"], row["currency"], row["billing_period"], row["line_id"]); derived_ids.append(fid)
            if provided is not None and provided != discount_percent: state = "PRICE_CONFLICT"
            groups[(row["currency"], row["price_basis"], row["billing_period"], item["effective_at"])].append((row["line_id"], list_amount, quote_amount))
        receipt = {k: row[k] for k in row if k not in {"quantity", "quoted_unit_price", "provided_discount_percent"}}
        receipt.update(observed_at=observed_text, quantity_fact_id=qfid, quoted_unit_price_fact_id=pfid, provided_discount_percent_fact_id=provided_fid, derived_fact_ids=derived_ids, state=state)
        if state == "PRICE_CONFLICT":
            for fid in [pfid, provided_fid, *derived_ids]:
                if fid is not None: blocked_price_facts[fid] = "PRICE_CONFLICT"
        line_receipts.append(receipt); item_lines[row["item_id"]].append(row["line_id"]); line_quantities[row["item_id"]] = line_quantities.get(row["item_id"], Decimal("0")) + quantity; line_states[row["line_id"]] = state
    actual_lines = {row["line_id"] for row in line_receipts}
    if actual_lines != declared or len(line_receipts) != len(declared): raise ValueError("quote line population does not reconcile")

    group_receipts: list[dict[str, Any]] = []
    for index, (key, values) in enumerate(sorted(groups.items())):
        currency, basis, period, effective_at = key; gid = f"group-{index + 1}"
        with localcontext() as ctx:
            ctx.prec = 80
            list_total = sum((v[1] for v in values), Decimal("0")); quote_total = sum((v[2] for v in values), Decimal("0")); discount_total = list_total - quote_total
        ids = []
        for suffix, kind, value in (("list-total", "group_list_amount", list_total), ("quoted-total", "group_quoted_amount", quote_total), ("discount-total", "group_discount_amount", discount_total)):
            fid = f"fact:{gid}:{suffix}"; add_fact(fid, kind, value, "money", basis, currency, period, gid); ids.append(fid)
        group_receipts.append({"group_id": gid, "currency": currency, "price_basis": basis, "billing_period": period, "effective_at": effective_at, "line_ids": sorted(v[0] for v in values), "fact_ids": ids})

    processes: dict[str, dict[str, Any]] = {}; process_receipts: list[dict[str, Any]] = []
    for index, raw in enumerate(_list(root["approval_processes"], "approval_processes")):
        row = _obj(raw, f"approval_processes[{index}]")
        _keys(row, {"process_id", "process_version", "mode", "active", "applicable_rule_ids", "reviewer_role_ids", "permission_receipt_id", "permission_state", "side_effects_receipt_id", "side_effects_state", "state", "source_id", "schema_version", "observed_at"}, set(), f"approval_processes[{index}]")
        for field in ("process_id", "permission_receipt_id", "side_effects_receipt_id", "source_id"): _id(row[field], field)
        _token(row["process_version"], "process_version"); _token(row["schema_version"], "schema_version")
        if row["process_id"] in processes: raise ValueError("duplicate approval process")
        if row["mode"] not in APPROVAL_MODES or any(row[field] not in APPROVAL_STATES for field in ("state", "permission_state", "side_effects_state")) or not isinstance(row["active"], bool): raise ValueError("invalid approval process state")
        rule_ids = [_id(v, "applicable_rule_id") for v in _list(row["applicable_rule_ids"], "applicable_rule_ids")]
        role_ids = [_id(v, "reviewer_role_id") for v in _list(row["reviewer_role_ids"], "reviewer_role_ids")]
        if len(rule_ids) != len(set(rule_ids)) or len(role_ids) != len(set(role_ids)): raise ValueError("duplicate approval process IDs")
        _check_source(row, "approval", bindings, "approval process")
        observed_text, observed = _ts(row["observed_at"], "observed_at")
        if observed > cutoff: raise ValueError("approval evidence after cutoff")
        row.update(applicable_rule_ids=sorted(rule_ids), reviewer_role_ids=sorted(role_ids), observed_at=observed_text)
        processes[row["process_id"]] = row; process_receipts.append(row)

    policy_rule_ids = {rule["rule_id"] for rule in rules}
    policy_rules = {rule["rule_id"]: rule for rule in rules}
    for process in processes.values():
        if not process["applicable_rule_ids"] or not set(process["applicable_rule_ids"]).issubset(policy_rule_ids): raise ValueError("approval process references unknown or empty policy rules")
        if not process["reviewer_role_ids"]: raise ValueError("approval process reviewer roles must not be empty")
        required_roles = {policy_rules[rid]["human_review_role_id"] for rid in process["applicable_rule_ids"]}
        if not required_roles.issubset(set(process["reviewer_role_ids"])): raise ValueError("approval process lacks a policy-rule reviewer role")

    results: list[dict[str, Any]] = []; matched_by_target: dict[tuple[str, int], set[str]] = defaultdict(set)
    item_set = set(item_lines)
    for rule in rules:
        rtype = rule["rule_type"]; fact_id = None
        if rtype == "numeric":
            fact_id = rule["fact_id"]; fact = fact_values.get(fact_id)
            if fact is None: state = "SOURCE_REQUIRED"
            elif fact_id in blocked_price_facts: state = blocked_price_facts[fact_id]
            else:
                value, unit, basis, currency, period = fact
                if (unit, basis, currency, period) != (rule["unit"], rule["basis"], rule["currency"], rule["billing_period"]): state = "NOT_COMPARABLE"
                else: state = "RULE_MATCHED" if _compare(value, rule["operator"], Decimal(rule["threshold"])) else "RULE_NOT_MATCHED"
            target = fact_id
        elif rtype == "quantity":
            quantity = line_quantities.get(rule["item_id"]); target = rule["item_id"]
            if quantity is None: state = "SOURCE_REQUIRED"
            elif items[rule["item_id"]]["unit"] != rule["unit"]: state = "NOT_COMPARABLE"
            else: state = "RULE_MATCHED" if _compare(quantity, rule["operator"], Decimal(rule["threshold"])) else "RULE_NOT_MATCHED"
        elif rtype == "requires_item":
            target = f"{rule['left_item_id']}:{rule['right_item_id']}"; state = "RULE_MATCHED" if (rule["left_item_id"] not in item_set or rule["right_item_id"] in item_set) else "RULE_NOT_MATCHED"
        elif rtype == "excludes_item":
            target = f"{rule['left_item_id']}:{rule['right_item_id']}"; state = "RULE_MATCHED" if not ({rule["left_item_id"], rule["right_item_id"]} <= item_set) else "RULE_NOT_MATCHED"
        else:
            target = rule["process_id"]; process = processes.get(rule["process_id"])
            state = "SOURCE_REQUIRED" if process is None or not process["active"] or process["permission_state"] != "OBSERVED" or process["side_effects_state"] != "OBSERVED" else ("RULE_MATCHED" if process["state"] == rule["expected_state"] else "RULE_NOT_MATCHED")
        if state == "RULE_MATCHED": matched_by_target[(target, rule["precedence"])].add(rule["observation_label"])
        results.append({"rule_id": rule["rule_id"], "fact_id": fact_id, "target_receipt_id": target, "state": state, "observation_label": rule["observation_label"], "human_review_role_id": rule["human_review_role_id"]})
    conflicts = {target for target, labels in matched_by_target.items() if len(labels) > 1}
    for result in results:
        rule = next(r for r in rules if r["rule_id"] == result["rule_id"])
        if (result["target_receipt_id"], rule["precedence"]) in conflicts: result["state"] = "RULE_CONFLICT"
    states = set(line_states.values()) | {r["state"] for r in results}
    review_state = "HUMAN_REVIEW_REQUIRED" if states & {"PRICE_CONFLICT", "RULE_CONFLICT", "SOURCE_REQUIRED", "NOT_COMPARABLE", "RULE_MATCHED"} else "OBSERVED"
    return {
        "review_type": "QUOTE_CONFIGURATION_EVIDENCE_REVIEW", "review_state": review_state,
        "policy_receipt": {"policy_id": policy["policy_id"], "policy_version": policy["policy_version"], "owner_id": policy["owner_id"], "human_reviewer_role_id": policy["human_reviewer_role_id"], "effective_at": policy["effective_at"], "expires_at": policy["expires_at"], "cutoff_at": policy["cutoff_at"], "timezone": policy["timezone"], "approved_purpose": policy["approved_purpose"], "prohibited_uses": sorted(policy["prohibited_uses"]), "correction_path": policy["correction_path"], "catalog_binding": cb, "calculation_policy": policy["calculation_policy"], "source_bindings": sorted([{"record_type": k[0], "source_id": k[1], "schema_version": v} for k, v in bindings.items()], key=lambda x: (x["record_type"], x["source_id"])), "rule_receipts": sorted(rules, key=lambda x: x["rule_id"])},
        "declared_population_receipt": {"quote_id": declaration["quote_id"], "account_id": declaration["account_id"], "line_ids": sorted(line_ids)},
        "catalog_item_receipts": sorted(catalog_receipts, key=lambda x: x["item_id"]), "quote_line_receipts": sorted(line_receipts, key=lambda x: x["line_id"]),
        "numeric_fact_receipts": sorted(facts, key=lambda x: x["fact_id"]), "amount_group_receipts": group_receipts,
        "approval_process_receipts": sorted(process_receipts, key=lambda x: x["process_id"]), "rule_results": sorted(results, key=lambda x: x["rule_id"]), "boundary": BOUNDARY,
    }


def render_review_output(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    try:
        payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")) if len(sys.argv) > 1 else json.load(sys.stdin)
        sys.stdout.write(render_review_output(review_quote_configuration(payload))); return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f"INPUT_ERROR: {exc}\n"); return 2


if __name__ == "__main__": raise SystemExit(main())
