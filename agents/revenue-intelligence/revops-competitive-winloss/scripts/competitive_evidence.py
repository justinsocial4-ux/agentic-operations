#!/usr/bin/env python3
"""Deterministic, read-only competitive win/loss evidence review."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
from pathlib import Path
from typing import Any


BOUNDARY = "NO CAUSAL EXPLANATION / NO THREAT, RANKING, STRATEGY, ALERT, CRM, OR WORKFORCE ACTION"
PURPOSE = "competitive_win_loss_evidence_review"
LANE_SUBJECT = {
    "crm_outcome": "opportunity",
    "crm_competitor": "opportunity",
    "crm_reason": "opportunity",
    "buyer_interview_code": "opportunity",
    "call_annotation_code": "opportunity",
    "public_observation": "competitor",
}
REQUIRED_PROHIBITED_USES = {
    "causal-explanation", "prediction", "ranking", "strategy", "alert", "crm-write", "workforce-action"
}
OPERATORS = {"lt", "le", "eq", "ge", "gt"}
ROUNDING_MODES = {"half_even": ROUND_HALF_EVEN, "half_up": ROUND_HALF_UP, "down": ROUND_DOWN}
R1_WORDS = {"small", "large", "enough", "limited", "insufficient", "good", "poor", "high", "low"}
ACTION_WORDS = {"send", "notify", "assign", "route", "update", "write", "create", "delete", "approve", "reject", "coach", "escalate", "message", "schedule"}
FORBIDDEN_KEYS = {
    "name", "domain", "url", "email", "phone", "address", "account_id", "contact_id",
    "free_text", "notes", "transcript", "quote", "review_text", "post_text", "job_title",
    "sentiment", "protected_trait", "disability", "accommodation", "worker_id", "seller_id",
    "manager_id", "performance", "quota", "compensation", "coaching", "confidence", "threat",
    "risk", "priority", "rank", "forecast", "lost_revenue", "market_share", "pricing_gap",
    "feature_gap", "recommendation", "recommended_action", "battle_card", "message", "channel",
}
FORBIDDEN_KEY_PARTS = {
    "name", "domain", "url", "email", "phone", "address", "account", "contact", "text", "notes",
    "transcript", "quote", "sentiment", "trait", "disability", "accommodation", "worker", "seller",
    "manager", "performance", "quota", "compensation", "coaching", "confidence", "threat", "ranking",
    "forecast", "recommendation", "message", "channel",
}
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,79}$")
TOKEN_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/+-]{0,159}$")
DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
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


def _scan(value: Any, path: str = "document") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            parts = {part for part in re.split(r"[^a-z0-9]+", key.lower()) if part}
            if key.lower() in FORBIDDEN_KEYS or parts & FORBIDDEN_KEY_PARTS:
                raise ValueError(f"{path}.{key} is prohibited")
            _scan(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan(child, f"{path}[{index}]")
    elif isinstance(value, str) and "@" in value:
        raise ValueError(f"{path} contains a direct contact identifier")


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be a stable pseudonymous identifier")
    parts = {part.lower() for part in re.split(r"[_.:-]+", value)}
    if parts & R1_WORDS:
        raise ValueError(f"{label} contains an unapproved adequacy token")
    if "allowed_code" in label and parts & ACTION_WORDS:
        raise ValueError(f"{label} contains an action token")
    return value


def _token(value: Any, label: str, allow_r1: bool = False) -> str:
    if not isinstance(value, str) or not TOKEN_PATTERN.fullmatch(value) or "@" in value:
        raise ValueError(f"{label} must be a non-contact token")
    parts = {part.lower() for part in re.split(r"[ _./:-]+", value)}
    if not allow_r1 and parts & R1_WORDS:
        raise ValueError(f"{label} contains an unapproved adequacy token")
    if "disposition_label" in label and parts & ACTION_WORDS:
        raise ValueError(f"{label} contains an action token")
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
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _decimal(value: Any, label: str) -> Decimal:
    if not isinstance(value, str) or not DECIMAL_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be a plain Decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} is not a Decimal") from exc
    if not number.is_finite():
        raise ValueError(f"{label} must be finite")
    return number


def _normal(number: Decimal) -> str:
    text = format(number, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _compare(actual: Decimal, operator: str, threshold: Decimal) -> bool:
    return {
        "lt": actual < threshold, "le": actual <= threshold, "eq": actual == threshold,
        "ge": actual >= threshold, "gt": actual > threshold,
    }[operator]


def _validate_policy(raw: Any) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, Any]], dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]], datetime]:
    policy = _object(raw, "policy")
    _keys(
        policy,
        {"policy_id", "policy_version", "owner_id", "human_reviewer_role_id", "effective_at", "expires_at",
         "cutoff_at", "timezone", "approved_purpose", "prohibited_uses", "correction_path",
         "calculation_policy", "bindings", "code_maps", "rules"},
        set(), "policy",
    )
    for field in ("policy_id", "owner_id", "human_reviewer_role_id"):
        _id(policy[field], f"policy.{field}")
    for field in ("policy_version", "timezone", "correction_path"):
        _token(policy[field], f"policy.{field}")
    if policy["approved_purpose"] != PURPOSE:
        raise ValueError("policy purpose is not authorized")
    prohibited = _list(policy["prohibited_uses"], "policy.prohibited_uses")
    for item in prohibited:
        _token(item, "policy.prohibited_uses item")
    if not REQUIRED_PROHIBITED_USES.issubset(set(prohibited)):
        raise ValueError("policy.prohibited_uses does not preserve the fixed boundary")
    effective_text, effective = _timestamp(policy["effective_at"], "policy.effective_at")
    cutoff_text, cutoff = _timestamp(policy["cutoff_at"], "policy.cutoff_at")
    if effective > cutoff:
        raise ValueError("policy is not effective at cutoff")
    expires_text = None
    if policy["expires_at"] is not None:
        expires_text, expires = _timestamp(policy["expires_at"], "policy.expires_at")
        if cutoff >= expires:
            raise ValueError("policy is expired at cutoff")
    policy.update(effective_at=effective_text, cutoff_at=cutoff_text, expires_at=expires_text)

    calculation = _object(policy["calculation_policy"], "policy.calculation_policy")
    _keys(calculation, {"rate_scale", "rounding_mode"}, set(), "policy.calculation_policy")
    if not isinstance(calculation["rate_scale"], int) or isinstance(calculation["rate_scale"], bool) or not 0 <= calculation["rate_scale"] <= 8:
        raise ValueError("rate_scale must be an integer from zero through eight")
    if calculation["rounding_mode"] not in ROUNDING_MODES:
        raise ValueError("rounding_mode is unsupported")

    bindings: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw_binding in enumerate(_list(policy["bindings"], "policy.bindings")):
        row = _object(raw_binding, f"policy.bindings[{index}]")
        _keys(row, {"lane", "subject_type", "source_id", "schema_version", "code_map_id", "code_map_version", "occurrence_semantics"}, set(), f"policy.bindings[{index}]")
        if row["lane"] not in LANE_SUBJECT or row["subject_type"] != LANE_SUBJECT[row["lane"]]:
            raise ValueError("binding lane and subject type do not match")
        for field in ("source_id", "code_map_id"):
            _id(row[field], f"binding.{field}")
        for field in ("schema_version", "code_map_version", "occurrence_semantics"):
            _token(row[field], f"binding.{field}")
        key = (row["lane"], row["source_id"])
        if key in bindings:
            raise ValueError("duplicate lane/source binding")
        bindings[key] = row
    if not bindings:
        raise ValueError("policy.bindings must not be empty")

    code_maps: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw_map in enumerate(_list(policy["code_maps"], "policy.code_maps")):
        row = _object(raw_map, f"policy.code_maps[{index}]")
        _keys(row, {"lane", "code_map_id", "code_map_version", "allowed_codes"}, set(), f"policy.code_maps[{index}]")
        if row["lane"] not in LANE_SUBJECT:
            raise ValueError("code-map lane is unsupported")
        _id(row["code_map_id"], "code_map.code_map_id")
        _token(row["code_map_version"], "code_map.code_map_version")
        codes = [_id(item, "code_map.allowed_code") for item in _list(row["allowed_codes"], "code_map.allowed_codes")]
        if not codes or len(codes) != len(set(codes)):
            raise ValueError("allowed codes must be non-empty and unique")
        row["allowed_codes"] = sorted(codes)
        key = (row["lane"], row["code_map_id"])
        if key in code_maps:
            raise ValueError("duplicate lane/code-map definition")
        code_maps[key] = row
    for binding in bindings.values():
        code_map = code_maps.get((binding["lane"], binding["code_map_id"]))
        if code_map is None or code_map["code_map_version"] != binding["code_map_version"]:
            raise ValueError("binding lacks its exact code map")

    rules: list[dict[str, Any]] = []
    seen_rules: set[str] = set()
    for index, raw_rule in enumerate(_list(policy["rules"], "policy.rules")):
        row = _object(raw_rule, f"policy.rules[{index}]")
        _keys(row, {"rule_id", "lane", "source_id", "code", "metric", "operator", "threshold",
                    "disposition_label", "human_review_role_id", "precedence"}, set(), f"policy.rules[{index}]")
        rule_id = _id(row["rule_id"], "rule.rule_id")
        if rule_id in seen_rules:
            raise ValueError("duplicate rule_id")
        seen_rules.add(rule_id)
        binding = bindings.get((row["lane"], row["source_id"]))
        if binding is None:
            raise ValueError("rule lacks an approved lane/source binding")
        code_map = code_maps[(row["lane"], binding["code_map_id"])]
        if row["code"] not in code_map["allowed_codes"]:
            raise ValueError("rule code is not approved")
        if row["metric"] not in {"count", "rate"} or row["operator"] not in OPERATORS:
            raise ValueError("rule metric or operator is unsupported")
        row["threshold"] = _normal(_decimal(row["threshold"], "rule.threshold"))
        _token(row["disposition_label"], "rule.disposition_label", allow_r1=True)
        if not row["disposition_label"].startswith(("review-observation-", "record-observation-")):
            raise ValueError("rule disposition must be a neutral observation label")
        _id(row["human_review_role_id"], "rule.human_review_role_id")
        if not isinstance(row["precedence"], int) or isinstance(row["precedence"], bool) or row["precedence"] < 0:
            raise ValueError("rule.precedence must be a non-negative integer")
        rules.append(row)
    return policy, bindings, code_maps, rules, cutoff


def review_competitive_evidence(document: dict[str, Any]) -> dict[str, Any]:
    root = _object(document, "document")
    _scan(root)
    _keys(root, {"policy", "declaration", "source_populations", "observations"}, set(), "document")
    policy, bindings, code_maps, rules, cutoff = _validate_policy(root["policy"])

    declaration = _object(root["declaration"], "declaration")
    _keys(declaration, {"review_id", "window_begin", "window_end", "declared_opportunity_count",
                        "opportunity_ids", "declared_competitor_count", "competitor_ids"}, set(), "declaration")
    _id(declaration["review_id"], "declaration.review_id")
    declaration["window_begin"], window_begin = _timestamp(declaration["window_begin"], "declaration.window_begin")
    declaration["window_end"], window_end = _timestamp(declaration["window_end"], "declaration.window_end")
    if window_begin >= window_end or window_end > cutoff:
        raise ValueError("review window is invalid at cutoff")
    declared_by_type: dict[str, list[str]] = {}
    for subject_type, count_field, ids_field in (
        ("opportunity", "declared_opportunity_count", "opportunity_ids"),
        ("competitor", "declared_competitor_count", "competitor_ids"),
    ):
        ids = [_id(item, f"declaration.{subject_type}_id") for item in _list(declaration[ids_field], f"declaration.{ids_field}")]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError(f"declared {subject_type} IDs must be non-empty and unique")
        count = declaration[count_field]
        if not isinstance(count, int) or isinstance(count, bool) or count != len(ids):
            raise ValueError(f"declared {subject_type} count does not reconcile")
        declared_by_type[subject_type] = sorted(ids)

    populations: list[dict[str, Any]] = []
    population_by_id: dict[str, dict[str, Any]] = {}
    population_keys: set[tuple[str, str]] = set()
    for index, raw_population in enumerate(_list(root["source_populations"], "source_populations")):
        row = _object(raw_population, f"source_populations[{index}]")
        _keys(row, {"population_receipt_id", "lane", "subject_type", "source_id", "schema_version",
                    "code_map_id", "code_map_version", "complete", "subject_ids", "observed_at"}, set(), f"source_populations[{index}]")
        for field in ("population_receipt_id", "source_id", "code_map_id"):
            _id(row[field], f"source_population.{field}")
        binding = bindings.get((row["lane"], row["source_id"]))
        if binding is None:
            raise ValueError("source population lacks an approved binding")
        for field in ("subject_type", "schema_version", "code_map_id", "code_map_version"):
            if row[field] != binding[field]:
                raise ValueError(f"source population does not match approved {field}")
        if row["complete"] is not True:
            raise ValueError("source population must be declared complete")
        subject_ids = [_id(item, "source_population.subject_id") for item in _list(row["subject_ids"], "source_population.subject_ids")]
        if len(subject_ids) != len(set(subject_ids)) or sorted(subject_ids) != declared_by_type[row["subject_type"]]:
            raise ValueError("source population does not exactly reconcile to its declaration")
        row["subject_ids"] = sorted(subject_ids)
        row["observed_at"], observed = _timestamp(row["observed_at"], "source_population.observed_at")
        if observed < window_end or observed > cutoff:
            raise ValueError("source population observation time is invalid")
        if row["population_receipt_id"] in population_by_id:
            raise ValueError("duplicate population receipt ID")
        key = (row["lane"], row["source_id"])
        if key in population_keys:
            raise ValueError("duplicate lane/source population")
        population_keys.add(key)
        population_by_id[row["population_receipt_id"]] = row
        populations.append(row)
    if population_keys != set(bindings):
        raise ValueError("source populations do not reconcile to approved bindings")

    observations: list[dict[str, Any]] = []
    observation_ids: set[str] = set()
    observation_keys: set[tuple[str, str, str]] = set()
    observations_by_population: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, raw_observation in enumerate(_list(root["observations"], "observations")):
        row = _object(raw_observation, f"observations[{index}]")
        _keys(row, {"observation_id", "lane", "subject_type", "subject_id", "source_id", "schema_version",
                    "code_map_id", "code_map_version", "code", "population_receipt_id", "occurred_at", "observed_at"}, set(), f"observations[{index}]")
        for field in ("observation_id", "subject_id", "source_id", "code_map_id", "population_receipt_id"):
            _id(row[field], f"observation.{field}")
        binding = bindings.get((row["lane"], row["source_id"]))
        if binding is None:
            raise ValueError("observation lacks an approved binding")
        for field in ("subject_type", "schema_version", "code_map_id", "code_map_version"):
            if row[field] != binding[field]:
                raise ValueError(f"observation does not match approved {field}")
        if row["subject_id"] not in declared_by_type[row["subject_type"]]:
            raise ValueError("observation references an undeclared subject")
        population = population_by_id.get(row["population_receipt_id"])
        if population is None or (population["lane"], population["source_id"]) != (row["lane"], row["source_id"]):
            raise ValueError("observation population receipt does not match lane/source")
        code_map = code_maps[(row["lane"], row["code_map_id"])]
        if row["code"] not in code_map["allowed_codes"]:
            raise ValueError("observation code is not approved")
        row["occurred_at"], occurred = _timestamp(row["occurred_at"], "observation.occurred_at")
        row["observed_at"], observed = _timestamp(row["observed_at"], "observation.observed_at")
        if occurred < window_begin or occurred >= window_end or observed < occurred or observed > cutoff:
            raise ValueError("observation timestamps do not fit the frozen review")
        if row["observation_id"] in observation_ids:
            raise ValueError("duplicate observation ID")
        observation_ids.add(row["observation_id"])
        key = (row["lane"], row["source_id"], row["subject_id"])
        if key in observation_keys:
            raise ValueError("subject has multiple observations for one lane/source")
        observation_keys.add(key)
        observations_by_population[row["population_receipt_id"]].append(row)
        observations.append(row)

    declared_receipts = [
        {"receipt_id": "declared-opportunity-population", "subject_type": "opportunity",
         "subject_ids": declared_by_type["opportunity"], "member_count": str(len(declared_by_type["opportunity"]))},
        {"receipt_id": "declared-competitor-population", "subject_type": "competitor",
         "subject_ids": declared_by_type["competitor"], "member_count": str(len(declared_by_type["competitor"]))},
    ]
    population_receipts: list[dict[str, Any]] = []
    count_receipts: list[dict[str, Any]] = []
    rate_receipts: list[dict[str, Any]] = []
    metric_lookup: dict[tuple[str, str, str, str], tuple[str, Decimal]] = {}
    subject_reviews: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    for population in sorted(populations, key=lambda row: (row["lane"], row["source_id"])):
        population_receipts.append({
            "population_receipt_id": population["population_receipt_id"], "lane": population["lane"],
            "subject_type": population["subject_type"], "source_id": population["source_id"],
            "schema_version": population["schema_version"], "code_map_id": population["code_map_id"],
            "code_map_version": population["code_map_version"], "complete": True,
            "subject_ids": population["subject_ids"], "member_count": str(len(population["subject_ids"])),
            "observed_at": population["observed_at"],
        })
        rows = sorted(observations_by_population[population["population_receipt_id"]], key=lambda row: row["observation_id"])
        observed_subjects = {row["subject_id"] for row in rows}
        observed_id = f"count-{population['lane']}-{population['source_id']}-observed"
        no_event_id = f"count-{population['lane']}-{population['source_id']}-no-event"
        count_receipts.append({"count_receipt_id": observed_id, "lane": population["lane"], "source_id": population["source_id"],
                               "kind": "observed", "value": str(len(rows))})
        count_receipts.append({"count_receipt_id": no_event_id, "lane": population["lane"], "source_id": population["source_id"],
                               "kind": "no_event_recorded", "value": str(len(population["subject_ids"]) - len(rows))})
        counts = Counter(row["code"] for row in rows)
        for code in code_maps[(population["lane"], population["code_map_id"])]["allowed_codes"]:
            count_id = f"count-{population['lane']}-{population['source_id']}-{code}"
            count_value = Decimal(counts.get(code, 0))
            count_receipts.append({"count_receipt_id": count_id, "lane": population["lane"], "source_id": population["source_id"],
                                   "kind": "code", "code": code, "value": _normal(count_value)})
            metric_lookup[(population["lane"], population["source_id"], code, "count")] = (count_id, count_value)
            denominator = Decimal(len(population["subject_ids"]))
            scale = policy["calculation_policy"]["rate_scale"]
            with localcontext() as context:
                context.prec = max(50, scale + 20)
                quantum = Decimal(1).scaleb(-scale)
                rate_value = ((count_value / denominator) * Decimal("100")).quantize(
                    quantum, rounding=ROUNDING_MODES[policy["calculation_policy"]["rounding_mode"]]
                )
            rate_id = f"rate-{population['lane']}-{population['source_id']}-{code}"
            rate_receipts.append({"rate_receipt_id": rate_id, "lane": population["lane"], "source_id": population["source_id"],
                                  "code": code, "numerator_count_receipt_id": count_id,
                                  "denominator_population_receipt_id": population["population_receipt_id"],
                                  "unit": "percent", "value": _normal(rate_value)})
            metric_lookup[(population["lane"], population["source_id"], code, "rate")] = (rate_id, rate_value)
        row_by_subject = {row["subject_id"]: row for row in rows}
        for subject_id in population["subject_ids"]:
            observation = row_by_subject.get(subject_id)
            subject_reviews[(population["subject_type"], subject_id)].append({
                "lane": population["lane"], "source_id": population["source_id"],
                "state": "OBSERVED" if subject_id in observed_subjects else "NO_EVENT_RECORDED",
                "observation_receipt_id": observation["observation_id"] if observation else "none",
                "population_receipt_id": population["population_receipt_id"],
            })

    rule_results: list[dict[str, str]] = []
    matched_by_key: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for rule in sorted(rules, key=lambda row: row["rule_id"]):
        receipt_id, actual = metric_lookup[(rule["lane"], rule["source_id"], rule["code"], rule["metric"])]
        matched = _compare(actual, rule["operator"], Decimal(rule["threshold"]))
        state = "RULE_MATCHED" if matched else "RULE_NOT_MATCHED"
        if matched:
            matched_by_key[(rule["lane"], rule["source_id"], rule["code"], rule["metric"])].append(rule)
        rule_results.append({"rule_id": rule["rule_id"], "state": state, "metric_receipt_id": receipt_id,
                             "human_review_role_id": rule["human_review_role_id"]})
    conflicts: set[str] = set()
    for matched in matched_by_key.values():
        top = max(row["precedence"] for row in matched)
        top_rules = [row for row in matched if row["precedence"] == top]
        if len({row["disposition_label"] for row in top_rules}) > 1:
            conflicts.update(row["rule_id"] for row in top_rules)
    for result in rule_results:
        if result["rule_id"] in conflicts:
            result["state"] = "HUMAN_REVIEW_REQUIRED"

    policy_receipt = {
        "policy_id": policy["policy_id"], "policy_version": policy["policy_version"], "owner_id": policy["owner_id"],
        "human_reviewer_role_id": policy["human_reviewer_role_id"], "effective_at": policy["effective_at"],
        "expires_at": policy["expires_at"], "cutoff_at": policy["cutoff_at"], "timezone": policy["timezone"],
        "approved_purpose": policy["approved_purpose"], "prohibited_uses": sorted(policy["prohibited_uses"]),
        "correction_path": policy["correction_path"], "calculation_policy": policy["calculation_policy"],
        "bindings": sorted(policy["bindings"], key=lambda row: (row["lane"], row["source_id"])),
        "code_maps": sorted(policy["code_maps"], key=lambda row: (row["lane"], row["code_map_id"])),
        "rules": sorted(policy["rules"], key=lambda row: row["rule_id"]),
    }
    subject_review_rows = [
        {"subject_type": subject_type, "subject_id": subject_id,
         "lane_reviews": sorted(rows, key=lambda row: (row["lane"], row["source_id"]))}
        for (subject_type, subject_id), rows in sorted(subject_reviews.items())
    ]
    return {
        "boundary": BOUNDARY,
        "count_receipts": sorted(count_receipts, key=lambda row: row["count_receipt_id"]),
        "declared_population_receipts": declared_receipts,
        "observation_receipts": sorted(observations, key=lambda row: row["observation_id"]),
        "policy_receipt": policy_receipt,
        "rate_receipts": sorted(rate_receipts, key=lambda row: row["rate_receipt_id"]),
        "review_id": declaration["review_id"],
        "review_state": "HUMAN_REVIEW_REQUIRED" if any(row["state"] in {"RULE_MATCHED", "HUMAN_REVIEW_REQUIRED"} for row in rule_results) else "OBSERVED",
        "review_type": "COMPETITIVE_WIN_LOSS_EVIDENCE_REVIEW",
        "review_window": {"window_begin": declaration["window_begin"], "window_end": declaration["window_end"]},
        "rule_results": rule_results,
        "source_population_receipts": population_receipts,
        "subject_reviews": subject_review_rows,
    }


def render_review_output(result: dict[str, Any]) -> str:
    """Render the complete result exactly once."""
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    try:
        if len(argv) > 2:
            raise ValueError("usage: competitive_evidence.py [input.json]")
        raw = Path(argv[1]).read_text(encoding="utf-8") if len(argv) == 2 else sys.stdin.read()
        document = json.loads(raw)
        sys.stdout.write(render_review_output(review_competitive_evidence(document)))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f"competitive evidence review failed: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
