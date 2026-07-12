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
    validate_rep_pseudonymization_receipt,
    validate_solver_receipt,
)


class TerritoryEvidenceTests(unittest.TestCase):
    REP_ONE = "rep-00000000000000000000000000000001"
    REP_TWO = "rep-00000000000000000000000000000002"
    REP_THREE = "rep-00000000000000000000000000000003"
    REP_UNKNOWN = "rep-ffffffffffffffffffffffffffffffff"

    def evidence(self):
        return [
            {"evidence_id": "E-1", "source_id": "crm-export", "source_version": "v7", "extracted_at": "2026-07-10T12:00:00Z", "as_of": "2026-07-10T11:59:59Z", "policy_id": "SRC-2", "purpose": "territory scenario review", "access_scope": "aggregate-and-pseudonymous"},
            {"evidence_id": "E-ROUTE", "source_id": "routes-api", "source_version": "2026-07", "extracted_at": "2026-07-10T12:00:00Z", "as_of": "2026-07-10T11:59:59Z", "policy_id": "ROUTE-SRC-1", "purpose": "territory route evidence review", "access_scope": "pseudonymous-work-anchor-routes"},
        ]

    def assignments(self, moved=False):
        return [
            {"assignment_id": "AS-1", "account_id": "A-1", "rep_ids": [self.REP_TWO if moved else self.REP_ONE], "evidence_ids": ["E-1"]},
            {"assignment_id": "AS-2", "account_id": "A-2", "rep_ids": [self.REP_TWO], "evidence_ids": ["E-1"]},
        ]

    def constraint(self, **overrides):
        row = {
            "constraint_id": "C-1",
            "constraint_version": "v1",
            "type": "PINNED",
            "account_id": "A-1",
            "rep_id": self.REP_ONE,
            "evidence_id": "E-1",
            "policy_id": "CON-1",
            "policy_version": "v1",
            "effective_at": "2026-07-01T00:00:00Z",
            "owner_role_id": "role-territory-policy-owner",
            "conflict_path_id": "path-territory-constraint-conflict-v1",
        }
        row.update(overrides)
        return {key: value for key, value in row.items() if value is not None}

    def constraints(self):
        return [
            self.constraint(),
            self.constraint(constraint_id="C-2", type="MAX_COUNT", account_id=None, rep_id=self.REP_TWO, value=2),
        ]

    def amounts(self):
        return [
            {"account_id": "A-1", "amount": "100.25", "currency": "USD", "period": "FY2026", "basis": "finance-approved-arr", "evidence_id": "E-1", "source_version": "v7", "cutoff_at": "2026-07-10T11:59:59Z", "metric_owner_role_id": "role-finance-metric-owner"},
            {"account_id": "A-2", "amount": "99.75", "currency": "usd", "period": "FY2026", "basis": "finance-approved-arr", "evidence_id": "E-1", "source_version": "v7", "cutoff_at": "2026-07-10T11:59:59Z", "metric_owner_role_id": "role-finance-metric-owner"},
        ]

    def routes(self, moved=False):
        return [
            {"route_id": "RT-1", "account_id": "A-1", "rep_id": self.REP_TWO if moved else self.REP_ONE, "duration_minutes": "30", "distance": "15.5", "distance_unit": "km", "mode": "DRIVE", "work_anchor_id": "WA-1", "departure_policy_id": "DEP-1", "routing_policy_id": "ROUTE-1", "source_id": "routes-api", "source_version": "2026-07", "status": "OK", "fallback": "NONE", "visit_frequency": "2", "evidence_id": "E-ROUTE"},
            {"route_id": "RT-2", "account_id": "A-2", "rep_id": self.REP_TWO, "duration_minutes": "20", "distance": "10", "distance_unit": "km", "mode": "DRIVE", "work_anchor_id": "WA-2", "departure_policy_id": "DEP-1", "routing_policy_id": "ROUTE-1", "source_id": "routes-api", "source_version": "2026-07", "status": "OK", "fallback": "NONE", "visit_frequency": "1", "evidence_id": "E-ROUTE"},
        ]

    def pseudonymization(self, rep_ids=None, approved=True):
        return {
            "receipt_id": "receipt-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "population_id": "population-territory-reps",
            "method_id": "method-hmac-sha256-truncated-128",
            "namespace_id": "namespace-territory-reps-v1",
            "policy_id": "policy-rep-pseudonymization-v1",
            "owner_role_id": "role-privacy-owner",
            "approved": approved,
            "declared_rep_ids": list(rep_ids or [self.REP_ONE, self.REP_TWO]),
        }

    def solver(self, status="OPTIMAL"):
        return {"formulation_id": "FORM-1", "objective_normalization_id": "OBJ-1", "solver": "external-solver", "solver_version": "1.2.3", "seed": 7, "status": status, "primal_bound": "10", "dual_bound": "10", "gap": "0", "tolerance": "0.0001", "time_limit": "60s", "memory_limit": "1GB", "determinism": "single-threaded", "constraint_violation_count": 0, "tie_policy_id": "TIE-1"}

    def review(self, scenario_id="S-1", moved=False, workforce="APPROVED"):
        constraints = self.constraints()
        if moved:
            constraints = constraints[1:]
        return scenario_review(scenario_id=scenario_id, account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments(moved), evidence_rows=self.evidence(), constraint_rows=constraints, amount_rows=self.amounts(), route_rows=self.routes(moved), workforce_review_state=workforce, rep_pseudonymization_receipt=self.pseudonymization(), solver_receipt=self.solver())

    def test_evidence_valid_and_sorted(self):
        rows = self.evidence() + [dict(self.evidence()[0], evidence_id="E-0", source_version="v6")]
        result = validate_evidence(rows)
        self.assertEqual([row["evidence_id"] for row in result["evidence"]], ["E-0", "E-1", "E-ROUTE"])

    def test_evidence_rejects_unpreserved_extra_fields(self):
        rows = self.evidence()
        rows[0]["notes"] = "contact alice@example.test"
        with self.assertRaises(ValueError):
            validate_evidence(rows)

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
        result = reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments())
        self.assertEqual(result["state"], "VALID")

    def test_assignment_rejects_unpreserved_extra_fields(self):
        rows = self.assignments()
        rows[0]["notes"] = "contact alice@example.test"
        with self.assertRaises(ValueError):
            reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=rows)

    def test_direct_rep_identity_rejected(self):
        rows = self.assignments()
        rows[0]["rep_ids"] = ["Alice Smith"]
        with self.assertRaises(ValueError):
            reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["Alice Smith", self.REP_TWO], assignment_rows=rows)

    def test_structurally_different_direct_rep_identity_rejected(self):
        rows = self.assignments()
        rows[0]["rep_ids"] = ["Jordan Lee"]
        with self.assertRaises(ValueError):
            reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["Jordan Lee", self.REP_TWO], assignment_rows=rows)

    def test_readable_prefixed_rep_identity_rejected(self):
        rows = self.assignments()
        rows[0]["rep_ids"] = ["rep-alice-smith"]
        with self.assertRaises(ValueError):
            reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["rep-alice-smith", self.REP_TWO], assignment_rows=rows)

    def test_email_bearing_rep_identity_rejected(self):
        rows = self.assignments()
        rows[0]["rep_ids"] = ["rep-jordan.lee@example.test"]
        with self.assertRaises(ValueError):
            reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=["rep-jordan.lee@example.test", self.REP_TWO], assignment_rows=rows)

    def test_malformed_opaque_rep_ids_rejected(self):
        malformed = [
            "rep-0123",
            "rep-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "rep-0000000000000000000000000000000g",
            "rep-00000000000000000000000000000001-extra",
        ]
        for value in malformed:
            with self.subTest(value=value), self.assertRaises(ValueError):
                reconcile_assignments(account_ids=["A-1"], rep_ids=[value], assignment_rows=[])

    def test_valid_pseudonymization_receipt_is_population_bound(self):
        result = validate_rep_pseudonymization_receipt(self.pseudonymization(), [self.REP_ONE, self.REP_TWO])
        self.assertEqual(result["declared_rep_ids"], [self.REP_ONE, self.REP_TWO])

    def test_pseudonymization_receipt_population_mismatch_rejected(self):
        receipt = self.pseudonymization([self.REP_ONE])
        with self.assertRaises(ValueError):
            validate_rep_pseudonymization_receipt(receipt, [self.REP_ONE, self.REP_TWO])

    def test_unapproved_pseudonymization_receipt_rejected(self):
        with self.assertRaises(ValueError):
            validate_rep_pseudonymization_receipt(self.pseudonymization(approved=False), [self.REP_ONE, self.REP_TWO])

    def test_pseudonymization_receipt_rejects_extra_free_text(self):
        receipt = self.pseudonymization()
        receipt["notes"] = "contact alice@example.test"
        with self.assertRaises(ValueError):
            validate_rep_pseudonymization_receipt(receipt, [self.REP_ONE, self.REP_TWO])

    def test_missing_account_is_visible(self):
        result = reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments()[:1])
        self.assertEqual((result["state"], result["missing_account_ids"]), ("INCOMPLETE_POPULATION", ["A-2"]))

    def test_duplicate_account_is_visible(self):
        rows = self.assignments() + [dict(self.assignments()[0], assignment_id="AS-3")]
        result = reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=rows)
        self.assertEqual(result["duplicate_account_ids"], ["A-1"])

    def test_unknown_rep_is_visible(self):
        rows = self.assignments(); rows[0]["rep_ids"] = [self.REP_UNKNOWN]
        result = reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=rows)
        self.assertEqual(result["unknown_rep_ids"], [self.REP_UNKNOWN])

    def test_shared_assignment_requires_approved_model(self):
        rows = self.assignments(); rows[0]["rep_ids"] = [self.REP_ONE, self.REP_TWO]
        result = reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=rows)
        self.assertEqual(result["unsupported_shared_account_ids"], ["A-1"])

    def test_approved_shared_model_is_preserved(self):
        rows = self.assignments(); rows[0]["rep_ids"] = [self.REP_ONE, self.REP_TWO]
        model = {"model_id": "TEAM-1", "approved": True, "role_policy_id": "ROLE-1", "counting_policy_id": "COUNT-1", "counting_method": "EACH_ASSIGNED_REP"}
        result = reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=rows, shared_model=model)
        self.assertEqual((result["state"], result["shared_model_id"]), ("VALID", "TEAM-1"))

    def test_unsupported_shared_counting_method_fails(self):
        rows = self.assignments(); rows[0]["rep_ids"] = [self.REP_ONE, self.REP_TWO]
        model = {"model_id": "TEAM-1", "approved": True, "role_policy_id": "ROLE-1", "counting_policy_id": "COUNT-1", "counting_method": "FRACTIONAL"}
        with self.assertRaises(ValueError): reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=rows, shared_model=model)

    def reconciliation(self):
        return reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments())

    def test_constraints_valid(self):
        self.assertEqual(validate_constraints(reconciliation=self.reconciliation(), constraint_rows=self.constraints())["state"], "VALID")

    def test_constraint_provenance_is_preserved(self):
        row = validate_constraints(reconciliation=self.reconciliation(), constraint_rows=self.constraints())["constraints"][0]
        self.assertEqual(
            {key: row[key] for key in ("constraint_version", "policy_version", "effective_at", "owner_role_id", "conflict_path_id")},
            {
                "constraint_version": "v1",
                "policy_version": "v1",
                "effective_at": "2026-07-01T00:00:00Z",
                "owner_role_id": "role-territory-policy-owner",
                "conflict_path_id": "path-territory-constraint-conflict-v1",
            },
        )

    def test_constraint_provenance_fields_are_required(self):
        for field in ("constraint_version", "policy_version", "effective_at", "owner_role_id", "conflict_path_id"):
            rows = self.constraints()
            del rows[0][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_constraints(reconciliation=self.reconciliation(), constraint_rows=rows)

    def test_constraint_effective_time_must_be_utc(self):
        rows = self.constraints()
        rows[0]["effective_at"] = "2026-07-01"
        with self.assertRaises(ValueError):
            validate_constraints(reconciliation=self.reconciliation(), constraint_rows=rows)

    def test_future_constraint_is_not_effective_for_referenced_evidence(self):
        rows = self.constraints()
        rows[0]["effective_at"] = "2026-07-11T00:00:00Z"
        with self.assertRaises(ValueError):
            scenario_review(scenario_id="S-FUTURE-C", account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments(), evidence_rows=self.evidence(), constraint_rows=rows, amount_rows=self.amounts(), route_rows=self.routes(), workforce_review_state="APPROVED", rep_pseudonymization_receipt=self.pseudonymization(), solver_receipt=self.solver())

    def test_constraint_rejects_unpreserved_free_text(self):
        rows = self.constraints()
        rows[0]["notes"] = "contact alice@example.test"
        with self.assertRaises(ValueError):
            validate_constraints(reconciliation=self.reconciliation(), constraint_rows=rows)

    def test_pinned_violation_is_visible(self):
        result = validate_constraints(reconciliation=reconcile_assignments(account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments(True)), constraint_rows=self.constraints())
        self.assertEqual(result["state"], "CONSTRAINT_VIOLATION")

    def test_conflicting_pinned_and_forbidden_is_visible(self):
        rows = self.constraints() + [self.constraint(constraint_id="C-3", type="FORBIDDEN")]
        result = validate_constraints(reconciliation=self.reconciliation(), constraint_rows=rows)
        self.assertTrue(result["conflicts"])

    def test_empty_constraint_register_requires_policy(self):
        self.assertEqual(validate_constraints(reconciliation=self.reconciliation(), constraint_rows=[])["state"], "POLICY_REQUIRED")

    def test_multiple_allowed_pairs_are_a_set(self):
        rows = [
            self.constraint(constraint_id="C-A1", type="ALLOWED_PAIR"),
            self.constraint(constraint_id="C-A2", type="ALLOWED_PAIR", rep_id=self.REP_TWO),
        ]
        self.assertEqual(validate_constraints(reconciliation=self.reconciliation(), constraint_rows=rows)["state"], "VALID")

    def test_unknown_constraint_target_is_conflict(self):
        rows = [self.constraint(constraint_id="C-X", account_id="A-X")]
        self.assertEqual(validate_constraints(reconciliation=self.reconciliation(), constraint_rows=rows)["state"], "CONSTRAINT_VIOLATION")

    def test_constraint_rep_identity_cannot_bypass_population_contract(self):
        rows = [self.constraint(constraint_id="C-X", rep_id="rep-alice-smith")]
        with self.assertRaises(ValueError):
            validate_constraints(reconciliation=self.reconciliation(), constraint_rows=rows)

    def test_scenario_rejects_undeclared_assignment_evidence(self):
        rows = self.assignments()
        rows[0]["evidence_ids"] = ["E-NOT-DECLARED"]
        with self.assertRaises(ValueError):
            scenario_review(scenario_id="S-BAD-A", account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=rows, evidence_rows=self.evidence(), constraint_rows=self.constraints(), amount_rows=self.amounts(), route_rows=self.routes(), workforce_review_state="APPROVED", rep_pseudonymization_receipt=self.pseudonymization(), solver_receipt=self.solver())

    def test_scenario_rejects_mixed_declared_and_undeclared_assignment_evidence(self):
        rows = self.assignments()
        rows[0]["evidence_ids"] = ["E-1", "E-ROGUE"]
        with self.assertRaises(ValueError):
            scenario_review(scenario_id="S-BAD-A2", account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=rows, evidence_rows=self.evidence(), constraint_rows=self.constraints(), amount_rows=self.amounts(), route_rows=self.routes(), workforce_review_state="APPROVED", rep_pseudonymization_receipt=self.pseudonymization(), solver_receipt=self.solver())

    def test_scenario_rejects_undeclared_constraint_evidence(self):
        rows = self.constraints()
        rows[0]["evidence_id"] = "E-NOT-DECLARED"
        with self.assertRaises(ValueError):
            scenario_review(scenario_id="S-BAD-C", account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments(), evidence_rows=self.evidence(), constraint_rows=rows, amount_rows=self.amounts(), route_rows=self.routes(), workforce_review_state="APPROVED", rep_pseudonymization_receipt=self.pseudonymization(), solver_receipt=self.solver())

    def test_scenario_rejects_undeclared_amount_evidence(self):
        rows = self.amounts()
        rows[0]["evidence_id"] = "E-NOT-DECLARED"
        with self.assertRaises(ValueError):
            scenario_review(scenario_id="S-BAD-M", account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments(), evidence_rows=self.evidence(), constraint_rows=self.constraints(), amount_rows=rows, route_rows=self.routes(), workforce_review_state="APPROVED", rep_pseudonymization_receipt=self.pseudonymization(), solver_receipt=self.solver())

    def test_scenario_rejects_undeclared_route_evidence(self):
        rows = self.routes()
        rows[0]["evidence_id"] = "E-NOT-DECLARED"
        with self.assertRaises(ValueError):
            scenario_review(scenario_id="S-BAD-R", account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments(), evidence_rows=self.evidence(), constraint_rows=self.constraints(), amount_rows=self.amounts(), route_rows=rows, workforce_review_state="APPROVED", rep_pseudonymization_receipt=self.pseudonymization(), solver_receipt=self.solver())

    def test_amounts_exact(self):
        result = summarize_amounts(reconciliation=self.reconciliation(), amount_rows=self.amounts())
        self.assertEqual((result["state"], result["per_rep_totals"]), ("VALID", [{"rep_id": self.REP_ONE, "amount": Decimal("100.25")}, {"rep_id": self.REP_TWO, "amount": Decimal("99.75")}]))

    def test_amount_provenance_fields_are_required(self):
        for field in ("source_version", "cutoff_at", "metric_owner_role_id"):
            rows = self.amounts()
            del rows[0][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                summarize_amounts(reconciliation=self.reconciliation(), amount_rows=rows)

    def test_amount_rejects_unpreserved_extra_fields(self):
        rows = self.amounts()
        rows[0]["notes"] = "contact alice@example.test"
        with self.assertRaises(ValueError):
            summarize_amounts(reconciliation=self.reconciliation(), amount_rows=rows)

    def test_amount_source_version_must_match_referenced_evidence(self):
        rows = self.amounts()
        rows[0]["source_version"] = "v999"
        with self.assertRaises(ValueError):
            scenario_review(scenario_id="S-BAD-AMOUNT-SOURCE", account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments(), evidence_rows=self.evidence(), constraint_rows=self.constraints(), amount_rows=rows, route_rows=self.routes(), workforce_review_state="APPROVED", rep_pseudonymization_receipt=self.pseudonymization(), solver_receipt=self.solver())

    def test_amount_cutoff_must_match_referenced_evidence(self):
        rows = self.amounts()
        rows[0]["cutoff_at"] = "2026-07-09T00:00:00Z"
        with self.assertRaises(ValueError):
            scenario_review(scenario_id="S-BAD-AMOUNT-CUTOFF", account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments(), evidence_rows=self.evidence(), constraint_rows=self.constraints(), amount_rows=rows, route_rows=self.routes(), workforce_review_state="APPROVED", rep_pseudonymization_receipt=self.pseudonymization(), solver_receipt=self.solver())

    def test_missing_amount_is_source_required(self):
        result = summarize_amounts(reconciliation=self.reconciliation(), amount_rows=self.amounts()[:1])
        self.assertEqual((result["state"], result["missing_account_ids"]), ("SOURCE_REQUIRED", ["A-2"]))

    def test_unknown_amount_is_not_zero(self):
        rows = self.amounts(); rows[1]["amount"] = None
        result = summarize_amounts(reconciliation=self.reconciliation(), amount_rows=rows)
        self.assertEqual((result["state"], result["unknown_amount_account_ids"]), ("SOURCE_REQUIRED", ["A-2"]))

    def test_mixed_currency_is_incomparable(self):
        rows = self.amounts(); rows[1]["currency"] = "EUR"
        result = summarize_amounts(reconciliation=self.reconciliation(), amount_rows=rows)
        self.assertEqual(result["state"], "INCOMPARABLE")
        self.assertEqual(result["per_rep_totals"], [
            {"rep_id": self.REP_ONE, "amount": None},
            {"rep_id": self.REP_TWO, "amount": None},
        ])

    def test_float_amount_fails(self):
        rows = self.amounts(); rows[0]["amount"] = 1.2
        with self.assertRaises(ValueError): summarize_amounts(reconciliation=self.reconciliation(), amount_rows=rows)

    def test_amount_person_field_fails(self):
        rows = self.amounts(); rows[0]["rep_name"] = "person"
        with self.assertRaises(ValueError): summarize_amounts(reconciliation=self.reconciliation(), amount_rows=rows)

    def test_extra_amount_record_is_visible(self):
        rows = self.amounts() + [dict(self.amounts()[0], account_id="A-X", amount="1")]
        result = summarize_amounts(reconciliation=self.reconciliation(), amount_rows=rows)
        self.assertEqual((result["state"], result["extra_account_ids"]), ("SOURCE_REQUIRED", ["A-X"]))

    def test_route_totals_use_supplied_frequency(self):
        result = summarize_routes(reconciliation=self.reconciliation(), route_rows=self.routes())
        self.assertEqual(result["per_rep_totals"][0]["duration_minutes"], Decimal("60"))

    def test_route_rejects_unpreserved_extra_fields(self):
        rows = self.routes()
        rows[0]["notes"] = "contact alice@example.test"
        with self.assertRaises(ValueError):
            summarize_routes(reconciliation=self.reconciliation(), route_rows=rows)

    def test_route_source_version_must_match_referenced_evidence(self):
        rows = self.routes()
        rows[0]["source_version"] = "2099-01"
        with self.assertRaises(ValueError):
            scenario_review(scenario_id="S-BAD-ROUTE-SOURCE", account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments(), evidence_rows=self.evidence(), constraint_rows=self.constraints(), amount_rows=self.amounts(), route_rows=rows, workforce_review_state="APPROVED", rep_pseudonymization_receipt=self.pseudonymization(), solver_receipt=self.solver())

    def test_zero_assignment_rep_is_present_in_all_summaries(self):
        reconciliation = reconcile_assignments(
            account_ids=["A-1", "A-2"],
            rep_ids=[self.REP_ONE, self.REP_TWO, self.REP_THREE],
            assignment_rows=self.assignments(),
        )
        review = scenario_review(
            scenario_id="S-ZERO",
            account_ids=["A-1", "A-2"],
            rep_ids=[self.REP_ONE, self.REP_TWO, self.REP_THREE],
            assignment_rows=self.assignments(),
            evidence_rows=self.evidence(),
            constraint_rows=self.constraints(),
            amount_rows=self.amounts(),
            route_rows=self.routes(),
            workforce_review_state="APPROVED",
            rep_pseudonymization_receipt=self.pseudonymization([self.REP_ONE, self.REP_TWO, self.REP_THREE]),
            solver_receipt=self.solver(),
        )
        self.assertEqual(reconciliation["rep_ids"], [self.REP_ONE, self.REP_TWO, self.REP_THREE])
        self.assertEqual(review["counts"][-1], {"rep_id": self.REP_THREE, "assigned_account_count": 0})
        self.assertEqual(review["amounts"]["per_rep_totals"][-1], {"rep_id": self.REP_THREE, "amount": Decimal("0")})
        self.assertEqual(review["routes"]["per_rep_totals"][-1], {"rep_id": self.REP_THREE, "duration_minutes": Decimal("0"), "distance": Decimal("0"), "route_count": 0})

    def test_missing_route_is_source_required(self):
        result = summarize_routes(reconciliation=self.reconciliation(), route_rows=self.routes()[:1])
        self.assertEqual((result["state"], result["missing_pairs"]), ("SOURCE_REQUIRED", [{"account_id": "A-2", "rep_id": self.REP_TWO}]))

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
        result = summarize_routes(reconciliation=self.reconciliation(), route_rows=rows)
        self.assertEqual(result["state"], "INCOMPARABLE")
        self.assertEqual(result["per_rep_totals"], [
            {"rep_id": self.REP_ONE, "duration_minutes": None, "distance": None, "route_count": 1},
            {"rep_id": self.REP_TWO, "duration_minutes": None, "distance": None, "route_count": 1},
        ])

    def test_route_rep_identity_cannot_leak_through_extra_pair(self):
        rows = self.routes()
        rows[0]["rep_id"] = "Jordan Lee"
        with self.assertRaises(ValueError):
            summarize_routes(reconciliation=self.reconciliation(), route_rows=rows)

    def test_solver_free_text_cannot_enter_receipt(self):
        receipt = self.solver()
        receipt["solver"] = "contact alice@example.test"
        with self.assertRaises(ValueError):
            validate_solver_receipt(receipt)

    def test_solver_rejects_unpreserved_extra_fields(self):
        receipt = self.solver()
        receipt["notes"] = "contact alice@example.test"
        with self.assertRaises(ValueError):
            validate_solver_receipt(receipt)

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
        result = scenario_review(scenario_id="S-I", account_ids=["A-1", "A-2"], rep_ids=[self.REP_ONE, self.REP_TWO], assignment_rows=self.assignments(), evidence_rows=self.evidence(), constraint_rows=self.constraints(), amount_rows=self.amounts(), route_rows=self.routes(), workforce_review_state="APPROVED", rep_pseudonymization_receipt=self.pseudonymization(), solver_receipt=solver)
        self.assertEqual(result["state"], "INCOMPARABLE")

    def test_scenario_valid(self):
        result = self.review()
        self.assertEqual((result["state"], result["boundary"]), ("VALID", BOUNDARY))

    def test_workforce_review_blocks_valid_state(self):
        self.assertEqual(self.review(workforce="REVIEW_REQUIRED")["state"], "POLICY_REQUIRED")

    def test_scenario_order_is_deterministic_without_mutation(self):
        assignments = self.assignments(); original = deepcopy(assignments)
        result_a = scenario_review(scenario_id="S-1", account_ids=["A-2", "A-1"], rep_ids=[self.REP_TWO, self.REP_ONE], assignment_rows=assignments, evidence_rows=self.evidence(), constraint_rows=list(reversed(self.constraints())), amount_rows=list(reversed(self.amounts())), route_rows=list(reversed(self.routes())), workforce_review_state="APPROVED", rep_pseudonymization_receipt=self.pseudonymization(), solver_receipt=self.solver())
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
        result = build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "SCOPE-1", "decision": "DEC-1"}, scenario_reviews=reviews, comparison=comparison, reviewer="role-territory-reviewer", approver="role-territory-approver")
        self.assertEqual(result["boundary"], BOUNDARY)
        self.assertFalse({"recommendation", "best_scenario", "confidence", "quota", "fairness_score"}.intersection(result))

    def test_receipt_rejects_selected_comparison(self):
        comparison = self.comparison(); comparison["selected_scenario_id"] = "S-1"
        with self.assertRaises(ValueError): build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "SCOPE-1"}, scenario_reviews=[self.review("S-1"), self.review("S-2")], comparison=comparison, reviewer="role-reviewer", approver="role-approver")

    def test_decision_review_requires_rule(self):
        with self.assertRaises(ValueError): build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "SCOPE-1"}, scenario_reviews=[self.review("S-1"), self.review("S-2")], comparison=self.comparison(), reviewer="role-reviewer", approver="role-approver", approval_state="APPROVED_FOR_DECISION_REVIEW")

    def test_decision_review_rejects_incomparable_evidence(self):
        reviews = [self.review("S-1"), self.review("S-2", workforce="REVIEW_REQUIRED")]
        comparison = compare_scenarios(scenario_reviews=reviews, current_assignment_rows=self.assignments(), same_population=True, same_policies=True, same_constraints=True, same_amount_basis=True, same_route_policy=True)
        with self.assertRaises(ValueError): build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "SCOPE-1"}, scenario_reviews=reviews, comparison=comparison, reviewer="role-reviewer", approver="role-approver", decision_rule_id="DEC-1", approval_state="APPROVED_FOR_DECISION_REVIEW")

    def test_exact_json_renderer_preserves_nested_field_names(self):
        reviews = [self.review("S-1"), self.review("S-2", True)]
        receipt = build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "SCOPE-1"}, scenario_reviews=reviews, comparison=self.comparison(), reviewer="role-reviewer", approver="role-approver")
        rendered = json.loads(render_receipt_json(receipt))
        self.assertEqual(rendered["scenarios"][0]["counts"][0], {"rep_id": self.REP_ONE, "assigned_account_count": 1})
        self.assertEqual(rendered["scenarios"][0]["amount_totals"][0], {"rep_id": self.REP_ONE, "amount": "100.25"})
        self.assertEqual(rendered["scenarios"][0]["rep_pseudonymization_receipt"]["declared_rep_ids"], [self.REP_ONE, self.REP_TWO])
        self.assertEqual(rendered["scenarios"][0]["evidence_reference_receipt"]["declared_evidence_ids"], ["E-1", "E-ROUTE"])
        self.assertEqual(rendered["scenarios"][0]["amount_provenance"][0]["metric_owner_role_id"], "role-finance-metric-owner")
        self.assertEqual(rendered["scenarios"][0]["constraint_register"][0]["constraint_version"], "v1")
        self.assertIn("solver_receipt", rendered["scenarios"][1])

    def test_exact_json_renderer_rejects_non_object(self):
        with self.assertRaises(ValueError): render_receipt_json([])

    def test_exact_json_renderer_is_the_full_unfenced_response(self):
        reviews = [self.review("S-1"), self.review("S-2", True)]
        receipt = build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "SCOPE-1"}, scenario_reviews=reviews, comparison=self.comparison(), reviewer="role-reviewer", approver="role-approver")
        rendered = render_receipt_json(receipt)
        self.assertTrue(rendered.startswith("{"))
        self.assertTrue(rendered.endswith("}"))
        self.assertFalse(rendered.endswith("\n"))
        self.assertNotIn("```", rendered)
        self.assertNotIn("Satisfied", rendered)

    def test_receipt_rejects_email_bearing_reviewer_role(self):
        with self.assertRaises(ValueError):
            build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "SCOPE-1"}, scenario_reviews=[self.review("S-1"), self.review("S-2")], comparison=self.comparison(), reviewer="role-alice@example.test", approver="role-approver")

    def test_receipt_rejects_free_text_policy_id(self):
        with self.assertRaises(ValueError):
            build_downstream_receipt(receipt_id="REC-1", cutoff="2026-07-10T12:00:00Z", timezone="UTC", policy_ids={"scope": "contact alice@example.test"}, scenario_reviews=[self.review("S-1"), self.review("S-2")], comparison=self.comparison(), reviewer="role-reviewer", approver="role-approver")


if __name__ == "__main__":
    unittest.main()
