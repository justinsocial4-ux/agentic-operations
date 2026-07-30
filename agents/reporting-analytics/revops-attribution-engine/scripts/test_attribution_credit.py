#!/usr/bin/env python3

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from attribution_credit import PURPOSE, REQUIRED_PROHIBITIONS, review_attribution_credit, render_allocation_output


def valid_document():
    return {
        "policy": {
            "policy_id": "policy-attribution-credit",
            "policy_version": "version-one",
            "approved_purpose": PURPOSE,
            "effective_at": "2026-01-01T00:00:00+00:00",
            "expires_at": "2026-12-31T23:59:59+00:00",
            "cutoff_at": "2026-07-03T12:00:00+00:00",
            "reviewed_at": "2026-07-03T13:00:00+00:00",
            "reviewer_role_id": "role-human-reviewer",
            "privacy_receipt_id": "receipt-privacy-review",
            "lawful_basis_receipt_id": "receipt-lawful-basis",
            "recipient_policy_receipt_id": "receipt-recipient-policy",
            "retention_policy_receipt_id": "receipt-retention-policy",
            "retention_rule_id": "retention-attribution-credit",
            "allowed_recipient_role_ids": ["role-finance-reviewer", "role-marketing-reviewer"],
            "prohibited_uses": sorted(REQUIRED_PROHIBITIONS),
        },
        "allocation_contract": {
            "contract_id": "contract-credit-allocation",
            "model_id": "model-customer-approved",
            "model_version": "version-one",
            "model_definition_receipt_id": "receipt-model-definition",
            "model_approval_receipt_id": "receipt-model-approval",
            "remainder_rule": "lexicographic-first-touchpoint",
            "remainder_rule_receipt_id": "receipt-remainder-rule",
            "source_id": "source-approved-export",
            "source_version": "version-one",
            "schema_id": "schema-attribution-evidence",
            "schema_version": "version-one",
            "authorization_receipt_id": "receipt-source-authorization",
            "authorization_effective_at": "2025-12-01T00:00:00+00:00",
            "authorization_expires_at": "2026-12-31T23:59:59+00:00",
            "query_receipt_id": "receipt-query-approved",
            "page_receipt_id": "receipt-pages-complete",
            "opportunity_population_receipt_id": "receipt-opportunity-population",
            "expected_opportunity_ids": ["anonymous-opportunity-one", "anonymous-opportunity-two"],
            "freshness_observed_at": "2026-07-02T12:00:00+00:00",
            "reporting_timezone": "America/New_York",
            "reporting_period_start": "2026-04-01T00:00:00-04:00",
            "reporting_period_end": "2026-07-01T00:00:00-04:00",
            "touchpoint_window_start": "2026-01-01T00:00:00-05:00",
            "touchpoint_window_end": "2026-07-01T00:00:00-04:00",
            "currency": "USD",
            "amount_basis": "contracted-amount",
            "measure_definition_id": "definition-approved-amount",
            "finance_approval_receipt_id": "receipt-finance-approval",
            "pseudonymization_receipt_id": "receipt-pseudonymization",
            "identity_linkage_policy_receipt_id": "receipt-identity-linkage-policy",
            "event_definition_policy_receipt_id": "receipt-event-definition-policy",
            "eligibility_policy_receipt_id": "receipt-eligibility-policy",
            "deduplication_policy_receipt_id": "receipt-deduplication-policy",
            "ordering_policy_receipt_id": "receipt-ordering-policy",
            "exclusion_policy_receipt_id": "receipt-exclusion-policy",
            "bucket_policy_receipt_id": "receipt-bucket-policy",
            "allowed_bucket_ids": ["anonymous-bucket-email", "anonymous-bucket-webinar"],
        },
        "opportunities": [
            {
                "opportunity_id": "anonymous-opportunity-one", "state": "AVAILABLE", "approved_amount": "100.00",
                "amount_source_receipt_id": "receipt-amount-one", "touchpoint_population_receipt_id": "receipt-touchpoint-population-one",
                "expected_touchpoint_ids": ["anonymous-touchpoint-one-a", "anonymous-touchpoint-one-b"],
            },
            {
                "opportunity_id": "anonymous-opportunity-two", "state": "AVAILABLE", "approved_amount": "50.00",
                "amount_source_receipt_id": "receipt-amount-two", "touchpoint_population_receipt_id": "receipt-touchpoint-population-two",
                "expected_touchpoint_ids": ["anonymous-touchpoint-two-a"],
            },
        ],
        "touchpoints": [
            {
                "touchpoint_id": "anonymous-touchpoint-one-a", "opportunity_id": "anonymous-opportunity-one", "state": "AVAILABLE",
                "bucket_id": "anonymous-bucket-email", "event_type_id": "event-approved-click", "event_at": "2026-02-01T10:00:00-05:00",
                "sequence_index": 1, "source_receipt_id": "receipt-source-one-a", "linkage_receipt_id": "receipt-link-one-a",
                "eligibility_receipt_id": "receipt-eligible-one-a", "bucket_mapping_receipt_id": "receipt-bucket-one-a",
            },
            {
                "touchpoint_id": "anonymous-touchpoint-one-b", "opportunity_id": "anonymous-opportunity-one", "state": "AVAILABLE",
                "bucket_id": "anonymous-bucket-webinar", "event_type_id": "event-approved-attendance", "event_at": "2026-03-01T10:00:00-05:00",
                "sequence_index": 2, "source_receipt_id": "receipt-source-one-b", "linkage_receipt_id": "receipt-link-one-b",
                "eligibility_receipt_id": "receipt-eligible-one-b", "bucket_mapping_receipt_id": "receipt-bucket-one-b",
            },
            {
                "touchpoint_id": "anonymous-touchpoint-two-a", "opportunity_id": "anonymous-opportunity-two", "state": "AVAILABLE",
                "bucket_id": "anonymous-bucket-email", "event_type_id": "event-approved-click", "event_at": "2026-05-01T10:00:00-04:00",
                "sequence_index": 1, "source_receipt_id": "receipt-source-two-a", "linkage_receipt_id": "receipt-link-two-a",
                "eligibility_receipt_id": "receipt-eligible-two-a", "bucket_mapping_receipt_id": "receipt-bucket-two-a",
            },
        ],
        "weights": [
            {"touchpoint_id": "anonymous-touchpoint-one-a", "state": "AVAILABLE", "raw_weight": "0.30", "weight_receipt_id": "receipt-weight-one-a"},
            {"touchpoint_id": "anonymous-touchpoint-one-b", "state": "AVAILABLE", "raw_weight": "0.70", "weight_receipt_id": "receipt-weight-one-b"},
            {"touchpoint_id": "anonymous-touchpoint-two-a", "state": "AVAILABLE", "raw_weight": "1.00", "weight_receipt_id": "receipt-weight-two-a"},
        ],
    }


class AttributionCreditTests(unittest.TestCase):
    def assert_invalid(self, mutate):
        document = valid_document()
        mutate(document)
        with self.assertRaises(ValueError):
            review_attribution_credit(document)

    def test_valid_allocation(self):
        result = review_attribution_credit(valid_document())
        credits = {row["bucket_id"]: row["policy_allocated_credit"] for row in result["bucket_credit_receipts"]}
        self.assertEqual(credits, {"anonymous-bucket-email": "80.000000", "anonymous-bucket-webinar": "70.000000"})
        self.assertTrue(all(row["conservation_state"] == "CONSERVED" for row in result["opportunity_evidence_receipts"]))
        self.assertFalse(result["causal_attribution_authorized"])
        self.assertFalse(result["ranking_authorized"])
        self.assertFalse(result["downstream_decision_authorized"])
        self.assertFalse(result["action_authorized"])

    def test_unresolved_touchpoint_blocks_only_its_opportunity(self):
        document = valid_document()
        document["touchpoints"][0].update({"state": "EVIDENCE_MISSING", "bucket_id": None, "event_type_id": None, "event_at": None, "sequence_index": None})
        result = review_attribution_credit(document)
        credits = {row["bucket_id"]: row["policy_allocated_credit"] for row in result["bucket_credit_receipts"]}
        self.assertEqual(credits, {"anonymous-bucket-email": "50.000000", "anonymous-bucket-webinar": "0.000000"})
        receipt = next(row for row in result["opportunity_evidence_receipts"] if row["opportunity_id"] == "anonymous-opportunity-one")
        self.assertEqual(receipt["state"], "EVIDENCE_MISSING")

    def test_unresolved_weight_blocks_opportunity(self):
        document = valid_document()
        document["weights"][0].update({"state": "SUPPRESSED", "raw_weight": None})
        result = review_attribution_credit(document)
        receipt = next(row for row in result["opportunity_evidence_receipts"] if row["opportunity_id"] == "anonymous-opportunity-one")
        self.assertEqual(receipt["state"], "SUPPRESSED")

    def test_mixed_unresolved_states_become_conflict(self):
        document = valid_document()
        document["touchpoints"][0].update({"state": "UNAUTHORIZED", "bucket_id": None, "event_type_id": None, "event_at": None, "sequence_index": None})
        document["weights"][1].update({"state": "SUPPRESSED", "raw_weight": None})
        result = review_attribution_credit(document)
        receipt = next(row for row in result["opportunity_evidence_receipts"] if row["opportunity_id"] == "anonymous-opportunity-one")
        self.assertEqual(receipt["state"], "EVIDENCE_CONFLICT")

    def test_empty_touchpoint_population_is_missing(self):
        document = valid_document()
        document["opportunities"][1]["expected_touchpoint_ids"] = []
        document["touchpoints"] = document["touchpoints"][:2]
        document["weights"] = document["weights"][:2]
        result = review_attribution_credit(document)
        receipt = next(row for row in result["opportunity_evidence_receipts"] if row["opportunity_id"] == "anonymous-opportunity-two")
        self.assertEqual(receipt["state"], "EVIDENCE_MISSING")

    def test_no_allocations_makes_bucket_values_missing(self):
        document = valid_document()
        for opportunity in document["opportunities"]:
            opportunity.update({"state": "EVIDENCE_MISSING", "approved_amount": None, "expected_touchpoint_ids": []})
        document["touchpoints"] = []
        document["weights"] = []
        result = review_attribution_credit(document)
        self.assertTrue(all(row["state"] == "EVIDENCE_MISSING" and row["policy_allocated_credit"] is None for row in result["bucket_credit_receipts"]))

    def test_rounding_remainder_goes_to_first_touchpoint_bucket(self):
        document = valid_document()
        document["allocation_contract"]["allowed_bucket_ids"].append("anonymous-bucket-content")
        document["opportunities"] = [document["opportunities"][0]]
        document["allocation_contract"]["expected_opportunity_ids"] = ["anonymous-opportunity-one"]
        document["opportunities"][0]["expected_touchpoint_ids"].append("anonymous-touchpoint-one-c")
        document["touchpoints"] = document["touchpoints"][:2] + [{
            "touchpoint_id": "anonymous-touchpoint-one-c", "opportunity_id": "anonymous-opportunity-one", "state": "AVAILABLE",
            "bucket_id": "anonymous-bucket-content", "event_type_id": "event-approved-view", "event_at": "2026-03-15T10:00:00-04:00",
            "sequence_index": 3, "source_receipt_id": "receipt-source-one-c", "linkage_receipt_id": "receipt-link-one-c",
            "eligibility_receipt_id": "receipt-eligible-one-c", "bucket_mapping_receipt_id": "receipt-bucket-one-c",
        }]
        document["weights"] = [
            {"touchpoint_id": item, "state": "AVAILABLE", "raw_weight": "1", "weight_receipt_id": f"receipt-weight-{item.removeprefix('anonymous-touchpoint-')}"}
            for item in document["opportunities"][0]["expected_touchpoint_ids"]
        ]
        result = review_attribution_credit(document)
        credits = {row["bucket_id"]: row["policy_allocated_credit"] for row in result["bucket_credit_receipts"]}
        self.assertEqual(credits["anonymous-bucket-email"], "33.333334")
        self.assertEqual(credits["anonymous-bucket-webinar"], "33.333333")
        self.assertEqual(credits["anonymous-bucket-content"], "33.333333")

    def test_zero_amount_is_conserved(self):
        document = valid_document()
        document["opportunities"][0]["approved_amount"] = "0"
        result = review_attribution_credit(document)
        self.assertEqual(result["opportunity_evidence_receipts"][0]["conservation_state"], "CONSERVED")

    def test_negative_zero_is_normalized(self):
        document = valid_document()
        document["opportunities"][0]["approved_amount"] = "-0"
        result = review_attribution_credit(document)
        credits = {row["bucket_id"]: row["policy_allocated_credit"] for row in result["bucket_credit_receipts"]}
        self.assertNotIn("-0.000000", credits.values())

    def test_deterministic_render_boundary(self):
        first = render_allocation_output(review_attribution_credit(valid_document()))
        second = render_allocation_output(review_attribution_credit(valid_document()))
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("{"))
        self.assertTrue(first.endswith("}\n\n"))
        self.assertNotIn("```", first)

    def test_numeric_values_only_in_bucket_receipts(self):
        result = review_attribution_credit(valid_document())
        other = dict(result)
        other.pop("bucket_credit_receipts")
        text = json.dumps(other)
        self.assertNotIn("80.000000", text)
        self.assertNotIn("70.000000", text)

    def test_cli_matches_renderer(self):
        document = valid_document()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            completed = subprocess.run(["python3", str(Path(__file__).with_name("attribution_credit.py")), str(path)], check=True, capture_output=True, text=True)
        self.assertEqual(completed.stdout, render_allocation_output(review_attribution_credit(document)))

    def test_unknown_document_field(self): self.assert_invalid(lambda d: d.update({"extra": 1}))
    def test_missing_document_field(self): self.assert_invalid(lambda d: d.pop("weights"))
    def test_forbidden_key(self): self.assert_invalid(lambda d: d.update({"contact_id": "anonymous"}))
    def test_email_like_value(self): self.assert_invalid(lambda d: d["policy"].update({"reviewer_role_id": "person@example.com"}))
    def test_url_like_value(self): self.assert_invalid(lambda d: d["policy"].update({"reviewer_role_id": "https://example.com"}))
    def test_wrong_purpose(self): self.assert_invalid(lambda d: d["policy"].update({"approved_purpose": "causal_attribution"}))
    def test_missing_prohibition(self): self.assert_invalid(lambda d: d["policy"].update({"prohibited_uses": sorted(REQUIRED_PROHIBITIONS - {"budget-action"})}))
    def test_policy_time_order(self): self.assert_invalid(lambda d: d["policy"].update({"reviewed_at": "2027-01-01T00:00:00+00:00"}))
    def test_duplicate_recipient(self): self.assert_invalid(lambda d: d["policy"].update({"allowed_recipient_role_ids": ["role-finance-reviewer", "role-finance-reviewer"]}))
    def test_wrong_remainder_rule(self): self.assert_invalid(lambda d: d["allocation_contract"].update({"remainder_rule": "largest-remainder"}))
    def test_invalid_currency(self): self.assert_invalid(lambda d: d["allocation_contract"].update({"currency": "usd"}))
    def test_invalid_timezone(self): self.assert_invalid(lambda d: d["allocation_contract"].update({"reporting_timezone": "EST"}))
    def test_reporting_offset_mismatch(self): self.assert_invalid(lambda d: d["allocation_contract"].update({"reporting_period_start": "2026-04-01T00:00:00-05:00"}))
    def test_window_offset_mismatch(self): self.assert_invalid(lambda d: d["allocation_contract"].update({"touchpoint_window_end": "2026-07-01T00:00:00-05:00"}))
    def test_authorization_order(self): self.assert_invalid(lambda d: d["allocation_contract"].update({"authorization_expires_at": "2026-06-01T00:00:00+00:00"}))
    def test_window_reverse(self): self.assert_invalid(lambda d: d["allocation_contract"].update({"touchpoint_window_end": "2025-12-01T00:00:00-05:00"}))
    def test_reporting_period_reverse(self): self.assert_invalid(lambda d: d["allocation_contract"].update({"reporting_period_end": "2026-03-01T00:00:00-05:00"}))
    def test_duplicate_expected_opportunity(self): self.assert_invalid(lambda d: d["allocation_contract"]["expected_opportunity_ids"].append("anonymous-opportunity-one"))
    def test_duplicate_allowed_bucket(self): self.assert_invalid(lambda d: d["allocation_contract"]["allowed_bucket_ids"].append("anonymous-bucket-email"))
    def test_unknown_contract_field(self): self.assert_invalid(lambda d: d["allocation_contract"].update({"extra": "bad"}))
    def test_invalid_opportunity_id(self): self.assert_invalid(lambda d: d["opportunities"][0].update({"opportunity_id": "OPP-1"}))
    def test_invalid_opportunity_state(self): self.assert_invalid(lambda d: d["opportunities"][0].update({"state": "UNKNOWN"}))
    def test_available_opportunity_requires_amount(self): self.assert_invalid(lambda d: d["opportunities"][0].update({"approved_amount": None}))
    def test_unavailable_opportunity_rejects_amount(self): self.assert_invalid(lambda d: d["opportunities"][0].update({"state": "SUPPRESSED"}))
    def test_negative_amount(self): self.assert_invalid(lambda d: d["opportunities"][0].update({"approved_amount": "-1"}))
    def test_amount_precision_bound(self): self.assert_invalid(lambda d: d["opportunities"][0].update({"approved_amount": "1.0000001"}))
    def test_amount_magnitude_bound(self): self.assert_invalid(lambda d: d["opportunities"][0].update({"approved_amount": "10000000000000000000"}))
    def test_duplicate_opportunity(self): self.assert_invalid(lambda d: d["opportunities"].append(copy.deepcopy(d["opportunities"][0])))
    def test_duplicate_amount_source_receipt(self): self.assert_invalid(lambda d: d["opportunities"][1].update({"amount_source_receipt_id": "receipt-amount-one"}))
    def test_duplicate_touchpoint_population_receipt(self): self.assert_invalid(lambda d: d["opportunities"][1].update({"touchpoint_population_receipt_id": "receipt-touchpoint-population-one"}))
    def test_missing_opportunity_population(self): self.assert_invalid(lambda d: d["opportunities"].pop())
    def test_extra_opportunity_population(self):
        def mutate(d):
            row = copy.deepcopy(d["opportunities"][0]); row["opportunity_id"] = "anonymous-opportunity-extra"; row["expected_touchpoint_ids"] = []
            d["opportunities"].append(row)
        self.assert_invalid(mutate)
    def test_touchpoint_declared_twice(self): self.assert_invalid(lambda d: d["opportunities"][1]["expected_touchpoint_ids"].append("anonymous-touchpoint-one-a"))
    def test_missing_touchpoint(self): self.assert_invalid(lambda d: d["touchpoints"].pop())
    def test_missing_weight(self): self.assert_invalid(lambda d: d["weights"].pop())
    def test_duplicate_touchpoint(self): self.assert_invalid(lambda d: d["touchpoints"].append(copy.deepcopy(d["touchpoints"][0])))
    def test_duplicate_weight(self): self.assert_invalid(lambda d: d["weights"].append(copy.deepcopy(d["weights"][0])))
    def test_duplicate_weight_receipt(self): self.assert_invalid(lambda d: d["weights"][1].update({"weight_receipt_id": "receipt-weight-one-a"}))
    def test_duplicate_touchpoint_source_receipt(self): self.assert_invalid(lambda d: d["touchpoints"][1].update({"source_receipt_id": "receipt-source-one-a"}))
    def test_duplicate_linkage_receipt(self): self.assert_invalid(lambda d: d["touchpoints"][1].update({"linkage_receipt_id": "receipt-link-one-a"}))
    def test_duplicate_eligibility_receipt(self): self.assert_invalid(lambda d: d["touchpoints"][1].update({"eligibility_receipt_id": "receipt-eligible-one-a"}))
    def test_duplicate_bucket_mapping_receipt(self): self.assert_invalid(lambda d: d["touchpoints"][1].update({"bucket_mapping_receipt_id": "receipt-bucket-one-a"}))
    def test_touchpoint_unknown_opportunity(self): self.assert_invalid(lambda d: d["touchpoints"][0].update({"opportunity_id": "anonymous-opportunity-unknown"}))
    def test_touchpoint_binding_mismatch(self): self.assert_invalid(lambda d: d["touchpoints"][0].update({"opportunity_id": "anonymous-opportunity-two"}))
    def test_touchpoint_bucket_not_allowed(self): self.assert_invalid(lambda d: d["touchpoints"][0].update({"bucket_id": "anonymous-bucket-other"}))
    def test_touchpoint_invalid_state(self): self.assert_invalid(lambda d: d["touchpoints"][0].update({"state": "UNKNOWN"}))
    def test_available_touchpoint_requires_bucket(self): self.assert_invalid(lambda d: d["touchpoints"][0].update({"bucket_id": None}))
    def test_unavailable_touchpoint_rejects_evidence(self): self.assert_invalid(lambda d: d["touchpoints"][0].update({"state": "SUPPRESSED"}))
    def test_touchpoint_outside_window(self): self.assert_invalid(lambda d: d["touchpoints"][0].update({"event_at": "2025-12-01T10:00:00-05:00"}))
    def test_touchpoint_offset_mismatch(self): self.assert_invalid(lambda d: d["touchpoints"][2].update({"event_at": "2026-05-01T10:00:00-05:00"}))
    def test_sequence_bool_rejected(self): self.assert_invalid(lambda d: d["touchpoints"][0].update({"sequence_index": True}))
    def test_sequence_gap_rejected(self): self.assert_invalid(lambda d: d["touchpoints"][1].update({"sequence_index": 3}))
    def test_sequence_chronology_conflict(self): self.assert_invalid(lambda d: d["touchpoints"][0].update({"event_at": "2026-03-15T10:00:00-04:00"}))
    def test_weight_invalid_state(self): self.assert_invalid(lambda d: d["weights"][0].update({"state": "UNKNOWN"}))
    def test_available_weight_requires_value(self): self.assert_invalid(lambda d: d["weights"][0].update({"raw_weight": None}))
    def test_unavailable_weight_rejects_value(self): self.assert_invalid(lambda d: d["weights"][0].update({"state": "UNAUTHORIZED"}))
    def test_negative_weight(self): self.assert_invalid(lambda d: d["weights"][0].update({"raw_weight": "-1"}))
    def test_weight_precision_bound(self): self.assert_invalid(lambda d: d["weights"][0].update({"raw_weight": "0.0000001"}))
    def test_zero_weight_total(self):
        def mutate(d):
            d["weights"][0]["raw_weight"] = "0"; d["weights"][1]["raw_weight"] = "0"
        self.assert_invalid(mutate)


if __name__ == "__main__":
    unittest.main()
