#!/usr/bin/env python3
"""Adversarial tests for campaign_measurement.py."""

from __future__ import annotations

import copy
import json
import unittest

from campaign_measurement import PURPOSE, REQUIRED_PROHIBITIONS, render_review_output, review_campaign_measurements


def fixture():
    contract_base = {
        "source_version": "version-one",
        "schema_id": "schema-campaign-measurement",
        "schema_version": "version-one",
        "authorization_receipt_id": "authorization-google",
        "authorization_effective_at": "2026-07-01T00:00:00Z",
        "authorization_expires_at": "2026-12-31T23:59:59Z",
        "query_receipt_id": "receipt-query-google",
        "complete_page_receipt_id": "receipt-page-google",
        "reporting_level": "campaign-daily",
        "reporting_timezone": "America/Guayaquil",
        "period_start_local": "2026-07-01T00:00:00-05:00",
        "period_end_local": "2026-07-08T00:00:00-05:00",
        "freshness_observed_at": "2026-07-10T12:00:00Z",
        "currency": "USD",
        "amount_basis": "source-recorded-media-spend",
        "spend_definition_id": "definition-spend-one",
        "impression_definition_id": "definition-impression-one",
        "click_definition_id": "definition-click-one",
        "conversion_definition_id": "definition-conversion-one",
        "conversion_action_id": "action-qualified-form",
        "conversion_action_category": "submitted-form",
        "counting_mode": "one-per-action",
        "attribution_model": "last-touch-customer-approved",
        "attribution_window": "window-thirty-days",
        "date_basis": "interaction-date",
    }
    google = dict(contract_base, contract_id="contract-google", source_id="source-google")
    linkedin = dict(
        contract_base,
        contract_id="contract-linkedin",
        source_id="source-linkedin",
        authorization_receipt_id="authorization-linkedin",
        query_receipt_id="receipt-query-linkedin",
        complete_page_receipt_id="receipt-page-linkedin",
        conversion_action_id="action-qualified-form-linkedin",
    )
    return {
        "review_id": "review-campaign-one",
        "policy": {
            "policy_id": "policy-campaign-measurement",
            "policy_version": "version-one",
            "approved_purpose": PURPOSE,
            "effective_at": "2026-07-01T00:00:00Z",
            "expires_at": "2026-12-31T23:59:59Z",
            "cutoff_at": "2026-07-11T12:00:00Z",
            "reviewed_at": "2026-07-11T14:00:00Z",
            "owner_role_id": "role-policy-owner",
            "human_reviewer_role_id": "role-human-reviewer",
            "source_policy_receipt_id": "receipt-source-policy",
            "measurement_policy_receipt_id": "receipt-measurement-policy",
            "equivalence_policy_receipt_id": "receipt-equivalence-policy",
            "recipient_policy_receipt_id": "receipt-recipient-policy",
            "retention_policy_receipt_id": "receipt-retention-policy",
            "retention_rule_id": "retention-rule-one",
            "allowed_recipient_role_ids": ["role-authorized-reviewer"],
            "approved_comparison_groups": [
                {
                    "group_id": "group-all-sources",
                    "contract_ids": ["contract-google", "contract-linkedin"],
                    "equivalence_receipt_id": "receipt-equivalence-all",
                }
            ],
            "prohibited_uses": sorted(REQUIRED_PROHIBITIONS),
        },
        "contracts": [google, linkedin],
        "population_receipts": [
            {
                "population_receipt_id": "population-google",
                "contract_id": "contract-google",
                "complete": True,
                "row_ids": ["row-google-one"],
                "observed_at": "2026-07-11T12:00:00Z",
            },
            {
                "population_receipt_id": "population-linkedin",
                "contract_id": "contract-linkedin",
                "complete": True,
                "row_ids": ["row-linkedin-one"],
                "observed_at": "2026-07-11T12:00:00Z",
            },
        ],
        "measurement_rows": [
            {
                "row_id": "row-google-one",
                "anonymous_campaign_id": "anonymous-campaign-google-one",
                "contract_id": "contract-google",
                "population_receipt_id": "population-google",
                "evidence_state": "AVAILABLE",
                "spend": "100",
                "impressions": "1000",
                "clicks": "50",
                "conversions": "5",
            },
            {
                "row_id": "row-linkedin-one",
                "anonymous_campaign_id": "anonymous-campaign-linkedin-one",
                "contract_id": "contract-linkedin",
                "population_receipt_id": "population-linkedin",
                "evidence_state": "AVAILABLE",
                "spend": "200",
                "impressions": "2000",
                "clicks": "100",
                "conversions": "10",
            },
        ],
        "comparison_groups": [
            {
                "group_id": "group-all-sources",
                "contract_ids": ["contract-google", "contract-linkedin"],
                "row_ids": ["row-google-one", "row-linkedin-one"],
                "equivalence_receipt_id": "receipt-equivalence-all",
            }
        ],
    }


class ValidReviewTests(unittest.TestCase):
    def test_valid_review(self):
        result = review_campaign_measurements(fixture())
        self.assertEqual(result["purpose"], PURPOSE)
        self.assertEqual(result["review_status"], "HUMAN_REVIEW_REQUIRED")

    def test_exact_group_metrics(self):
        receipt = review_campaign_measurements(fixture())["measurement_groups"][0]
        self.assertEqual(receipt["total_spend"], "300.000000")
        self.assertEqual(receipt["total_impressions"], "3000.000000")
        self.assertEqual(receipt["total_clicks"], "150.000000")
        self.assertEqual(receipt["total_conversions"], "15.000000")
        self.assertEqual(receipt["ctr"], "0.050000")
        self.assertEqual(receipt["cpc"], "2.000000")
        self.assertEqual(receipt["cost_per_conversion"], "20.000000")

    def test_false_authorizations(self):
        result = review_campaign_measurements(fixture())
        self.assertFalse(result["ranking_authorized"])
        self.assertFalse(result["attribution_authorized"])
        self.assertFalse(result["action_authorized"])

    def test_zero_denominators_are_null(self):
        doc = fixture()
        for row in doc["measurement_rows"]:
            row["impressions"] = row["clicks"] = row["conversions"] = "0"
        receipt = review_campaign_measurements(doc)["measurement_groups"][0]
        self.assertIsNone(receipt["ctr"])
        self.assertIsNone(receipt["cpc"])
        self.assertIsNone(receipt["cost_per_conversion"])

    def test_unresolved_row_has_no_metrics(self):
        doc = fixture()
        row = doc["measurement_rows"][1]
        row["evidence_state"] = "EVIDENCE_MISSING"
        row["spend"] = row["impressions"] = row["clicks"] = row["conversions"] = None
        result = review_campaign_measurements(doc)
        self.assertEqual(result["row_evidence"][1]["evidence_state"], "EVIDENCE_MISSING")
        self.assertEqual(result["measurement_groups"][0]["included_row_count"], 1)
        self.assertEqual(result["measurement_groups"][0]["total_spend"], "100.000000")

    def test_all_unresolved_yields_zero_totals(self):
        doc = fixture()
        for row in doc["measurement_rows"]:
            row["evidence_state"] = "SUPPRESSED"
            row["spend"] = row["impressions"] = row["clicks"] = row["conversions"] = None
        receipt = review_campaign_measurements(doc)["measurement_groups"][0]
        self.assertEqual(receipt["included_row_count"], 0)
        self.assertEqual(receipt["total_spend"], "0.000000")

    def test_fractional_conversion_decimal(self):
        doc = fixture()
        doc["measurement_rows"][0]["conversions"] = "2.5"
        receipt = review_campaign_measurements(doc)["measurement_groups"][0]
        self.assertEqual(receipt["total_conversions"], "12.500000")

    def test_deterministic_sorting(self):
        doc = fixture()
        doc["contracts"].reverse()
        doc["population_receipts"].reverse()
        doc["measurement_rows"].reverse()
        result = review_campaign_measurements(doc)
        self.assertEqual(result["contracts"][0]["contract_id"], "contract-google")
        self.assertEqual(result["row_evidence"][0]["row_id"], "row-google-one")

    def test_renderer_boundary(self):
        rendered = render_review_output(review_campaign_measurements(fixture()))
        self.assertTrue(rendered.startswith("{"))
        self.assertTrue(rendered.endswith("}\n\n"))
        self.assertEqual(json.loads(rendered)["purpose"], PURPOSE)

    def test_input_not_mutated(self):
        doc = fixture()
        frozen = copy.deepcopy(doc)
        review_campaign_measurements(doc)
        self.assertEqual(doc, frozen)


def set_path(doc, path, value):
    target = doc
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value


def delete_path(doc, path):
    target = doc
    for part in path[:-1]:
        target = target[part]
    del target[path[-1]]


def mutate(path, value):
    def apply(doc):
        set_path(doc, path, value)
    return apply


def remove(path):
    def apply(doc):
        delete_path(doc, path)
    return apply


def append(path, value):
    def apply(doc):
        target = doc
        for part in path:
            target = target[part]
        target.append(value)
    return apply


INVALID_CASES = [
    ("unknown_document_field", lambda d: d.update({"extra": True})),
    ("missing_document_field", remove(("review_id",))),
    ("bad_review_id", mutate(("review_id",), "Review One")),
    ("email_like_value", mutate(("review_id",), "review-a@b")),
    ("wrong_purpose", mutate(("policy", "approved_purpose"), "campaign-optimization")),
    ("missing_prohibition", lambda d: d["policy"]["prohibited_uses"].remove("budget-change")),
    ("duplicate_recipient", append(("policy", "allowed_recipient_role_ids"), "role-authorized-reviewer")),
    ("empty_recipients", mutate(("policy", "allowed_recipient_role_ids"), [])),
    ("policy_before_effective", mutate(("policy", "cutoff_at"), "2026-06-01T00:00:00Z")),
    ("policy_after_expiry", mutate(("policy", "reviewed_at"), "2027-01-01T00:00:00Z")),
    ("naive_policy_time", mutate(("policy", "cutoff_at"), "2026-07-11T12:00:00")),
    ("unknown_policy_field", lambda d: d["policy"].update({"campaign_name": "forbidden"})),
    ("missing_approved_groups", mutate(("policy", "approved_comparison_groups"), [])),
    ("duplicate_approved_group", append(("policy", "approved_comparison_groups"), copy.deepcopy(fixture()["policy"]["approved_comparison_groups"][0]))),
    ("approved_group_contract_mismatch", mutate(("policy", "approved_comparison_groups", 0, "contract_ids"), ["contract-google"])),
    ("approved_group_receipt_mismatch", mutate(("policy", "approved_comparison_groups", 0, "equivalence_receipt_id"), "receipt-other")),
    ("no_contracts", mutate(("contracts",), [])),
    ("duplicate_contract_id", mutate(("contracts", 1, "contract_id"), "contract-google")),
    ("bad_timezone", mutate(("contracts", 0, "reporting_timezone"), "Mars/Olympus")),
    ("bad_currency", mutate(("contracts", 0, "currency"), "US")),
    ("authorization_starts_late", mutate(("contracts", 0, "authorization_effective_at"), "2026-08-01T00:00:00Z")),
    ("authorization_ends_early", mutate(("contracts", 0, "authorization_expires_at"), "2026-07-02T00:00:00Z")),
    ("period_reversed", mutate(("contracts", 0, "period_end_local"), "2026-06-01T00:00:00-05:00")),
    ("period_start_wrong_offset", mutate(("contracts", 0, "period_start_local"), "2026-07-01T00:00:00+00:00")),
    ("period_end_wrong_offset", mutate(("contracts", 0, "period_end_local"), "2026-07-08T00:00:00+00:00")),
    ("freshness_before_period", mutate(("contracts", 0, "freshness_observed_at"), "2026-07-01T00:00:00Z")),
    ("freshness_after_cutoff", mutate(("contracts", 0, "freshness_observed_at"), "2026-07-12T00:00:00Z")),
    ("duplicate_query_receipt", mutate(("contracts", 1, "query_receipt_id"), "receipt-query-google")),
    ("duplicate_page_receipt", mutate(("contracts", 1, "complete_page_receipt_id"), "receipt-page-google")),
    ("unknown_contract_field", lambda d: d["contracts"][0].update({"campaign_name": "forbidden"})),
    ("population_count_mismatch", lambda d: d["population_receipts"].pop()),
    ("population_not_complete", mutate(("population_receipts", 0, "complete"), False)),
    ("population_wrong_cutoff", mutate(("population_receipts", 0, "observed_at"), "2026-07-11T11:00:00Z")),
    ("duplicate_population_id", mutate(("population_receipts", 1, "population_receipt_id"), "population-google")),
    ("duplicate_population_contract", mutate(("population_receipts", 1, "contract_id"), "contract-google")),
    ("population_unknown_contract", mutate(("population_receipts", 0, "contract_id"), "contract-unknown")),
    ("row_in_two_populations", mutate(("population_receipts", 1, "row_ids"), ["row-google-one"])),
    ("duplicate_row_in_population", mutate(("population_receipts", 0, "row_ids"), ["row-google-one", "row-google-one"])),
    ("rows_not_list", mutate(("measurement_rows",), {})),
    ("bad_anonymous_campaign", mutate(("measurement_rows", 0, "anonymous_campaign_id"), "campaign-google")),
    ("invalid_evidence_state", mutate(("measurement_rows", 0, "evidence_state"), "UNDERPERFORMING")),
    ("unresolved_with_metric", mutate(("measurement_rows", 0, "evidence_state"), "EVIDENCE_MISSING")),
    ("available_null_metric", mutate(("measurement_rows", 0, "spend"), None)),
    ("numeric_not_string", mutate(("measurement_rows", 0, "spend"), 100)),
    ("negative_metric", mutate(("measurement_rows", 0, "spend"), "-1")),
    ("nan_metric", mutate(("measurement_rows", 0, "spend"), "NaN")),
    ("excess_metric_precision", mutate(("measurement_rows", 0, "spend"), "1.0000001")),
    ("excess_metric_size", mutate(("measurement_rows", 0, "spend"), "10000000000000000000")),
    ("fractional_impressions", mutate(("measurement_rows", 0, "impressions"), "1.5")),
    ("fractional_clicks", mutate(("measurement_rows", 0, "clicks"), "1.5")),
    ("duplicate_measurement_row", append(("measurement_rows",), copy.deepcopy(fixture()["measurement_rows"][0]))),
    ("row_unknown_contract", mutate(("measurement_rows", 0, "contract_id"), "contract-unknown")),
    ("row_unknown_population", mutate(("measurement_rows", 0, "population_receipt_id"), "population-unknown")),
    ("row_wrong_population", mutate(("measurement_rows", 0, "population_receipt_id"), "population-linkedin")),
    ("undeclared_row", mutate(("measurement_rows", 0, "row_id"), "row-other")),
    ("missing_group", mutate(("comparison_groups",), [])),
    ("group_unknown_contract", mutate(("comparison_groups", 0, "contract_ids"), ["contract-google", "contract-unknown"])),
    ("group_unknown_row", mutate(("comparison_groups", 0, "row_ids"), ["row-google-one", "row-unknown"])),
    ("group_missing_row", mutate(("comparison_groups", 0, "row_ids"), ["row-google-one"])),
    ("duplicate_group_contract", append(("comparison_groups",), {"group_id": "group-other", "contract_ids": ["contract-google"], "row_ids": ["row-google-one"], "equivalence_receipt_id": "receipt-equivalence-other"})),
    ("duplicate_group_id", append(("comparison_groups",), {"group_id": "group-all-sources", "contract_ids": ["contract-google"], "row_ids": ["row-google-one"], "equivalence_receipt_id": "receipt-equivalence-other"})),
    ("duplicate_equivalence_receipt", lambda d: d["comparison_groups"].append({"group_id": "group-other", "contract_ids": ["contract-google"], "row_ids": ["row-google-one"], "equivalence_receipt_id": "receipt-equivalence-all"})),
]


for field in (
    "reporting_level",
    "reporting_timezone",
    "period_start_local",
    "period_end_local",
    "currency",
    "amount_basis",
    "spend_definition_id",
    "impression_definition_id",
    "click_definition_id",
    "conversion_definition_id",
    "conversion_action_category",
    "counting_mode",
    "attribution_model",
    "attribution_window",
    "date_basis",
):
    value = "EUR" if field == "currency" else ("UTC" if field == "reporting_timezone" else "different-basis")
    INVALID_CASES.append((f"incomparable_{field}", mutate(("contracts", 1, field), value)))


class InvalidReviewTests(unittest.TestCase):
    pass


def _make_invalid_test(mutator):
    def test(self):
        doc = fixture()
        mutator(doc)
        with self.assertRaises(ValueError):
            review_campaign_measurements(doc)
    return test


for case_name, case_mutator in INVALID_CASES:
    setattr(InvalidReviewTests, f"test_{case_name}", _make_invalid_test(case_mutator))


if __name__ == "__main__":
    unittest.main()
