#!/usr/bin/env python3

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from qbr_packet import PURPOSE, REQUIRED_PROHIBITIONS, assemble_qbr_packet, render_qbr_output


def contract(contract_id, metric_id, begin, finish):
    suffix = contract_id.removeprefix("contract-")
    return {
        "contract_id": contract_id,
        "metric_id": metric_id,
        "section_id": "section-adoption-evidence",
        "slot_id": "slot-adoption",
        "source_id": "source-approved-product",
        "source_version": "version-one",
        "schema_id": "schema-approved-events",
        "schema_version": "version-one",
        "authorization_receipt_id": "receipt-source-authorization",
        "authorization_effective_at": "2025-12-01T00:00:00+00:00",
        "authorization_expires_at": "2026-12-31T23:59:59+00:00",
        "query_receipt_id": "receipt-query-approved",
        "page_receipt_id": "receipt-pages-complete",
        "population_receipt_id": f"receipt-population-{suffix}",
        "pseudonymization_receipt_id": "receipt-pseudonymization-approved",
        "expected_record_ids": [f"record-{suffix}"],
        "reporting_timezone": "America/New_York",
        "period_begin": begin,
        "period_end": finish,
        "freshness_observed_at": "2026-07-02T12:00:00+00:00",
        "unit": "COUNT",
        "currency": "NONE",
        "amount_basis": "not-applicable",
        "metric_definition_id": "definition-approved-adoption",
        "aggregation_method": "AS_PROVIDED",
        "aggregation_rule_receipt_id": "receipt-aggregation-approved",
        "approval_receipt_id": f"receipt-approval-{suffix}",
    }


def valid_document():
    prior = contract("contract-prior-adoption", "metric-prior-adoption", "2026-01-01T00:00:00-05:00", "2026-04-01T00:00:00-04:00")
    current = contract("contract-current-adoption", "metric-current-adoption", "2026-04-01T00:00:00-04:00", "2026-07-01T00:00:00-04:00")
    return {
        "policy": {
            "policy_id": "policy-qbr-packet",
            "policy_version": "version-one",
            "approved_purpose": PURPOSE,
            "effective_at": "2026-01-01T00:00:00+00:00",
            "expires_at": "2026-12-31T23:59:59+00:00",
            "cutoff_at": "2026-07-03T12:00:00+00:00",
            "reviewed_at": "2026-07-03T13:00:00+00:00",
            "audience_class_id": "audience-customer-review",
            "confidentiality_class_id": "confidentiality-restricted",
            "reviewer_role_id": "role-customer-reviewer",
            "allowed_recipient_role_ids": ["role-approved-attendee"],
            "retention_rule_id": "retention-qbr-packet",
            "authority_receipt_id": "receipt-packet-authority",
            "privacy_receipt_id": "receipt-privacy-approval",
            "recipient_receipt_id": "receipt-recipient-policy",
            "retention_receipt_id": "receipt-retention-policy",
            "publication_policy_receipt_id": "receipt-publication-policy",
            "blueprint_id": "blueprint-quarterly-review",
            "blueprint_version": "version-one",
            "allowed_section_ids": ["section-adoption-evidence"],
            "prohibited_uses": sorted(REQUIRED_PROHIBITIONS),
        },
        "blueprint": {
            "blueprint_id": "blueprint-quarterly-review",
            "blueprint_version": "version-one",
            "allowed_section_ids": ["section-adoption-evidence"],
            "allowed_slot_ids": ["slot-adoption"],
            "approval_receipt_id": "receipt-blueprint-approval",
        },
        "metric_contracts": [prior, current],
        "records": [
            {"record_id": "record-prior-adoption", "contract_id": "contract-prior-adoption", "state": "AVAILABLE", "value": "100", "source_receipt_id": "receipt-source-prior"},
            {"record_id": "record-current-adoption", "contract_id": "contract-current-adoption", "state": "AVAILABLE", "value": "125", "source_receipt_id": "receipt-source-current"},
        ],
        "comparisons": [{
            "comparison_id": "comparison-adoption-periods",
            "current_contract_id": "contract-current-adoption",
            "prior_contract_id": "contract-prior-adoption",
            "comparison_basis_receipt_id": "receipt-comparison-basis",
            "approval_receipt_id": "receipt-comparison-approval",
        }],
        "claims": [{
            "claim_id": "claim-adoption-change",
            "template_id": "template-approved-change",
            "evidence_contract_ids": ["contract-current-adoption"],
            "evidence_comparison_ids": ["comparison-adoption-periods"],
            "approval_receipt_id": "receipt-claim-approval",
        }],
        "sections": [{
            "section_id": "section-adoption-evidence",
            "metric_contract_ids": ["contract-current-adoption", "contract-prior-adoption"],
            "comparison_ids": ["comparison-adoption-periods"],
            "claim_ids": ["claim-adoption-change"],
            "blueprint_slot_receipt_id": "receipt-section-slot",
        }],
    }


class QbrPacketTests(unittest.TestCase):
    def assert_invalid(self, mutate):
        doc = valid_document()
        mutate(doc)
        with self.assertRaises(ValueError):
            assemble_qbr_packet(doc)

    def test_valid_packet(self):
        result = assemble_qbr_packet(valid_document())
        self.assertEqual(result["review_state"], "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(result["narrative_authorized"])
        self.assertFalse(result["action_authorized"])
        self.assertFalse(result["delivery_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertEqual(result["comparison_receipts"][0]["delta"], "25.000000")
        self.assertEqual(result["comparison_receipts"][0]["percent_change"], "25.000000")

    def test_deterministic_render_and_terminal_boundary(self):
        first = render_qbr_output(assemble_qbr_packet(valid_document()))
        second = render_qbr_output(assemble_qbr_packet(valid_document()))
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("{"))
        self.assertTrue(first.endswith("}\n\n"))
        self.assertNotIn("```", first)

    def test_numbers_not_repeated_in_claim_or_section(self):
        result = assemble_qbr_packet(valid_document())
        rendered = json.dumps({"claims": result["claim_ledger"], "sections": result["section_blocks"]})
        self.assertNotIn("125.000000", rendered)
        self.assertNotIn("25.000000", rendered)

    def test_missing_current_propagates(self):
        doc = valid_document()
        doc["records"][1].update({"state": "EVIDENCE_MISSING", "value": None})
        result = assemble_qbr_packet(doc)
        self.assertEqual(result["comparison_receipts"][0]["state"], "EVIDENCE_MISSING")
        self.assertEqual(result["claim_ledger"][0]["state"], "EVIDENCE_MISSING")
        self.assertEqual(result["unresolved_evidence"], [{"contract_id": "contract-current-adoption", "state": "EVIDENCE_MISSING"}])

    def test_sum_aggregation(self):
        doc = valid_document()
        target = doc["metric_contracts"][1]
        target["aggregation_method"] = "SUM"
        doc["metric_contracts"][0]["aggregation_method"] = "SUM"
        target["expected_record_ids"].append("record-current-adoption-two")
        doc["records"].append({"record_id": "record-current-adoption-two", "contract_id": target["contract_id"], "state": "AVAILABLE", "value": "5", "source_receipt_id": "receipt-source-current-two"})
        result = assemble_qbr_packet(doc)
        receipt = next(row for row in result["metric_receipts"] if row["contract_id"] == target["contract_id"])
        self.assertEqual(receipt["value"], "130.000000")

    def test_mixed_states_conflict(self):
        doc = valid_document()
        target = doc["metric_contracts"][1]
        target["aggregation_method"] = "SUM"
        doc["metric_contracts"][0]["aggregation_method"] = "SUM"
        target["expected_record_ids"].append("record-current-adoption-two")
        doc["records"][1].update({"state": "SUPPRESSED", "value": None})
        doc["records"].append({"record_id": "record-current-adoption-two", "contract_id": target["contract_id"], "state": "UNAUTHORIZED", "value": None, "source_receipt_id": "receipt-source-current-two"})
        result = assemble_qbr_packet(doc)
        receipt = next(row for row in result["metric_receipts"] if row["contract_id"] == target["contract_id"])
        self.assertEqual(receipt["state"], "EVIDENCE_CONFLICT")

    def test_zero_prior_percent_is_null(self):
        doc = valid_document()
        doc["records"][0]["value"] = "0"
        self.assertIsNone(assemble_qbr_packet(doc)["comparison_receipts"][0]["percent_change"])

    def test_negative_zero_normalized(self):
        doc = valid_document()
        doc["records"][0]["value"] = "0"
        doc["records"][1]["value"] = "-0"
        receipt = assemble_qbr_packet(doc)["metric_receipts"][0]
        self.assertNotEqual(receipt["value"], "-0.000000")

    def test_cli_matches_renderer(self):
        doc = valid_document()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(doc), encoding="utf-8")
            completed = subprocess.run(["python3", str(Path(__file__).with_name("qbr_packet.py")), str(path)], check=True, capture_output=True, text=True)
        self.assertEqual(completed.stdout, render_qbr_output(assemble_qbr_packet(doc)))

    def test_unknown_document_field(self): self.assert_invalid(lambda d: d.update({"extra": 1}))
    def test_missing_document_field(self): self.assert_invalid(lambda d: d.pop("claims"))
    def test_forbidden_key(self): self.assert_invalid(lambda d: d.update({"account_name": "anonymous"}))
    def test_email_like_value(self): self.assert_invalid(lambda d: d["policy"].update({"audience_class_id": "user@example.com"}))
    def test_wrong_purpose(self): self.assert_invalid(lambda d: d["policy"].update({"approved_purpose": "generate-qbr"}))
    def test_missing_prohibition(self): self.assert_invalid(lambda d: d["policy"].update({"prohibited_uses": sorted(REQUIRED_PROHIBITIONS - {"publication"})}))
    def test_policy_time_order(self): self.assert_invalid(lambda d: d["policy"].update({"reviewed_at": "2027-01-01T00:00:00+00:00"}))
    def test_policy_section_mismatch(self): self.assert_invalid(lambda d: d["policy"].update({"allowed_section_ids": ["section-other"]}))
    def test_duplicate_recipient(self): self.assert_invalid(lambda d: d["policy"].update({"allowed_recipient_role_ids": ["role-approved-attendee", "role-approved-attendee"]}))
    def test_blueprint_identity_mismatch(self): self.assert_invalid(lambda d: d["blueprint"].update({"blueprint_id": "blueprint-other-review"}))
    def test_unknown_contract_field(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"extra": "bad"}))
    def test_contract_unknown_section(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"section_id": "section-other"}))
    def test_contract_unknown_slot(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"slot_id": "slot-other"}))
    def test_invalid_contract_id(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"contract_id": "Bad ID"}))
    def test_invalid_unit(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"unit": "PEOPLE"}))
    def test_non_currency_rejects_currency(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"currency": "USD"}))
    def test_currency_requires_basis(self):
        def mutate(d): d["metric_contracts"][0].update({"unit": "CURRENCY", "currency": "USD"})
        self.assert_invalid(mutate)
    def test_invalid_timezone(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"reporting_timezone": "EST"}))
    def test_timezone_offset_mismatch(self): self.assert_invalid(lambda d: d["metric_contracts"][1].update({"period_begin": "2026-04-01T00:00:00-05:00"}))
    def test_future_freshness(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"freshness_observed_at": "2026-08-01T00:00:00+00:00"}))
    def test_period_reverse(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"period_end": "2025-12-01T00:00:00-05:00"}))
    def test_as_provided_multiple_records(self): self.assert_invalid(lambda d: d["metric_contracts"][0]["expected_record_ids"].append("record-extra"))
    def test_duplicate_contract(self): self.assert_invalid(lambda d: d["metric_contracts"].append(copy.deepcopy(d["metric_contracts"][0])))
    def test_duplicate_record(self): self.assert_invalid(lambda d: d["records"].append(copy.deepcopy(d["records"][0])))
    def test_duplicate_source_receipt(self): self.assert_invalid(lambda d: d["records"][1].update({"source_receipt_id": "receipt-source-prior"}))
    def test_missing_record(self): self.assert_invalid(lambda d: d["records"].pop())
    def test_extra_record(self): self.assert_invalid(lambda d: d["records"].append({"record_id": "record-extra", "contract_id": "contract-current-adoption", "state": "AVAILABLE", "value": "1", "source_receipt_id": "receipt-extra"}))
    def test_invalid_state(self): self.assert_invalid(lambda d: d["records"][0].update({"state": "UNKNOWN"}))
    def test_available_requires_value(self): self.assert_invalid(lambda d: d["records"][0].update({"value": None}))
    def test_unavailable_rejects_value(self): self.assert_invalid(lambda d: d["records"][0].update({"state": "SUPPRESSED"}))
    def test_count_must_be_whole(self): self.assert_invalid(lambda d: d["records"][0].update({"value": "2.5"}))
    def test_precision_bound(self): self.assert_invalid(lambda d: d["records"][0].update({"value": "1.0000001"}))
    def test_comparison_unknown_contract(self): self.assert_invalid(lambda d: d["comparisons"][0].update({"current_contract_id": "contract-unknown"}))
    def test_comparison_self(self): self.assert_invalid(lambda d: d["comparisons"][0].update({"current_contract_id": "contract-prior-adoption"}))
    def test_comparison_definition_mismatch(self): self.assert_invalid(lambda d: d["metric_contracts"][1].update({"metric_definition_id": "definition-other"}))
    def test_comparison_overlap(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"period_end": "2026-05-01T00:00:00-04:00"}))
    def test_duplicate_comparison(self): self.assert_invalid(lambda d: d["comparisons"].append(copy.deepcopy(d["comparisons"][0])))
    def test_claim_without_evidence(self): self.assert_invalid(lambda d: d["claims"][0].update({"evidence_contract_ids": [], "evidence_comparison_ids": []}))
    def test_claim_unknown_evidence(self): self.assert_invalid(lambda d: d["claims"][0].update({"evidence_contract_ids": ["contract-unknown"]}))
    def test_duplicate_claim(self): self.assert_invalid(lambda d: d["claims"].append(copy.deepcopy(d["claims"][0])))
    def test_section_unknown_metric(self): self.assert_invalid(lambda d: d["sections"][0].update({"metric_contract_ids": ["contract-unknown"]}))
    def test_section_empty(self): self.assert_invalid(lambda d: d["sections"][0].update({"metric_contract_ids": [], "comparison_ids": [], "claim_ids": []}))
    def test_claim_evidence_must_share_section(self): self.assert_invalid(lambda d: d["sections"][0].update({"metric_contract_ids": ["contract-prior-adoption"]}))
    def test_unassigned_comparison(self): self.assert_invalid(lambda d: d["sections"][0].update({"comparison_ids": [], "claim_ids": []}))
    def test_duplicate_section(self): self.assert_invalid(lambda d: d["sections"].append(copy.deepcopy(d["sections"][0])))


if __name__ == "__main__":
    unittest.main()
