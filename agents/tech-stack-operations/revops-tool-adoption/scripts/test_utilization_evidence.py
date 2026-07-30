#!/usr/bin/env python3
import unittest
from decimal import Decimal

from utilization_evidence import build_tso03_handoff, compare_windows, cost_per, currency_total, population_receipt, rate, validate_evidence


class UtilizationEvidenceTests(unittest.TestCase):
    def test_rate(self): self.assertEqual(rate(60, 80), Decimal("0.75"))
    def test_zero_denominator(self): self.assertIsNone(rate(0, 0))
    def test_rate_over_denominator_fails(self):
        with self.assertRaises(ValueError): rate(2, 1)
    def test_bool_count_fails(self):
        with self.assertRaises(ValueError): rate(True, 1)
    def test_cost_per_exact(self): self.assertEqual(cost_per("24000", 60), Decimal("400"))
    def test_cost_per_zero_denominator(self): self.assertIsNone(cost_per("24000", 0))
    def test_cost_per_float_fails(self):
        with self.assertRaises(ValueError): cost_per(24000.0, 60)

    def receipt(self, **overrides):
        values = dict(paid_entitlements=120, assigned_entitlements=100, eligible_assigned=80, active_eligible=60, excluded=10, unmatched=5, unknown=3, withheld=0, conflicting=2, named_seat_model=True)
        values.update(overrides)
        return population_receipt(**values)

    def test_population_exact_rates(self):
        result = self.receipt()
        self.assertEqual((result["assignment_rate"], result["observed_active_assigned_rate"], result["observed_active_entitlement_rate"]), (Decimal("100") / Decimal("120"), Decimal("0.75"), Decimal("0.5")))
    def test_population_conflict_state(self): self.assertEqual(self.receipt()["state"], "CONFLICTING")
    def test_population_identity_review(self): self.assertEqual(self.receipt(conflicting=0)["state"], "IDENTITY_REVIEW")
    def test_population_calculated(self): self.assertEqual(self.receipt(conflicting=0, unmatched=0, unknown=0, excluded=20)["state"], "CALCULATED")
    def test_population_zero_denominator(self): self.assertEqual(self.receipt(eligible_assigned=0, active_eligible=0, excluded=100, unmatched=0, unknown=0, conflicting=0)["state"], "ZERO_DENOMINATOR")
    def test_unclassified_assigned_requires_identity_review(self):
        result = self.receipt(conflicting=0, unmatched=0, unknown=0)
        self.assertEqual((result["unclassified_assigned"], result["state"]), (10, "IDENTITY_REVIEW"))
    def test_assigned_over_paid_fails(self):
        with self.assertRaises(ValueError): self.receipt(assigned_entitlements=121)
    def test_active_over_eligible_fails(self):
        with self.assertRaises(ValueError): self.receipt(active_eligible=81)
    def test_partitions_over_assigned_fail(self):
        with self.assertRaises(ValueError): self.receipt(excluded=20)
    def test_non_named_model_suppresses_entitlement_rates(self):
        result = self.receipt(paid_entitlements=None, assigned_entitlements=None, named_seat_model=False)
        self.assertIsNone(result["assignment_rate"])
        self.assertIsNone(result["observed_active_entitlement_rate"])
        self.assertIsNone(result["unassigned_entitlements"])
    def test_named_model_requires_counts(self):
        with self.assertRaises(ValueError): self.receipt(paid_entitlements=None)

    def comparison(self, **overrides):
        values = dict(current_numerator=60, current_denominator=80, prior_numerator=54, prior_denominator=80, same_policy=True, equal_duration=True, non_overlapping=True, comparable_coverage=True, current_mature=True, prior_mature=True)
        values.update(overrides)
        return compare_windows(**values)

    def test_comparison_exact(self):
        result = self.comparison()
        self.assertEqual((result["current_rate"], result["prior_rate"], result["percentage_point_change"], result["relative_change"], result["denominator_change"]), (Decimal("0.75"), Decimal("0.675"), Decimal("7.500"), Decimal("1") / Decimal("9"), 0))
    def test_incomparable_policy(self): self.assertEqual(self.comparison(same_policy=False)["state"], "INCOMPARABLE")
    def test_incomparable_duration(self): self.assertEqual(self.comparison(equal_duration=False)["state"], "INCOMPARABLE")
    def test_incomparable_overlap(self): self.assertEqual(self.comparison(non_overlapping=False)["state"], "INCOMPARABLE")
    def test_incomparable_coverage(self): self.assertEqual(self.comparison(comparable_coverage=False)["state"], "INCOMPARABLE")
    def test_immature_window(self): self.assertEqual(self.comparison(current_mature=False)["state"], "IMMATURE_WINDOW")
    def test_zero_comparison_denominator(self): self.assertEqual(self.comparison(prior_numerator=0, prior_denominator=0)["state"], "ZERO_DENOMINATOR")
    def test_prior_zero_relative_unavailable(self):
        result = self.comparison(prior_numerator=0)
        self.assertEqual((result["state"], result["percentage_point_change"], result["relative_change"]), ("RELATIVE_CHANGE_UNAVAILABLE", Decimal("75.00"), None))
    def test_non_boolean_comparison_flag_fails(self):
        with self.assertRaises(ValueError): self.comparison(same_policy="yes")
    def test_incomparable_still_rejects_negative_count(self):
        with self.assertRaises(ValueError): self.comparison(same_policy=False, current_numerator=-1)
    def test_immature_still_rejects_boolean_count(self):
        with self.assertRaises(ValueError): self.comparison(current_mature=False, prior_denominator=True)

    def amount_rows(self):
        return [{"record_id": "I-1", "amount": "20000.25", "currency": "USD"}, {"record_id": "I-2", "amount": "3999.75", "currency": "usd"}]

    def test_currency_total(self): self.assertEqual(currency_total(self.amount_rows(), "USD")["total"], Decimal("24000.00"))
    def test_empty_currency_source(self): self.assertEqual(currency_total([], "USD")["state"], "SOURCE_REQUIRED")
    def test_mixed_currency_fails(self):
        rows = self.amount_rows(); rows[1]["currency"] = "EUR"
        with self.assertRaisesRegex(ValueError, "MIXED_CURRENCY"): currency_total(rows, "USD")
    def test_duplicate_amount_fails(self):
        rows = self.amount_rows()
        with self.assertRaises(ValueError): currency_total(rows + [dict(rows[0])], "USD")
    def test_float_amount_fails(self):
        rows = self.amount_rows(); rows[0]["amount"] = 1.2
        with self.assertRaises(ValueError): currency_total(rows, "USD")

    def evidence(self):
        return [{"evidence_id": "E-1", "source_id": "usage-report", "source_version": "s1", "extracted_at": "2026-07-10T00:00:00Z", "policy_id": "UP-2", "event_taxonomy_version": "EV-3", "aggregate_only": True}]

    def test_evidence_valid(self): self.assertEqual(validate_evidence(self.evidence())["evidence_count"], 1)
    def test_empty_evidence_fails(self):
        with self.assertRaises(ValueError): validate_evidence([])
    def test_duplicate_evidence_fails(self):
        rows = self.evidence()
        with self.assertRaises(ValueError): validate_evidence(rows + [dict(rows[0])])
    def test_missing_provenance_fails(self):
        rows = self.evidence(); rows[0]["source_version"] = ""
        with self.assertRaises(ValueError): validate_evidence(rows)
    def test_aggregate_flag_must_be_boolean(self):
        rows = self.evidence(); rows[0]["aggregate_only"] = "yes"
        with self.assertRaises(ValueError): validate_evidence(rows)

    def handoff(self, **overrides):
        policies = {"utilization": "UTL-8-v2", "population": "POP-4-v3", "identity": "ID-7-v5", "event": "EVT-9-v2", "privacy": "PRIV-3-v4", "comparison": "CMP-2-v1", "cost": "COST-2-v2", "downstream": "DOWN-6-v1"}
        comparison_inputs = dict(current_numerator=60, current_denominator=80, prior_numerator=54, prior_denominator=80, same_policy=True, equal_duration=True, non_overlapping=True, comparable_coverage=True, current_mature=True, prior_mature=True)
        values = dict(tool_id="tool-1", window_start="2026-06-01", window_end="2026-06-30", cutoff="2026-07-10T00:00:00Z", timezone="UTC", policy_ids=policies, evidence_rows=self.evidence(), population=self.receipt(), coverage={"state": "COMPLETE", "lag": "MATURE", "missingness": "NONE_REPORTED"}, comparison_inputs=comparison_inputs, cost_basis={"basis": "invoice", "currency": "USD", "period": "2026-06", "amount": "24000"})
        values.update(overrides)
        return build_tso03_handoff(**values)

    def test_handoff_bounded(self):
        result = self.handoff()
        self.assertEqual(result["observed_active_assigned_rate"], Decimal("0.75"))
        expected = {"lane", "tool_id", "window_start", "window_end", "cutoff", "timezone", "policy_ids", "evidence_ids", "evidence", "population_state", "paid_entitlements", "assigned_entitlements", "unassigned_entitlements", "eligible_assigned", "active_eligible", "unclassified_assigned", "excluded", "unmatched", "unknown", "withheld", "conflicting", "assignment_rate", "observed_active_assigned_rate", "observed_active_entitlement_rate", "coverage", "comparison", "cost_basis"}
        self.assertEqual(set(result), expected)
        self.assertEqual(result["evidence"][0]["extracted_at"], "2026-07-10T00:00:00Z")
        prohibited = {"adoption_score", "renewal_risk", "consolidation_flag", "savings", "recommendation", "confidence"}
        self.assertFalse(prohibited.intersection(result))
    def test_handoff_duplicate_evidence_fails(self):
        rows = self.evidence()
        with self.assertRaises(ValueError): self.handoff(evidence_rows=rows + [dict(rows[0])])
    def test_handoff_missing_population_fails(self):
        with self.assertRaises(ValueError): self.handoff(population={})
    def test_handoff_bad_cost_fields_fail(self):
        with self.assertRaises(ValueError): self.handoff(cost_basis={"amount": "1", "currency": "USD"})
    def test_handoff_bad_cost_amount_fails(self):
        with self.assertRaises(ValueError): self.handoff(cost_basis={"basis": "invoice", "currency": "USD", "period": "2026-06", "amount": "bad"})
    def test_handoff_empty_cost_basis_fails(self):
        with self.assertRaises(ValueError): self.handoff(cost_basis={"basis": "", "currency": "USD", "period": "2026-06", "amount": "1"})
    def test_handoff_normalizes_exact_cost(self):
        self.assertEqual(self.handoff()["cost_basis"]["amount"], Decimal("24000"))
    def test_handoff_rejects_inconsistent_population_state(self):
        population = self.receipt(); population["state"] = "CALCULATED"
        with self.assertRaises(ValueError): self.handoff(population=population)
    def test_handoff_rejects_minimal_forged_population(self):
        with self.assertRaises(ValueError): self.handoff(population={"state": "CALCULATED", "observed_active_assigned_rate": Decimal("1")})
    def test_handoff_missing_policy_fails(self):
        policies = self.handoff()["policy_ids"]; policies.pop("privacy")
        with self.assertRaises(ValueError): self.handoff(policy_ids=policies)
    def test_handoff_bad_coverage_fails(self):
        with self.assertRaises(ValueError): self.handoff(coverage={"state": "COMPLETE"})
    def test_handoff_preserves_required_lag_state(self):
        result = self.handoff(coverage={"state": "COMPLETE", "lag": "SOURCE_REQUIRED", "missingness": "NONE_REPORTED"})
        self.assertEqual(result["coverage"]["lag"], "SOURCE_REQUIRED")
    def test_handoff_recomputes_comparison(self):
        self.assertEqual(self.handoff()["comparison"]["percentage_point_change"], Decimal("7.500"))
    def test_handoff_rejects_bad_comparison_count(self):
        inputs = dict(self.handoff()["comparison"])
        with self.assertRaises(ValueError): self.handoff(comparison_inputs=inputs)
    def test_handoff_preserves_no_person_fields(self):
        result = self.handoff()
        self.assertFalse({"user_id", "name", "email", "department", "manager"}.intersection(result))
    def test_handoff_evidence_order_is_deterministic_without_mutation(self):
        rows = self.evidence()
        second = dict(rows[0], evidence_id="E-2", source_version="s2")
        original = [second, rows[0]]
        result = self.handoff(evidence_rows=original)
        reverse = self.handoff(evidence_rows=list(reversed(original)))
        self.assertEqual(result["evidence_ids"], ["E-1", "E-2"])
        self.assertEqual(result, reverse)
        self.assertEqual(original[0]["evidence_id"], "E-2")


if __name__ == "__main__":
    unittest.main()
