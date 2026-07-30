#!/usr/bin/env python3

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention_evidence import BOUNDARY, render_review_output, review_retention_evidence


LANES = ("usage", "support", "survey", "engagement", "contract", "billing", "outcome")


def fixture():
    bindings = []
    links = []
    populations = []
    facts = []
    for lane in LANES:
        bindings.append({"lane": lane, "source_id": f"source-{lane}", "schema_version": f"schema-{lane}",
                         "metric_id": f"metric-{lane}", "metric_version": f"metric-version-{lane}",
                         "link_version": f"link-version-{lane}"})
        links.append({"link_id": f"link-{lane}", "account_id": "account-alpha",
                      "external_account_id": f"external-{lane}", "lane": lane,
                      "source_id": f"source-{lane}", "schema_version": f"schema-{lane}",
                      "link_version": f"link-version-{lane}", "observed_at": "2026-07-10T08:00:00Z"})
        populations.append({"population_receipt_id": f"population-{lane}", "lane": lane,
                            "source_id": f"source-{lane}", "schema_version": f"schema-{lane}",
                            "metric_id": f"metric-{lane}", "metric_version": f"metric-version-{lane}",
                            "complete": True, "account_ids": ["account-alpha"],
                            "observed_at": "2026-07-10T09:00:00Z"})
        fact = {"fact_id": f"fact-{lane}", "lane": lane, "account_id": "account-alpha",
                "kind": f"kind-{lane}", "value_type": "decimal", "current_value": "12.50",
                "prior_value": "10", "unit": "count", "basis": f"basis-{lane}", "currency": None,
                "window_begin": "2026-07-01T00:00:00Z", "window_end": "2026-07-08T00:00:00Z",
                "prior_window_begin": "2026-06-24T00:00:00Z", "prior_window_end": "2026-07-01T00:00:00Z",
                "timezone": "UTC", "population_receipt_id": f"population-{lane}",
                "identity_link_id": f"link-{lane}", "source_id": f"source-{lane}",
                "schema_version": f"schema-{lane}", "metric_id": f"metric-{lane}",
                "metric_version": f"metric-version-{lane}", "observed_at": "2026-07-08T01:00:00Z"}
        if lane == "contract":
            fact.update(value_type="timestamp", current_value="2026-07-09T00:00:00Z", prior_value=None,
                        unit="date", prior_window_begin=None, prior_window_end=None)
        elif lane == "outcome":
            fact.update(value_type="token", current_value="observed-renewal-event", prior_value=None,
                        unit="event", prior_window_begin=None, prior_window_end=None)
        facts.append(fact)
    return {
        "policy": {
            "policy_id": "policy-alpha", "policy_version": "version-alpha", "owner_id": "owner-alpha",
            "human_reviewer_role_id": "reviewer-alpha", "effective_at": "2026-07-01T00:00:00Z",
            "expires_at": None, "cutoff_at": "2026-07-11T00:00:00Z", "timezone": "America/Guayaquil",
            "approved_purpose": "customer_retention_evidence_review",
            "prohibited_uses": ["prediction", "ranking", "crm-write", "outreach", "playbook", "forecast", "workforce-action"],
            "correction_path": "submit-correction-receipt", "bindings": bindings,
            "rules": [
                {"rule_id": "rule-usage", "lane": "usage", "fact_kind": "kind-usage", "value_type": "decimal", "operator": "ge",
                 "threshold": "11", "unit": "count", "basis": "basis-usage", "currency": None,
                 "disposition_label": "review-observation-alpha", "human_review_role_id": "reviewer-alpha", "precedence": 10},
                {"rule_id": "rule-billing", "lane": "billing", "fact_kind": "kind-billing", "value_type": "decimal", "operator": "lt",
                 "threshold": "20", "unit": "count", "basis": "basis-billing", "currency": None,
                 "disposition_label": "review-observation-beta", "human_review_role_id": "reviewer-beta", "precedence": 10},
            ],
        },
        "declaration": {"declared_account_count": 1, "account_ids": ["account-alpha"]},
        "identity_links": links, "source_populations": populations, "facts": facts,
    }


def lane(result, name):
    return next(row for row in result["account_reviews"][0]["lane_reviews"] if row["lane"] == name)


class RetentionEvidenceTests(unittest.TestCase):
    def test_valid_all_lanes(self):
        result = review_retention_evidence(fixture())
        self.assertEqual(result["review_type"], "CUSTOMER_RETENTION_EVIDENCE_REVIEW")
        self.assertEqual(lane(result, "usage")["state"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(lane(result, "contract")["state"], "OBSERVED")

    def test_fixed_boundary(self):
        self.assertEqual(review_retention_evidence(fixture())["boundary"], BOUNDARY)

    def test_exact_renderer(self):
        result = review_retention_evidence(fixture())
        self.assertEqual(render_review_output(result), json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    def test_numeric_values_live_only_in_fact_and_rule_receipts(self):
        output = render_review_output(review_retention_evidence(fixture()))
        self.assertEqual(output.count('"current_value": "12.5"'), 5)
        self.assertEqual(output.count('"threshold": "11"'), 1)
        self.assertNotIn("current_value", lane(review_retention_evidence(fixture()), "usage")["rule_results"][0])

    def test_rule_matches_reference_receipts(self):
        row = lane(review_retention_evidence(fixture()), "usage")["rule_results"][0]
        self.assertEqual(row["state"], "RULE_MATCHED")
        self.assertEqual(row["fact_id"], "fact-usage")

    def test_no_prediction_or_action_fields(self):
        output = render_review_output(review_retention_evidence(fixture())).lower()
        for key in ('"score":', '"probability":', '"rank":', '"forecast":', '"recommended_action":', '"crm_write":'):
            self.assertNotIn(key, output)

    def test_r1_labels_absent(self):
        output = render_review_output(review_retention_evidence(fixture())).lower()
        for word in ("small", "large", "enough", "limited", "insufficient", "good", "poor", "high", "low"):
            self.assertNotIn(word, output)

    def test_unknown_root_field_rejected(self):
        data = fixture(); data["extra"] = True
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_unknown_fact_field_rejected(self):
        data = fixture(); data["facts"][0]["extra"] = "x"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_direct_email_rejected(self):
        data = fixture(); data["facts"][0]["current_value"] = "person@example.com"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_direct_identity_key_rejected(self):
        data = fixture(); data["facts"][0]["name"] = "person"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_fuzzy_domain_rejected(self):
        data = fixture(); data["identity_links"][0]["domain"] = "example"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_free_text_rejected(self):
        data = fixture(); data["facts"][1]["ticket_text"] = "content"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_r1_identifier_rejected(self):
        data = fixture(); data["declaration"]["account_ids"] = ["account-high"]
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_wrong_purpose_rejected(self):
        data = fixture(); data["policy"]["approved_purpose"] = "churn-prediction"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_empty_prohibited_uses_rejected(self):
        data = fixture(); data["policy"]["prohibited_uses"] = []
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_missing_fixed_prohibited_use_rejected(self):
        data = fixture(); data["policy"]["prohibited_uses"].remove("outreach")
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_policy_not_effective_rejected(self):
        data = fixture(); data["policy"]["effective_at"] = "2026-07-12T00:00:00Z"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_expired_policy_rejected(self):
        data = fixture(); data["policy"]["expires_at"] = "2026-07-10T00:00:00Z"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_naive_timestamp_rejected(self):
        data = fixture(); data["facts"][0]["observed_at"] = "2026-07-08T00:00:00"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_offset_timestamp_normalized(self):
        data = fixture(); data["facts"][0]["observed_at"] = "2026-07-07T20:00:00-04:00"
        result = review_retention_evidence(data)
        fact = next(row for row in result["fact_receipts"] if row["fact_id"] == "fact-usage")
        self.assertEqual(fact["observed_at"], "2026-07-08T00:00:00Z")

    def test_future_fact_rejected(self):
        data = fixture(); data["facts"][0]["observed_at"] = "2026-07-12T00:00:00Z"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_fact_observed_before_window_end_rejected(self):
        data = fixture(); data["facts"][0]["observed_at"] = "2026-07-07T00:00:00Z"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_bad_declared_count_rejected(self):
        data = fixture(); data["declaration"]["declared_account_count"] = 2
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_duplicate_declared_account_rejected(self):
        data = fixture(); data["declaration"] = {"declared_account_count": 2, "account_ids": ["account-alpha", "account-alpha"]}
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_undeclared_population_account_rejected(self):
        data = fixture(); data["source_populations"][0]["account_ids"].append("account-beta")
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_complete_population_missing_declared_account_rejected(self):
        data = fixture(); data["declaration"] = {"declared_account_count": 2, "account_ids": ["account-alpha", "account-beta"]}
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_duplicate_population_account_rejected(self):
        data = fixture(); data["source_populations"][0]["account_ids"].append("account-alpha")
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_schema_mismatch_rejected(self):
        data = fixture(); data["facts"][0]["schema_version"] = "schema-other"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_metric_version_mismatch_rejected(self):
        data = fixture(); data["facts"][0]["metric_version"] = "metric-version-other"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_missing_binding_rejected(self):
        data = fixture(); data["policy"]["bindings"] = data["policy"]["bindings"][1:]
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_duplicate_binding_rejected(self):
        data = fixture(); data["policy"]["bindings"].append(copy.deepcopy(data["policy"]["bindings"][0]))
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_wrong_link_version_rejected(self):
        data = fixture(); data["identity_links"][0]["link_version"] = "link-other"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_one_to_many_link_rejected(self):
        data = fixture(); duplicate = copy.deepcopy(data["identity_links"][0]); duplicate["link_id"] = "link-usage-beta"; duplicate["external_account_id"] = "external-usage-beta"; data["identity_links"].append(duplicate)
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_many_to_one_link_rejected(self):
        data = fixture(); data["declaration"] = {"declared_account_count": 2, "account_ids": ["account-alpha", "account-beta"]}; duplicate = copy.deepcopy(data["identity_links"][0]); duplicate["link_id"] = "link-usage-beta"; duplicate["account_id"] = "account-beta"; data["identity_links"].append(duplicate)
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_missing_identity_link_rejected(self):
        data = fixture(); data["facts"][0]["identity_link_id"] = "link-missing"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_fact_absent_from_population_rejected(self):
        data = fixture(); data["source_populations"][0]["account_ids"] = []
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_decimal_exponent_rejected(self):
        data = fixture(); data["facts"][0]["current_value"] = "1e2"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_currency_rule_conflict(self):
        data = fixture(); data["policy"]["rules"][0]["currency"] = "USD"
        self.assertEqual(lane(review_retention_evidence(data), "usage")["rule_results"][0]["state"], "METRIC_CONFLICT")

    def test_basis_rule_conflict(self):
        data = fixture(); data["policy"]["rules"][0]["basis"] = "basis-other"
        self.assertEqual(lane(review_retention_evidence(data), "usage")["rule_results"][0]["state"], "METRIC_CONFLICT")

    def test_overlapping_windows_not_comparable(self):
        data = fixture(); data["facts"][0]["prior_window_end"] = "2026-07-02T00:00:00Z"
        self.assertEqual(lane(review_retention_evidence(data), "usage")["state"], "NOT_COMPARABLE")

    def test_prior_value_without_window_rejected(self):
        data = fixture(); data["facts"][0]["prior_window_begin"] = None
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_prior_window_without_value_rejected(self):
        data = fixture(); data["facts"][0]["prior_value"] = None
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_token_fact_prior_value_rejected(self):
        data = fixture(); fact = next(row for row in data["facts"] if row["lane"] == "outcome"); fact["prior_value"] = "another-event"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_numeric_lane_token_rejected(self):
        data = fixture(); data["facts"][0]["value_type"] = "token"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_outcome_decimal_rejected(self):
        data = fixture(); fact = next(row for row in data["facts"] if row["lane"] == "outcome"); fact.update(value_type="decimal", current_value="1")
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_complete_population_without_fact_is_no_event(self):
        data = fixture(); data["facts"] = [row for row in data["facts"] if row["lane"] != "support"]
        self.assertEqual(lane(review_retention_evidence(data), "support")["state"], "NO_EVENT_RECORDED")

    def test_incomplete_population_without_fact_requires_source(self):
        data = fixture(); data["facts"] = [row for row in data["facts"] if row["lane"] != "support"]; next(row for row in data["source_populations"] if row["lane"] == "support")["complete"] = False
        self.assertEqual(lane(review_retention_evidence(data), "support")["state"], "SOURCE_REQUIRED")

    def test_incomplete_population_with_fact_requires_source(self):
        data = fixture(); next(row for row in data["source_populations"] if row["lane"] == "usage")["complete"] = False
        result = review_retention_evidence(data)
        self.assertEqual(lane(result, "usage")["state"], "SOURCE_REQUIRED")
        self.assertEqual(lane(result, "usage")["rule_results"][0]["state"], "SOURCE_REQUIRED")

    def test_population_account_requires_identity_link(self):
        data = fixture(); data["facts"] = [row for row in data["facts"] if row["lane"] != "support"]; data["identity_links"] = [row for row in data["identity_links"] if row["lane"] != "support"]
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_every_binding_requires_population(self):
        data = fixture(); data["source_populations"] = data["source_populations"][1:]
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_empty_rules_rejected(self):
        data = fixture(); data["policy"]["rules"] = []
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_action_disposition_rejected(self):
        data = fixture(); data["policy"]["rules"][0]["disposition_label"] = "auto-contact"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_action_hidden_after_review_prefix_rejected(self):
        data = fixture(); data["policy"]["rules"][0]["disposition_label"] = "review-send-message"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_contract_timestamp_rule(self):
        data = fixture(); data["policy"]["rules"].append({"rule_id": "rule-contract", "lane": "contract", "fact_kind": "kind-contract", "value_type": "timestamp", "operator": "ge", "threshold": "2026-07-08T00:00:00Z", "unit": "date", "basis": "basis-contract", "currency": None, "disposition_label": "review-observation-contract", "human_review_role_id": "reviewer-alpha", "precedence": 10})
        result = review_retention_evidence(data)
        self.assertEqual(lane(result, "contract")["rule_results"][0]["state"], "RULE_MATCHED")

    def test_outcome_token_rule(self):
        data = fixture(); data["policy"]["rules"].append({"rule_id": "rule-outcome", "lane": "outcome", "fact_kind": "kind-outcome", "value_type": "token", "operator": "eq", "threshold": "observed-renewal-event", "unit": "event", "basis": "basis-outcome", "currency": None, "disposition_label": "record-observation-outcome", "human_review_role_id": "reviewer-alpha", "precedence": 10})
        result = review_retention_evidence(data)
        self.assertEqual(lane(result, "outcome")["rule_results"][0]["state"], "RULE_MATCHED")

    def test_token_rule_non_eq_rejected(self):
        data = fixture(); data["policy"]["rules"][0]["value_type"] = "token"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_future_contract_date_allowed_as_recorded_value(self):
        data = fixture(); fact = next(row for row in data["facts"] if row["lane"] == "contract"); fact["current_value"] = "2026-12-01T00:00:00Z"
        result = review_retention_evidence(data)
        receipt = next(row for row in result["fact_receipts"] if row["lane"] == "contract")
        self.assertEqual(receipt["current_value"], "2026-12-01T00:00:00Z")

    def test_future_outcome_timestamp_rejected(self):
        data = fixture(); fact = next(row for row in data["facts"] if row["lane"] == "outcome"); fact.update(value_type="timestamp", current_value="2026-12-01T00:00:00Z")
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_composite_email_key_rejected(self):
        data = fixture(); data["facts"][0]["customer_email"] = "masked"
        with self.assertRaises(ValueError): review_retention_evidence(data)

    def test_survey_nonresponse_not_negative(self):
        data = fixture(); data["facts"] = [row for row in data["facts"] if row["lane"] != "survey"]
        self.assertEqual(lane(review_retention_evidence(data), "survey")["state"], "NO_EVENT_RECORDED")

    def test_duplicate_fact_kind_is_metric_conflict(self):
        data = fixture(); duplicate = copy.deepcopy(data["facts"][0]); duplicate["fact_id"] = "fact-usage-beta"; data["facts"].append(duplicate)
        self.assertEqual(lane(review_retention_evidence(data), "usage")["rule_results"][0]["state"], "METRIC_CONFLICT")

    def test_conflicting_top_precedence_dispositions_require_review(self):
        data = fixture(); duplicate = copy.deepcopy(data["policy"]["rules"][0]); duplicate["rule_id"] = "rule-usage-beta"; duplicate["disposition_label"] = "review-observation-gamma"; data["policy"]["rules"].append(duplicate)
        self.assertEqual(lane(review_retention_evidence(data), "usage")["state"], "HUMAN_REVIEW_REQUIRED")

    def test_nonmatching_rule_is_not_prediction(self):
        data = fixture(); data["policy"]["rules"][0]["threshold"] = "99"
        row = lane(review_retention_evidence(data), "usage")["rule_results"][0]
        self.assertEqual(row["state"], "RULE_NOT_MATCHED")

    def test_missing_rule_fact_requires_source(self):
        data = fixture(); data["policy"]["rules"][0]["fact_kind"] = "kind-missing"
        self.assertEqual(lane(review_retention_evidence(data), "usage")["rule_results"][0]["state"], "SOURCE_REQUIRED")

    def test_empty_declared_population(self):
        data = fixture(); data["declaration"] = {"declared_account_count": 0, "account_ids": []}; data["identity_links"] = []; data["facts"] = []
        for row in data["source_populations"]: row["account_ids"] = []
        result = review_retention_evidence(data)
        self.assertEqual(result["account_reviews"], [])

    def test_order_independence(self):
        first = render_review_output(review_retention_evidence(fixture()))
        data = fixture(); data["policy"]["bindings"].reverse(); data["policy"]["rules"].reverse(); data["identity_links"].reverse(); data["source_populations"].reverse(); data["facts"].reverse()
        self.assertEqual(first, render_review_output(review_retention_evidence(data)))


if __name__ == "__main__":
    unittest.main()
