#!/usr/bin/env python3
"""Deterministic, read-only validation for supplied territory scenarios."""

from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import json


BOUNDARY = "NO TERRITORY OR OWNERSHIP CHANGE / NO QUOTA OR WORKFORCE ACTION"
PROHIBITED_PERSON_FIELDS = {
    "name", "email", "home_address", "home_coordinates", "latitude", "longitude",
    "protected_trait", "protected_traits", "manager_narrative", "performance",
    "quota_attainment", "discipline", "attrition_risk", "productivity_score",
}
SOLVER_STATUSES = {"OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNBOUNDED", "LIMIT", "UNDETERMINED", "NOT_RUN"}


def _identifier(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _identifier_list(values, name, allow_empty=False):
    if not isinstance(values, list) or (not values and not allow_empty):
        raise ValueError(f"{name} must be a {'list' if allow_empty else 'non-empty list'}")
    cleaned = [_identifier(value, name) for value in values]
    if len(cleaned) != len(set(cleaned)):
        raise ValueError(f"{name} must contain unique IDs")
    return cleaned


def _count(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _decimal(value, name, allow_none=False):
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"{name} must be an exact decimal-compatible value")
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"{name} must be an exact decimal-compatible value") from error
    if not result.is_finite() or result < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return result


def _boolean(value, name):
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def _required_fields(row, fields, label):
    if not isinstance(row, dict):
        raise ValueError(f"each {label} must be an object")
    missing = [field for field in fields if field not in row]
    if missing:
        raise ValueError(f"{label} missing fields: {', '.join(sorted(missing))}")


def assert_no_person_fields(value, path="root"):
    """Reject disallowed person-level fields anywhere in an input packet."""
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} keys must be strings")
            folded = key.casefold()
            rep_identity_field = folded.startswith("rep_") and folded.removeprefix("rep_") in {"name", "email", "home_address", "home_coordinates", "performance", "quota_attainment"}
            if folded in PROHIBITED_PERSON_FIELDS or rep_identity_field or folded.startswith("protected_trait"):
                raise ValueError(f"prohibited person field: {path}.{key}")
            assert_no_person_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_person_fields(child, f"{path}[{index}]")
    return {"state": "VALID"}


def validate_evidence(rows):
    required = {
        "evidence_id", "source_id", "source_version", "extracted_at", "as_of",
        "policy_id", "purpose", "access_scope",
    }
    if not isinstance(rows, list) or not rows:
        raise ValueError("evidence rows must be a non-empty list")
    seen = set()
    normalized = []
    for row in rows:
        _required_fields(row, required, "evidence row")
        assert_no_person_fields(row)
        evidence_id = _identifier(row["evidence_id"], "evidence_id")
        if evidence_id in seen:
            raise ValueError("evidence IDs must be unique")
        clean = {field: _identifier(row[field], field) for field in sorted(required)}
        seen.add(evidence_id)
        normalized.append(clean)
    return {"state": "VALID", "evidence_count": len(normalized), "evidence": sorted(normalized, key=lambda row: row["evidence_id"])}


def reconcile_assignments(*, account_ids, rep_ids, assignment_rows, shared_model=None):
    accounts = _identifier_list(account_ids, "account_ids")
    reps = _identifier_list(rep_ids, "rep_ids")
    if not isinstance(assignment_rows, list):
        raise ValueError("assignment_rows must be a list")
    shared_approved = False
    shared_model_id = None
    shared_counting_method = None
    if shared_model is not None:
        _required_fields(shared_model, {"model_id", "approved", "role_policy_id", "counting_policy_id", "counting_method"}, "shared model")
        shared_model_id = _identifier(shared_model["model_id"], "model_id")
        shared_approved = _boolean(shared_model["approved"], "shared model approved")
        _identifier(shared_model["role_policy_id"], "role_policy_id")
        _identifier(shared_model["counting_policy_id"], "counting_policy_id")
        shared_counting_method = _identifier(shared_model["counting_method"], "counting_method").upper()
        if shared_approved and shared_counting_method != "EACH_ASSIGNED_REP":
            raise ValueError("unsupported approved shared counting method")
    known_accounts = set(accounts)
    known_reps = set(reps)
    by_account = defaultdict(list)
    unknown_accounts = set()
    unknown_reps = set()
    duplicate_assignment_ids = set()
    seen_assignment_ids = set()
    invalid_shared = set()
    normalized = []
    for row in assignment_rows:
        _required_fields(row, {"assignment_id", "account_id", "rep_ids", "evidence_ids"}, "assignment row")
        assert_no_person_fields(row)
        assignment_id = _identifier(row["assignment_id"], "assignment_id")
        account_id = _identifier(row["account_id"], "account_id")
        assigned_reps = _identifier_list(row["rep_ids"], "assignment rep_ids")
        evidence_ids = _identifier_list(row["evidence_ids"], "assignment evidence_ids")
        if assignment_id in seen_assignment_ids:
            duplicate_assignment_ids.add(assignment_id)
        seen_assignment_ids.add(assignment_id)
        if account_id not in known_accounts:
            unknown_accounts.add(account_id)
        for rep_id in assigned_reps:
            if rep_id not in known_reps:
                unknown_reps.add(rep_id)
        if len(assigned_reps) > 1 and not shared_approved:
            invalid_shared.add(account_id)
        normalized_row = {
            "assignment_id": assignment_id,
            "account_id": account_id,
            "rep_ids": sorted(assigned_reps),
            "evidence_ids": sorted(evidence_ids),
        }
        normalized.append(normalized_row)
        by_account[account_id].append(normalized_row)
    missing = sorted(known_accounts - set(by_account))
    duplicate_accounts = sorted(account_id for account_id in known_accounts if len(by_account[account_id]) > 1)
    issues = {
        "missing_account_ids": missing,
        "duplicate_account_ids": duplicate_accounts,
        "unknown_account_ids": sorted(unknown_accounts),
        "unknown_rep_ids": sorted(unknown_reps),
        "duplicate_assignment_ids": sorted(duplicate_assignment_ids),
        "unsupported_shared_account_ids": sorted(invalid_shared),
    }
    state = "VALID" if not any(issues.values()) else "INCOMPLETE_POPULATION"
    return {
        "state": state,
        "account_ids": sorted(accounts),
        "rep_ids": sorted(reps),
        "account_count": len(accounts),
        "rep_count": len(reps),
        "assignment_row_count": len(assignment_rows),
        "shared_model_id": shared_model_id if shared_approved else None,
        "shared_counting_method": shared_counting_method if shared_approved else None,
        "assignments": sorted(normalized, key=lambda row: (row["account_id"], row["assignment_id"])),
        **issues,
    }


def _assignment_pairs(reconciliation):
    if not isinstance(reconciliation, dict) or "assignments" not in reconciliation:
        raise ValueError("assignment reconciliation is required")
    return {(row["account_id"], rep_id) for row in reconciliation["assignments"] for rep_id in row["rep_ids"]}


def validate_constraints(*, reconciliation, constraint_rows):
    if not isinstance(constraint_rows, list) or not constraint_rows:
        return {"state": "POLICY_REQUIRED", "constraint_count": 0, "violations": [], "conflicts": []}
    pairs = _assignment_pairs(reconciliation)
    counts = Counter(rep_id for _, rep_id in pairs)
    account_reps = defaultdict(set)
    for account_id, rep_id in pairs:
        account_reps[account_id].add(rep_id)
    seen = set()
    normalized = []
    violations = []
    conflicts = []
    pinned = {}
    forbidden = set()
    lower_bounds = {}
    upper_bounds = {}
    allowed_pairs = defaultdict(set)
    known_accounts = set(reconciliation.get("account_ids", []))
    known_reps = set(reconciliation.get("rep_ids", []))
    for row in constraint_rows:
        _required_fields(row, {"constraint_id", "type", "evidence_id", "policy_id", "owner"}, "constraint row")
        assert_no_person_fields(row)
        constraint_id = _identifier(row["constraint_id"], "constraint_id")
        if constraint_id in seen:
            raise ValueError("constraint IDs must be unique")
        seen.add(constraint_id)
        kind = _identifier(row["type"], "constraint type").upper()
        base = {key: _identifier(row[key], key) for key in ("constraint_id", "evidence_id", "policy_id", "owner")}
        base["type"] = kind
        if kind in {"PINNED", "FORBIDDEN", "ALLOWED_PAIR", "RELATIONSHIP_REQUIRED"}:
            account_id = _identifier(row.get("account_id"), "account_id")
            rep_id = _identifier(row.get("rep_id"), "rep_id")
            base.update(account_id=account_id, rep_id=rep_id)
            if account_id not in known_accounts or rep_id not in known_reps:
                conflicts.append({"constraint_id": constraint_id, "reason": "constraint references an unknown account or rep"})
            assigned = (account_id, rep_id) in pairs
            if kind in {"PINNED", "RELATIONSHIP_REQUIRED"} and not assigned:
                violations.append({"constraint_id": constraint_id, "reason": "required pair is not assigned"})
            if kind == "FORBIDDEN" and assigned:
                violations.append({"constraint_id": constraint_id, "reason": "forbidden pair is assigned"})
            if kind == "ALLOWED_PAIR":
                allowed_pairs[account_id].add(rep_id)
            if kind == "PINNED":
                if account_id in pinned and pinned[account_id] != rep_id:
                    conflicts.append({"constraint_id": constraint_id, "reason": "account has conflicting pinned reps"})
                pinned[account_id] = rep_id
            if kind == "FORBIDDEN":
                forbidden.add((account_id, rep_id))
        elif kind in {"MIN_COUNT", "MAX_COUNT"}:
            rep_id = _identifier(row.get("rep_id"), "rep_id")
            value = _count(row.get("value"), "constraint value")
            base.update(rep_id=rep_id, value=value)
            if rep_id not in known_reps:
                conflicts.append({"constraint_id": constraint_id, "reason": "count constraint references an unknown rep"})
            if kind == "MIN_COUNT":
                lower_bounds[rep_id] = max(lower_bounds.get(rep_id, 0), value)
                if counts[rep_id] < value:
                    violations.append({"constraint_id": constraint_id, "reason": "assigned count is below approved minimum"})
            else:
                upper_bounds[rep_id] = min(upper_bounds.get(rep_id, value), value)
                if counts[rep_id] > value:
                    violations.append({"constraint_id": constraint_id, "reason": "assigned count exceeds approved maximum"})
        else:
            raise ValueError(f"unsupported constraint type: {kind}")
        normalized.append(base)
    for account_id, rep_id in pinned.items():
        if (account_id, rep_id) in forbidden:
            conflicts.append({"account_id": account_id, "rep_id": rep_id, "reason": "pair is both pinned and forbidden"})
    for account_id, allowed_reps in allowed_pairs.items():
        disallowed = sorted(account_reps.get(account_id, set()) - allowed_reps)
        if disallowed:
            violations.append({"constraint_id": ",".join(sorted(row["constraint_id"] for row in normalized if row["type"] == "ALLOWED_PAIR" and row.get("account_id") == account_id)), "reason": f"account is assigned to disallowed reps: {', '.join(disallowed)}"})
    for rep_id in set(lower_bounds) & set(upper_bounds):
        if lower_bounds[rep_id] > upper_bounds[rep_id]:
            conflicts.append({"rep_id": rep_id, "reason": "approved minimum exceeds approved maximum"})
    state = "CONSTRAINT_VIOLATION" if violations or conflicts else "VALID"
    return {
        "state": state,
        "constraint_count": len(normalized),
        "constraints": sorted(normalized, key=lambda row: row["constraint_id"]),
        "violations": sorted(violations, key=lambda row: row["constraint_id"]),
        "conflicts": sorted(conflicts, key=lambda row: (row.get("account_id", ""), row.get("rep_id", ""), row.get("constraint_id", ""))),
    }


def summarize_counts(reconciliation):
    counts = Counter()
    for row in reconciliation.get("assignments", []):
        for rep_id in row["rep_ids"]:
            counts[rep_id] += 1
    return [{"rep_id": rep_id, "assigned_account_count": counts[rep_id]} for rep_id in sorted(counts)]


def summarize_amounts(*, reconciliation, amount_rows):
    if not isinstance(amount_rows, list):
        raise ValueError("amount_rows must be a list")
    pairs = _assignment_pairs(reconciliation)
    assigned_accounts = {account_id for account_id, _ in pairs}
    seen = set()
    by_account = {}
    bases = set()
    for row in amount_rows:
        _required_fields(row, {"account_id", "amount", "currency", "period", "basis", "evidence_id"}, "amount row")
        assert_no_person_fields(row)
        account_id = _identifier(row["account_id"], "account_id")
        if account_id in seen:
            raise ValueError("amount account IDs must be unique")
        seen.add(account_id)
        normalized = {
            "account_id": account_id,
            "amount": _decimal(row["amount"], "amount", allow_none=True),
            "currency": _identifier(row["currency"], "currency").upper(),
            "period": _identifier(row["period"], "period"),
            "basis": _identifier(row["basis"], "basis"),
            "evidence_id": _identifier(row["evidence_id"], "evidence_id"),
        }
        by_account[account_id] = normalized
        bases.add((normalized["currency"], normalized["period"], normalized["basis"]))
    missing = sorted(assigned_accounts - set(by_account))
    extra = sorted(set(by_account) - assigned_accounts)
    unknown = sorted(account_id for account_id in assigned_accounts if account_id in by_account and by_account[account_id]["amount"] is None)
    if len(bases) > 1:
        state = "INCOMPARABLE"
    elif missing or extra or unknown:
        state = "SOURCE_REQUIRED"
    elif not bases:
        state = "SOURCE_REQUIRED"
    else:
        state = "VALID"
    totals = defaultdict(lambda: Decimal("0"))
    if len(bases) == 1:
        for account_id, rep_id in pairs:
            row = by_account.get(account_id)
            if row and row["amount"] is not None:
                totals[rep_id] += row["amount"]
    basis = None if len(bases) != 1 else dict(zip(("currency", "period", "basis"), next(iter(bases))))
    return {
        "state": state,
        "basis": basis,
        "covered_account_count": len(assigned_accounts - set(missing) - set(unknown)),
        "assigned_account_count": len(assigned_accounts),
        "missing_account_ids": missing,
        "extra_account_ids": extra,
        "unknown_amount_account_ids": unknown,
        "per_rep_totals": [{"rep_id": rep_id, "amount": totals[rep_id]} for rep_id in sorted(totals)] if basis else [],
    }


def summarize_routes(*, reconciliation, route_rows):
    if not isinstance(route_rows, list):
        raise ValueError("route_rows must be a list")
    pairs = _assignment_pairs(reconciliation)
    seen_routes = set()
    by_pair = {}
    policy_keys = set()
    invalid_status_pairs = set()
    for row in route_rows:
        required = {"route_id", "account_id", "rep_id", "duration_minutes", "distance", "distance_unit", "mode", "work_anchor_id", "departure_policy_id", "routing_policy_id", "source_id", "source_version", "status", "fallback", "visit_frequency", "evidence_id"}
        _required_fields(row, required, "route row")
        assert_no_person_fields(row)
        route_id = _identifier(row["route_id"], "route_id")
        if route_id in seen_routes:
            raise ValueError("route IDs must be unique")
        seen_routes.add(route_id)
        pair = (_identifier(row["account_id"], "account_id"), _identifier(row["rep_id"], "rep_id"))
        if pair in by_pair:
            raise ValueError("each assigned account/rep pair may have one route row")
        normalized = {
            "route_id": route_id,
            "account_id": pair[0],
            "rep_id": pair[1],
            "duration_minutes": _decimal(row["duration_minutes"], "duration_minutes", allow_none=True),
            "distance": _decimal(row["distance"], "distance", allow_none=True),
            "distance_unit": _identifier(row["distance_unit"], "distance_unit"),
            "mode": _identifier(row["mode"], "mode"),
            "work_anchor_id": _identifier(row["work_anchor_id"], "work_anchor_id"),
            "departure_policy_id": _identifier(row["departure_policy_id"], "departure_policy_id"),
            "routing_policy_id": _identifier(row["routing_policy_id"], "routing_policy_id"),
            "source_id": _identifier(row["source_id"], "source_id"),
            "source_version": _identifier(row["source_version"], "source_version"),
            "status": _identifier(row["status"], "status").upper(),
            "fallback": _identifier(row["fallback"], "fallback").upper(),
            "visit_frequency": _decimal(row["visit_frequency"], "visit_frequency"),
            "evidence_id": _identifier(row["evidence_id"], "evidence_id"),
        }
        if normalized["status"] != "OK" or normalized["fallback"] not in {"NONE", "APPROVED"} or normalized["duration_minutes"] is None or normalized["distance"] is None:
            invalid_status_pairs.add(pair)
        by_pair[pair] = normalized
        policy_keys.add((normalized["mode"], normalized["departure_policy_id"], normalized["routing_policy_id"], normalized["distance_unit"]))
    missing_pairs = sorted(pairs - set(by_pair))
    extra_pairs = sorted(set(by_pair) - pairs)
    usable_pairs = pairs & set(by_pair) - invalid_status_pairs
    totals = defaultdict(lambda: {"duration_minutes": Decimal("0"), "distance": Decimal("0"), "route_count": 0})
    if len(policy_keys) == 1:
        for pair in usable_pairs:
            row = by_pair[pair]
            totals[pair[1]]["duration_minutes"] += row["duration_minutes"] * row["visit_frequency"]
            if row["distance"] is not None:
                totals[pair[1]]["distance"] += row["distance"] * row["visit_frequency"]
            totals[pair[1]]["route_count"] += 1
    if len(policy_keys) > 1:
        state = "INCOMPARABLE"
    elif missing_pairs or extra_pairs or invalid_status_pairs:
        state = "SOURCE_REQUIRED"
    elif not pairs:
        state = "INCOMPLETE_POPULATION"
    else:
        state = "VALID"
    return {
        "state": state,
        "assigned_pair_count": len(pairs),
        "usable_pair_count": len(usable_pairs),
        "missing_pairs": [{"account_id": account_id, "rep_id": rep_id} for account_id, rep_id in missing_pairs],
        "extra_pairs": [{"account_id": account_id, "rep_id": rep_id} for account_id, rep_id in extra_pairs],
        "invalid_status_pairs": [{"account_id": account_id, "rep_id": rep_id} for account_id, rep_id in sorted(invalid_status_pairs)],
        "route_policy": None if len(policy_keys) != 1 else dict(zip(("mode", "departure_policy_id", "routing_policy_id", "distance_unit"), next(iter(policy_keys)))),
        "per_rep_totals": [{"rep_id": rep_id, **totals[rep_id]} for rep_id in sorted(totals)] if len(policy_keys) == 1 else [],
    }


def validate_solver_receipt(receipt):
    if receipt is None:
        return {"state": "NOT_RUN", "claimed_optimal": False}
    required = {"formulation_id", "objective_normalization_id", "solver", "solver_version", "seed", "status", "primal_bound", "dual_bound", "gap", "tolerance", "time_limit", "memory_limit", "determinism", "constraint_violation_count", "tie_policy_id"}
    _required_fields(receipt, required, "solver receipt")
    assert_no_person_fields(receipt)
    clean = {field: receipt[field] for field in required}
    for field in ("formulation_id", "objective_normalization_id", "solver", "solver_version", "time_limit", "memory_limit", "determinism", "tie_policy_id"):
        clean[field] = _identifier(clean[field], field)
    clean["seed"] = _count(clean["seed"], "seed")
    clean["constraint_violation_count"] = _count(clean["constraint_violation_count"], "constraint_violation_count")
    for field in ("primal_bound", "dual_bound", "gap", "tolerance"):
        clean[field] = _decimal(clean[field], field, allow_none=True)
    clean["status"] = _identifier(clean["status"], "status").upper()
    if clean["status"] not in SOLVER_STATUSES:
        raise ValueError("unsupported solver status")
    claimed_optimal = clean["status"] == "OPTIMAL"
    complete_optimal = claimed_optimal and all(clean[field] is not None for field in ("primal_bound", "dual_bound", "gap", "tolerance")) and clean["constraint_violation_count"] == 0
    if claimed_optimal and not complete_optimal:
        state = "POLICY_REQUIRED"
    elif clean["status"] in {"LIMIT", "UNDETERMINED"}:
        state = "SOLVER_LIMIT"
    elif clean["constraint_violation_count"]:
        state = "CONSTRAINT_VIOLATION"
    else:
        state = clean["status"]
    return {"state": state, "claimed_optimal": claimed_optimal, **{field: clean[field] for field in sorted(clean)}}


def scenario_review(*, scenario_id, account_ids, rep_ids, assignment_rows, evidence_rows, constraint_rows, amount_rows, route_rows, workforce_review_state, shared_model=None, solver_receipt=None):
    scenario_id = _identifier(scenario_id, "scenario_id")
    workforce_review_state = _identifier(workforce_review_state, "workforce_review_state").upper()
    if workforce_review_state not in {"APPROVED", "REVIEW_REQUIRED", "IDENTITY_REVIEW", "POLICY_REQUIRED"}:
        raise ValueError("unsupported workforce review state")
    evidence = validate_evidence(evidence_rows)
    assignments = reconcile_assignments(account_ids=account_ids, rep_ids=rep_ids, assignment_rows=assignment_rows, shared_model=shared_model)
    constraints = validate_constraints(reconciliation=assignments, constraint_rows=constraint_rows)
    amounts = summarize_amounts(reconciliation=assignments, amount_rows=amount_rows)
    routes = summarize_routes(reconciliation=assignments, route_rows=route_rows)
    solver = validate_solver_receipt(solver_receipt)
    states = [assignments["state"], constraints["state"], amounts["state"], routes["state"], solver["state"], workforce_review_state]
    if assignments["state"] != "VALID":
        overall = "INCOMPLETE_POPULATION"
    elif constraints["state"] == "CONSTRAINT_VIOLATION":
        overall = "CONSTRAINT_VIOLATION"
    elif any(state in {"POLICY_REQUIRED", "SOURCE_REQUIRED", "IDENTITY_REVIEW", "REVIEW_REQUIRED"} for state in states):
        overall = "POLICY_REQUIRED"
    elif any(state in {"INCOMPARABLE", "SOLVER_LIMIT", "INFEASIBLE", "UNBOUNDED"} for state in states):
        overall = "INCOMPARABLE"
    else:
        overall = "VALID"
    return {
        "scenario_id": scenario_id,
        "state": overall,
        "evidence": evidence,
        "assignments": assignments,
        "constraints": constraints,
        "counts": summarize_counts(assignments),
        "amounts": amounts,
        "routes": routes,
        "solver": solver,
        "workforce_review_state": workforce_review_state,
        "boundary": BOUNDARY,
    }


def compare_scenarios(*, scenario_reviews, current_assignment_rows, same_population, same_policies, same_constraints, same_amount_basis, same_route_policy, current_shared_model=None):
    if not isinstance(scenario_reviews, list) or len(scenario_reviews) < 2:
        raise ValueError("at least two scenario reviews are required")
    flags = {"same_population": same_population, "same_policies": same_policies, "same_constraints": same_constraints, "same_amount_basis": same_amount_basis, "same_route_policy": same_route_policy}
    for name, value in flags.items():
        _boolean(value, name)
    population_signatures = {
        (tuple(review["assignments"]["account_ids"]), tuple(review["assignments"]["rep_ids"]), review["assignments"]["shared_model_id"], review["assignments"]["shared_counting_method"])
        for review in scenario_reviews
    }
    policy_signatures = {
        tuple(sorted((row["policy_id"] for row in review["evidence"]["evidence"])))
        for review in scenario_reviews
    }
    constraint_signatures = {
        tuple(tuple(sorted(row.items())) for row in review["constraints"].get("constraints", []))
        for review in scenario_reviews
    }
    amount_signatures = {tuple(sorted((review["amounts"]["basis"] or {}).items())) for review in scenario_reviews}
    route_signatures = {tuple(sorted((review["routes"]["route_policy"] or {}).items())) for review in scenario_reviews}
    actual_checks = {
        "same_population": len(population_signatures) == 1,
        "same_policies": len(policy_signatures) == 1,
        "same_constraints": len(constraint_signatures) == 1,
        "same_amount_basis": len(amount_signatures) == 1,
        "same_route_policy": len(route_signatures) == 1,
    }
    current = reconcile_assignments(
        account_ids=sorted({account_id for review in scenario_reviews for account_id in review["assignments"]["account_ids"]}),
        rep_ids=sorted({rep_id for review in scenario_reviews for rep_id in review["assignments"]["rep_ids"]}),
        assignment_rows=current_assignment_rows,
        shared_model=current_shared_model,
    )
    current_map = {row["account_id"]: tuple(row["rep_ids"]) for row in current["assignments"]}
    rows = []
    for review in sorted(scenario_reviews, key=lambda item: item["scenario_id"]):
        candidate_map = {row["account_id"]: tuple(row["rep_ids"]) for row in review["assignments"]["assignments"]}
        moved = sorted(account_id for account_id in current_map if candidate_map.get(account_id) != current_map[account_id])
        rows.append({
            "scenario_id": review["scenario_id"],
            "scenario_state": review["state"],
            "assignment_state": review["assignments"]["state"],
            "constraint_state": review["constraints"]["state"],
            "amount_state": review["amounts"]["state"],
            "route_state": review["routes"]["state"],
            "solver_state": review["solver"]["state"],
            "workforce_review_state": review["workforce_review_state"],
            "moved_account_count": len(moved),
            "moved_account_ids": moved,
            "counts": review["counts"],
            "amount_basis": review["amounts"]["basis"],
            "amount_coverage": {"covered_account_count": review["amounts"]["covered_account_count"], "assigned_account_count": review["amounts"]["assigned_account_count"], "missing_account_ids": review["amounts"]["missing_account_ids"], "unknown_amount_account_ids": review["amounts"]["unknown_amount_account_ids"]},
            "amount_totals": review["amounts"]["per_rep_totals"],
            "route_policy": review["routes"]["route_policy"],
            "route_coverage": {"assigned_pair_count": review["routes"]["assigned_pair_count"], "usable_pair_count": review["routes"]["usable_pair_count"], "missing_pairs": review["routes"]["missing_pairs"], "invalid_status_pairs": review["routes"]["invalid_status_pairs"]},
            "route_totals": review["routes"]["per_rep_totals"],
            "solver_receipt": review["solver"],
        })
    comparable = all(flags.values()) and all(actual_checks.values()) and current["state"] == "VALID" and all(review["state"] == "VALID" for review in scenario_reviews)
    return {"state": "VALID" if comparable else "INCOMPARABLE", "ranked": False, "selected_scenario_id": None, "declared_flags": flags, "actual_checks": actual_checks, "scenarios": rows, "boundary": BOUNDARY}


def build_downstream_receipt(*, receipt_id, cutoff, timezone, policy_ids, scenario_reviews, comparison, reviewer, approver, decision_rule_id=None, approval_state="APPROVAL_REQUIRED"):
    for value, name in ((receipt_id, "receipt_id"), (cutoff, "cutoff"), (timezone, "timezone"), (reviewer, "reviewer"), (approver, "approver")):
        _identifier(value, name)
    if not isinstance(policy_ids, dict) or not policy_ids:
        raise ValueError("policy_ids must be a non-empty object")
    clean_policies = {str(key): _identifier(value, "policy ID") for key, value in sorted(policy_ids.items())}
    approval_state = _identifier(approval_state, "approval_state").upper()
    if approval_state not in {"APPROVAL_REQUIRED", "REVIEW_REQUIRED", "APPROVED_FOR_DECISION_REVIEW"}:
        raise ValueError("unsupported approval state")
    if approval_state == "APPROVED_FOR_DECISION_REVIEW" and not decision_rule_id:
        raise ValueError("decision_rule_id is required for decision review")
    if approval_state == "APPROVED_FOR_DECISION_REVIEW" and (comparison.get("state") != "VALID" or any(review.get("state") != "VALID" for review in scenario_reviews)):
        raise ValueError("decision review requires complete comparable scenario evidence")
    if comparison.get("selected_scenario_id") is not None or comparison.get("ranked") is not False:
        raise ValueError("comparison must remain non-ranked and unselected")
    scenario_rows = []
    for review in sorted(scenario_reviews, key=lambda item: item["scenario_id"]):
        scenario_rows.append({
            "scenario_id": review["scenario_id"],
            "state": review["state"],
            "population_state": review["assignments"]["state"],
            "constraint_state": review["constraints"]["state"],
            "amount_state": review["amounts"]["state"],
            "route_state": review["routes"]["state"],
            "solver_state": review["solver"]["state"],
            "workforce_review_state": review["workforce_review_state"],
            "evidence_ids": [row["evidence_id"] for row in review["evidence"]["evidence"]],
            "counts": review["counts"],
            "constraint_violations": review["constraints"]["violations"],
            "constraint_conflicts": review["constraints"]["conflicts"],
            "amount_basis": review["amounts"]["basis"],
            "amount_coverage": {"covered_account_count": review["amounts"]["covered_account_count"], "assigned_account_count": review["amounts"]["assigned_account_count"], "missing_account_ids": review["amounts"]["missing_account_ids"], "extra_account_ids": review["amounts"]["extra_account_ids"], "unknown_amount_account_ids": review["amounts"]["unknown_amount_account_ids"]},
            "amount_totals": review["amounts"]["per_rep_totals"],
            "route_policy": review["routes"]["route_policy"],
            "route_coverage": {"assigned_pair_count": review["routes"]["assigned_pair_count"], "usable_pair_count": review["routes"]["usable_pair_count"], "missing_pairs": review["routes"]["missing_pairs"], "extra_pairs": review["routes"]["extra_pairs"], "invalid_status_pairs": review["routes"]["invalid_status_pairs"]},
            "route_totals": review["routes"]["per_rep_totals"],
            "solver_receipt": review["solver"],
        })
    receipt = {
        "receipt_id": _identifier(receipt_id, "receipt_id"),
        "cutoff": _identifier(cutoff, "cutoff"),
        "timezone": _identifier(timezone, "timezone"),
        "policy_ids": clean_policies,
        "scenarios": scenario_rows,
        "comparison_state": comparison["state"],
        "ranked": False,
        "selected_scenario_id": None,
        "decision_rule_id": _identifier(decision_rule_id, "decision_rule_id") if decision_rule_id else None,
        "approval_state": approval_state,
        "reviewer": _identifier(reviewer, "reviewer"),
        "approver": _identifier(approver, "approver"),
        "boundary": BOUNDARY,
    }
    assert_no_person_fields(receipt)
    return receipt


def render_receipt_json(receipt):
    """Serialize a bounded receipt without renaming or dropping nested fields."""
    if not isinstance(receipt, dict):
        raise ValueError("receipt must be an object")

    def convert(value):
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, dict):
            return {key: convert(child) for key, child in value.items()}
        if isinstance(value, list):
            return [convert(child) for child in value]
        return value

    return json.dumps(convert(receipt), ensure_ascii=False, indent=2, sort_keys=True)
