#!/usr/bin/env python3
"""Deterministic, read-only internal pricing scenario evidence review."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


BOUNDARY = "NO OPTIMAL-PRICE, ELASTICITY, ARR, PRICE, DISCOUNT, PACKAGE, APPROVAL, CRM, CUSTOMER, OR WORKFORCE ACTION"
PURPOSE = "internal_pricing_scenario_evidence_review"
LANES = {"approved_list", "approved_quote", "approved_final", "approved_contract", "customer_scenario"}
REQUIRED_PROHIBITED = {
    "price-recommendation", "discount-recommendation", "optimal-price-claim", "elasticity-claim",
    "arr-claim", "competitor-data", "pricing-approval", "downstream-decision", "monitoring", "alert",
    "system-read", "crm-write", "publication", "customer-action", "workforce-action",
}
ROUNDING = {"half_even": ROUND_HALF_EVEN, "half_up": ROUND_HALF_UP, "down": ROUND_DOWN}
R1_WORDS = {"small", "large", "enough", "limited", "insufficient", "good", "poor", "high", "low"}
ACTION_WORDS = {"send", "notify", "assign", "route", "update", "write", "create", "delete", "approve", "reject", "coach", "escalate", "message", "schedule"}
FORBIDDEN_PARTS = {"name", "domain", "url", "email", "phone", "address", "contact", "text", "notes", "transcript", "quote", "post", "seller", "manager", "worker", "trait", "sentiment", "confidence", "threat", "risk", "rank", "forecast", "recommendation", "message", "channel"}
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,79}$")
TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/+-]{0,159}$")
DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


def _obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _arr(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _keys(row: dict[str, Any], required: set[str], label: str) -> None:
    missing = required - set(row)
    extra = set(row) - required
    if missing:
        raise ValueError(f"{label} missing fields: {sorted(missing)}")
    if extra:
        raise ValueError(f"{label} has unsupported fields: {sorted(extra)}")


def _scan(value: Any, path: str = "document") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            parts = {part for part in re.split(r"[^a-z0-9]+", key.lower()) if part}
            if parts & FORBIDDEN_PARTS:
                raise ValueError(f"{path}.{key} is prohibited")
            _scan(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan(child, f"{path}[{index}]")
    elif isinstance(value, str) and "@" in value:
        raise ValueError(f"{path} contains a direct contact identifier")


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ValueError(f"{label} must be a stable pseudonymous identifier")
    parts = {part.lower() for part in re.split(r"[_.:-]+", value)}
    if parts & R1_WORDS or parts & ACTION_WORDS:
        raise ValueError(f"{label} contains a prohibited token")
    return value


def _token(value: Any, label: str, allow_action: bool = False) -> str:
    if not isinstance(value, str) or not TOKEN_RE.fullmatch(value) or "@" in value:
        raise ValueError(f"{label} must be a structured token")
    parts = {part.lower() for part in re.split(r"[_.:/+-]+", value)}
    if parts & R1_WORDS or (not allow_action and parts & ACTION_WORDS):
        raise ValueError(f"{label} contains a prohibited token")
    return value


def _time(value: Any, label: str) -> tuple[str, datetime]:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO-8601 timestamp")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include an offset")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _timezone_name(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an IANA timezone")
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"{label} must be an IANA timezone") from exc
    return value


def _dec(value: Any, label: str) -> Decimal:
    if not isinstance(value, str) or not DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{label} must be a positive plain Decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} is invalid") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError(f"{label} must be positive and finite")
    return number


def _normal(number: Decimal) -> str:
    text = format(number, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def review_price_evidence(document: dict[str, Any]) -> dict[str, Any]:
    root = _obj(document, "document")
    _scan(root)
    _keys(root, {"policy", "declaration", "source_populations", "observations", "comparisons"}, "document")

    policy = _obj(root["policy"], "policy")
    _keys(policy, {"policy_id", "policy_version", "owner_id", "human_reviewer_role_id", "finance_approval_id", "legal_competition_approval_id", "privacy_approval_id", "workforce_approval_id", "recipient_policy_id", "retention_policy_id", "scenario_policy_id", "effective_at", "expires_at", "cutoff_at", "timezone", "approved_purpose", "prohibited_uses", "correction_path", "calculation_policy", "source_bindings", "comparison_bases"}, "policy")
    for field in ("policy_id", "owner_id", "human_reviewer_role_id", "finance_approval_id", "legal_competition_approval_id", "privacy_approval_id", "workforce_approval_id", "recipient_policy_id", "retention_policy_id", "scenario_policy_id"):
        _id(policy[field], f"policy.{field}")
    for field in ("policy_version", "correction_path"):
        _token(policy[field], f"policy.{field}")
    policy["timezone"] = _timezone_name(policy["timezone"], "policy.timezone")
    if policy["approved_purpose"] != PURPOSE:
        raise ValueError("policy purpose is not authorized")
    prohibited = [_token(item, "policy.prohibited_use", allow_action=True) for item in _arr(policy["prohibited_uses"], "policy.prohibited_uses")]
    if not REQUIRED_PROHIBITED.issubset(set(prohibited)):
        raise ValueError("policy does not preserve the fixed boundary")
    policy["effective_at"], effective = _time(policy["effective_at"], "policy.effective_at")
    policy["cutoff_at"], cutoff = _time(policy["cutoff_at"], "policy.cutoff_at")
    if effective > cutoff:
        raise ValueError("policy is not effective at cutoff")
    if policy["expires_at"] is not None:
        policy["expires_at"], expires = _time(policy["expires_at"], "policy.expires_at")
        if cutoff >= expires:
            raise ValueError("policy is expired at cutoff")

    calc = _obj(policy["calculation_policy"], "policy.calculation_policy")
    _keys(calc, {"percentage_scale", "rounding_mode"}, "policy.calculation_policy")
    if not isinstance(calc["percentage_scale"], int) or isinstance(calc["percentage_scale"], bool) or not 0 <= calc["percentage_scale"] <= 8:
        raise ValueError("percentage_scale is invalid")
    if calc["rounding_mode"] not in ROUNDING:
        raise ValueError("rounding_mode is unsupported")

    bindings: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw in enumerate(_arr(policy["source_bindings"], "policy.source_bindings")):
        row = _obj(raw, f"source_bindings[{index}]")
        _keys(row, {"lane", "source_id", "schema_version", "authorization_id", "query_receipt_id", "page_receipt_id", "pseudonymization_receipt_id", "authorization_effective_at", "authorization_expires_at"}, f"source_bindings[{index}]")
        if row["lane"] not in LANES:
            raise ValueError("source lane is unsupported")
        for field in ("source_id", "authorization_id", "query_receipt_id", "page_receipt_id", "pseudonymization_receipt_id"):
            _id(row[field], f"source_binding.{field}")
        _token(row["schema_version"], "source_binding.schema_version")
        row["authorization_effective_at"], auth_effective = _time(row["authorization_effective_at"], "source_binding.authorization_effective_at")
        if auth_effective > cutoff:
            raise ValueError("source authorization is not effective at cutoff")
        if row["authorization_expires_at"] is not None:
            row["authorization_expires_at"], auth_expires = _time(row["authorization_expires_at"], "source_binding.authorization_expires_at")
            if cutoff >= auth_expires:
                raise ValueError("source authorization is expired at cutoff")
        key = (row["lane"], row["source_id"])
        if key in bindings:
            raise ValueError("duplicate source binding")
        bindings[key] = row
    if not bindings:
        raise ValueError("source bindings must not be empty")

    bases: dict[str, dict[str, Any]] = {}
    basis_fields = {"basis_id", "basis_version", "basis_approval_id", "product_scope_id", "configuration_scope_id", "quantity", "unit", "currency", "price_kind", "billing_basis", "billing_period", "contract_term", "region", "tax_basis", "fee_basis", "discount_basis"}
    for index, raw in enumerate(_arr(policy["comparison_bases"], "policy.comparison_bases")):
        row = _obj(raw, f"comparison_bases[{index}]")
        _keys(row, basis_fields, f"comparison_bases[{index}]")
        for field in ("basis_id", "basis_approval_id", "product_scope_id", "configuration_scope_id"):
            _id(row[field], f"basis.{field}")
        for field in basis_fields - {"basis_id", "basis_approval_id", "product_scope_id", "configuration_scope_id", "quantity"}:
            _token(row[field], f"basis.{field}")
        row["quantity"] = _normal(_dec(row["quantity"], "basis.quantity"))
        if row["basis_id"] in bases:
            raise ValueError("duplicate comparison basis")
        bases[row["basis_id"]] = row
    if not bases:
        raise ValueError("comparison bases must not be empty")

    declaration = _obj(root["declaration"], "declaration")
    _keys(declaration, {"review_id", "declared_observation_count", "observation_ids"}, "declaration")
    _id(declaration["review_id"], "declaration.review_id")
    declared_ids = [_id(item, "declaration.observation_id") for item in _arr(declaration["observation_ids"], "declaration.observation_ids")]
    if not declared_ids or len(declared_ids) != len(set(declared_ids)):
        raise ValueError("declared observation IDs must be non-empty and unique")
    if not isinstance(declaration["declared_observation_count"], int) or isinstance(declaration["declared_observation_count"], bool) or declaration["declared_observation_count"] != len(declared_ids):
        raise ValueError("declared observation count does not reconcile")
    declared = set(declared_ids)

    populations: list[dict[str, Any]] = []
    population_by_id: dict[str, dict[str, Any]] = {}
    population_keys: set[tuple[str, str]] = set()
    partition: list[str] = []
    for index, raw in enumerate(_arr(root["source_populations"], "source_populations")):
        row = _obj(raw, f"source_populations[{index}]")
        _keys(row, {"population_receipt_id", "lane", "source_id", "schema_version", "authorization_id", "complete", "observation_ids", "captured_at"}, f"source_populations[{index}]")
        for field in ("population_receipt_id", "source_id", "authorization_id"):
            _id(row[field], f"source_population.{field}")
        binding = bindings.get((row["lane"], row["source_id"]))
        if binding is None:
            raise ValueError("population lacks an approved source binding")
        for field in ("schema_version", "authorization_id"):
            if row[field] != binding[field]:
                raise ValueError(f"population does not match approved {field}")
        if row["complete"] is not True:
            raise ValueError("source population must be complete")
        ids = [_id(item, "source_population.observation_id") for item in _arr(row["observation_ids"], "source_population.observation_ids")]
        if not ids or len(ids) != len(set(ids)) or not set(ids).issubset(declared):
            raise ValueError("source population IDs are invalid")
        row["observation_ids"] = sorted(ids)
        partition.extend(ids)
        row["captured_at"], captured = _time(row["captured_at"], "source_population.captured_at")
        if captured > cutoff:
            raise ValueError("population capture occurs after cutoff")
        if row["population_receipt_id"] in population_by_id or (row["lane"], row["source_id"]) in population_keys:
            raise ValueError("duplicate source population")
        population_by_id[row["population_receipt_id"]] = row
        population_keys.add((row["lane"], row["source_id"]))
        populations.append(row)
    if population_keys != set(bindings) or sorted(partition) != sorted(declared_ids):
        raise ValueError("source populations do not exactly partition the declaration")

    observations: list[dict[str, Any]] = []
    observation_by_id: dict[str, dict[str, Any]] = {}
    observation_fields = {"observation_id", "lane", "party_id", "item_id", "source_id", "schema_version", "authorization_id", "basis_id", "basis_version", "amount", "effective_begin", "effective_end", "occurred_at", "captured_at", "population_receipt_id", "source_receipt_id"}
    source_receipt_ids: set[str] = set()
    for index, raw in enumerate(_arr(root["observations"], "observations")):
        row = _obj(raw, f"observations[{index}]")
        _keys(row, observation_fields, f"observations[{index}]")
        for field in ("observation_id", "party_id", "item_id", "source_id", "authorization_id", "basis_id", "population_receipt_id", "source_receipt_id"):
            _id(row[field], f"observation.{field}")
        if row["source_receipt_id"] in source_receipt_ids:
            raise ValueError("observation source receipts must be unique")
        source_receipt_ids.add(row["source_receipt_id"])
        if row["observation_id"] not in declared or row["observation_id"] in observation_by_id:
            raise ValueError("observation ID is undeclared or duplicated")
        binding = bindings.get((row["lane"], row["source_id"]))
        if binding is None or row["schema_version"] != binding["schema_version"] or row["authorization_id"] != binding["authorization_id"]:
            raise ValueError("observation source binding is invalid")
        basis = bases.get(row["basis_id"])
        if basis is None or row["basis_version"] != basis["basis_version"]:
            raise ValueError("observation basis is invalid")
        population = population_by_id.get(row["population_receipt_id"])
        if population is None or row["observation_id"] not in population["observation_ids"] or (row["lane"], row["source_id"]) != (population["lane"], population["source_id"]):
            raise ValueError("observation population receipt is invalid")
        row["amount"] = _normal(_dec(row["amount"], "observation.amount"))
        row["effective_begin"], begin = _time(row["effective_begin"], "observation.effective_begin")
        row["effective_end"], end = _time(row["effective_end"], "observation.effective_end")
        row["occurred_at"], occurred = _time(row["occurred_at"], "observation.occurred_at")
        row["captured_at"], captured = _time(row["captured_at"], "observation.captured_at")
        auth_effective = _time(binding["authorization_effective_at"], "binding.authorization_effective_at")[1]
        auth_expires = None if binding["authorization_expires_at"] is None else _time(binding["authorization_expires_at"], "binding.authorization_expires_at")[1]
        if begin >= end or occurred > captured or captured > cutoff or min(begin, occurred, captured) < auth_effective or (auth_expires is not None and max(end, occurred, captured) > auth_expires):
            raise ValueError("observation timestamps are invalid")
        observation_by_id[row["observation_id"]] = row
        observations.append(row)
    if set(observation_by_id) != declared:
        raise ValueError("observations do not reconcile to declaration")
    for population in populations:
        population_capture = _time(population["captured_at"], "population.captured_at")[1]
        if any(_time(observation_by_id[item]["captured_at"], "observation.captured_at")[1] > population_capture for item in population["observation_ids"]):
            raise ValueError("source population completion predates an observation")

    comparisons: list[dict[str, Any]] = []
    numeric_receipts: list[dict[str, str]] = []
    comparison_ids: set[str] = set()
    for index, raw in enumerate(_arr(root["comparisons"], "comparisons")):
        row = _obj(raw, f"comparisons[{index}]")
        _keys(row, {"comparison_id", "left_observation_id", "right_observation_id", "comparison_at"}, f"comparisons[{index}]")
        for field in ("comparison_id", "left_observation_id", "right_observation_id"):
            _id(row[field], f"comparison.{field}")
        if row["comparison_id"] in comparison_ids:
            raise ValueError("duplicate comparison ID")
        comparison_ids.add(row["comparison_id"])
        row["comparison_at"], at = _time(row["comparison_at"], "comparison.comparison_at")
        left = observation_by_id.get(row["left_observation_id"])
        right = observation_by_id.get(row["right_observation_id"])
        result = {"comparison_id": row["comparison_id"], "left_observation_receipt_id": row["left_observation_id"], "right_observation_receipt_id": row["right_observation_id"], "comparison_at": row["comparison_at"]}
        if left is None or right is None:
            result.update(state="SOURCE_REQUIRED", numeric_receipt_ids=[])
        elif left["observation_id"] == right["observation_id"]:
            result.update(state="NOT_COMPARABLE", numeric_receipt_ids=[])
        elif left["basis_id"] != right["basis_id"] or left["basis_version"] != right["basis_version"]:
            result.update(state="NOT_COMPARABLE", numeric_receipt_ids=[])
        elif "customer_scenario" not in {left["lane"], right["lane"]} or left["lane"] == right["lane"]:
            result.update(state="NOT_COMPARABLE", numeric_receipt_ids=[])
        else:
            left_begin = _time(left["effective_begin"], "left.effective_begin")[1]
            left_end = _time(left["effective_end"], "left.effective_end")[1]
            right_begin = _time(right["effective_begin"], "right.effective_begin")[1]
            right_end = _time(right["effective_end"], "right.effective_end")[1]
            if not (left_begin <= at < left_end and right_begin <= at < right_end):
                result.update(state="NOT_COMPARABLE", numeric_receipt_ids=[])
            else:
                left_amount, right_amount = Decimal(left["amount"]), Decimal(right["amount"])
                difference = left_amount - right_amount
                scale = calc["percentage_scale"]
                with localcontext() as context:
                    context.prec = max(50, scale + 20)
                    percentage = ((difference / right_amount) * Decimal("100")).quantize(Decimal(1).scaleb(-scale), rounding=ROUNDING[calc["rounding_mode"]])
                difference_id = f"numeric-{row['comparison_id']}-difference"
                percentage_id = f"numeric-{row['comparison_id']}-percentage"
                numeric_receipts.extend([
                    {"numeric_receipt_id": difference_id, "kind": "amount_difference", "left_observation_receipt_id": left["observation_id"], "right_observation_receipt_id": right["observation_id"], "unit_basis_receipt_id": left["basis_id"], "value": _normal(difference)},
                    {"numeric_receipt_id": percentage_id, "kind": "percentage_difference", "left_observation_receipt_id": left["observation_id"], "right_observation_receipt_id": right["observation_id"], "unit": "percent", "value": _normal(percentage)},
                ])
                result.update(state="COMPARABLE", numeric_receipt_ids=[difference_id, percentage_id])
        comparisons.append(result)

    policy_receipt = dict(policy)
    policy_receipt["prohibited_uses"] = sorted(prohibited)
    policy_receipt["source_bindings"] = sorted(policy["source_bindings"], key=lambda row: (row["lane"], row["source_id"]))
    policy_receipt["comparison_bases"] = sorted(policy["comparison_bases"], key=lambda row: row["basis_id"])
    population_receipts = [dict(row, member_count=str(len(row["observation_ids"]))) for row in sorted(populations, key=lambda row: row["population_receipt_id"])]
    return {
        "boundary": BOUNDARY,
        "comparison_receipts": sorted(comparisons, key=lambda row: row["comparison_id"]),
        "declared_population_receipt": {"observation_ids": sorted(declared_ids), "member_count": str(len(declared_ids))},
        "numeric_receipts": sorted(numeric_receipts, key=lambda row: row["numeric_receipt_id"]),
        "observation_receipts": sorted(observations, key=lambda row: row["observation_id"]),
        "policy_receipt": policy_receipt,
        "review_id": declaration["review_id"],
        "review_state": "HUMAN_REVIEW_REQUIRED" if any(row["state"] == "COMPARABLE" for row in comparisons) else "OBSERVED",
        "review_type": "INTERNAL_PRICING_SCENARIO_EVIDENCE_REVIEW",
        "source_population_receipts": population_receipts,
        "pricing_action_authorized": False,
        "system_action_authorized": False,
        "publication_authorized": False,
        "downstream_decision_authorized": False,
    }


def render_review_output(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n\n"


def main(argv: list[str]) -> int:
    try:
        if len(argv) > 2:
            raise ValueError("usage: pricing_evidence.py [input.json]")
        raw = Path(argv[1]).read_text(encoding="utf-8") if len(argv) == 2 else sys.stdin.read()
        sys.stdout.write(render_review_output(review_price_evidence(json.loads(raw))))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f"pricing scenario evidence review failed: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
