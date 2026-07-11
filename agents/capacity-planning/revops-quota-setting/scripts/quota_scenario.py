#!/usr/bin/env python3
"""Deterministic anonymous quota-policy scenario evidence review."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_EVEN
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PURPOSE = "quota_policy_scenario_review"
SOURCE_KIND = "customer-supplied-anonymous-quota-plan"
COVERAGE_STATES = {"accepted", "missing", "conflicting", "suppressed"}
CALCULATION_RULES = {"candidate-plan-total", "coverage-ratio", "prior-quota-delta", "target-difference"}
REQUIRED_PROHIBITIONS = {
    "account-reassignment",
    "alert",
    "benchmark-substitution",
    "causal-claim",
    "compensation-decision",
    "confidence-score",
    "crm-read",
    "crm-write",
    "customer-action",
    "employment-decision",
    "fairness-label",
    "forecast",
    "quota-achievability-label",
    "quota-recommendation",
    "quota-write",
    "territory-change",
    "worker-monitoring",
    "worker-ranking",
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


def _anonymous_id(value: Any, label: str) -> str:
    result = _id(value, label)
    if not result.startswith("anonymous-"):
        raise ValueError(f"{label} must begin with anonymous-")
    return result


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
    if len(value.partition(".")[2]) > scale:
        raise ValueError(f"{label} exceeds the approved scale")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} is invalid") from exc
    if not result.is_finite() or result < 0 or (positive and result <= 0):
        raise ValueError(f"{label} is outside its allowed range")
    return result


def _format(value: Decimal, scale: int, rounding: str) -> str:
    quantum = Decimal(1).scaleb(-scale)
    return format(value.quantize(quantum, rounding=ROUNDING[rounding]), "f")


def _unique_ids(values: list[Any], label: str, *, anonymous: bool = False) -> list[str]:
    parse = _anonymous_id if anonymous else _id
    result = [parse(value, f"{label}[]") for value in values]
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
            "prohibited_uses", "correction_path", "appeal_path", "privacy_review_receipt_id",
            "workforce_review_receipt_id", "compensation_review_receipt_id",
            "affected_worker_notice_receipt_id", "calculation_policy", "source_bindings",
        },
        "policy",
    )
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

    calculation = _object(row["calculation_policy"], "policy.calculation_policy")
    _keys(calculation, {"amount_scale", "ratio_scale", "rounding_mode", "approved_rule_ids"}, "policy.calculation_policy")
    amount_scale = _integer(calculation["amount_scale"], "amount_scale", 0, 6)
    ratio_scale = _integer(calculation["ratio_scale"], "ratio_scale", 0, 6)
    rounding_mode = _token(calculation["rounding_mode"], "rounding_mode")
    if rounding_mode not in ROUNDING:
        raise ValueError("rounding_mode is not supported")
    approved_rules = _unique_ids(_list(calculation["approved_rule_ids"], "approved_rule_ids"), "approved_rule_ids")
    if set(approved_rules) != CALCULATION_RULES:
        raise ValueError("approved_rule_ids must match the exact helper calculations")

    bindings: dict[tuple[str, str], dict[str, Any]] = {}
    binding_fields = {
        "source_id", "source_version", "source_kind", "schema_id", "schema_version",
        "authorization_id", "authorization_effective_at", "authorization_expires_at",
        "approved_currency", "approved_amount_basis", "approved_period_id",
        "approved_territory_basis", "approved_coverage_basis",
    }
    for index, raw_binding in enumerate(_list(row["source_bindings"], "policy.source_bindings")):
        binding = _object(raw_binding, f"source_bindings[{index}]")
        _keys(binding, binding_fields, f"source_bindings[{index}]")
        normalized = {
            "source_id": _id(binding["source_id"], "source_id"),
            "source_version": _id(binding["source_version"], "source_version"),
            "source_kind": _id(binding["source_kind"], "source_kind"),
            "schema_id": _id(binding["schema_id"], "schema_id"),
            "schema_version": _id(binding["schema_version"], "schema_version"),
            "authorization_id": _id(binding["authorization_id"], "authorization_id"),
            "approved_currency": binding["approved_currency"],
            "approved_amount_basis": _id(binding["approved_amount_basis"], "approved_amount_basis"),
            "approved_period_id": _id(binding["approved_period_id"], "approved_period_id"),
            "approved_territory_basis": _id(binding["approved_territory_basis"], "approved_territory_basis"),
            "approved_coverage_basis": _id(binding["approved_coverage_basis"], "approved_coverage_basis"),
        }
        if normalized["source_kind"] != SOURCE_KIND:
            raise ValueError("source_kind is not allowed")
        if not isinstance(normalized["approved_currency"], str) or not CURRENCY_RE.fullmatch(normalized["approved_currency"]):
            raise ValueError("approved_currency must be a three-letter uppercase code")
        if not normalized["approved_territory_basis"].startswith("anonymous-"):
            raise ValueError("approved_territory_basis must be anonymous")
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
        "policy_id": _id(row["policy_id"], "policy.policy_id"),
        "policy_version": _id(row["policy_version"], "policy.policy_version"),
        "owner_role_id": _id(row["owner_role_id"], "policy.owner_role_id"),
        "human_reviewer_role_id": _id(row["human_reviewer_role_id"], "policy.human_reviewer_role_id"),
        "effective_at": effective_text,
        "expires_at": expires_text,
        "cutoff_at": cutoff_text,
        "timezone": timezone_name,
        "approved_purpose": PURPOSE,
        "prohibited_uses": sorted(prohibited),
        "correction_path": _text(row["correction_path"], "policy.correction_path"),
        "appeal_path": _text(row["appeal_path"], "policy.appeal_path"),
        "privacy_review_receipt_id": _id(row["privacy_review_receipt_id"], "privacy_review_receipt_id"),
        "workforce_review_receipt_id": _id(row["workforce_review_receipt_id"], "workforce_review_receipt_id"),
        "compensation_review_receipt_id": _id(row["compensation_review_receipt_id"], "compensation_review_receipt_id"),
        "affected_worker_notice_receipt_id": _id(row["affected_worker_notice_receipt_id"], "affected_worker_notice_receipt_id"),
        "calculation_policy": {
            "amount_scale": amount_scale,
            "ratio_scale": ratio_scale,
            "rounding_mode": rounding_mode,
            "approved_rule_ids": sorted(approved_rules),
        },
    }
    return policy, bindings


def review_quota_scenarios(document: Any) -> dict[str, Any]:
    root = _object(document, "document")
    _keys(root, {"review_id", "policy", "source_populations", "scenarios"}, "document")
    review_id = _id(root["review_id"], "review_id")
    policy, bindings = _policy(root["policy"])
    cutoff = _when(policy["cutoff_at"], "policy.cutoff_at")[1]

    populations: dict[str, dict[str, Any]] = {}
    declared_scenarios: set[str] = set()
    population_fields = {
        "population_receipt_id", "source_id", "source_version", "source_kind", "schema_id",
        "schema_version", "authorization_id", "complete", "scenario_ids", "observed_at", "captured_at",
    }
    for index, raw_population in enumerate(_list(root["source_populations"], "source_populations")):
        row = _object(raw_population, f"source_populations[{index}]")
        _keys(row, population_fields, f"source_populations[{index}]")
        population_id = _id(row["population_receipt_id"], "population_receipt_id")
        if population_id in populations:
            raise ValueError("duplicate population receipt")
        source_id = _id(row["source_id"], "source_id")
        source_version = _id(row["source_version"], "source_version")
        binding = bindings.get((source_id, source_version))
        if binding is None:
            raise ValueError("population does not match an approved source binding")
        for field in ("source_kind", "schema_id", "schema_version", "authorization_id"):
            if _id(row[field], field) != binding[field]:
                raise ValueError("population does not match source schema or authorization")
        if _boolean(row["complete"], "population.complete") is not True:
            raise ValueError("source population must be complete")
        scenario_ids = _unique_ids(_list(row["scenario_ids"], "population.scenario_ids"), "population.scenario_ids")
        if not scenario_ids or declared_scenarios.intersection(scenario_ids):
            raise ValueError("source population is empty or overlaps another population")
        declared_scenarios.update(scenario_ids)
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
            "binding": binding,
        }
    if not populations:
        raise ValueError("at least one source population is required")
    if {(p["source_id"], p["source_version"]) for p in populations.values()} != set(bindings):
        raise ValueError("source binding population is incomplete or contains extras")

    amount_scale = policy["calculation_policy"]["amount_scale"]
    ratio_scale = policy["calculation_policy"]["ratio_scale"]
    rounding_mode = policy["calculation_policy"]["rounding_mode"]
    observed_scenarios: set[str] = set()
    receipts: list[dict[str, Any]] = []
    scenario_fields = {
        "scenario_id", "population_receipt_id", "source_id", "source_version", "source_kind",
        "schema_id", "schema_version", "authorization_id", "observed_at", "captured_at",
        "currency", "amount_basis", "period_id", "territory_basis", "coverage_basis",
        "territory_population_receipt_id", "territory_population_complete", "declared_territory_ids",
        "corporate_target_amount", "territory_rows",
    }
    row_fields = {"territory_id", "candidate_quota_amount", "prior_quota_amount", "coverage_state", "coverage_amount"}
    for index, raw_scenario in enumerate(_list(root["scenarios"], "scenarios")):
        row = _object(raw_scenario, f"scenarios[{index}]")
        _keys(row, scenario_fields, f"scenarios[{index}]")
        scenario_id = _id(row["scenario_id"], "scenario_id")
        if scenario_id in observed_scenarios:
            raise ValueError("duplicate scenario")
        observed_scenarios.add(scenario_id)
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
        binding = population["binding"]
        bases = {
            "currency": row["currency"],
            "amount_basis": _id(row["amount_basis"], "amount_basis"),
            "period_id": _id(row["period_id"], "period_id"),
            "territory_basis": _id(row["territory_basis"], "territory_basis"),
            "coverage_basis": _id(row["coverage_basis"], "coverage_basis"),
        }
        if not isinstance(bases["currency"], str) or not CURRENCY_RE.fullmatch(bases["currency"]):
            raise ValueError("currency must be a three-letter uppercase code")
        for actual, approved in (
            (bases["currency"], binding["approved_currency"]),
            (bases["amount_basis"], binding["approved_amount_basis"]),
            (bases["period_id"], binding["approved_period_id"]),
            (bases["territory_basis"], binding["approved_territory_basis"]),
            (bases["coverage_basis"], binding["approved_coverage_basis"]),
        ):
            if actual != approved:
                raise ValueError("scenario basis does not match approved source binding")
        if not bases["territory_basis"].startswith("anonymous-"):
            raise ValueError("territory_basis must be anonymous")
        if _boolean(row["territory_population_complete"], "territory_population_complete") is not True:
            raise ValueError("territory population must be complete")
        territory_population_id = _id(row["territory_population_receipt_id"], "territory_population_receipt_id")
        declared_territories = _unique_ids(
            _list(row["declared_territory_ids"], "declared_territory_ids"),
            "declared_territory_ids",
            anonymous=True,
        )
        if not declared_territories:
            raise ValueError("territory population cannot be empty")
        target = _decimal(row["corporate_target_amount"], "corporate_target_amount", amount_scale)

        observed_territories: set[str] = set()
        territory_receipts: list[dict[str, Any]] = []
        plan_total = Decimal(0)
        for row_index, raw_territory in enumerate(_list(row["territory_rows"], "territory_rows")):
            territory = _object(raw_territory, f"territory_rows[{row_index}]")
            _keys(territory, row_fields, f"territory_rows[{row_index}]")
            territory_id = _anonymous_id(territory["territory_id"], "territory_id")
            if territory_id in observed_territories:
                raise ValueError("duplicate territory row")
            observed_territories.add(territory_id)
            candidate = _decimal(territory["candidate_quota_amount"], "candidate_quota_amount", amount_scale, positive=True)
            prior = _decimal(territory["prior_quota_amount"], "prior_quota_amount", amount_scale)
            state = _id(territory["coverage_state"], "coverage_state")
            if state not in COVERAGE_STATES:
                raise ValueError("coverage_state is not supported")
            coverage_raw = territory["coverage_amount"]
            if state == "accepted":
                coverage = _decimal(coverage_raw, "coverage_amount", amount_scale)
                ratio = coverage / candidate
                ratio_text = _format(ratio, ratio_scale, rounding_mode)
                coverage_text = _format(coverage, amount_scale, rounding_mode)
            else:
                if coverage_raw is not None:
                    raise ValueError("unresolved coverage state must not carry an amount")
                ratio_text = None
                coverage_text = None
            plan_total += candidate
            territory_receipts.append({
                "territory_id": territory_id,
                "input_receipt": {
                    "candidate_quota_amount": _format(candidate, amount_scale, rounding_mode),
                    "prior_quota_amount": _format(prior, amount_scale, rounding_mode),
                    "coverage_state": state,
                    "coverage_amount": coverage_text,
                },
                "calculation_receipt": {
                    "prior_quota_delta": _format(candidate - prior, amount_scale, rounding_mode),
                    "coverage_ratio": ratio_text,
                },
            })
        if observed_territories != set(declared_territories):
            raise ValueError("territory population is incomplete or contains extras")

        receipts.append({
            "scenario_id": scenario_id,
            "review_state": "HUMAN_REVIEW_REQUIRED",
            "action_authorized": False,
            "input_receipt": {
                "population_receipt_id": population_id,
                "territory_population_receipt_id": territory_population_id,
                "source_id": population["source_id"],
                "source_version": population["source_version"],
                "source_kind": population["source_kind"],
                "schema_id": population["schema_id"],
                "schema_version": population["schema_version"],
                "authorization_id": population["authorization_id"],
                "authorization_effective_at": binding["authorization_effective_at"],
                "authorization_expires_at": binding["authorization_expires_at"],
                "observed_at": observed_text,
                "captured_at": captured_text,
                **bases,
                "corporate_target_amount": _format(target, amount_scale, rounding_mode),
                "declared_territory_ids": sorted(declared_territories),
            },
            "calculation_receipt": {
                "candidate_plan_total": _format(plan_total, amount_scale, rounding_mode),
                "target_difference": _format(plan_total - target, amount_scale, rounding_mode),
            },
            "territory_receipts": sorted(territory_receipts, key=lambda item: item["territory_id"]),
            "limitations": [
                "anonymous-customer-authored-scenario-arithmetic-only",
                "no-fairness-or-achievability-label",
                "no-forecast-confidence-or-causal-claim",
                "no-quota-compensation-territory-account-worker-customer-or-crm-action",
            ],
        })
    if observed_scenarios != declared_scenarios:
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
    sys.stdout.write(render_review_output(review_quota_scenarios(payload)))
