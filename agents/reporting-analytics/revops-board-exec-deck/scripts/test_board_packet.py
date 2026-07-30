#!/usr/bin/env python3

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from board_packet import PURPOSE, REQUIRED_PROHIBITIONS, assemble_board_packet, render_packet_output


def contract(contract_id, metric_id, period_begin, period_finish, unit="CURRENCY", currency="USD", amount_basis="contracted-amount", financial_basis="OPERATING"):
    suffix = contract_id.removeprefix("contract-")
    row = {
        "contract_id": contract_id,
        "metric_id": metric_id,
        "display_label_id": f"label-{metric_id.removeprefix('metric-')}",
        "source_id": "source-approved-ledger",
        "source_version": "version-one",
        "schema_id": "schema-approved-metrics",
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
        "period_start": period_begin,
        "period_end": period_finish,
        "freshness_observed_at": "2026-07-02T12:00:00+00:00",
        "unit": unit,
        "currency": currency,
        "amount_basis": amount_basis,
        "metric_definition_id": "definition-approved-pipeline",
        "aggregation_method": "AS_PROVIDED",
        "financial_basis": financial_basis,
        "non_gaap_label_id": "not-applicable",
        "comparable_gaap_contract_id": "not-applicable",
        "reconciliation_receipt_id": "not-applicable",
        "period_consistency_receipt_id": "not-applicable",
        "approval_receipt_id": f"receipt-approval-{suffix}",
    }
    return row


def valid_document():
    prior = contract("contract-prior-pipeline", "metric-pipeline", "2026-01-01T00:00:00-05:00", "2026-04-01T00:00:00-04:00")
    current = contract("contract-current-pipeline", "metric-current-pipeline", "2026-04-01T00:00:00-04:00", "2026-07-01T00:00:00-04:00")
    gaap = contract("contract-current-gaap", "metric-gaap-revenue", "2026-04-01T00:00:00-04:00", "2026-07-01T00:00:00-04:00", financial_basis="GAAP")
    gaap["metric_definition_id"] = "definition-gaap-revenue"
    nong = contract("contract-current-adjusted", "metric-adjusted-revenue", "2026-04-01T00:00:00-04:00", "2026-07-01T00:00:00-04:00", financial_basis="NON_GAAP")
    nong.update({
        "metric_definition_id": "definition-adjusted-revenue",
        "non_gaap_label_id": "label-adjusted-revenue",
        "comparable_gaap_contract_id": "contract-current-gaap",
        "reconciliation_receipt_id": "receipt-non-gaap-reconciliation",
        "period_consistency_receipt_id": "receipt-period-consistency",
    })
    values = {
        "record-prior-pipeline": "100.00",
        "record-current-pipeline": "125.50",
        "record-current-gaap": "80.00",
        "record-current-adjusted": "90.00",
    }
    records = []
    for item in (prior, current, gaap, nong):
        record_id = item["expected_record_ids"][0]
        records.append({"record_id": record_id, "contract_id": item["contract_id"], "state": "AVAILABLE", "value": values[record_id], "source_receipt_id": f"receipt-source-{record_id.removeprefix('record-')}"})
    return {
        "policy": {
            "policy_id": "policy-board-packet",
            "policy_version": "version-one",
            "approved_purpose": PURPOSE,
            "effective_at": "2026-01-01T00:00:00+00:00",
            "expires_at": "2026-12-31T23:59:59+00:00",
            "cutoff_at": "2026-07-03T12:00:00+00:00",
            "reviewed_at": "2026-07-03T13:00:00+00:00",
            "audience_class_id": "audience-board",
            "confidentiality_class_id": "confidentiality-restricted",
            "reviewer_role_id": "role-finance-reviewer",
            "allowed_recipient_role_ids": ["role-board-member", "role-executive-reviewer"],
            "retention_rule_id": "retention-board-packet",
            "authority_receipt_id": "receipt-packet-authority",
            "privacy_receipt_id": "receipt-privacy-approval",
            "recipient_receipt_id": "receipt-recipient-policy",
            "retention_receipt_id": "receipt-retention-policy",
            "blueprint_id": "blueprint-quarterly-board",
            "blueprint_version": "version-one",
            "blueprint_receipt_id": "receipt-blueprint-approval",
            "allowed_slide_ids": ["slide-financial", "slide-pipeline"],
            "prohibited_uses": sorted(REQUIRED_PROHIBITIONS),
        },
        "metric_contracts": [prior, current, gaap, nong],
        "records": records,
        "comparisons": [{
            "comparison_id": "comparison-pipeline-periods",
            "current_contract_id": "contract-current-pipeline",
            "prior_contract_id": "contract-prior-pipeline",
            "comparison_basis_receipt_id": "receipt-comparison-basis",
            "approval_receipt_id": "receipt-comparison-approval",
        }],
        "claims": [{
            "claim_id": "claim-pipeline-change",
            "template_id": "template-approved-change",
            "evidence_metric_contract_ids": ["contract-current-pipeline"],
            "evidence_comparison_ids": ["comparison-pipeline-periods"],
            "approval_receipt_id": "receipt-claim-approval",
        }],
        "slides": [
            {"slide_id": "slide-financial", "metric_contract_ids": ["contract-current-adjusted", "contract-current-gaap"], "comparison_ids": [], "claim_ids": [], "blueprint_slot_receipt_id": "receipt-slot-financial"},
            {"slide_id": "slide-pipeline", "metric_contract_ids": ["contract-current-pipeline", "contract-prior-pipeline"], "comparison_ids": ["comparison-pipeline-periods"], "claim_ids": ["claim-pipeline-change"], "blueprint_slot_receipt_id": "receipt-slot-pipeline"},
        ],
    }


class BoardPacketTests(unittest.TestCase):
    def assert_invalid(self, mutate):
        doc = valid_document()
        mutate(doc)
        with self.assertRaises(ValueError):
            assemble_board_packet(doc)

    def test_valid_packet(self):
        result = assemble_board_packet(valid_document())
        self.assertEqual(result["review_state"], "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(result["narrative_authorized"])
        self.assertFalse(result["action_authorized"])
        self.assertFalse(result["publication_authorized"])
        comparison = result["comparison_receipts"][0]
        self.assertEqual(comparison["delta"], "25.500000")
        self.assertEqual(comparison["percent_change"], "25.500000")

    def test_deterministic_render_and_terminal_boundary(self):
        first = render_packet_output(assemble_board_packet(valid_document()))
        second = render_packet_output(assemble_board_packet(valid_document()))
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("{"))
        self.assertTrue(first.endswith("}\n\n"))
        self.assertNotIn("```", first)

    def test_numbers_not_repeated_in_slide_or_claim_blocks(self):
        result = assemble_board_packet(valid_document())
        serialized = json.dumps({"slides": result["slide_blocks"], "claims": result["claim_ledger"]})
        self.assertNotIn("125.500000", serialized)
        self.assertNotIn("25.500000", serialized)

    def test_unresolved_metric_blocks_comparison(self):
        doc = valid_document()
        doc["records"][1]["state"] = "EVIDENCE_MISSING"
        doc["records"][1]["value"] = None
        result = assemble_board_packet(doc)
        receipt = next(row for row in result["metric_receipts"] if row["contract_id"] == "contract-current-pipeline")
        self.assertEqual(receipt["state"], "EVIDENCE_MISSING")
        self.assertEqual(result["comparison_receipts"][0]["state"], "EVIDENCE_MISSING")
        self.assertEqual(result["claim_ledger"][0]["state"], "EVIDENCE_MISSING")
        self.assertEqual(len(result["unresolved_evidence"]), 1)

    def test_mixed_unresolved_states_become_conflict(self):
        doc = valid_document()
        target = doc["metric_contracts"][1]
        target["aggregation_method"] = "SUM"
        doc["metric_contracts"][0]["aggregation_method"] = "SUM"
        target["expected_record_ids"].append("record-current-pipeline-two")
        doc["records"][1].update({"state": "SUPPRESSED", "value": None})
        doc["records"].append({"record_id": "record-current-pipeline-two", "contract_id": target["contract_id"], "state": "UNAUTHORIZED", "value": None, "source_receipt_id": "receipt-source-current-two"})
        result = assemble_board_packet(doc)
        receipt = next(row for row in result["metric_receipts"] if row["contract_id"] == target["contract_id"])
        self.assertEqual(receipt["state"], "EVIDENCE_CONFLICT")

    def test_sum_aggregation(self):
        doc = valid_document()
        target = doc["metric_contracts"][1]
        target["aggregation_method"] = "SUM"
        doc["metric_contracts"][0]["aggregation_method"] = "SUM"
        target["expected_record_ids"].append("record-current-pipeline-two")
        doc["records"].append({"record_id": "record-current-pipeline-two", "contract_id": target["contract_id"], "state": "AVAILABLE", "value": "4.50", "source_receipt_id": "receipt-source-current-two"})
        result = assemble_board_packet(doc)
        receipt = next(row for row in result["metric_receipts"] if row["contract_id"] == target["contract_id"])
        self.assertEqual(receipt["value"], "130.000000")

    def test_zero_prior_percent_change_is_null(self):
        doc = valid_document()
        doc["records"][0]["value"] = "0"
        result = assemble_board_packet(doc)
        self.assertIsNone(result["comparison_receipts"][0]["percent_change"])

    def test_negative_currency_supported(self):
        doc = valid_document()
        doc["records"][2]["value"] = "-5.25"
        result = assemble_board_packet(doc)
        receipt = next(row for row in result["metric_receipts"] if row["contract_id"] == "contract-current-gaap")
        self.assertEqual(receipt["value"], "-5.250000")

    def test_cli_matches_renderer(self):
        doc = valid_document()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(doc), encoding="utf-8")
            completed = subprocess.run(["python3", str(Path(__file__).with_name("board_packet.py")), str(path)], check=True, capture_output=True, text=True)
        self.assertEqual(completed.stdout, render_packet_output(assemble_board_packet(doc)))

    def test_unknown_document_field(self): self.assert_invalid(lambda d: d.update({"extra": 1}))
    def test_missing_document_field(self): self.assert_invalid(lambda d: d.pop("claims"))
    def test_forbidden_key(self): self.assert_invalid(lambda d: d.update({"account_name": "anonymous"}))
    def test_email_like_value(self): self.assert_invalid(lambda d: d["policy"].update({"audience_class_id": "user@example.com"}))
    def test_wrong_purpose(self): self.assert_invalid(lambda d: d["policy"].update({"approved_purpose": "generate_board_deck"}))
    def test_missing_prohibition(self): self.assert_invalid(lambda d: d["policy"].update({"prohibited_uses": sorted(REQUIRED_PROHIBITIONS - {"publication"})}))
    def test_policy_time_order(self): self.assert_invalid(lambda d: d["policy"].update({"reviewed_at": "2027-01-01T00:00:00+00:00"}))
    def test_policy_slide_mismatch(self): self.assert_invalid(lambda d: d["policy"].update({"allowed_slide_ids": ["slide-financial"]}))
    def test_duplicate_policy_recipient(self): self.assert_invalid(lambda d: d["policy"].update({"allowed_recipient_role_ids": ["role-board-member", "role-board-member"]}))
    def test_unknown_contract_field(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"extra": "bad"}))
    def test_invalid_contract_id(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"contract_id": "Bad ID"}))
    def test_invalid_unit(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"unit": "MONEY"}))
    def test_currency_required(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"currency": "NONE"}))
    def test_amount_basis_required(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"amount_basis": "not-applicable"}))
    def test_non_currency_rejects_currency(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"unit": "COUNT", "amount_basis": "not-applicable"}))
    def test_invalid_timezone(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"reporting_timezone": "EST"}))
    def test_timezone_offset_mismatch(self): self.assert_invalid(lambda d: d["metric_contracts"][1].update({"period_start": "2026-04-01T00:00:00-05:00"}))
    def test_missing_pseudonymization_receipt(self): self.assert_invalid(lambda d: d["metric_contracts"][0].pop("pseudonymization_receipt_id"))
    def test_missing_privacy_receipt(self): self.assert_invalid(lambda d: d["policy"].pop("privacy_receipt_id"))
    def test_contract_future_freshness(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"freshness_observed_at": "2026-08-01T00:00:00+00:00"}))
    def test_contract_period_reverse(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"period_end": "2025-12-01T00:00:00-05:00"}))
    def test_as_provided_multiple_records(self): self.assert_invalid(lambda d: d["metric_contracts"][0]["expected_record_ids"].append("record-extra"))
    def test_non_gaap_missing_reconciliation(self): self.assert_invalid(lambda d: d["metric_contracts"][3].update({"reconciliation_receipt_id": "not-applicable"}))
    def test_gaap_rejects_non_gaap_fields(self): self.assert_invalid(lambda d: d["metric_contracts"][2].update({"non_gaap_label_id": "label-wrong"}))
    def test_non_gaap_unknown_comparable(self): self.assert_invalid(lambda d: d["metric_contracts"][3].update({"comparable_gaap_contract_id": "contract-unknown"}))
    def test_non_gaap_comparable_must_be_gaap(self): self.assert_invalid(lambda d: d["metric_contracts"][3].update({"comparable_gaap_contract_id": "contract-current-pipeline"}))
    def test_non_gaap_basis_mismatch(self): self.assert_invalid(lambda d: d["metric_contracts"][2].update({"amount_basis": "recognized-revenue"}))
    def test_duplicate_record(self): self.assert_invalid(lambda d: d["records"].append(copy.deepcopy(d["records"][0])))
    def test_missing_record(self): self.assert_invalid(lambda d: d["records"].pop())
    def test_extra_record(self): self.assert_invalid(lambda d: d["records"].append({"record_id": "record-extra", "contract_id": "contract-current-gaap", "state": "AVAILABLE", "value": "1", "source_receipt_id": "receipt-extra"}))
    def test_invalid_state(self): self.assert_invalid(lambda d: d["records"][0].update({"state": "UNKNOWN"}))
    def test_available_requires_value(self): self.assert_invalid(lambda d: d["records"][0].update({"value": None}))
    def test_unavailable_rejects_value(self): self.assert_invalid(lambda d: d["records"][0].update({"state": "SUPPRESSED"}))
    def test_precision_bound(self): self.assert_invalid(lambda d: d["records"][0].update({"value": "1.0000001"}))
    def test_magnitude_bound(self): self.assert_invalid(lambda d: d["records"][0].update({"value": "10000000000000000000"}))
    def test_count_must_be_whole(self):
        def mutate(d):
            d["metric_contracts"][0].update({"unit": "COUNT", "currency": "NONE", "amount_basis": "not-applicable"})
            d["metric_contracts"][1].update({"unit": "COUNT", "currency": "NONE", "amount_basis": "not-applicable"})
            d["records"][0]["value"] = "2.5"
        self.assert_invalid(mutate)
    def test_comparison_unknown_contract(self): self.assert_invalid(lambda d: d["comparisons"][0].update({"current_contract_id": "contract-unknown"}))
    def test_comparison_self(self): self.assert_invalid(lambda d: d["comparisons"][0].update({"current_contract_id": "contract-prior-pipeline"}))
    def test_comparison_definition_mismatch(self): self.assert_invalid(lambda d: d["metric_contracts"][1].update({"metric_definition_id": "definition-other"}))
    def test_comparison_financial_basis_mismatch(self): self.assert_invalid(lambda d: d["metric_contracts"][1].update({"financial_basis": "GAAP"}))
    def test_comparison_currency_mismatch(self): self.assert_invalid(lambda d: d["metric_contracts"][1].update({"currency": "EUR"}))
    def test_comparison_overlap(self): self.assert_invalid(lambda d: d["metric_contracts"][0].update({"period_end": "2026-05-01T00:00:00-04:00"}))
    def test_claim_without_evidence(self): self.assert_invalid(lambda d: d["claims"][0].update({"evidence_metric_contract_ids": [], "evidence_comparison_ids": []}))
    def test_claim_unknown_evidence(self): self.assert_invalid(lambda d: d["claims"][0].update({"evidence_metric_contract_ids": ["contract-unknown"]}))
    def test_slide_unknown_metric(self): self.assert_invalid(lambda d: d["slides"][0].update({"metric_contract_ids": ["contract-unknown"]}))
    def test_slide_unknown_claim(self): self.assert_invalid(lambda d: d["slides"][1].update({"claim_ids": ["claim-unknown"]}))
    def test_unassigned_metric_rejected(self): self.assert_invalid(lambda d: d["slides"][0].update({"metric_contract_ids": ["contract-current-gaap"]}))
    def test_claim_evidence_must_be_on_slide(self): self.assert_invalid(lambda d: d["slides"][1].update({"metric_contract_ids": ["contract-prior-pipeline"]}))
    def test_empty_slide(self): self.assert_invalid(lambda d: d["slides"][0].update({"metric_contract_ids": [], "comparison_ids": [], "claim_ids": []}))
    def test_duplicate_slide(self): self.assert_invalid(lambda d: d["slides"].append(copy.deepcopy(d["slides"][0])))


if __name__ == "__main__":
    unittest.main()
