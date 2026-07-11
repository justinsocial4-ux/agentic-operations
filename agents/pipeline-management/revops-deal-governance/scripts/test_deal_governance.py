#!/usr/bin/env python3

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deal_governance import BOUNDARY, render_review_output, review_governance


def fixture():
    return {
        "policy": {
            "policy_id": "policy-alpha",
            "policy_version": "version-beta",
            "owner_id": "owner-alpha",
            "human_reviewer_role_id": "reviewer-alpha",
            "effective_at": "2026-07-01T00:00:00Z",
            "expires_at": None,
            "cutoff_at": "2026-07-10T12:00:00Z",
            "timezone": "America/Guayaquil",
            "approved_purpose": "deal_governance_evidence_review",
            "prohibited_uses": ["crm-write", "legal-determination", "workforce-decision"],
            "correction_path": "submit-correction-receipt",
            "source_bindings": [
                {"source_id": "crm-alpha", "schema_version": "schema-alpha"},
                {"source_id": "doc-alpha", "schema_version": "schema-doc"},
                {"source_id": "process-alpha", "schema_version": "schema-process"},
            ],
            "rules": [
                {
                    "rule_id": "rule-discount", "rule_type": "numeric",
                    "applies_to_tags": ["segment-alpha"], "disposition": "HUMAN_REVIEW",
                    "human_review_role_id": "finance-reviewer", "precedence": 20,
                    "fact_kind": "discount_pct", "operator": "le", "threshold": "25",
                    "unit": "percent", "basis": "annual-net", "currency": "USD",
                },
                {
                    "rule_id": "rule-document", "rule_type": "document",
                    "applies_to_tags": ["segment-alpha"], "disposition": "HUMAN_REVIEW",
                    "human_review_role_id": "legal-reviewer", "precedence": 20,
                    "observation_key": "data-processing-key", "expected_state": "OBSERVED",
                },
                {
                    "rule_id": "rule-process", "rule_type": "process",
                    "applies_to_tags": ["segment-alpha"], "disposition": "RECORD_ONLY",
                    "human_review_role_id": "operations-reviewer", "precedence": 20,
                    "observation_key": "manager-review-key", "expected_state": "OBSERVED",
                },
            ],
        },
        "declaration": {"declared_deal_count": 1, "deal_ids": ["deal-alpha"]},
        "deals": [
            {
                "deal_id": "deal-alpha", "account_id": "account-alpha", "owner_id": "owner-beta",
                "source_id": "crm-alpha", "schema_version": "schema-alpha",
                "observed_at": "2026-07-10T10:00:00-02:00", "scope_tags": ["segment-alpha"],
            }
        ],
        "numeric_facts": [
            {
                "fact_id": "fact-list", "deal_id": "deal-alpha", "kind": "list_amount",
                "value": "125", "unit": "money", "basis": "annual-net", "currency": "USD",
                "source_id": "crm-alpha", "schema_version": "schema-alpha",
                "observed_at": "2026-07-10T09:00:00Z",
            },
            {
                "fact_id": "fact-quote", "deal_id": "deal-alpha", "kind": "quoted_amount",
                "value": "100", "unit": "money", "basis": "annual-net", "currency": "USD",
                "source_id": "crm-alpha", "schema_version": "schema-alpha",
                "observed_at": "2026-07-10T09:00:00Z",
            },
        ],
        "document_observations": [
            {
                "observation_id": "observation-alpha", "deal_id": "deal-alpha",
                "observation_key": "data-processing-key", "state": "OBSERVED",
                "document_id": "document-alpha", "document_version": "version-gamma",
                "document_sha256": "a" * 64, "locator": "page-six-section-beta",
                "method": "approved-human-annotation", "complete_document": True,
                "amendments_complete": True, "precedence_complete": True,
                "source_id": "doc-alpha", "schema_version": "schema-doc",
                "observed_at": "2026-07-10T08:00:00Z",
            }
        ],
        "process_observations": [
            {
                "process_observation_id": "process-observation-alpha", "deal_id": "deal-alpha",
                "observation_key": "manager-review-key", "state": "OBSERVED",
                "process_id": "approval-process-alpha", "process_version": "version-delta",
                "permissions_receipt_id": "permissions-alpha", "side_effects_receipt_id": "effects-alpha",
                "source_id": "process-alpha", "schema_version": "schema-process",
                "observed_at": "2026-07-10T07:00:00Z",
            }
        ],
    }


def states(result):
    return {row["target"]: row["state"] for row in result["deal_reviews"][0]["rule_results"]}


class DealGovernanceTests(unittest.TestCase):
    def test_valid_review(self):
        result = review_governance(fixture())
        self.assertEqual(result["review_type"], "DEAL_GOVERNANCE_EVIDENCE_REVIEW")
        self.assertEqual(result["review_state"], "HUMAN_APPROVAL_REQUIRED")
        self.assertEqual(states(result)["discount_pct"], "RULE_MATCHED")

    def test_fixed_boundary(self):
        self.assertEqual(review_governance(fixture())["boundary"], BOUNDARY)

    def test_exact_renderer(self):
        result = review_governance(fixture())
        output = render_review_output(result)
        self.assertEqual(output, json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    def test_numeric_results_reference_receipts(self):
        result = review_governance(fixture())
        row = next(item for item in result["deal_reviews"][0]["rule_results"] if item["target"] == "discount_pct")
        self.assertNotIn("value", row)
        self.assertIn("fact_id", row)
        self.assertIn("threshold_receipt_id", row)

    def test_document_and_process_receipts_render_once(self):
        result = review_governance(fixture())
        self.assertEqual(result["document_observation_receipts"][0]["observation_id"], "observation-alpha")
        self.assertEqual(result["process_observation_receipts"][0]["process_observation_id"], "process-observation-alpha")
        output = render_review_output(result)
        self.assertEqual(output.count('"document_sha256"'), 1)
        self.assertEqual(output.count('"permissions_receipt_id"'), 1)

    def test_policy_receipt_includes_bindings_and_prohibited_uses(self):
        receipt = review_governance(fixture())["policy_receipt"]
        self.assertEqual(len(receipt["source_bindings"]), 3)
        self.assertIn("crm-write", receipt["prohibited_uses"])

    def test_no_action_fields_in_output(self):
        output = render_review_output(review_governance(fixture())).lower()
        for term in ('"approve"', '"reject"', '"route_to"', '"notify"', '"crm_write"'):
            self.assertNotIn(term, output)

    def test_r1_terms_absent(self):
        output = render_review_output(review_governance(fixture())).lower()
        for term in ("small", "large", "enough", "limited", "insufficient", " poor ", " high ", " low "):
            self.assertNotIn(term, output)

    def test_unknown_root_field_rejected(self):
        data = fixture(); data["extra"] = True
        with self.assertRaises(ValueError): review_governance(data)

    def test_unknown_deal_field_rejected(self):
        data = fixture(); data["deals"][0]["extra"] = "x"
        with self.assertRaises(ValueError): review_governance(data)

    def test_forbidden_email_key_rejected(self):
        data = fixture(); data["deals"][0]["email"] = "person@example.com"
        with self.assertRaises(ValueError): review_governance(data)

    def test_contact_identifier_rejected(self):
        data = fixture(); data["policy"]["owner_id"] = "person@example.com"
        with self.assertRaises(ValueError): review_governance(data)

    def test_r1_identifier_rejected(self):
        data = fixture(); data["deals"][0]["deal_id"] = "deal-high"
        data["declaration"]["deal_ids"] = ["deal-high"]
        with self.assertRaises(ValueError): review_governance(data)

    def test_unapproved_purpose_rejected(self):
        data = fixture(); data["policy"]["approved_purpose"] = "auto-approval"
        with self.assertRaises(ValueError): review_governance(data)

    def test_unapproved_disposition_rejected(self):
        data = fixture(); data["policy"]["rules"][0]["disposition"] = "AUTO_APPROVE"
        with self.assertRaises(ValueError): review_governance(data)

    def test_naive_timestamp_rejected(self):
        data = fixture(); data["deals"][0]["observed_at"] = "2026-07-10T10:00:00"
        with self.assertRaises(ValueError): review_governance(data)

    def test_future_evidence_rejected(self):
        data = fixture(); data["numeric_facts"][0]["observed_at"] = "2026-07-11T00:00:00Z"
        with self.assertRaises(ValueError): review_governance(data)

    def test_ineffective_policy_rejected(self):
        data = fixture(); data["policy"]["effective_at"] = "2026-07-11T00:00:00Z"
        with self.assertRaises(ValueError): review_governance(data)

    def test_expired_policy_rejected(self):
        data = fixture(); data["policy"]["expires_at"] = "2026-07-10T11:00:00Z"
        with self.assertRaises(ValueError): review_governance(data)

    def test_source_binding_mismatch_rejected(self):
        data = fixture(); data["numeric_facts"][0]["schema_version"] = "other-schema"
        with self.assertRaises(ValueError): review_governance(data)

    def test_duplicate_rule_rejected(self):
        data = fixture(); data["policy"]["rules"].append(copy.deepcopy(data["policy"]["rules"][0]))
        with self.assertRaises(ValueError): review_governance(data)

    def test_duplicate_deal_rejected(self):
        data = fixture(); data["deals"].append(copy.deepcopy(data["deals"][0]))
        with self.assertRaises(ValueError): review_governance(data)

    def test_duplicate_fact_rejected(self):
        data = fixture(); data["numeric_facts"].append(copy.deepcopy(data["numeric_facts"][0]))
        with self.assertRaises(ValueError): review_governance(data)

    def test_declared_count_mismatch_rejected(self):
        data = fixture(); data["declaration"]["declared_deal_count"] = 2
        with self.assertRaises(ValueError): review_governance(data)

    def test_declared_ids_mismatch_rejected(self):
        data = fixture(); data["declaration"]["deal_ids"] = ["deal-beta"]
        with self.assertRaises(ValueError): review_governance(data)

    def test_scientific_decimal_rejected(self):
        data = fixture(); data["numeric_facts"][0]["value"] = "1e3"
        with self.assertRaises(ValueError): review_governance(data)

    def test_negative_decimal_rejected(self):
        data = fixture(); data["numeric_facts"][0]["value"] = "-1"
        with self.assertRaises(ValueError): review_governance(data)

    def test_zero_list_amount_rejected(self):
        data = fixture(); data["numeric_facts"][0]["value"] = "0"
        with self.assertRaises(ValueError): review_governance(data)

    def test_currency_mismatch_is_not_evaluable(self):
        data = fixture(); data["policy"]["rules"][0]["currency"] = "EUR"
        self.assertEqual(states(review_governance(data))["discount_pct"], "NOT_EVALUABLE")

    def test_price_currency_conflict_is_preserved(self):
        data = fixture(); data["numeric_facts"][1]["currency"] = "EUR"
        self.assertEqual(states(review_governance(data))["discount_pct"], "EVIDENCE_CONFLICT")

    def test_price_basis_conflict_is_preserved(self):
        data = fixture(); data["numeric_facts"][1]["basis"] = "total-net"
        self.assertEqual(states(review_governance(data))["discount_pct"], "EVIDENCE_CONFLICT")

    def test_duplicate_list_amount_is_preserved_as_conflict(self):
        data = fixture()
        row = copy.deepcopy(data["numeric_facts"][0]); row["fact_id"] = "fact-list-secondary"
        data["numeric_facts"].append(row)
        self.assertEqual(states(review_governance(data))["discount_pct"], "EVIDENCE_CONFLICT")

    def test_quote_above_list_is_preserved_as_conflict(self):
        data = fixture(); data["numeric_facts"][1]["value"] = "130"
        self.assertEqual(states(review_governance(data))["discount_pct"], "EVIDENCE_CONFLICT")

    def test_basis_mismatch_is_not_evaluable(self):
        data = fixture(); data["policy"]["rules"][0]["basis"] = "total-net"
        self.assertEqual(states(review_governance(data))["discount_pct"], "NOT_EVALUABLE")

    def test_missing_numeric_evidence_is_not_evaluable(self):
        data = fixture(); data["numeric_facts"] = []
        self.assertEqual(states(review_governance(data))["discount_pct"], "NOT_EVALUABLE")

    def test_provided_and_derived_discount_conflict(self):
        data = fixture()
        data["numeric_facts"].append({
            "fact_id": "fact-provided", "deal_id": "deal-alpha", "kind": "discount_pct",
            "value": "19", "unit": "percent", "basis": "annual-net", "currency": "USD",
            "source_id": "crm-alpha", "schema_version": "schema-alpha", "observed_at": "2026-07-10T09:00:00Z",
        })
        self.assertEqual(states(review_governance(data))["discount_pct"], "EVIDENCE_CONFLICT")

    def test_provided_and_derived_discount_agree(self):
        data = fixture()
        data["numeric_facts"].append({
            "fact_id": "fact-provided", "deal_id": "deal-alpha", "kind": "discount_pct",
            "value": "20", "unit": "percent", "basis": "annual-net", "currency": "USD",
            "source_id": "crm-alpha", "schema_version": "schema-alpha", "observed_at": "2026-07-10T09:00:00Z",
        })
        self.assertEqual(states(review_governance(data))["discount_pct"], "RULE_MATCHED")

    def test_rule_not_matched(self):
        data = fixture(); data["policy"]["rules"][0]["threshold"] = "15"
        self.assertEqual(states(review_governance(data))["discount_pct"], "RULE_NOT_MATCHED")

    def test_document_missing_requires_review(self):
        data = fixture(); data["document_observations"] = []
        self.assertEqual(states(review_governance(data))["data-processing-key"], "DOCUMENT_REVIEW_REQUIRED")

    def test_document_incomplete_requires_review(self):
        data = fixture(); data["document_observations"][0]["amendments_complete"] = False
        self.assertEqual(states(review_governance(data))["data-processing-key"], "DOCUMENT_REVIEW_REQUIRED")

    def test_document_conflict_preserved(self):
        data = fixture(); data["document_observations"][0]["state"] = "CONFLICT"
        self.assertEqual(states(review_governance(data))["data-processing-key"], "EVIDENCE_CONFLICT")

    def test_document_rule_not_matched(self):
        data = fixture(); data["document_observations"][0]["state"] = "NOT_OBSERVED"
        self.assertEqual(states(review_governance(data))["data-processing-key"], "RULE_NOT_MATCHED")

    def test_bad_document_hash_rejected(self):
        data = fixture(); data["document_observations"][0]["document_sha256"] = "abc"
        with self.assertRaises(ValueError): review_governance(data)

    def test_process_missing_not_evaluable(self):
        data = fixture(); data["process_observations"] = []
        self.assertEqual(states(review_governance(data))["manager-review-key"], "NOT_EVALUABLE")

    def test_process_conflict_preserved(self):
        data = fixture(); data["process_observations"][0]["state"] = "UNRESOLVED"
        self.assertEqual(states(review_governance(data))["manager-review-key"], "EVIDENCE_CONFLICT")

    def test_process_rule_not_matched(self):
        data = fixture(); data["process_observations"][0]["state"] = "NOT_OBSERVED"
        self.assertEqual(states(review_governance(data))["manager-review-key"], "RULE_NOT_MATCHED")

    def test_higher_precedence_rule_selected(self):
        data = fixture()
        rule = copy.deepcopy(data["policy"]["rules"][0])
        rule["rule_id"] = "rule-discount-secondary"; rule["precedence"] = 10; rule["threshold"] = "5"
        data["policy"]["rules"].append(rule)
        self.assertEqual(states(review_governance(data))["discount_pct"], "RULE_MATCHED")

    def test_equal_precedence_overlap_is_policy_conflict(self):
        data = fixture()
        rule = copy.deepcopy(data["policy"]["rules"][0])
        rule["rule_id"] = "rule-discount-secondary"; rule["threshold"] = "5"
        data["policy"]["rules"].append(rule)
        self.assertEqual(states(review_governance(data))["discount_pct"], "POLICY_CONFLICT")

    def test_non_applicable_rule_is_omitted(self):
        data = fixture(); data["policy"]["rules"][0]["applies_to_tags"] = ["segment-beta"]
        self.assertNotIn("discount_pct", states(review_governance(data)))

    def test_no_applicable_rules_requires_policy(self):
        data = fixture()
        for rule in data["policy"]["rules"]:
            rule["applies_to_tags"] = ["segment-beta"]
        result = review_governance(data)
        self.assertEqual(result["deal_reviews"][0]["unresolved_states"], ["POLICY_REQUIRED"])

    def test_order_independence(self):
        first = render_review_output(review_governance(fixture()))
        data = fixture()
        data["policy"]["rules"].reverse(); data["numeric_facts"].reverse()
        self.assertEqual(first, render_review_output(review_governance(data)))


if __name__ == "__main__":
    unittest.main()
