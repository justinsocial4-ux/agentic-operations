#!/usr/bin/env python3
import unittest
from copy import deepcopy
from decimal import Decimal
import json

from territory_evidence import (
    BOUNDARY,
    assert_no_person_fields,
    build_downstream_receipt,
    compare_scenarios,
    reconcile_assignments,
    render_receipt_json,
    scenario_review,
    summarize_amounts,
    summarize_routes,
    validate_constraints,
    validate_evidence,
    validate_solver_receipt,
)


class TerritoryEvidenceTests(unittest.TestCase):
    def evidence(self):
        return [{"evidence_id": "E-1", "source_id": "crm-export", "source_version": "v7", "extracted_at": "2026-07-10T12:00:00Z", "as_of": "2026-07-10T11:59:59Z", "policy_id": "SRC-2", "purpose": "territory scenario review", "access_scope": "aggregate-and-pseudonymous"}]

    def assignments(self, moved=False):
        return [
            {"assignment_id": "AS-1", "account_id": "A-1", "rep_ids": ["R-2" if moved else "R-1"], "evidence_ids": ["E-1"]},
            {"assignment_id": "AS-2", "account_id": "A-2", "rep_ids": ["R-2"], "evidence_ids": ["E-1"]},
        ]

    def constraints(self):
        return [
            {"constraint_id": "C-1", "type": "PINNED", "account_id": "A-1", "rep_id": "R-1", "evidence_id": "E-1", "policy_id": "CON-1", "owner": "territory-policy-owner"},
            {"constraint_id": "C-2", "type": "MAX_COUNT", "rep_id": "R-2", "value": 2, "evidence_id": "E-1", "policy_id": "CON-1", "owner": "territory-policy-owner"},
        ]

    def amounts(self):
        return [
            {"account_id": "A-1", "amount": "100.25", "currency": "USD", "period": "FY2026", "basis": "finance-approved-arr", "evidence_id": "E-1"},
            {"account_id": "A-2", "amount": "99.75", "currency": "usd", "period": "FY2026", "basis": "finance-approved-arr", "evidence_id": "E-1"},
        ]

    def routes(self, moved=False):
        return [
            {"route_id": "RT-1", "account_id": "A-1", "rep_id": "R-2" if moved else "R-1", "duration_minutes": "30", "distance": "15.5", "distance_unit": "km", "mode": "DRIVE", "work_anchor_id": "WA-1", "departure_policy_id": "DEP-1", "routing_policy_id": "ROUTE-1", "source_id": "routes-api", "source_version": "2026-07", "status": "OK", "fallback": "NONE", "visit_frequency": "2", "evidence_id": "E-1"},
            {"route_id": "RT-2", "account_id": "A-2", "rep_id": "R-2", "duration_minutes": "20", "distance": "10", "distance_unit": "km", "mode": "DRIVE", "work_anchor_id": "WA-2", "departure_policy_id": "DEP-1", "routing_policy_id": "ROUTE-1", "source_id": "routes-api", "source_version": "2026-07", "status": "OK", "fallback": "NONE", "visit_frequency": "1", "evidence_id": "E-1"},
        ]

    def solver(self, status="OPTIMAL"):
        return {"formulation_id": "FORM-1", "objective_normalization_id": "OBJ-1", "solver": "external-solver", "solver_version": "1.2.3", "seed": 7, "status": status, "primal_bound": "10", "dual_bound": "10", "gap": "0", "tolerance": "0.0001", "time_limit": "60s", "memory_limit": "1GB", "determinism": "single-threaded", "constraint_violation_count": 0, "tie_policy_id": "TIE-1"}

    def review(self, scenario_id="S-1", moved=False, workforce="APPROVED"):
        constraints = self.constraints()
        if moved:
            constraints = constraints[1:]
        return scenario_review(scenario_id=scenario_id, account_ids=["A-1", "A-2"], rep_ids=["R-1", "R-2"], assignment_rows=self.assignments(moved), evidence_rows=self.evidence(), constraint_rows=constraints, amount_rows=self.amounts(), route_rows=self.routes(moved), workforce_review_state=workforce, solver_receipt=self.solver())

    def test_evidence_valid_and_sorted(self):
        rows = self.evidence() + [dict(self.evidence()[0], evidence_id="E-0", source_version="v6")]
        result = validate_evidence(rows)
        self.assertEqual([row["evidence_id"] for row in result["evidence"]], ["E-0", "E-1"])

    def test_evidence_duplicate_fails(self):
        with self.assertRaises(ValueError): validate_evidence(self.evidence() * 2)

    def test_evidence_missing_provenance_fails(self):
        rows = self.evidence(); rows[0]["as_of"] = ""
        with self.assertRaises(ValueError): validate_evidence(rows)

    def test_person_fields_fail_at_any_depth(self):
        with self.assertRaisesRegex(ValueError, "prohibited person field"): assert_no_person_fields({"nested": [{"email": "x@example.test"}]})

    def test_prefixed_rep_identity_field_fails(self):
        with self.assertRaisesRegex(ValueError, "prohibited person field"): assert_no_person_fields({"rep_email": "x@example.test"})

    def test_complete_assignment_is_valid(self):
        result = reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["R-1", "R-2"], assignment_rows=self.assignments())
        self.assertEqual(result["state"], "VALID")

    def test_missing_account_is_visible(self):
        result = reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["R-1", "R-2"], assignment_rows=self.assignments()[:1])
        self.assertEqual((result["state"], result["missing_account_ids"]), ("INCOMPLETE_POPULATION", ["A-2"]))

    def test_duplicate_account_is_visible(self):
        rows = self.assignments() + [dict(self.assignments()[0], assignment_id="AS-3")]
        result = reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["R-1", "R-2"], assignment_rows=rows)
        self.assertEqual(result["duplicate_account_ids"], ["A-1"])

    def test_unknown_rep_is_visible(self):
        rows = self.assignments(); rows[0]["rep_ids"] = ["R-X"]
        result = reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["R-1", "R-2"], assignment_rows=rows)
        self.assertEqual(result["unknown_rep_ids"], ["R-X"])

    def test_shared_assignment_requires_approved_model(self):
        rows = self.assignments(); rows[0]["rep_ids"] = ["R-1", "R-2"]
        result = reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["R-1", "R-2"], assignment_rows=rows)
        self.assertEqual(result["unsupported_shared_account_ids"], ["A-1"])

    def test_approved_shared_model_is_preserved(self):
        rows = self.assignments(); rows[0]["rep_ids"] = ["R-1", "R-2"]
        model = {"model_id": "TEAM-1", "approved": True, "role_policy_id": "ROLE-1", "counting_policy_id": "COUNT-1", "counting_method": "EACH_ASSIGNED_REP"}
        result = reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["R-1", "R-2"], assignment_rows=rows, shared_model=model)
        self.assertEqual((result["state"], result["shared_model_id"]), ("VALID", "TEAM-1"))

    def test_unsupported_shared_counting_method_fails(self):
        rows = self.assignments(); rows[0]["rep_ids"] = ["R-1", "R-2"]
        model = {"model_id": "TEAM-1", "approved": True, "role_policy_id": "ROLE-1", "counting_policy_id": "COUNT-1", "counting_method": "FRACTIONAL"}
        with self.assertRaises(ValueError): reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["R-1", "R-2"], assignment_rows=rows, shared_model=model)

    def reconciliation(self):
        return reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["R-1", "R-2"], assignment_rows=self.assignments())

    def test_constraints_valid(self):
        self.assertEqual(validate_constraints(reconciliation=self.reconciliation(), constraint_rows=self.constraints())["state"], "VALID")

    def test_pinned_violation_is_visible(self):
        result = validate_constraints(reconciliation=reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["R-1", "R-2"], assignment_rows=self.assignments(True)), constraint_rows=self.constraints())
        self.assertEqual(result["state"], "CONSTRAINT_VIOLATION")

    def test_conflicting_pinned_and_forbidden_is_visible(self):
        rows = self.constraints() + [{"constraint_id": "C-3", "type": "FORBIDDEN", "account_id": "A-1", "rep_id": "R-1", "evidence_id": "E-1", "policy_id": "CON-1", "owner": "territory-policy-owner"}]
        result = validate_constraints(reconciliation=self.reconciliation(), constraint_rows=rows)
        self.assertTrue(result["conflicts"])

    def test_empty_constraint_register_requires_policy(self):
        self.assertEqual(validate_constraints(reconciliation=self.reconciliation(), constraint_rows=[])["state"], "POLICY_REQUIRED")

    def test_multiple_allowed_pairs_are_a_set(self):
        rows = [
            {"constraint_id": "C-A1", "type": "ALLOWED_PAIR", "account_id": "A-1", "rep_id": "R-1", "evidence_id": "E-1", "policy_id": "CON-1", "owner": "territory-policy-owner"},
            {"constraint_id": "C-A2", "type": "ALLOWED_PAIR", "account_id": "A-1", "rep_id": "R-2", "evidence_id": "E-1", "policy_id": "CON-1", "owner": "territory-policy-owner"},
        ]
        self.assertEqual(validate_constraints(reconciliation=self.reconciliation(), constraint_rows=rows)["state"], "VALID")

    def test_unknown_constraint_target_is_conflict(self):
        rows = [{"constraint_id": "C-X", "type": "PINNED", "account_id": "A-X", "rep_id": "R-1", "evidence_id": "E-1", "policy_id": "CON-1", "owner": "territory-policy-owner"}]
        self.assertEqual(validate_constraints(reconciliation=self.reconciliation(), constraint_rows=rows)["state"], "CONSTRAINT_VIOLATION")

    def test_amounts_exact(self):
        result = summarize_amounts(reconciliation=self.reconciliation(), amount_rows=self.amounts())
        self.assertEqual((result["state"], result["per_rep_totals"]), ("VALID", [{"rep_id": "R-1", "amount": Decimal("100.25")}, {"rep_id": "R-2", "amount": Decimal("99.75")}]))

    def test_missing_amount_is_source_required(self):
        result = summarize_amounts(reconciliation=self.reconciliation(), amount_rows=self.amounts()[:1])
        self.assertEqual((result["state"], result["missing_account_ids"]), ("SOURCE_REQUIRED", ["A-2"]))

    def test_unknown_amount_is_not_zero(self):
        rows = self.amounts(); rows[1]["amount"] = None
        result = summarize_amounts(reconciliation=self.reconciliation(), amount_rows=rows)
        self.assertEqual((result["state"], result["unknown_amount_account_ids"]), ("SOURCE_REQUIRED", ["A-2"]))

    def test_mixed_currency_is_incomparable(self):
        rows = self.amounts(); rows[1]["currency"] = "EUR"
        self.assertEqual(summarize_amounts(reconciliation=self.reconciliation(), amount_rows=rows)["state"], "INCOMPARABLE")

    def test_float_amount_fails(self):
        rows = self.amounts(); rows[0]["amount"] = 1.2
        with self.assertRaises(ValueError): summarize_amounts(reconciliation=self.reconciliation(), amount_rows=rows)

    def test_amount_person_field_fails(self):
        rows = self.amounts(); rows[0]["rep_name"] = "person"
        with self.assertRaises(ValueError): summarize_amounts(reconciliation=self.reconciliation(), amount_rows=rows)

    def test_extra_amount_record_is_visible(self):
        rows = self.amounts() + [{"account_id": "A-X", "amount": "1", "currency": "USD", "period": "FY2026", "basis": "finance-approved-arr", "evidence_id": "E-1"}]
        result = summarize_amounts(reconciliation=self.reconciliation(), amount_rows=rows)
        self.assertEqual((result["state"], result["extra_account_ids"]), ("SOURCE_REQUIRED", ["A-X"]))

    def test_route_totals_use_supplied_frequency(self):
        result = summarize_routes(reconciliation=self.reconciliation(), route_rows=self.routes())
        self.assertEqual(result["per_rep_totals"][0]["duration_minutes"], Decimal("60"))

    def test_missing_route_is_source_required(self):
        result = summarize_routes(reconciliation=self.reconciliation(), route_rows=self.routes()[:1])
        self.assertEqual((result["state"], result["missing_pairs"]), ("SOURCE_REQUIRED", [{"account_id": "A-2", "rep_id": "R-2"}]))

    def test_route_error_is_not_counted(self):
        rows = self.routes(); rows[0]["status"] = "ELEMENT_ERROR"; rows[0]["duration_minutes"] = None
        result = summarize_routes(reconciliation=self.reconciliation(), route_rows=rows)
        self.assertEqual((result["state"], result["usable_pair_count"]), ("SOURCE_REQUIRED", 1))

    def test_missing_route_distance_is_not_zero(self):
        rows = self.routes(); rows[0]["distance"] = None
        result = summarize_routes(reconciliation=self.reconciliation(), route_rows=rows)
        self.assertEqual((result["state"], result["usable_pair_count"]), ("SOURCE_REQUIRED", 1))

    def test_mixed_route_policy_is_incomparable(self):
        rows = self.routes(); rows[1]["mode"] = "TRANSIT"
        self.assertEqual(summarize_routes(reconciliation=self.reconciliation(), route_rows=rows)["state"], "INCOMPARABLE")

    def test_solver_optimal_receipt(self):
        self.assertEqual(validate_solver_receipt(self.solver())["state"], "OPTIMAL")

    def test_feasible_is_not_optimal(self):
        result = validate_solver_receipt(self.solver("FEASIBLE"))
        self.assertEqual((result["state"], result["claimed_optimal"]), ("FEASIBLE", False))

    def test_limit_is_solver_limit(self):
        self.assertEqual(validate_solver_receipt(self.solver("LIMIT"))["state"], "SOLVER_LIMIT")

    def test_forged_optimal_without_gap_fails_closed(self):
        receipt = self.solver(); receipt["gap"] = None
        self.assertEqual(validate_solver_receipt(receipt)["state"], "POLICY_REQUIRED")

    def test_solver_constraint_violation_survives(self):
        receipt = self.solver("FEASIBLE"); receipt["constraint_violation_count"] = 1
        self.assertEqual(validate_solver_receipt(receipt)["state"], "CONSTRAINT_VIOLATION")

    def test_infeasible_solver_blocks_scenario(self):
        solver = self.solver("INFEASIBLE")
        result = scenario_review(scenario_id="S-I", account_ids=["A-1", "A-2"], rep_ids=["R-1", "R-2"], assignment_rows=self.assignments(), evidence_rows=self.evidence(), constraint_rows=self.constraints(), amount_rows=self.amounts(), route_rows=self.routes(), workforce_review_state="APPROVED", solver_receipt=solver)
        self.assertEqual(result["state"], "INCOMPARABLE")

    def test_scenario_valid(self):
        result = self.review()
        self.assertEqual((result["state"], result["boundary"]), ("VALID", BOUNDARY))

    def test_workforce_review_blocks_valid_state(self):
        self.assertEqual(self.review(workforce="REVIEW_REQUIRED")["state"], "POLICY_REQUIRED")

    def test_scenario_order_is_deterministic_without_mutation(self):
        assignments = self.assignments(); original = deepcopy(assignments)
        result_a = scenario_review(scenario_id="S-1", account_ids=["A-2", "A-1"], rep_ids=["R-2", "R-1"], assignment_rows=assignments, evidence_rows=self.evidence(), constraint_rows=list(reversed(self.constraints())), amount_rows=list(reversed(self.amounts())), route_rows=list(reversed(self.routes())), workforce_review_state="APPROVED", solver_receipt=self.solver())
        result_b = self.review()
        self.assertEqual(result_a, result_b)
        self.assertEqual(assignments, original)

    def comparison(self):
        return compare_scenarios(scenario_reviews=[self.review("S-2", True), self.review("S-1")], current_assignment_rows=self.assignments(), same_population=True, same_policies=True, same_constraints=True, same_amount_basis=True, same_route_policy=True)

    def test_comparison_is_non_ranked_and_sorted(self):
        result = self.comparison()
        self.assertEqual((result["ranked"], result["selected_scenario_id"], [row["scenario_id"] for row in result["scenarios"]]), (False, None, ["S-1", "S-2"]))

    def test_comparison_reports_moved_accounts(self):
        result = self.comparison()
        self.assertEqual(result["scenarios"][1]["moved_account_ids"], ["A-1"])

    def test_comparison_preserves_amount_route_and_solver_receipts(self):
        row = self.comparison()["scenarios"][0]
        self.assertEqual((row["amount_totals"][0]["amount"], row["route_totals"][0]["duration_minutes"], row["solver_receipt"]["state"]), (Decimal("100.25"), Decimal("60"), "OPTIMAL"))

    def test_changed_population_is_incomparable(self):
        result = compare_scenarios(scenario_reviews=[self.review("S-1"), self.review("S-2")], current_assignment_rows=self.assignments(), same_population=False, same_policies=True, same_constraints=True, same_amount_basis=True, same_route_policy=True)
        self.assertEqual(result["state"], "INCOMPARABLE")

    def test_declared_same_population_cannot_hide_actual_difference(self):
        second = self.review("S-2")
        second["assignments"]["account_ids"] = ["A-1", "A-2", "A-3"]
        result = compare_scenarios(scenario_reviews=[self.review("S-1"), second], current_assignment_rows=self.assignments(), same_population=True, same_policies=True, same_constraints=True, same_amount_basis=True, same_route_policy=True)
        self.assertEqual((result["state"], result["actual_checks"]["same_population"]), ("INCOMPARABLE", False))

    def test_receipt_is_bounded(self):
        reviews = [self.review("S-1"), self.review("S-2", True)]
        comparison = self.comparison()
        result = build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "SCOPE-1", "decision": "DEC-1"}, scenario_reviews=reviews, comparison=comparison, reviewer="territory-reviewer-role", approver="named-approver-role")
        self.assertEqual(result["boundary"], BOUNDARY)
        self.assertFalse({"recommendation", "best_scenario", "confidence", "quota", "fairness_score"}.intersection(result))

    def test_receipt_rejects_selected_comparison(self):
        comparison = self.comparison(); comparison["selected_scenario_id"] = "S-1"
        with self.assertRaises(ValueError): build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "SCOPE-1"}, scenario_reviews=[self.review("S-1"), self.review("S-2")], comparison=comparison, reviewer="reviewer-role", approver="approver-role")

    def test_decision_review_requires_rule(self):
        with self.assertRaises(ValueError): build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "SCOPE-1"}, scenario_reviews=[self.review("S-1"), self.review("S-2")], comparison=self.comparison(), reviewer="reviewer-role", approver="approver-role", approval_state="APPROVED_FOR_DECISION_REVIEW")

    def test_decision_review_rejects_incomparable_evidence(self):
        reviews = [self.review("S-1"), self.review("S-2", workforce="REVIEW_REQUIRED")]
        comparison = compare_scenarios(scenario_reviews=reviews, current_assignment_rows=self.assignments(), same_population=True, same_policies=True, same_constraints=True, same_amount_basis=True, same_route_policy=True)
        with self.assertRaises(ValueError): build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "SCOPE-1"}, scenario_reviews=reviews, comparison=comparison, reviewer="reviewer-role", approver="approver-role", decision_rule_id="DEC-1", approval_state="APPROVED_FOR_DECISION_REVIEW")

    def test_exact_json_renderer_preserves_nested_field_names(self):
        reviews = [self.review("S-1"), self.review("S-2", True)]
        receipt = build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "SCOPE-1"}, scenario_reviews=reviews, comparison=self.comparison(), reviewer="reviewer-role", approver="approver-role")
        rendered = json.loads(render_receipt_json(receipt))
        self.assertEqual(rendered["scenarios"][0]["counts"][0], {"rep_id": "R-1", "assigned_account_count": 1})
        self.assertEqual(rendered["scenarios"][0]["amount_totals"][0], {"rep_id": "R-1", "amount": "100.25"})
        self.assertIn("solver_receipt", rendered["scenarios"][1])

    def test_exact_json_renderer_rejects_non_object(self):
        with self.assertRaises(ValueError): render_receipt_json([])


if __name__ == "__main__":
    unittest.main()
