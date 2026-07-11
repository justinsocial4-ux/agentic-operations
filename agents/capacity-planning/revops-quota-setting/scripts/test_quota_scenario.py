#!/usr/bin/env python3

import copy
import json
import unittest

from quota_scenario import REQUIRED_PROHIBITIONS, render_review_output, review_quota_scenarios


def fixture():
    binding = {
        "source_id": "source-plan",
        "source_version": "snapshot-alpha",
        "source_kind": "customer-supplied-anonymous-quota-plan",
        "schema_id": "schema-quota",
        "schema_version": "schema-alpha",
        "authorization_id": "authorization-alpha",
        "authorization_effective_at": "2026-07-01T00:00:00Z",
        "authorization_expires_at": None,
        "approved_currency": "USD",
        "approved_amount_basis": "booked-recurring-revenue",
        "approved_period_id": "period-alpha",
        "approved_territory_basis": "anonymous-sales-territory",
        "approved_coverage_basis": "qualified-pipeline-same-period",
    }
    return {
        "review_id": "review-alpha",
        "policy": {
            "policy_id": "policy-alpha",
            "policy_version": "version-alpha",
            "owner_role_id": "policy-owner",
            "human_reviewer_role_id": "human-reviewer",
            "effective_at": "2026-07-01T00:00:00Z",
            "expires_at": None,
            "cutoff_at": "2026-07-11T00:00:00Z",
            "timezone": "America/Guayaquil",
            "approved_purpose": "quota_policy_scenario_review",
            "prohibited_uses": sorted(REQUIRED_PROHIBITIONS),
            "correction_path": "submit a new correction receipt",
            "appeal_path": "submit an appeal to the named human reviewer",
            "privacy_review_receipt_id": "privacy-review-alpha",
            "workforce_review_receipt_id": "workforce-review-alpha",
            "compensation_review_receipt_id": "compensation-review-alpha",
            "affected_worker_notice_receipt_id": "worker-notice-alpha",
            "calculation_policy": {
                "amount_scale": 2,
                "ratio_scale": 3,
                "rounding_mode": "half_even",
                "approved_rule_ids": ["candidate-plan-total", "coverage-ratio", "prior-quota-delta", "target-difference"],
            },
            "source_bindings": [binding],
        },
        "source_populations": [{
            "population_receipt_id": "population-alpha",
            "source_id": "source-plan",
            "source_version": "snapshot-alpha",
            "source_kind": "customer-supplied-anonymous-quota-plan",
            "schema_id": "schema-quota",
            "schema_version": "schema-alpha",
            "authorization_id": "authorization-alpha",
            "complete": True,
            "scenario_ids": ["scenario-alpha"],
            "observed_at": "2026-07-09T00:00:00Z",
            "captured_at": "2026-07-10T00:00:00Z",
        }],
        "scenarios": [{
            "scenario_id": "scenario-alpha",
            "population_receipt_id": "population-alpha",
            "source_id": "source-plan",
            "source_version": "snapshot-alpha",
            "source_kind": "customer-supplied-anonymous-quota-plan",
            "schema_id": "schema-quota",
            "schema_version": "schema-alpha",
            "authorization_id": "authorization-alpha",
            "observed_at": "2026-07-09T00:00:00Z",
            "captured_at": "2026-07-10T00:00:00Z",
            "currency": "USD",
            "amount_basis": "booked-recurring-revenue",
            "period_id": "period-alpha",
            "territory_basis": "anonymous-sales-territory",
            "coverage_basis": "qualified-pipeline-same-period",
            "territory_population_receipt_id": "territory-population-alpha",
            "territory_population_complete": True,
            "declared_territory_ids": ["anonymous-territory-a", "anonymous-territory-b"],
            "corporate_target_amount": "1000.00",
            "territory_rows": [
                {
                    "territory_id": "anonymous-territory-a",
                    "candidate_quota_amount": "600.00",
                    "prior_quota_amount": "500.00",
                    "coverage_state": "accepted",
                    "coverage_amount": "1800.00",
                },
                {
                    "territory_id": "anonymous-territory-b",
                    "candidate_quota_amount": "500.00",
                    "prior_quota_amount": "550.00",
                    "coverage_state": "missing",
                    "coverage_amount": None,
                },
            ],
        }],
    }


class QuotaScenarioTests(unittest.TestCase):
    def review(self, value=None):
        return review_quota_scenarios(fixture() if value is None else value)

    def test_happy_path_plan_math(self):
        receipt = self.review()["scenario_receipts"][0]
        self.assertEqual(receipt["calculation_receipt"], {
            "candidate_plan_total": "1100.00",
            "target_difference": "100.00",
        })

    def test_happy_path_territory_math(self):
        rows = self.review()["scenario_receipts"][0]["territory_receipts"]
        self.assertEqual(rows[0]["calculation_receipt"], {
            "prior_quota_delta": "100.00",
            "coverage_ratio": "3.000",
        })
        self.assertEqual(rows[1]["calculation_receipt"], {
            "prior_quota_delta": "-50.00",
            "coverage_ratio": None,
        })

    def test_action_never_authorized(self):
        result = self.review()
        self.assertFalse(result["action_authorized"])
        self.assertFalse(result["scenario_receipts"][0]["action_authorized"])

    def test_human_review_state(self):
        self.assertEqual(self.review()["review_state"], "HUMAN_REVIEW_REQUIRED")

    def test_exact_renderer(self):
        output = render_review_output(self.review())
        self.assertTrue(output.startswith("{"))
        self.assertTrue(output.endswith("}\n"))
        self.assertEqual(json.loads(output), self.review())

    def test_deterministic_renderer(self):
        self.assertEqual(render_review_output(self.review()), render_review_output(self.review()))

    def test_scenarios_sorted(self):
        data = fixture(); second = copy.deepcopy(data["scenarios"][0]); second["scenario_id"] = "scenario-beta"
        data["scenarios"] = [second, data["scenarios"][0]]
        data["source_populations"][0]["scenario_ids"] = ["scenario-beta", "scenario-alpha"]
        ids = [item["scenario_id"] for item in self.review(data)["scenario_receipts"]]
        self.assertEqual(ids, ["scenario-alpha", "scenario-beta"])

    def test_territories_sorted(self):
        data = fixture(); data["scenarios"][0]["territory_rows"].reverse()
        ids = [item["territory_id"] for item in self.review(data)["scenario_receipts"][0]["territory_receipts"]]
        self.assertEqual(ids, ["anonymous-territory-a", "anonymous-territory-b"])

    def test_down_rounding(self):
        data = fixture(); data["policy"]["calculation_policy"]["rounding_mode"] = "down"
        data["scenarios"][0]["territory_rows"][0]["coverage_amount"] = "1000.00"
        ratio = self.review(data)["scenario_receipts"][0]["territory_receipts"][0]["calculation_receipt"]["coverage_ratio"]
        self.assertEqual(ratio, "1.666")

    def test_zero_target_allowed(self):
        data = fixture(); data["scenarios"][0]["corporate_target_amount"] = "0.00"
        self.assertEqual(self.review(data)["scenario_receipts"][0]["calculation_receipt"]["target_difference"], "1100.00")

    def test_zero_prior_allowed(self):
        data = fixture(); data["scenarios"][0]["territory_rows"][0]["prior_quota_amount"] = "0.00"
        delta = self.review(data)["scenario_receipts"][0]["territory_receipts"][0]["calculation_receipt"]["prior_quota_delta"]
        self.assertEqual(delta, "600.00")

    def test_zero_coverage_allowed(self):
        data = fixture(); data["scenarios"][0]["territory_rows"][0]["coverage_amount"] = "0.00"
        ratio = self.review(data)["scenario_receipts"][0]["territory_receipts"][0]["calculation_receipt"]["coverage_ratio"]
        self.assertEqual(ratio, "0.000")

    def test_unresolved_coverage_states_preserved(self):
        for state in ("missing", "conflicting", "suppressed"):
            data = fixture(); row = data["scenarios"][0]["territory_rows"][0]
            row["coverage_state"] = state; row["coverage_amount"] = None
            receipt = self.review(data)["scenario_receipts"][0]["territory_receipts"][0]
            self.assertEqual(receipt["input_receipt"]["coverage_state"], state)
            self.assertIsNone(receipt["calculation_receipt"]["coverage_ratio"])

    def test_accepted_coverage_requires_amount(self):
        data = fixture(); data["scenarios"][0]["territory_rows"][0]["coverage_amount"] = None
        self.assertRaises(ValueError, self.review, data)

    def test_unresolved_coverage_rejects_amount(self):
        data = fixture(); row = data["scenarios"][0]["territory_rows"][0]
        row["coverage_state"] = "conflicting"
        self.assertRaises(ValueError, self.review, data)

    def test_unknown_coverage_state_rejected(self):
        data = fixture(); data["scenarios"][0]["territory_rows"][0]["coverage_state"] = "estimated"
        self.assertRaises(ValueError, self.review, data)

    def test_float_rejected(self):
        data = fixture(); data["scenarios"][0]["corporate_target_amount"] = 1000.0
        self.assertRaises(ValueError, self.review, data)

    def test_exponent_rejected(self):
        data = fixture(); data["scenarios"][0]["corporate_target_amount"] = "1E3"
        self.assertRaises(ValueError, self.review, data)

    def test_negative_amount_rejected(self):
        data = fixture(); data["scenarios"][0]["territory_rows"][0]["prior_quota_amount"] = "-1.00"
        self.assertRaises(ValueError, self.review, data)

    def test_zero_candidate_rejected(self):
        data = fixture(); data["scenarios"][0]["territory_rows"][0]["candidate_quota_amount"] = "0.00"
        self.assertRaises(ValueError, self.review, data)

    def test_excess_scale_rejected(self):
        data = fixture(); data["scenarios"][0]["corporate_target_amount"] = "1.001"
        self.assertRaises(ValueError, self.review, data)

    def test_unknown_root_key_rejected(self):
        data = fixture(); data["advice"] = "increase quota"
        self.assertRaises(ValueError, self.review, data)

    def test_unknown_scenario_key_rejected(self):
        data = fixture(); data["scenarios"][0]["worker_rank"] = "one"
        self.assertRaises(ValueError, self.review, data)

    def test_unknown_row_key_rejected(self):
        data = fixture(); data["scenarios"][0]["territory_rows"][0]["worker_name"] = "person"
        self.assertRaises(ValueError, self.review, data)

    def test_direct_territory_identifier_rejected(self):
        data = fixture(); row = data["scenarios"][0]["territory_rows"][0]
        row["territory_id"] = "west-alice"
        data["scenarios"][0]["declared_territory_ids"][0] = "west-alice"
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_territory_rejected(self):
        data = fixture(); data["scenarios"][0]["territory_rows"].append(copy.deepcopy(data["scenarios"][0]["territory_rows"][0]))
        self.assertRaises(ValueError, self.review, data)

    def test_missing_territory_rejected(self):
        data = fixture(); data["scenarios"][0]["territory_rows"].pop()
        self.assertRaises(ValueError, self.review, data)

    def test_extra_territory_rejected(self):
        data = fixture(); data["scenarios"][0]["declared_territory_ids"].pop()
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_declared_territory_rejected(self):
        data = fixture(); data["scenarios"][0]["declared_territory_ids"].append("anonymous-territory-a")
        self.assertRaises(ValueError, self.review, data)

    def test_empty_territory_population_rejected(self):
        data = fixture(); data["scenarios"][0]["declared_territory_ids"] = []; data["scenarios"][0]["territory_rows"] = []
        self.assertRaises(ValueError, self.review, data)

    def test_incomplete_territory_population_rejected(self):
        data = fixture(); data["scenarios"][0]["territory_population_complete"] = False
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_scenario_rejected(self):
        data = fixture(); data["scenarios"].append(copy.deepcopy(data["scenarios"][0]))
        self.assertRaises(ValueError, self.review, data)

    def test_missing_declared_scenario_rejected(self):
        data = fixture(); data["source_populations"][0]["scenario_ids"].append("scenario-beta")
        self.assertRaises(ValueError, self.review, data)

    def test_extra_scenario_rejected(self):
        data = fixture(); data["source_populations"][0]["scenario_ids"] = ["scenario-beta"]
        self.assertRaises(ValueError, self.review, data)

    def test_incomplete_source_population_rejected(self):
        data = fixture(); data["source_populations"][0]["complete"] = False
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_population_rejected(self):
        data = fixture(); data["source_populations"].append(copy.deepcopy(data["source_populations"][0]))
        self.assertRaises(ValueError, self.review, data)

    def test_schema_mismatch_rejected(self):
        data = fixture(); data["scenarios"][0]["schema_version"] = "schema-beta"
        self.assertRaises(ValueError, self.review, data)

    def test_authorization_mismatch_rejected(self):
        data = fixture(); data["scenarios"][0]["authorization_id"] = "authorization-beta"
        self.assertRaises(ValueError, self.review, data)

    def test_source_mismatch_rejected(self):
        data = fixture(); data["scenarios"][0]["source_id"] = "source-other"
        self.assertRaises(ValueError, self.review, data)

    def test_non_anonymous_source_kind_rejected(self):
        data = fixture(); data["policy"]["source_bindings"][0]["source_kind"] = "crm-worker-records"
        data["source_populations"][0]["source_kind"] = "crm-worker-records"
        data["scenarios"][0]["source_kind"] = "crm-worker-records"
        self.assertRaises(ValueError, self.review, data)

    def test_unused_source_binding_rejected(self):
        data = fixture(); second = copy.deepcopy(data["policy"]["source_bindings"][0]); second["source_id"] = "source-beta"
        data["policy"]["source_bindings"].append(second)
        self.assertRaises(ValueError, self.review, data)

    def test_currency_mismatch_rejected(self):
        data = fixture(); data["scenarios"][0]["currency"] = "EUR"
        self.assertRaises(ValueError, self.review, data)

    def test_lowercase_currency_rejected(self):
        data = fixture(); data["policy"]["source_bindings"][0]["approved_currency"] = "usd"
        self.assertRaises(ValueError, self.review, data)

    def test_amount_basis_mismatch_rejected(self):
        data = fixture(); data["scenarios"][0]["amount_basis"] = "total-contract-value"
        self.assertRaises(ValueError, self.review, data)

    def test_period_mismatch_rejected(self):
        data = fixture(); data["scenarios"][0]["period_id"] = "period-beta"
        self.assertRaises(ValueError, self.review, data)

    def test_territory_basis_mismatch_rejected(self):
        data = fixture(); data["scenarios"][0]["territory_basis"] = "anonymous-other-territory"
        self.assertRaises(ValueError, self.review, data)

    def test_non_anonymous_approved_territory_basis_rejected(self):
        data = fixture(); data["policy"]["source_bindings"][0]["approved_territory_basis"] = "sales-territory"
        self.assertRaises(ValueError, self.review, data)

    def test_coverage_basis_mismatch_rejected(self):
        data = fixture(); data["scenarios"][0]["coverage_basis"] = "unqualified-pipeline"
        self.assertRaises(ValueError, self.review, data)

    def test_future_capture_rejected(self):
        data = fixture(); data["source_populations"][0]["captured_at"] = "2026-07-12T00:00:00Z"
        data["scenarios"][0]["captured_at"] = "2026-07-12T00:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_observed_after_capture_rejected(self):
        data = fixture(); data["source_populations"][0]["observed_at"] = "2026-07-10T12:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_timestamp_mismatch_rejected(self):
        data = fixture(); data["scenarios"][0]["observed_at"] = "2026-07-08T00:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_non_utc_timestamp_rejected(self):
        data = fixture(); data["scenarios"][0]["captured_at"] = "2026-07-10T00:00:00+00:00"
        self.assertRaises(ValueError, self.review, data)

    def test_invalid_timezone_rejected(self):
        data = fixture(); data["policy"]["timezone"] = "Planet/Unknown"
        self.assertRaises(ValueError, self.review, data)

    def test_policy_not_effective_rejected(self):
        data = fixture(); data["policy"]["effective_at"] = "2026-07-12T00:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_policy_expired_rejected(self):
        data = fixture(); data["policy"]["expires_at"] = "2026-07-10T00:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_authorization_not_effective_rejected(self):
        data = fixture(); data["policy"]["source_bindings"][0]["authorization_effective_at"] = "2026-07-12T00:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_authorization_expired_rejected(self):
        data = fixture(); data["policy"]["source_bindings"][0]["authorization_expires_at"] = "2026-07-10T00:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_wrong_purpose_rejected(self):
        data = fixture(); data["policy"]["approved_purpose"] = "quota-recommendation"
        self.assertRaises(ValueError, self.review, data)

    def test_bad_rounding_rejected(self):
        data = fixture(); data["policy"]["calculation_policy"]["rounding_mode"] = "up"
        self.assertRaises(ValueError, self.review, data)

    def test_missing_calculation_rule_rejected(self):
        data = fixture(); data["policy"]["calculation_policy"]["approved_rule_ids"].pop()
        self.assertRaises(ValueError, self.review, data)

    def test_extra_calculation_rule_rejected(self):
        data = fixture(); data["policy"]["calculation_policy"]["approved_rule_ids"].append("quota-optimization")
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_calculation_rule_rejected(self):
        data = fixture(); data["policy"]["calculation_policy"]["approved_rule_ids"].append("target-difference")
        self.assertRaises(ValueError, self.review, data)

    def test_authorization_window_in_receipt(self):
        receipt = self.review()["scenario_receipts"][0]["input_receipt"]
        self.assertEqual(receipt["authorization_effective_at"], "2026-07-01T00:00:00Z")
        self.assertIsNone(receipt["authorization_expires_at"])

    def test_review_receipts_in_policy_output(self):
        receipt = self.review()["policy_receipt"]
        self.assertEqual(receipt["privacy_review_receipt_id"], "privacy-review-alpha")
        self.assertEqual(receipt["workforce_review_receipt_id"], "workforce-review-alpha")
        self.assertEqual(receipt["compensation_review_receipt_id"], "compensation-review-alpha")
        self.assertEqual(receipt["affected_worker_notice_receipt_id"], "worker-notice-alpha")

    def test_untrimmed_appeal_path_rejected(self):
        data = fixture(); data["policy"]["appeal_path"] = " appeal "
        self.assertRaises(ValueError, self.review, data)

    def test_boolean_integer_rejected(self):
        data = fixture(); data["policy"]["calculation_policy"]["amount_scale"] = True
        self.assertRaises(ValueError, self.review, data)

    def test_empty_sources_rejected(self):
        data = fixture(); data["policy"]["source_bindings"] = []
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_source_binding_rejected(self):
        data = fixture(); data["policy"]["source_bindings"].append(copy.deepcopy(data["policy"]["source_bindings"][0]))
        self.assertRaises(ValueError, self.review, data)

    def test_no_population_rejected(self):
        data = fixture(); data["source_populations"] = []
        self.assertRaises(ValueError, self.review, data)

    def test_empty_source_population_rejected(self):
        data = fixture(); data["source_populations"][0]["scenario_ids"] = []
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_declared_scenario_rejected(self):
        data = fixture(); data["source_populations"][0]["scenario_ids"].append("scenario-alpha")
        self.assertRaises(ValueError, self.review, data)

    def test_free_text_basis_rejected(self):
        data = fixture(); data["scenarios"][0]["amount_basis"] = "revenue with notes"
        self.assertRaises(ValueError, self.review, data)

    def test_untrimmed_correction_path_rejected(self):
        data = fixture(); data["policy"]["correction_path"] = " correction "
        self.assertRaises(ValueError, self.review, data)

    def test_output_has_no_decision_labels(self):
        output = render_review_output(self.review()).lower()
        for term in ('"fairness":', '"achievable":', '"confidence":', '"worker_name":', '"recommended_quota":'):
            self.assertNotIn(term, output)

    def test_input_number_appears_once(self):
        output = render_review_output(self.review())
        self.assertEqual(output.count('"corporate_target_amount":"1000.00"'), 1)

    def test_derived_number_appears_once(self):
        output = render_review_output(self.review())
        self.assertEqual(output.count('"candidate_plan_total":"1100.00"'), 1)


def _missing_prohibition_test(prohibition):
    def test(self):
        data = fixture(); data["policy"]["prohibited_uses"].remove(prohibition)
        self.assertRaises(ValueError, self.review, data)
    return test


for _index, _prohibition in enumerate(sorted(REQUIRED_PROHIBITIONS)):
    setattr(QuotaScenarioTests, f"test_required_prohibition_{_index}", _missing_prohibition_test(_prohibition))


def _missing_scenario_field_test(field):
    def test(self):
        data = fixture(); del data["scenarios"][0][field]
        self.assertRaises(ValueError, self.review, data)
    return test


for _index, _field in enumerate(sorted(fixture()["scenarios"][0])):
    setattr(QuotaScenarioTests, f"test_required_scenario_field_{_index}", _missing_scenario_field_test(_field))


def _missing_row_field_test(field):
    def test(self):
        data = fixture(); del data["scenarios"][0]["territory_rows"][0][field]
        self.assertRaises(ValueError, self.review, data)
    return test


for _index, _field in enumerate(sorted(fixture()["scenarios"][0]["territory_rows"][0])):
    setattr(QuotaScenarioTests, f"test_required_row_field_{_index}", _missing_row_field_test(_field))


if __name__ == "__main__":
    unittest.main()
