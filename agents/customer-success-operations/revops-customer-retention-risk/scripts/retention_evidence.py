#!/usr/bin/env python3
"""Deterministic, read-only customer-retention evidence review."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


BOUNDARY = "NO CHURN OR RENEWAL PREDICTION / NO RANKING, CRM, OUTREACH, PLAYBOOK, FORECAST, OR WORKFORCE ACTION"
PURPOSE = "customer_retention_evidence_review"
LANES = {"usage", "support", "survey", "engagement", "contract", "billing", "outcome"}
NUMERIC_LANES = {"usage", "support", "survey", "engagement", "billing"}
REQUIRED_PROHIBITED_USES = {"prediction", "ranking", "crm-write", "outreach", "playbook", "forecast", "workforce-action"}
OPERATORS = {"lt", "le", "eq", "ge", "gt"}
R1_WORDS = {"small", "large", "enough", "limited", "insufficient", "good", "poor", "high", "low"}
FORBIDDEN_KEYS = {
    "name", "domain", "email", "phone", "address", "contact_id", "contact_name",
    "free_text", "ticket_text", "survey_text", "message", "notes", "sentiment",
    "protected_trait", "disability", "accommodation", "home_location", "employee_count",
    "csm_name", "owner_name", "performance", "quota", "compensation", "coaching",
    "health_score", "risk_score", "churn_probability", "renewal_probability", "confidence",
    "priority", "rank", "forecast", "arr_at_risk", "playbook", "recommended_action",
}
FORBIDDEN_KEY_PARTS = {
    "name", "domain", "email", "phone", "address", "contact", "text", "message", "notes",
    "sentiment", "trait", "disability", "accommodation", "performance", "quota", "compensation",
    "coaching", "ranking",
}
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,79}$")
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
            key_parts = {part for part in re.split(r"[^a-z0-9]+", key.lower()) if part}
            if key.lower() in FORBIDDEN_KEYS or key_parts & FORBIDDEN_KEY_PARTS:
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
    return value


def _token(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 160 or "@" in value:
        raise ValueError(f"{label} must be a non-contact token")
    parts = {part.lower() for part in re.split(r"[ _./:-]+", value)}
    if parts & R1_WORDS:
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


def _compare(actual: Any, operator: str, threshold: Any) -> bool:
    return {"lt": actual < threshold, "le": actual <= threshold, "eq": actual == threshold,
            "ge": actual >= threshold, "gt": actual > threshold}[operator]


def _validate_policy(raw: Any) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, str]], list[dict[str, Any]], datetime]:
    policy = _object(raw, "policy")
    _keys(policy, {"policy_id", "policy_version", "owner_id", "human_reviewer_role_id",
                   "effective_at", "expires_at", "cutoff_at", "timezone", "approved_purpose",
                   "prohibited_uses", "correction_path", "bindings", "rules"}, set(), "policy")
    for field in ("policy_id", "owner_id", "human_reviewer_role_id"):
        _id(policy[field], f"policy.{field}")
    _token(policy["policy_version"], "policy.policy_version")
    _token(policy["timezone"], "policy.timezone")
    _token(policy["correction_path"], "policy.correction_path")
    if policy["approved_purpose"] != PURPOSE:
        raise ValueError("policy purpose is not authorized")
    prohibited = _list(policy["prohibited_uses"], "policy.prohibited_uses")
    if not prohibited:
        raise ValueError("policy.prohibited_uses must not be empty")
    for item in prohibited:
        _token(item, "policy.prohibited_uses item")
    if not REQUIRED_PROHIBITED_USES.issubset(set(prohibited)):
        raise ValueError("policy.prohibited_uses does not preserve the fixed action boundary")
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

    bindings: dict[tuple[str, str], dict[str, str]] = {}
    for index, raw_binding in enumerate(_list(policy["bindings"], "policy.bindings")):
        row = _object(raw_binding, f"policy.bindings[{index}]")
        _keys(row, {"lane", "source_id", "schema_version", "metric_id", "metric_version", "link_version"}, set(), f"policy.bindings[{index}]")
        if row["lane"] not in LANES:
            raise ValueError("binding lane is unsupported")
        for field in ("source_id", "metric_id"):
            _id(row[field], f"binding.{field}")
        for field in ("schema_version", "metric_version", "link_version"):
            _token(row[field], f"binding.{field}")
        key = (row["lane"], row["source_id"])
        if key in bindings:
            raise ValueError("duplicate lane/source binding")
        bindings[key] = row
    if not bindings:
        raise ValueError("policy.bindings must not be empty")

    rules: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_rule in enumerate(_list(policy["rules"], "policy.rules")):
        row = _object(raw_rule, f"policy.rules[{index}]")
        _keys(row, {"rule_id", "lane", "fact_kind", "value_type", "operator", "threshold", "unit", "basis",
                    "currency", "disposition_label", "human_review_role_id", "precedence"}, set(), f"policy.rules[{index}]")
        rule_id = _id(row["rule_id"], "rule.rule_id")
        if rule_id in seen:
            raise ValueError("duplicate rule_id")
        seen.add(rule_id)
        if row["lane"] not in LANES:
            raise ValueError("rule lane is unsupported")
        _token(row["fact_kind"], "rule.fact_kind")
        if row["value_type"] not in {"decimal", "token", "timestamp"}:
            raise ValueError("rule value_type is unsupported")
        if row["operator"] not in OPERATORS or (row["value_type"] == "token" and row["operator"] != "eq"):
            raise ValueError("rule operator is unsupported")
        if row["value_type"] == "decimal":
            row["threshold"] = _normal(_decimal(row["threshold"], "rule.threshold"))
        elif row["value_type"] == "token":
            _id(row["threshold"], "rule.threshold")
        else:
            row["threshold"], _ = _timestamp(row["threshold"], "rule.threshold")
        for field in ("unit", "basis", "disposition_label"):
            _token(row[field], f"rule.{field}")
        if not row["disposition_label"].startswith(("review-observation-", "record-observation-")):
            raise ValueError("rule.disposition_label must be a neutral observation label")
        if row["currency"] is not None:
            _token(row["currency"], "rule.currency")
        _id(row["human_review_role_id"], "rule.human_review_role_id")
        if not isinstance(row["precedence"], int) or isinstance(row["precedence"], bool) or row["precedence"] < 0:
            raise ValueError("rule.precedence must be a non-negative integer")
        rules.append(row)
    if not rules:
        raise ValueError("policy.rules must not be empty")
    return policy, bindings, rules, cutoff


def _check_binding(row: dict[str, Any], bindings: dict[tuple[str, str], dict[str, str]], label: str) -> dict[str, str]:
    key = (row["lane"], row["source_id"])
    binding = bindings.get(key)
    if binding is None:
        raise ValueError(f"{label} lacks an approved lane/source binding")
    for field in ("schema_version", "metric_id", "metric_version"):
        if row[field] != binding[field]:
            raise ValueError(f"{label} does not match the approved {field}")
    return binding


def review_retention_evidence(document: dict[str, Any]) -> dict[str, Any]:
    root = _object(document, "document")
    _scan(root)
    _keys(root, {"policy", "declaration", "identity_links", "source_populations", "facts"}, set(), "document")
    policy, bindings, rules, cutoff = _validate_policy(root["policy"])

    declaration = _object(root["declaration"], "declaration")
    _keys(declaration, {"declared_account_count", "account_ids"}, set(), "declaration")
    account_ids = [_id(item, "declaration.account_id") for item in _list(declaration["account_ids"], "declaration.account_ids")]
    if len(account_ids) != len(set(account_ids)):
        raise ValueError("declaration contains duplicate account IDs")
    if not isinstance(declaration["declared_account_count"], int) or isinstance(declaration["declared_account_count"], bool):
        raise ValueError("declared_account_count must be an integer")
    if declaration["declared_account_count"] != len(account_ids):
        raise ValueError("declared account count does not reconcile")
    declared = set(account_ids)

    links: list[dict[str, Any]] = []
    link_ids: set[str] = set()
    link_keys: set[tuple[str, str, str]] = set()
    external_keys: dict[tuple[str, str], str] = {}
    for index, raw_link in enumerate(_list(root["identity_links"], "identity_links")):
        row = _object(raw_link, f"identity_links[{index}]")
        _keys(row, {"link_id", "account_id", "external_account_id", "lane", "source_id", "schema_version", "link_version", "observed_at"}, set(), f"identity_links[{index}]")
        for field in ("link_id", "account_id", "external_account_id", "source_id"):
            _id(row[field], f"identity_link.{field}")
        if row["account_id"] not in declared:
            raise ValueError("identity link references an undeclared account")
        if row["lane"] not in LANES:
            raise ValueError("identity link lane is unsupported")
        binding = bindings.get((row["lane"], row["source_id"]))
        if binding is None or row["schema_version"] != binding["schema_version"] or row["link_version"] != binding["link_version"]:
            raise ValueError("identity link does not match approved binding")
        row["observed_at"], observed = _timestamp(row["observed_at"], "identity_link.observed_at")
        if observed > cutoff:
            raise ValueError("identity link occurs after cutoff")
        if row["link_id"] in link_ids:
            raise ValueError("duplicate link_id")
        link_ids.add(row["link_id"])
        key = (row["account_id"], row["lane"], row["source_id"])
        if key in link_keys:
            raise ValueError("one account has multiple links for a lane/source")
        link_keys.add(key)
        external_key = (row["source_id"], row["external_account_id"])
        if external_key in external_keys and external_keys[external_key] != row["account_id"]:
            raise ValueError("one external account links to multiple declared accounts")
        external_keys[external_key] = row["account_id"]
        links.append(row)

    populations: list[dict[str, Any]] = []
    population_by_id: dict[str, dict[str, Any]] = {}
    population_keys: set[tuple[str, str]] = set()
    for index, raw_population in enumerate(_list(root["source_populations"], "source_populations")):
        row = _object(raw_population, f"source_populations[{index}]")
        _keys(row, {"population_receipt_id", "lane", "source_id", "schema_version", "metric_id", "metric_version", "complete", "account_ids", "observed_at"}, set(), f"source_populations[{index}]")
        _id(row["population_receipt_id"], "population_receipt_id")
        _id(row["source_id"], "source_population.source_id")
        _id(row["metric_id"], "source_population.metric_id")
        _token(row["schema_version"], "source_population.schema_version")
        _token(row["metric_version"], "source_population.metric_version")
        _check_binding(row, bindings, "source population")
        if not isinstance(row["complete"], bool):
            raise ValueError("source population complete must be boolean")
        ids = [_id(item, "source_population.account_id") for item in _list(row["account_ids"], "source_population.account_ids")]
        if len(ids) != len(set(ids)):
            raise ValueError("source population contains duplicate accounts")
        if not set(ids).issubset(declared):
            raise ValueError("source population contains undeclared accounts")
        if row["complete"] and set(ids) != declared:
            raise ValueError("complete source population does not reconcile to the declared population")
        row["observed_at"], observed = _timestamp(row["observed_at"], "source_population.observed_at")
        if observed > cutoff:
            raise ValueError("source population occurs after cutoff")
        if row["population_receipt_id"] in population_by_id:
            raise ValueError("duplicate population receipt ID")
        key = (row["lane"], row["source_id"])
        if key in population_keys:
            raise ValueError("duplicate lane/source population")
        population_keys.add(key)
        population_by_id[row["population_receipt_id"]] = row
        populations.append(row)

    if population_keys != set(bindings):
        raise ValueError("source populations do not reconcile to approved lane/source bindings")
    link_lookup = {(row["account_id"], row["lane"], row["source_id"]): row for row in links}
    for population in populations:
        for account_id in population["account_ids"]:
            if (account_id, population["lane"], population["source_id"]) not in link_lookup:
                raise ValueError("source population account lacks an exact identity link")

    facts: list[dict[str, Any]] = []
    fact_by_id: dict[str, dict[str, Any]] = {}
    account_lane_facts: dict[tuple[str, str], list[str]] = defaultdict(list)
    comparison_states: dict[str, str] = {}
    for index, raw_fact in enumerate(_list(root["facts"], "facts")):
        row = _object(raw_fact, f"facts[{index}]")
        _keys(row, {"fact_id", "lane", "account_id", "kind", "value_type", "current_value", "prior_value",
                    "unit", "basis", "currency", "window_begin", "window_end", "prior_window_begin",
                    "prior_window_end", "timezone", "population_receipt_id", "identity_link_id", "source_id",
                    "schema_version", "metric_id", "metric_version", "observed_at"}, set(), f"facts[{index}]")
        for field in ("fact_id", "account_id", "source_id", "metric_id", "population_receipt_id", "identity_link_id"):
            _id(row[field], f"fact.{field}")
        if row["account_id"] not in declared:
            raise ValueError("fact references an undeclared account")
        if row["lane"] not in LANES:
            raise ValueError("fact lane is unsupported")
        _token(row["kind"], "fact.kind")
        for field in ("unit", "basis", "timezone", "schema_version", "metric_version"):
            _token(row[field], f"fact.{field}")
        if row["currency"] is not None:
            _token(row["currency"], "fact.currency")
        binding = _check_binding(row, bindings, "fact")
        population = population_by_id.get(row["population_receipt_id"])
        if population is None or any(row[field] != population[field] for field in ("lane", "source_id", "schema_version", "metric_id", "metric_version")):
            raise ValueError("fact population receipt does not match fact semantics")
        if row["account_id"] not in population["account_ids"]:
            raise ValueError("fact account is absent from its source population")
        link_key = (row["account_id"], row["lane"], row["source_id"])
        link = next((item for item in links if item["link_id"] == row["identity_link_id"]), None)
        if link is None or (link["account_id"], link["lane"], link["source_id"]) != link_key or link["link_version"] != binding["link_version"]:
            raise ValueError("fact identity link does not match fact semantics")
        row["observed_at"], observed = _timestamp(row["observed_at"], "fact.observed_at")
        if observed > cutoff:
            raise ValueError("fact occurs after cutoff")
        row["window_begin"], window_begin = _timestamp(row["window_begin"], "fact.window_begin")
        row["window_end"], window_end = _timestamp(row["window_end"], "fact.window_end")
        if not window_begin < window_end or window_end > cutoff:
            raise ValueError("fact current window is invalid")
        if observed < window_end:
            raise ValueError("fact was observed before its current window ended")
        comparison = "OBSERVED"
        if row["value_type"] == "decimal":
            row["current_value"] = _normal(_decimal(row["current_value"], "fact.current_value"))
            if row["prior_value"] is None:
                if row["prior_window_begin"] is not None or row["prior_window_end"] is not None:
                    raise ValueError("prior window without prior value")
            else:
                row["prior_value"] = _normal(_decimal(row["prior_value"], "fact.prior_value"))
                if row["prior_window_begin"] is None or row["prior_window_end"] is None:
                    raise ValueError("prior value requires a prior window")
                row["prior_window_begin"], prior_begin = _timestamp(row["prior_window_begin"], "fact.prior_window_begin")
                row["prior_window_end"], prior_end = _timestamp(row["prior_window_end"], "fact.prior_window_end")
                if not prior_begin < prior_end or prior_end > window_begin:
                    comparison = "NOT_COMPARABLE"
        elif row["value_type"] in {"token", "timestamp"}:
            if row["prior_value"] is not None or row["prior_window_begin"] is not None or row["prior_window_end"] is not None:
                raise ValueError("non-decimal fact cannot contain prior comparison fields")
            if row["value_type"] == "token":
                _id(row["current_value"], "fact.current_value")
            else:
                row["current_value"], value_time = _timestamp(row["current_value"], "fact.current_value")
                if row["lane"] == "outcome" and value_time > cutoff:
                    raise ValueError("timestamp fact value occurs after cutoff")
        else:
            raise ValueError("fact.value_type is unsupported")
        if row["lane"] in NUMERIC_LANES and row["value_type"] != "decimal":
            raise ValueError("numeric lane requires Decimal evidence")
        if row["lane"] in {"contract", "outcome"} and row["value_type"] == "decimal":
            raise ValueError("contract and outcome lanes require recorded token or timestamp evidence")
        if row["fact_id"] in fact_by_id:
            raise ValueError("duplicate fact_id")
        fact_by_id[row["fact_id"]] = row
        comparison_states[row["fact_id"]] = comparison
        account_lane_facts[(row["account_id"], row["lane"])].append(row["fact_id"])
        facts.append(row)

    rule_receipts = sorted(rules, key=lambda item: item["rule_id"])
    account_reviews: list[dict[str, Any]] = []
    review_states: set[str] = set()
    for account_id in sorted(account_ids):
        lane_reviews: list[dict[str, Any]] = []
        for lane in sorted(LANES):
            lane_fact_ids = sorted(account_lane_facts[(account_id, lane)])
            all_lane_populations = [row for row in populations if row["lane"] == lane]
            lane_populations = [row for row in all_lane_populations if account_id in row["account_ids"]]
            lane_sources_complete = bool(all_lane_populations) and all(row["complete"] for row in all_lane_populations)
            if not lane_sources_complete:
                lane_state = "SOURCE_REQUIRED"
            elif lane_fact_ids:
                lane_state = "NOT_COMPARABLE" if any(comparison_states[fact_id] == "NOT_COMPARABLE" for fact_id in lane_fact_ids) else "OBSERVED"
            elif all_lane_populations:
                lane_state = "NO_EVENT_RECORDED"
            else:
                lane_state = "SOURCE_REQUIRED"
            rule_results: list[dict[str, Any]] = []
            for rule in [item for item in rules if item["lane"] == lane]:
                matching = [fact_by_id[fact_id] for fact_id in lane_fact_ids if fact_by_id[fact_id]["kind"] == rule["fact_kind"]]
                if not lane_sources_complete:
                    state, fact_id = "SOURCE_REQUIRED", None
                elif not matching:
                    state, fact_id = "SOURCE_REQUIRED", None
                elif len(matching) > 1:
                    state, fact_id = "METRIC_CONFLICT", None
                else:
                    fact = matching[0]
                    fact_id = fact["fact_id"]
                    if fact["value_type"] != rule["value_type"] or comparison_states[fact_id] == "NOT_COMPARABLE":
                        state = "NOT_COMPARABLE"
                    elif fact["unit"] != rule["unit"] or fact["basis"] != rule["basis"] or fact["currency"] != rule["currency"]:
                        state = "METRIC_CONFLICT"
                    else:
                        if rule["value_type"] == "decimal":
                            actual, threshold = Decimal(fact["current_value"]), Decimal(rule["threshold"])
                        elif rule["value_type"] == "timestamp":
                            _, actual = _timestamp(fact["current_value"], "fact.current_value")
                            _, threshold = _timestamp(rule["threshold"], "rule.threshold")
                        else:
                            actual, threshold = fact["current_value"], rule["threshold"]
                        state = "RULE_MATCHED" if _compare(actual, rule["operator"], threshold) else "RULE_NOT_MATCHED"
                rule_results.append({"rule_id": rule["rule_id"], "fact_id": fact_id, "state": state,
                                     "disposition_label": rule["disposition_label"],
                                     "human_review_role_id": rule["human_review_role_id"]})
            grouped: dict[tuple[str, int], set[str]] = defaultdict(set)
            for result in rule_results:
                rule = next(item for item in rules if item["rule_id"] == result["rule_id"])
                if result["state"] == "RULE_MATCHED":
                    grouped[(rule["fact_kind"], rule["precedence"])].add(rule["disposition_label"])
            if any(len(values) > 1 for values in grouped.values()):
                lane_state = "HUMAN_REVIEW_REQUIRED"
            elif any(result["state"] == "RULE_MATCHED" for result in rule_results):
                lane_state = "HUMAN_REVIEW_REQUIRED"
            review_states.add(lane_state)
            lane_reviews.append({"lane": lane, "state": lane_state, "fact_ids": lane_fact_ids,
                                 "population_receipt_ids": sorted(row["population_receipt_id"] for row in lane_populations),
                                 "rule_results": sorted(rule_results, key=lambda item: item["rule_id"])})
        account_reviews.append({"account_id": account_id, "lane_reviews": lane_reviews})

    if "HUMAN_REVIEW_REQUIRED" in review_states:
        review_state = "HUMAN_REVIEW_REQUIRED"
    elif review_states & {"SOURCE_REQUIRED", "NOT_COMPARABLE", "METRIC_CONFLICT"}:
        review_state = "HUMAN_REVIEW_REQUIRED"
    else:
        review_state = "OBSERVED"

    return {
        "review_type": "CUSTOMER_RETENTION_EVIDENCE_REVIEW",
        "review_state": review_state,
        "policy_receipt": {
            "policy_id": policy["policy_id"], "policy_version": policy["policy_version"],
            "owner_id": policy["owner_id"], "human_reviewer_role_id": policy["human_reviewer_role_id"],
            "effective_at": policy["effective_at"], "expires_at": policy["expires_at"],
            "cutoff_at": policy["cutoff_at"], "timezone": policy["timezone"],
            "approved_purpose": policy["approved_purpose"], "prohibited_uses": sorted(policy["prohibited_uses"]),
            "correction_path": policy["correction_path"], "bindings": sorted(bindings.values(), key=lambda item: (item["lane"], item["source_id"])),
            "rule_receipts": rule_receipts,
        },
        "declared_population_receipt": {"account_ids": sorted(account_ids), "population_state": "OBSERVED"},
        "identity_link_receipts": sorted(links, key=lambda item: item["link_id"]),
        "source_population_receipts": sorted(populations, key=lambda item: item["population_receipt_id"]),
        "fact_receipts": sorted(facts, key=lambda item: item["fact_id"]),
        "account_reviews": account_reviews,
        "boundary": BOUNDARY,
    }


def render_review_output(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    try:
        payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")) if len(sys.argv) > 1 else json.load(sys.stdin)
        sys.stdout.write(render_review_output(review_retention_evidence(payload)))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f"INPUT_ERROR: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
