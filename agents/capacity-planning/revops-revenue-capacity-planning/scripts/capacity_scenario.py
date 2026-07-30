#!/usr/bin/env python3
"""Deterministic anonymous revenue-capacity scenario review."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_DOWN, ROUND_HALF_EVEN
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "revenue_capacity_scenario_review"
REQUIRED_PROHIBITIONS = {
    "employment-decision",
    "compensation-decision",
    "worker-ranking",
    "worker-monitoring",
    "quota-change",
    "territory-change",
    "recruiting-action",
    "budget-approval",
    "crm-write",
    "alert",
    "forecast",
    "confidence-score",
    "benchmark-substitution",
    "customer-action",
}
ROUNDING = {"half_even": ROUND_HALF_EVEN, "down": ROUND_DOWN}
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/-]*$")
DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _keys(row: dict[str, Any], required: set[str], label: str) -> None:
    actual = set(row)
    if actual != required:
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        raise ValueError(f"{label} keys mismatch; missing={missing}; extra={extra}")


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ValueError(f"{label} must be a stable lowercase ID")
    return value


def _token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} must be a structured token")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be non-empty trimmed text")
    return value


def _boolean(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{label} must be boolean")
    return value


def _integer(value: Any, label: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{label} must be an integer from {minimum} through {maximum}")
    return value


def _when(value: Any, label: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        raise ValueError(f"{label} must be second-precision UTC ending in Z")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    return value, parsed.astimezone(timezone.utc)


def _optional_when(value: Any, label: str) -> tuple[str | None, datetime | None]:
    if value is None:
        return None, None
    return _when(value, label)


def _decimal(value: Any, label: str, scale: int, *, positive: bool = False) -> Decimal:
    if not isinstance(value, str) or not DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{label} must be a non-negative plain decimal string")
    fractional = len(value.partition(".")[2])
    if fractional > scale:
        raise ValueError(f"{label} exceeds the approved scale")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} is invalid") from exc
    if not result.is_finite() or result < 0 or (positive and result <= 0):
        raise ValueError(f"{label} is outside its allowed range")
    return result


def _format(value: Decimal, scale: int) -> str:
    quantum = Decimal(1).scaleb(-scale)
    return format(value.quantize(quantum), "f")


def _unique_ids(values: list[Any], label: str) -> list[str]:
    result = [_id(value, f"{label}[]") for value in values]
    if len(result) != len(set(result)):
        raise ValueError(f"{label} contains duplicates")
    return result


def _policy(raw: Any) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, Any]]]:
    row = _object(raw, "policy")
    _keys(
        row,
        {
            "policy_id", "policy_version", "owner_role_id", "human_reviewer_role_id",
            "effective_at", "expires_at", "cutoff_at", "timezone", "approved_purpose",
            "prohibited_uses", "correction_path", "calculation_policy", "source_bindings",
        },
        "policy",
    )
    policy_id = _id(row["policy_id"], "policy.policy_id")
    policy_version = _id(row["policy_version"], "policy.policy_version")
    owner_role_id = _id(row["owner_role_id"], "policy.owner_role_id")
    reviewer_role_id = _id(row["human_reviewer_role_id"], "policy.human_reviewer_role_id")
    effective_text, effective = _when(row["effective_at"], "policy.effective_at")
    expires_text, expires = _optional_when(row["expires_at"], "policy.expires_at")
    cutoff_text, cutoff = _when(row["cutoff_at"], "policy.cutoff_at")
    timezone_name = _token(row["timezone"], "policy.timezone")
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("policy.timezone must be an IANA timezone") from exc
    if row["approved_purpose"] != PURPOSE:
        raise ValueError("policy.approved_purpose is not allowed")
    if effective > cutoff or (expires is not None and expires < cutoff):
        raise ValueError("policy is not effective at cutoff")
    prohibited = _unique_ids(_list(row["prohibited_uses"], "policy.prohibited_uses"), "policy.prohibited_uses")
    if not REQUIRED_PROHIBITIONS.issubset(prohibited):
        raise ValueError("policy.prohibited_uses is missing a required boundary")
    correction_path = _text(row["correction_path"], "policy.correction_path")

    calculation = _object(row["calculation_policy"], "policy.calculation_policy")
    _keys(calculation, {"amount_scale", "unit_scale", "rounding_mode", "allow_whole_unit_ceiling"}, "policy.calculation_policy")
    amount_scale = _integer(calculation["amount_scale"], "amount_scale", 0, 6)
    unit_scale = _integer(calculation["unit_scale"], "unit_scale", 0, 6)
    rounding_mode = _token(calculation["rounding_mode"], "rounding_mode")
    if rounding_mode not in ROUNDING:
        raise ValueError("rounding_mode is not supported")
    allow_ceiling = _boolean(calculation["allow_whole_unit_ceiling"], "allow_whole_unit_ceiling")

    bindings: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw_binding in enumerate(_list(row["source_bindings"], "policy.source_bindings")):
        binding = _object(raw_binding, f"source_bindings[{index}]")
        _keys(binding, {"source_id", "source_version", "source_kind", "schema_id", "schema_version", "authorization_id", "authorization_effective_at", "authorization_expires_at"}, f"source_bindings[{index}]")
        normalized = {
            "source_id": _id(binding["source_id"], "source_id"),
            "source_version": _id(binding["source_version"], "source_version"),
            "source_kind": _id(binding["source_kind"], "source_kind"),
            "schema_id": _id(binding["schema_id"], "schema_id"),
            "schema_version": _id(binding["schema_version"], "schema_version"),
            "authorization_id": _id(binding["authorization_id"], "authorization_id"),
        }
        if normalized["source_kind"] != "customer-supplied-anonymous-aggregate":
            raise ValueError("source_kind is not allowed")
        auth_effective_text, auth_effective = _when(binding["authorization_effective_at"], "authorization_effective_at")
        auth_expires_text, auth_expires = _optional_when(binding["authorization_expires_at"], "authorization_expires_at")
        if auth_effective > cutoff or (auth_expires is not None and auth_expires < cutoff):
            raise ValueError("source authorization is not effective at cutoff")
        normalized["authorization_effective_at"] = auth_effective_text
        normalized["authorization_expires_at"] = auth_expires_text
        key = (normalized["source_id"], normalized["source_version"])
        if key in bindings:
            raise ValueError("duplicate source binding")
        bindings[key] = normalized
    if not bindings:
        raise ValueError("at least one source binding is required")

    policy = {
        "policy_id": policy_id,
        "policy_version": policy_version,
        "owner_role_id": owner_role_id,
        "human_reviewer_role_id": reviewer_role_id,
        "effective_at": effective_text,
        "expires_at": expires_text,
        "cutoff_at": cutoff_text,
        "timezone": timezone_name,
        "approved_purpose": PURPOSE,
        "prohibited_uses": sorted(prohibited),
        "correction_path": correction_path,
        "calculation_policy": {
            "amount_scale": amount_scale,
            "unit_scale": unit_scale,
            "rounding_mode": rounding_mode,
            "allow_whole_unit_ceiling": allow_ceiling,
        },
    }
    return policy, bindings


def review_capacity_scenarios(document: Any) -> dict[str, Any]:
    root = _object(document, "document")
    _keys(root, {"review_id", "policy", "source_populations", "scenarios"}, "document")
    review_id = _id(root["review_id"], "review_id")
    policy, bindings = _policy(root["policy"])
    cutoff = _when(policy["cutoff_at"], "policy.cutoff_at")[1]

    populations: dict[str, dict[str, Any]] = {}
    declared_union: set[str] = set()
    for index, raw_population in enumerate(_list(root["source_populations"], "source_populations")):
        row = _object(raw_population, f"source_populations[{index}]")
        _keys(row, {"population_receipt_id", "source_id", "source_version", "source_kind", "schema_id", "schema_version", "authorization_id", "complete", "scenario_ids", "observed_at", "captured_at"}, f"source_populations[{index}]")
        population_id = _id(row["population_receipt_id"], "population_receipt_id")
        if population_id in populations:
            raise ValueError("duplicate population receipt")
        source_id = _id(row["source_id"], "source_id")
        source_version = _id(row["source_version"], "source_version")
        binding = bindings.get((source_id, source_version))
        if binding is None:
            raise ValueError("population does not match an approved source binding")
        if _id(row["source_kind"], "source_kind") != binding["source_kind"]:
            raise ValueError("population source kind is not allowed")
        for field in ("schema_id", "schema_version", "authorization_id"):
            if _id(row[field], field) != binding[field]:
                raise ValueError("population does not match source schema or authorization")
        if _boolean(row["complete"], "population.complete") is not True:
            raise ValueError("source population must be complete")
        scenario_ids = _unique_ids(_list(row["scenario_ids"], "population.scenario_ids"), "population.scenario_ids")
        if not scenario_ids:
            raise ValueError("source population cannot be empty")
        if declared_union.intersection(scenario_ids):
            raise ValueError("scenario appears in more than one source population")
        declared_union.update(scenario_ids)
        observed_text, observed = _when(row["observed_at"], "population.observed_at")
        captured_text, captured = _when(row["captured_at"], "population.captured_at")
        if observed > captured or captured > cutoff:
            raise ValueError("population timestamps are inconsistent with cutoff")
        populations[population_id] = {
            "population_receipt_id": population_id,
            "source_id": source_id,
            "source_version": source_version,
            "source_kind": binding["source_kind"],
            "schema_id": binding["schema_id"],
            "schema_version": binding["schema_version"],
            "authorization_id": binding["authorization_id"],
            "observed_at": observed_text,
            "captured_at": captured_text,
            "scenario_ids": scenario_ids,
        }
    if not populations:
        raise ValueError("at least one source population is required")
    population_source_keys = {(row["source_id"], row["source_version"]) for row in populations.values()}
    if population_source_keys != set(bindings):
        raise ValueError("source binding population is incomplete or contains extras")

    amount_scale = policy["calculation_policy"]["amount_scale"]
    unit_scale = policy["calculation_policy"]["unit_scale"]
    rounding = ROUNDING[policy["calculation_policy"]["rounding_mode"]]
    receipts: list[dict[str, Any]] = []
    observed_ids: set[str] = set()
    scenario_fields = {
        "scenario_id", "population_receipt_id", "source_id", "source_version", "source_kind", "schema_id",
        "schema_version", "authorization_id", "observed_at", "captured_at", "currency",
        "amount_basis", "period_id", "capacity_unit_basis", "target_amount",
        "retained_contribution_amount", "expansion_contribution_amount", "current_capacity_units",
        "observed_output_per_capacity_unit", "request_whole_unit_ceiling",
    }
    for index, raw_scenario in enumerate(_list(root["scenarios"], "scenarios")):
        row = _object(raw_scenario, f"scenarios[{index}]")
        _keys(row, scenario_fields, f"scenarios[{index}]")
        scenario_id = _id(row["scenario_id"], "scenario_id")
        if scenario_id in observed_ids:
            raise ValueError("duplicate scenario")
        observed_ids.add(scenario_id)
        population_id = _id(row["population_receipt_id"], "population_receipt_id")
        population = populations.get(population_id)
        if population is None or scenario_id not in population["scenario_ids"]:
            raise ValueError("scenario is absent from its complete source population")
        for field in ("source_id", "source_version", "source_kind", "schema_id", "schema_version", "authorization_id"):
            if _id(row[field], field) != population[field]:
                raise ValueError("scenario lineage does not match population")
        observed_text, observed = _when(row["observed_at"], "scenario.observed_at")
        captured_text, captured = _when(row["captured_at"], "scenario.captured_at")
        if observed > captured or captured > cutoff or observed_text != population["observed_at"] or captured_text != population["captured_at"]:
            raise ValueError("scenario timestamps do not match population")
        currency = row["currency"]
        if not isinstance(currency, str) or not CURRENCY_RE.fullmatch(currency):
            raise ValueError("currency must be a three-letter uppercase code")
        amount_basis = _id(row["amount_basis"], "amount_basis")
        period_id = _id(row["period_id"], "period_id")
        unit_basis = _id(row["capacity_unit_basis"], "capacity_unit_basis")
        if not unit_basis.startswith("anonymous-"):
            raise ValueError("capacity_unit_basis must be anonymous")
        target = _decimal(row["target_amount"], "target_amount", amount_scale)
        retained = _decimal(row["retained_contribution_amount"], "retained_contribution_amount", amount_scale)
        expansion = _decimal(row["expansion_contribution_amount"], "expansion_contribution_amount", amount_scale)
        current_units = _decimal(row["current_capacity_units"], "current_capacity_units", unit_scale)
        output_per_unit = _decimal(row["observed_output_per_capacity_unit"], "observed_output_per_capacity_unit", amount_scale, positive=True)
        request_ceiling = _boolean(row["request_whole_unit_ceiling"], "request_whole_unit_ceiling")
        if request_ceiling and not policy["calculation_policy"]["allow_whole_unit_ceiling"]:
            raise ValueError("whole-unit ceiling is not authorized by policy")

        gap = target - retained - expansion
        raw_units = gap / output_per_unit if gap > 0 else Decimal(0)
        difference = raw_units - current_units
        whole_ceiling = raw_units.to_integral_value(rounding=ROUND_CEILING) if request_ceiling else None
        receipts.append({
            "scenario_id": scenario_id,
            "review_state": "HUMAN_REVIEW_REQUIRED",
            "action_authorized": False,
            "input_receipt": {
                "population_receipt_id": population_id,
                "source_id": population["source_id"],
                "source_version": population["source_version"],
                "source_kind": population["source_kind"],
                "schema_id": population["schema_id"],
                "schema_version": population["schema_version"],
                "authorization_id": population["authorization_id"],
                "observed_at": observed_text,
                "captured_at": captured_text,
                "currency": currency,
                "amount_basis": amount_basis,
                "period_id": period_id,
                "capacity_unit_basis": unit_basis,
                "target_amount": _format(target, amount_scale),
                "retained_contribution_amount": _format(retained, amount_scale),
                "expansion_contribution_amount": _format(expansion, amount_scale),
                "current_capacity_units": _format(current_units, unit_scale),
                "observed_output_per_capacity_unit": _format(output_per_unit, amount_scale),
                "request_whole_unit_ceiling": request_ceiling,
            },
            "calculation_receipt": {
                "capacity_gap_amount": _format(gap, amount_scale),
                "modeled_capacity_units": _format(raw_units.quantize(Decimal(1).scaleb(-unit_scale), rounding=rounding), unit_scale),
                "whole_unit_ceiling": format(whole_ceiling, "f") if whole_ceiling is not None else None,
                "capacity_unit_difference": _format(difference.quantize(Decimal(1).scaleb(-unit_scale), rounding=rounding), unit_scale),
            },
            "limitations": [
                "anonymous-scenario-arithmetic-only",
                "no-benchmark-substitution",
                "no-forecast-or-causal-claim",
                "no-employment-financial-customer-or-operational-action",
            ],
        })
    if observed_ids != declared_union:
        raise ValueError("scenario population is incomplete or contains extras")

    return {
        "review_id": review_id,
        "review_state": "HUMAN_REVIEW_REQUIRED",
        "action_authorized": False,
        "policy_receipt": policy,
        "scenario_receipts": sorted(receipts, key=lambda item: item["scenario_id"]),
    }


def render_review_output(result: dict[str, Any]) -> str:
    return json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


if __name__ == "__main__":
    import sys

    payload = json.load(sys.stdin)
    sys.stdout.write(render_review_output(review_capacity_scenarios(payload)))
