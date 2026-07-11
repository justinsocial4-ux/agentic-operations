#!/usr/bin/env python3

import copy
import json
import unittest

from capacity_scenario import REQUIRED_PROHIBITIONS, render_review_output, review_capacity_scenarios


def fixture():
    source_binding = {
        "source_id": "source-aggregate",
        "source_version": "snapshot-alpha",
        "source_kind": "customer-supplied-anonymous-aggregate",
        "schema_id": "schema-capacity",
        "schema_version": "schema-alpha",
        "authorization_id": "authorization-alpha",
        "authorization_effective_at": "2026-07-01T00:00:00Z",
        "authorization_expires_at": None,
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
            "approved_purpose": "revenue_capacity_scenario_review",
            "prohibited_uses": sorted(REQUIRED_PROHIBITIONS),
            "correction_path": "submit a new correction receipt",
            "calculation_policy": {
                "amount_scale": 2,
                "unit_scale": 3,
                "rounding_mode": "half_even",
                "allow_whole_unit_ceiling": True,
            },
            "source_bindings": [source_binding],
        },
        "source_populations": [{
            "population_receipt_id": "population-alpha",
            "source_id": "source-aggregate",
            "source_version": "snapshot-alpha",
            "source_kind": "customer-supplied-anonymous-aggregate",
            "schema_id": "schema-capacity",
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
            "source_id": "source-aggregate",
            "source_version": "snapshot-alpha",
            "source_kind": "customer-supplied-anonymous-aggregate",
            "schema_id": "schema-capacity",
            "schema_version": "schema-alpha",
            "authorization_id": "authorization-alpha",
            "observed_at": "2026-07-09T00:00:00Z",
            "captured_at": "2026-07-10T00:00:00Z",
            "currency": "USD",
            "amount_basis": "annual-recurring-revenue",
            "period_id": "period-alpha",
            "capacity_unit_basis": "anonymous-capacity-unit",
            "target_amount": "1000.00",
            "retained_contribution_amount": "400.00",
            "expansion_contribution_amount": "100.00",
            "current_capacity_units": "2.000",
            "observed_output_per_capacity_unit": "200.00",
            "request_whole_unit_ceiling": True,
        }],
    }


class CapacityScenarioTests(unittest.TestCase):
    def review(self, value=None):
        return review_capacity_scenarios(fixture() if value is None else value)

    def test_happy_path_math(self):
        receipt = self.review()["scenario_receipts"][0]
        self.assertEqual(receipt["calculation_receipt"], {
            "capacity_gap_amount": "500.00",
            "modeled_capacity_units": "2.500",
            "whole_unit_ceiling": "3",
            "capacity_unit_difference": "0.500",
        })

    def test_action_never_authorized(self):
        result = self.review()
        self.assertFalse(result["action_authorized"])
        self.assertFalse(result["scenario_receipts"][0]["action_authorized"])

    def test_human_review_state(self):
        result = self.review()
        self.assertEqual(result["review_state"], "HUMAN_REVIEW_REQUIRED")

    def test_exact_renderer(self):
        output = render_review_output(self.review())
        self.assertTrue(output.startswith("{"))
        self.assertTrue(output.endswith("}\n"))
        self.assertEqual(json.loads(output), self.review())

    def test_deterministic_renderer(self):
        self.assertEqual(render_review_output(self.review()), render_review_output(self.review()))

    def test_output_numbers_are_strings(self):
        receipt = self.review()["scenario_receipts"][0]
        for value in receipt["calculation_receipt"].values():
            self.assertTrue(value is None or isinstance(value, str))

    def test_zero_gap(self):
        data = fixture(); data["scenarios"][0]["retained_contribution_amount"] = "900.00"
        data["scenarios"][0]["expansion_contribution_amount"] = "100.00"
        calc = self.review(data)["scenario_receipts"][0]["calculation_receipt"]
        self.assertEqual(calc["modeled_capacity_units"], "0.000")
        self.assertEqual(calc["capacity_unit_difference"], "-2.000")

    def test_negative_gap_preserved(self):
        data = fixture(); data["scenarios"][0]["retained_contribution_amount"] = "1100.00"
        calc = self.review(data)["scenario_receipts"][0]["calculation_receipt"]
        self.assertEqual(calc["capacity_gap_amount"], "-200.00")

    def test_ceiling_can_be_omitted(self):
        data = fixture(); data["scenarios"][0]["request_whole_unit_ceiling"] = False
        self.assertIsNone(self.review(data)["scenario_receipts"][0]["calculation_receipt"]["whole_unit_ceiling"])

    def test_policy_can_disable_ceiling(self):
        data = fixture(); data["policy"]["calculation_policy"]["allow_whole_unit_ceiling"] = False
        data["scenarios"][0]["request_whole_unit_ceiling"] = False
        self.assertIsNone(self.review(data)["scenario_receipts"][0]["calculation_receipt"]["whole_unit_ceiling"])

    def test_unauthorized_ceiling_rejected(self):
        data = fixture(); data["policy"]["calculation_policy"]["allow_whole_unit_ceiling"] = False
        self.assertRaises(ValueError, self.review, data)

    def test_down_rounding(self):
        data = fixture(); data["policy"]["calculation_policy"]["rounding_mode"] = "down"
        data["scenarios"][0]["observed_output_per_capacity_unit"] = "300.00"
        calc = self.review(data)["scenario_receipts"][0]["calculation_receipt"]
        self.assertEqual(calc["modeled_capacity_units"], "1.666")

    def test_multiple_scenarios_sorted(self):
        data = fixture(); second = copy.deepcopy(data["scenarios"][0]); second["scenario_id"] = "scenario-beta"
        data["scenarios"] = [second, data["scenarios"][0]]
        data["source_populations"][0]["scenario_ids"] = ["scenario-beta", "scenario-alpha"]
        ids = [x["scenario_id"] for x in self.review(data)["scenario_receipts"]]
        self.assertEqual(ids, ["scenario-alpha", "scenario-beta"])

    def test_float_rejected(self):
        data = fixture(); data["scenarios"][0]["target_amount"] = 1000.0
        self.assertRaises(ValueError, self.review, data)

    def test_exponent_rejected(self):
        data = fixture(); data["scenarios"][0]["target_amount"] = "1E3"
        self.assertRaises(ValueError, self.review, data)

    def test_negative_input_rejected(self):
        data = fixture(); data["scenarios"][0]["target_amount"] = "-1.00"
        self.assertRaises(ValueError, self.review, data)

    def test_zero_output_per_unit_rejected(self):
        data = fixture(); data["scenarios"][0]["observed_output_per_capacity_unit"] = "0.00"
        self.assertRaises(ValueError, self.review, data)

    def test_excess_scale_rejected(self):
        data = fixture(); data["scenarios"][0]["target_amount"] = "1.001"
        self.assertRaises(ValueError, self.review, data)

    def test_lowercase_currency_rejected(self):
        data = fixture(); data["scenarios"][0]["currency"] = "usd"
        self.assertRaises(ValueError, self.review, data)

    def test_unknown_root_key_rejected(self):
        data = fixture(); data["advice"] = "hire"
        self.assertRaises(ValueError, self.review, data)

    def test_unknown_scenario_key_rejected(self):
        data = fixture(); data["scenarios"][0]["worker_name"] = "person"
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

    def test_incomplete_population_rejected(self):
        data = fixture(); data["source_populations"][0]["complete"] = False
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_population_id_rejected(self):
        data = fixture(); data["source_populations"].append(copy.deepcopy(data["source_populations"][0]))
        self.assertRaises(ValueError, self.review, data)

    def test_scenario_in_two_populations_rejected(self):
        data = fixture(); second = copy.deepcopy(data["source_populations"][0]); second["population_receipt_id"] = "population-beta"
        data["source_populations"].append(second)
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

    def test_source_kind_mismatch_rejected(self):
        data = fixture(); data["scenarios"][0]["source_kind"] = "other-source-kind"
        self.assertRaises(ValueError, self.review, data)

    def test_non_anonymous_unit_basis_rejected(self):
        data = fixture(); data["scenarios"][0]["capacity_unit_basis"] = "account-executive"
        self.assertRaises(ValueError, self.review, data)

    def test_invalid_timezone_rejected(self):
        data = fixture(); data["policy"]["timezone"] = "Planet/Unknown"
        self.assertRaises(ValueError, self.review, data)

    def test_unused_source_binding_rejected(self):
        data = fixture(); second = copy.deepcopy(data["policy"]["source_bindings"][0])
        second["source_id"] = "source-beta"; data["policy"]["source_bindings"].append(second)
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
        data = fixture(); data["policy"]["approved_purpose"] = "staffing-recommendation"
        self.assertRaises(ValueError, self.review, data)

    def test_bad_rounding_rejected(self):
        data = fixture(); data["policy"]["calculation_policy"]["rounding_mode"] = "up"
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

    def test_empty_population_rejected(self):
        data = fixture(); data["source_populations"][0]["scenario_ids"] = []
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_declared_id_rejected(self):
        data = fixture(); data["source_populations"][0]["scenario_ids"].append("scenario-alpha")
        self.assertRaises(ValueError, self.review, data)

    def test_free_text_basis_rejected(self):
        data = fixture(); data["scenarios"][0]["amount_basis"] = "annual revenue with notes"
        self.assertRaises(ValueError, self.review, data)

    def test_untrimmed_correction_path_rejected(self):
        data = fixture(); data["policy"]["correction_path"] = " correction "
        self.assertRaises(ValueError, self.review, data)

    def test_output_does_not_contain_advice_terms(self):
        output = render_review_output(self.review()).lower()
        for term in ("hire ", "fire ", "recommend", "sufficient", "insufficient", '"confidence":'):
            self.assertNotIn(term, output)

    def test_input_value_appears_once(self):
        output = render_review_output(self.review())
        self.assertEqual(output.count('"target_amount":"1000.00"'), 1)

    def test_derived_value_appears_once(self):
        output = render_review_output(self.review())
        self.assertEqual(output.count('"capacity_gap_amount":"500.00"'), 1)


def _missing_prohibition_test(prohibition):
    def test(self):
        data = fixture(); data["policy"]["prohibited_uses"].remove(prohibition)
        self.assertRaises(ValueError, self.review, data)
    return test


for _index, _prohibition in enumerate(sorted(REQUIRED_PROHIBITIONS)):
    setattr(CapacityScenarioTests, f"test_required_prohibition_{_index}", _missing_prohibition_test(_prohibition))


def _missing_scenario_field_test(field):
    def test(self):
        data = fixture(); del data["scenarios"][0][field]
        self.assertRaises(ValueError, self.review, data)
    return test


for _index, _field in enumerate(sorted(fixture()["scenarios"][0])):
    setattr(CapacityScenarioTests, f"test_required_scenario_field_{_index}", _missing_scenario_field_test(_field))


if __name__ == "__main__":
    unittest.main()
