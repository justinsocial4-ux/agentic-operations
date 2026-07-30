#!/usr/bin/env python3

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from competitive_evidence import BOUNDARY, render_review_output, review_competitive_evidence


LANES = (
    "crm_outcome", "crm_competitor", "crm_reason", "buyer_interview_code",
    "call_annotation_code", "public_observation",
)


def fixture():
    bindings = []
    code_maps = []
    populations = []
    observations = []
    for lane in LANES:
        subject_type = "competitor" if lane == "public_observation" else "opportunity"
        subject_ids = ["competitor-alpha", "competitor-beta"] if subject_type == "competitor" else ["opportunity-alpha", "opportunity-beta"]
        source_id = f"source-{lane}"
        map_id = f"map-{lane}"
        bindings.append({
            "lane": lane, "subject_type": subject_type, "source_id": source_id,
            "schema_version": f"schema-{lane}", "code_map_id": map_id,
            "code_map_version": f"map-version-{lane}", "occurrence_semantics": f"occurred-{lane}",
        })
        code_maps.append({
            "lane": lane, "code_map_id": map_id, "code_map_version": f"map-version-{lane}",
            "allowed_codes": ["recorded-alpha", "recorded-beta"],
        })
        populations.append({
            "population_receipt_id": f"population-{lane}", "lane": lane, "subject_type": subject_type,
            "source_id": source_id, "schema_version": f"schema-{lane}", "code_map_id": map_id,
            "code_map_version": f"map-version-{lane}", "complete": True, "subject_ids": subject_ids,
            "observed_at": "2026-07-10T13:00:00Z",
        })
        observations.append({
            "observation_id": f"observation-{lane}", "lane": lane, "subject_type": subject_type,
            "subject_id": subject_ids[0], "source_id": source_id, "schema_version": f"schema-{lane}",
            "code_map_id": map_id, "code_map_version": f"map-version-{lane}", "code": "recorded-alpha",
            "population_receipt_id": f"population-{lane}", "occurred_at": "2026-07-08T12:00:00Z",
            "observed_at": "2026-07-09T12:00:00Z",
        })
    return {
        "policy": {
            "policy_id": "policy-alpha", "policy_version": "version-alpha", "owner_id": "owner-alpha",
            "human_reviewer_role_id": "reviewer-alpha", "effective_at": "2026-07-01T00:00:00Z",
            "expires_at": None, "cutoff_at": "2026-07-11T00:00:00Z", "timezone": "America-Guayaquil",
            "approved_purpose": "competitive_win_loss_evidence_review",
            "prohibited_uses": ["causal-explanation", "prediction", "ranking", "strategy", "alert", "crm-write", "workforce-action"],
            "correction_path": "submit-correction-receipt",
            "calculation_policy": {"rate_scale": 2, "rounding_mode": "half_even"},
            "bindings": bindings, "code_maps": code_maps,
            "rules": [
                {"rule_id": "rule-count", "lane": "crm_outcome", "source_id": "source-crm_outcome",
                 "code": "recorded-alpha", "metric": "count", "operator": "ge", "threshold": "1",
                 "disposition_label": "review-observation-alpha", "human_review_role_id": "reviewer-alpha", "precedence": 10},
                {"rule_id": "rule-rate", "lane": "crm_outcome", "source_id": "source-crm_outcome",
                 "code": "recorded-alpha", "metric": "rate", "operator": "ge", "threshold": "50",
                 "disposition_label": "review-observation-beta", "human_review_role_id": "reviewer-alpha", "precedence": 10},
            ],
        },
        "declaration": {
            "review_id": "review-alpha", "window_begin": "2026-07-01T00:00:00Z",
            "window_end": "2026-07-10T12:00:00Z", "declared_opportunity_count": 2,
            "opportunity_ids": ["opportunity-alpha", "opportunity-beta"], "declared_competitor_count": 2,
            "competitor_ids": ["competitor-alpha", "competitor-beta"],
        },
        "source_populations": populations,
        "observations": observations,
    }


def receipt(result, collection, receipt_id, field):
    return next(row for row in result[collection] if row[field] == receipt_id)


class CompetitiveEvidenceTests(unittest.TestCase):
    def test_valid_review(self):
        result = review_competitive_evidence(fixture())
        self.assertEqual(result["review_type"], "COMPETITIVE_WIN_LOSS_EVIDENCE_REVIEW")
        self.assertEqual(result["review_state"], "HUMAN_REVIEW_REQUIRED")

    def test_fixed_boundary(self):
        self.assertEqual(review_competitive_evidence(fixture())["boundary"], BOUNDARY)

    def test_exact_renderer(self):
        result = review_competitive_evidence(fixture())
        self.assertEqual(render_review_output(result), json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    def test_input_order_independent(self):
        first = fixture(); second = fixture()
        second["source_populations"].reverse(); second["observations"].reverse()
        second["policy"]["bindings"].reverse(); second["policy"]["code_maps"].reverse()
        self.assertEqual(render_review_output(review_competitive_evidence(first)), render_review_output(review_competitive_evidence(second)))

    def test_observed_and_no_event_counts(self):
        result = review_competitive_evidence(fixture())
        observed = receipt(result, "count_receipts", "count-crm_outcome-source-crm_outcome-observed", "count_receipt_id")
        absent = receipt(result, "count_receipts", "count-crm_outcome-source-crm_outcome-no-event", "count_receipt_id")
        self.assertEqual((observed["value"], absent["value"]), ("1", "1"))

    def test_rate_references_count_and_population(self):
        result = review_competitive_evidence(fixture())
        row = receipt(result, "rate_receipts", "rate-crm_outcome-source-crm_outcome-recorded-alpha", "rate_receipt_id")
        self.assertEqual(row["value"], "50")
        self.assertEqual(row["numerator_count_receipt_id"], "count-crm_outcome-source-crm_outcome-recorded-alpha")
        self.assertEqual(row["denominator_population_receipt_id"], "population-crm_outcome")

    def test_numbers_not_repeated_in_subject_reviews(self):
        output = json.dumps(review_competitive_evidence(fixture())["subject_reviews"], sort_keys=True)
        for key in ("value", "member_count", "threshold", "rate_scale"):
            self.assertNotIn(f'"{key}"', output)

    def test_rule_results_reference_metric_receipts(self):
        result = review_competitive_evidence(fixture())
        row = next(item for item in result["rule_results"] if item["rule_id"] == "rule-count")
        self.assertEqual(row["state"], "RULE_MATCHED")
        self.assertEqual(row["metric_receipt_id"], "count-crm_outcome-source-crm_outcome-recorded-alpha")

    def test_equal_precedence_conflicting_labels_require_review(self):
        data = fixture()
        extra = copy.deepcopy(data["policy"]["rules"][0]); extra["rule_id"] = "rule-count-other"
        extra["disposition_label"] = "record-observation-other"
        data["policy"]["rules"].append(extra)
        states = {row["rule_id"]: row["state"] for row in review_competitive_evidence(data)["rule_results"]}
        self.assertEqual(states["rule-count"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(states["rule-count-other"], "HUMAN_REVIEW_REQUIRED")

    def test_r1_label_allowed_only_on_numeric_rule(self):
        data = fixture(); data["policy"]["rules"][0]["disposition_label"] = "review-observation-high"
        result = review_competitive_evidence(data)
        self.assertEqual(result["policy_receipt"]["rules"][0]["disposition_label"], "review-observation-high")

    def test_r1_identifier_rejected(self):
        data = fixture(); data["declaration"]["opportunity_ids"][0] = "opportunity-high"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_unknown_root_field_rejected(self):
        data = fixture(); data["extra"] = True
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_unknown_policy_field_rejected(self):
        data = fixture(); data["policy"]["extra"] = True
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_unknown_observation_field_rejected(self):
        data = fixture(); data["observations"][0]["extra"] = True
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_direct_identity_key_rejected(self):
        data = fixture(); data["observations"][0]["name"] = "person"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_direct_email_rejected(self):
        data = fixture(); data["policy"]["correction_path"] = "person@example.com"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_free_text_key_rejected(self):
        data = fixture(); data["observations"][0]["free_text"] = "content"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_worker_field_rejected(self):
        data = fixture(); data["observations"][0]["seller_id"] = "seller-alpha"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_wrong_purpose_rejected(self):
        data = fixture(); data["policy"]["approved_purpose"] = "competitor-strategy"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_missing_prohibited_use_rejected(self):
        data = fixture(); data["policy"]["prohibited_uses"].remove("alert")
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_future_effective_policy_rejected(self):
        data = fixture(); data["policy"]["effective_at"] = "2026-07-12T00:00:00Z"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_expired_policy_rejected(self):
        data = fixture(); data["policy"]["expires_at"] = "2026-07-10T00:00:00Z"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_naive_timestamp_rejected(self):
        data = fixture(); data["observations"][0]["observed_at"] = "2026-07-09T12:00:00"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_offset_timestamp_normalized(self):
        data = fixture(); data["observations"][0]["observed_at"] = "2026-07-09T08:00:00-04:00"
        result = review_competitive_evidence(data)
        self.assertEqual(result["observation_receipts"][0]["observed_at"], "2026-07-09T12:00:00Z")

    def test_bad_rounding_mode_rejected(self):
        data = fixture(); data["policy"]["calculation_policy"]["rounding_mode"] = "ambient"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_bad_rate_scale_rejected(self):
        data = fixture(); data["policy"]["calculation_policy"]["rate_scale"] = 9
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_repeating_rate_uses_approved_rounding(self):
        data = fixture()
        data["declaration"]["declared_opportunity_count"] = 3
        data["declaration"]["opportunity_ids"].append("opportunity-gamma")
        for population in data["source_populations"]:
            if population["subject_type"] == "opportunity":
                population["subject_ids"].append("opportunity-gamma")
        result = review_competitive_evidence(data)
        row = receipt(result, "rate_receipts", "rate-crm_outcome-source-crm_outcome-recorded-alpha", "rate_receipt_id")
        self.assertEqual(row["value"], "33.33")

    def test_float_rule_threshold_rejected(self):
        data = fixture(); data["policy"]["rules"][0]["threshold"] = 1.0
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_duplicate_binding_rejected(self):
        data = fixture(); data["policy"]["bindings"].append(copy.deepcopy(data["policy"]["bindings"][0]))
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_missing_code_map_rejected(self):
        data = fixture(); data["policy"]["code_maps"] = data["policy"]["code_maps"][1:]
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_duplicate_code_rejected(self):
        data = fixture(); data["policy"]["code_maps"][0]["allowed_codes"].append("recorded-alpha")
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_action_code_rejected(self):
        data = fixture(); data["policy"]["code_maps"][0]["allowed_codes"][0] = "send-message"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_action_disposition_rejected(self):
        data = fixture(); data["policy"]["rules"][0]["disposition_label"] = "review-observation-notify"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_prose_token_rejected(self):
        data = fixture(); data["policy"]["bindings"][0]["occurrence_semantics"] = "customer said this happened"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_binding_subject_type_rejected(self):
        data = fixture(); data["policy"]["bindings"][0]["subject_type"] = "competitor"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_bad_declared_opportunity_count_rejected(self):
        data = fixture(); data["declaration"]["declared_opportunity_count"] = 3
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_duplicate_declared_competitor_rejected(self):
        data = fixture(); data["declaration"]["competitor_ids"][1] = "competitor-alpha"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_empty_declared_population_rejected(self):
        data = fixture(); data["declaration"]["opportunity_ids"] = []; data["declaration"]["declared_opportunity_count"] = 0
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_invalid_window_rejected(self):
        data = fixture(); data["declaration"]["window_end"] = "2026-06-30T00:00:00Z"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_window_after_cutoff_rejected(self):
        data = fixture(); data["declaration"]["window_end"] = "2026-07-12T00:00:00Z"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_incomplete_source_population_rejected(self):
        data = fixture(); data["source_populations"][0]["complete"] = False
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_source_population_missing_subject_rejected(self):
        data = fixture(); data["source_populations"][0]["subject_ids"] = ["opportunity-alpha"]
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_source_population_extra_subject_rejected(self):
        data = fixture(); data["source_populations"][0]["subject_ids"].append("opportunity-gamma")
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_source_population_before_window_end_rejected(self):
        data = fixture(); data["source_populations"][0]["observed_at"] = "2026-07-10T11:00:00Z"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_missing_bound_population_rejected(self):
        data = fixture(); data["source_populations"] = data["source_populations"][1:]
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_duplicate_population_lane_source_rejected(self):
        data = fixture(); duplicate = copy.deepcopy(data["source_populations"][0]); duplicate["population_receipt_id"] = "population-other"; data["source_populations"].append(duplicate)
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_observation_schema_mismatch_rejected(self):
        data = fixture(); data["observations"][0]["schema_version"] = "schema-other"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_observation_code_map_version_mismatch_rejected(self):
        data = fixture(); data["observations"][0]["code_map_version"] = "map-version-other"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_unapproved_code_rejected(self):
        data = fixture(); data["observations"][0]["code"] = "inferred-cause"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_undeclared_subject_rejected(self):
        data = fixture(); data["observations"][0]["subject_id"] = "opportunity-gamma"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_wrong_population_receipt_rejected(self):
        data = fixture(); data["observations"][0]["population_receipt_id"] = "population-crm_reason"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_duplicate_observation_id_rejected(self):
        data = fixture(); duplicate = copy.deepcopy(data["observations"][0]); duplicate["lane"] = "crm_reason"; duplicate["source_id"] = "source-crm_reason"; duplicate["schema_version"] = "schema-crm_reason"; duplicate["code_map_id"] = "map-crm_reason"; duplicate["code_map_version"] = "map-version-crm_reason"; duplicate["population_receipt_id"] = "population-crm_reason"; data["observations"].append(duplicate)
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_multiple_observations_for_subject_lane_rejected(self):
        data = fixture(); duplicate = copy.deepcopy(data["observations"][0]); duplicate["observation_id"] = "observation-other"; duplicate["code"] = "recorded-beta"; data["observations"].append(duplicate)
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_occurrence_before_window_rejected(self):
        data = fixture(); data["observations"][0]["occurred_at"] = "2026-06-30T12:00:00Z"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_occurrence_at_window_end_rejected(self):
        data = fixture(); data["observations"][0]["occurred_at"] = "2026-07-10T12:00:00Z"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_observed_before_occurrence_rejected(self):
        data = fixture(); data["observations"][0]["observed_at"] = "2026-07-08T11:00:00Z"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_observed_after_cutoff_rejected(self):
        data = fixture(); data["observations"][0]["observed_at"] = "2026-07-12T00:00:00Z"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_public_lane_cannot_use_opportunity_subject(self):
        data = fixture(); row = data["observations"][-1]; row["subject_type"] = "opportunity"; row["subject_id"] = "opportunity-alpha"
        with self.assertRaises(ValueError): review_competitive_evidence(data)

    def test_missing_lane_observation_does_not_cross_fill(self):
        data = fixture(); data["observations"] = [row for row in data["observations"] if row["lane"] != "crm_reason"]
        result = review_competitive_evidence(data)
        review = next(row for row in result["subject_reviews"] if row["subject_id"] == "opportunity-alpha")
        reason = next(row for row in review["lane_reviews"] if row["lane"] == "crm_reason")
        self.assertEqual(reason["state"], "NO_EVENT_RECORDED")

    def test_no_causal_or_action_output_fields(self):
        output = render_review_output(review_competitive_evidence(fixture())).lower()
        for key in ('"confidence":', '"threat":', '"rank":', '"forecast":', '"recommendation":', '"crm_write":', '"coaching":'):
            self.assertNotIn(key, output)


if __name__ == "__main__":
    unittest.main()
