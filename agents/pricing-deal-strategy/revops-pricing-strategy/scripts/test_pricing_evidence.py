#!/usr/bin/env python3

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pricing_evidence import BOUNDARY, render_review_output, review_price_evidence


def fixture():
    basis = {"basis_id":"basis-alpha","basis_version":"version-alpha","basis_approval_id":"approval-basis","product_scope_id":"product-alpha","configuration_scope_id":"configuration-alpha","quantity":"10","unit":"seat","currency":"USD","price_kind":"list-price","billing_basis":"per-seat","billing_period":"month","contract_term":"term-alpha","region":"region-alpha","tax_basis":"tax-excluded","fee_basis":"fees-excluded","discount_basis":"discount-none"}
    return {
            "policy":{"policy_id":"policy-alpha","policy_version":"version-alpha","owner_id":"owner-alpha","human_reviewer_role_id":"reviewer-alpha","finance_approval_id":"approval-finance","legal_competition_approval_id":"approval-legal","privacy_approval_id":"approval-privacy","workforce_approval_id":"approval-workforce","recipient_policy_id":"policy-recipient","retention_policy_id":"policy-retention","scenario_policy_id":"policy-scenario","effective_at":"2026-07-01T00:00:00Z","expires_at":None,"cutoff_at":"2026-07-11T00:00:00Z","timezone":"America/Guayaquil","approved_purpose":"internal_pricing_scenario_evidence_review","prohibited_uses":["price-recommendation","discount-recommendation","optimal-price-claim","elasticity-claim","arr-claim","competitor-data","pricing-approval","downstream-decision","monitoring","alert","system-read","crm-write","publication","customer-action","workforce-action"],"correction_path":"submit-correction-receipt","calculation_policy":{"percentage_scale":2,"rounding_mode":"half_even"},"source_bindings":[{"lane":"approved_final","source_id":"source-internal","schema_version":"schema-internal","authorization_id":"authorization-internal","query_receipt_id":"receipt-query-internal","page_receipt_id":"receipt-pages-internal","pseudonymization_receipt_id":"receipt-pseudonymization-internal","authorization_effective_at":"2026-07-01T00:00:00Z","authorization_expires_at":None},{"lane":"customer_scenario","source_id":"source-scenario","schema_version":"schema-scenario","authorization_id":"authorization-scenario","query_receipt_id":"receipt-query-scenario","page_receipt_id":"receipt-pages-scenario","pseudonymization_receipt_id":"receipt-pseudonymization-scenario","authorization_effective_at":"2026-07-01T00:00:00Z","authorization_expires_at":None}],"comparison_bases":[basis]},
        "declaration":{"review_id":"review-alpha","declared_observation_count":2,"observation_ids":["observation-left","observation-right"]},
        "source_populations":[{"population_receipt_id":"population-left","lane":"approved_final","source_id":"source-internal","schema_version":"schema-internal","authorization_id":"authorization-internal","complete":True,"observation_ids":["observation-left"],"captured_at":"2026-07-10T12:00:00Z"},{"population_receipt_id":"population-right","lane":"customer_scenario","source_id":"source-scenario","schema_version":"schema-scenario","authorization_id":"authorization-scenario","complete":True,"observation_ids":["observation-right"],"captured_at":"2026-07-10T12:00:00Z"}],
        "observations":[{"observation_id":"observation-left","lane":"approved_final","party_id":"party-internal","item_id":"item-internal","source_id":"source-internal","schema_version":"schema-internal","authorization_id":"authorization-internal","basis_id":"basis-alpha","basis_version":"version-alpha","amount":"120.00","effective_begin":"2026-07-01T00:00:00Z","effective_end":"2026-08-01T00:00:00Z","occurred_at":"2026-07-08T00:00:00Z","captured_at":"2026-07-09T00:00:00Z","population_receipt_id":"population-left","source_receipt_id":"receipt-source-left"},{"observation_id":"observation-right","lane":"customer_scenario","party_id":"party-scenario","item_id":"item-scenario","source_id":"source-scenario","schema_version":"schema-scenario","authorization_id":"authorization-scenario","basis_id":"basis-alpha","basis_version":"version-alpha","amount":"100","effective_begin":"2026-07-01T00:00:00Z","effective_end":"2026-08-01T00:00:00Z","occurred_at":"2026-07-07T00:00:00Z","captured_at":"2026-07-09T00:00:00Z","population_receipt_id":"population-right","source_receipt_id":"receipt-source-right"}],
        "comparisons":[{"comparison_id":"comparison-alpha","left_observation_id":"observation-left","right_observation_id":"observation-right","comparison_at":"2026-07-10T00:00:00Z"}]
    }


class PricingEvidenceTests(unittest.TestCase):
    def test_valid(self):
        result=review_price_evidence(fixture()); self.assertEqual(result["review_type"],"INTERNAL_PRICING_SCENARIO_EVIDENCE_REVIEW"); self.assertEqual(result["comparison_receipts"][0]["state"],"COMPARABLE")
    def test_boundary(self): self.assertEqual(review_price_evidence(fixture())["boundary"],BOUNDARY)
    def test_renderer(self):
        r=review_price_evidence(fixture()); self.assertEqual(render_review_output(r),json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+"\n\n")
    def test_difference(self):
        rows=review_price_evidence(fixture())["numeric_receipts"]; self.assertEqual([r["value"] for r in rows],["20","20"])
    def test_negative_difference(self):
        d=fixture(); d["observations"][0]["amount"]="80"; rows=review_price_evidence(d)["numeric_receipts"]; self.assertEqual([r["value"] for r in rows],["-20","-20"])
    def test_rounding(self):
        d=fixture(); d["observations"][0]["amount"]="2"; d["observations"][1]["amount"]="3"; rows=review_price_evidence(d)["numeric_receipts"]; self.assertEqual(rows[1]["value"],"-33.33")
    def test_input_order(self):
        a=fixture(); b=fixture(); b["observations"].reverse(); b["source_populations"].reverse(); b["policy"]["source_bindings"].reverse(); self.assertEqual(render_review_output(review_price_evidence(a)),render_review_output(review_price_evidence(b)))
    def test_numbers_not_in_comparison(self): self.assertNotIn("value",review_price_evidence(fixture())["comparison_receipts"][0])
    def test_unknown_root(self):
        d=fixture(); d["extra"]=1; self.assertRaises(ValueError,review_price_evidence,d)
    def test_unknown_observation(self):
        d=fixture(); d["observations"][0]["extra"]=1; self.assertRaises(ValueError,review_price_evidence,d)
    def test_direct_identity_key(self):
        d=fixture(); d["observations"][0]["name"]="x"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_free_text(self):
        d=fixture(); d["observations"][0]["free_text"]="x"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_email(self):
        d=fixture(); d["policy"]["correction_path"]="x@example.com"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_invalid_policy_timezone(self):
        d=fixture(); d["policy"]["timezone"]="Mars/Olympus"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_r1_token(self):
        d=fixture(); d["observations"][0]["party_id"]="party-high"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_action_id(self):
        d=fixture(); d["observations"][0]["party_id"]="party-notify"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_wrong_purpose(self):
        d=fixture(); d["policy"]["approved_purpose"]="price-action"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_missing_finance_approval(self):
        d=fixture(); d["policy"].pop("finance_approval_id"); self.assertRaises(ValueError,review_price_evidence,d)
    def test_missing_legal_approval(self):
        d=fixture(); d["policy"].pop("legal_competition_approval_id"); self.assertRaises(ValueError,review_price_evidence,d)
    def test_missing_privacy_approval(self):
        d=fixture(); d["policy"].pop("privacy_approval_id"); self.assertRaises(ValueError,review_price_evidence,d)
    def test_missing_workforce_approval(self):
        d=fixture(); d["policy"].pop("workforce_approval_id"); self.assertRaises(ValueError,review_price_evidence,d)
    def test_missing_scenario_policy(self):
        d=fixture(); d["policy"].pop("scenario_policy_id"); self.assertRaises(ValueError,review_price_evidence,d)
    def test_missing_prohibition(self):
        d=fixture(); d["policy"]["prohibited_uses"].remove("alert"); self.assertRaises(ValueError,review_price_evidence,d)
    def test_future_policy(self):
        d=fixture(); d["policy"]["effective_at"]="2026-07-12T00:00:00Z"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_expired_policy(self):
        d=fixture(); d["policy"]["expires_at"]="2026-07-10T00:00:00Z"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_bad_scale(self):
        d=fixture(); d["policy"]["calculation_policy"]["percentage_scale"]=9; self.assertRaises(ValueError,review_price_evidence,d)
    def test_bad_rounding(self):
        d=fixture(); d["policy"]["calculation_policy"]["rounding_mode"]="ambient"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_duplicate_binding(self):
        d=fixture(); d["policy"]["source_bindings"].append(copy.deepcopy(d["policy"]["source_bindings"][0])); self.assertRaises(ValueError,review_price_evidence,d)
    def test_future_source_authorization(self):
        d=fixture(); d["policy"]["source_bindings"][0]["authorization_effective_at"]="2026-07-12T00:00:00Z"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_source_authorization_excludes_occurrence(self):
        d=fixture(); d["policy"]["source_bindings"][0]["authorization_effective_at"]="2026-07-08T12:00:00Z"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_missing_query_receipt(self):
        d=fixture(); d["policy"]["source_bindings"][0].pop("query_receipt_id"); self.assertRaises(ValueError,review_price_evidence,d)
    def test_missing_pseudonymization_receipt(self):
        d=fixture(); d["policy"]["source_bindings"][0].pop("pseudonymization_receipt_id"); self.assertRaises(ValueError,review_price_evidence,d)
    def test_expired_source_authorization(self):
        d=fixture(); d["policy"]["source_bindings"][0]["authorization_expires_at"]="2026-07-10T00:00:00Z"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_bad_lane(self):
        d=fixture(); d["policy"]["source_bindings"][0]["lane"]="social"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_duplicate_basis(self):
        d=fixture(); d["policy"]["comparison_bases"].append(copy.deepcopy(d["policy"]["comparison_bases"][0])); self.assertRaises(ValueError,review_price_evidence,d)
    def test_missing_basis_approval(self):
        d=fixture(); d["policy"]["comparison_bases"][0].pop("basis_approval_id"); self.assertRaises(ValueError,review_price_evidence,d)
    def test_float_quantity(self):
        d=fixture(); d["policy"]["comparison_bases"][0]["quantity"]=10.0; self.assertRaises(ValueError,review_price_evidence,d)
    def test_zero_quantity(self):
        d=fixture(); d["policy"]["comparison_bases"][0]["quantity"]="0"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_bad_declared_count(self):
        d=fixture(); d["declaration"]["declared_observation_count"]=3; self.assertRaises(ValueError,review_price_evidence,d)
    def test_duplicate_declared_id(self):
        d=fixture(); d["declaration"]["observation_ids"][1]="observation-left"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_incomplete_population(self):
        d=fixture(); d["source_populations"][0]["complete"]=False; self.assertRaises(ValueError,review_price_evidence,d)
    def test_population_extra_id(self):
        d=fixture(); d["source_populations"][0]["observation_ids"].append("observation-extra"); self.assertRaises(ValueError,review_price_evidence,d)
    def test_population_overlap(self):
        d=fixture(); d["source_populations"][1]["observation_ids"]=["observation-left"]; self.assertRaises(ValueError,review_price_evidence,d)
    def test_missing_population(self):
        d=fixture(); d["source_populations"]=d["source_populations"][:1]; self.assertRaises(ValueError,review_price_evidence,d)
    def test_population_after_cutoff(self):
        d=fixture(); d["source_populations"][0]["captured_at"]="2026-07-12T00:00:00Z"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_population_completion_before_observation(self):
        d=fixture(); d["source_populations"][0]["captured_at"]="2026-07-08T12:00:00Z"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_float_amount(self):
        d=fixture(); d["observations"][0]["amount"]=120.0; self.assertRaises(ValueError,review_price_evidence,d)
    def test_zero_amount(self):
        d=fixture(); d["observations"][0]["amount"]="0"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_schema_mismatch(self):
        d=fixture(); d["observations"][0]["schema_version"]="other"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_authorization_mismatch(self):
        d=fixture(); d["observations"][0]["authorization_id"]="authorization-other"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_basis_version_mismatch(self):
        d=fixture(); d["observations"][0]["basis_version"]="other"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_wrong_population_receipt(self):
        d=fixture(); d["observations"][0]["population_receipt_id"]="population-right"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_duplicate_observation(self):
        d=fixture(); d["observations"][1]["observation_id"]="observation-left"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_duplicate_observation_source_receipt(self):
        d=fixture(); d["observations"][1]["source_receipt_id"]="receipt-source-left"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_naive_time(self):
        d=fixture(); d["observations"][0]["captured_at"]="2026-07-09T00:00:00"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_bad_effective_window(self):
        d=fixture(); d["observations"][0]["effective_end"]="2026-06-01T00:00:00Z"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_capture_before_occurrence(self):
        d=fixture(); d["observations"][0]["captured_at"]="2026-07-07T00:00:00Z"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_capture_after_cutoff(self):
        d=fixture(); d["observations"][0]["captured_at"]="2026-07-12T00:00:00Z"; self.assertRaises(ValueError,review_price_evidence,d)
    def test_missing_comparison_observation(self):
        d=fixture(); d["comparisons"][0]["left_observation_id"]="observation-missing"; self.assertEqual(review_price_evidence(d)["comparison_receipts"][0]["state"],"SOURCE_REQUIRED")
    def test_mismatched_basis_not_comparable(self):
        d=fixture(); second=copy.deepcopy(d["policy"]["comparison_bases"][0]); second["basis_id"]="basis-beta"; d["policy"]["comparison_bases"].append(second); d["observations"][1]["basis_id"]="basis-beta"; self.assertEqual(review_price_evidence(d)["comparison_receipts"][0]["state"],"NOT_COMPARABLE")
    def test_time_outside_window_not_comparable(self):
        d=fixture(); d["comparisons"][0]["comparison_at"]="2026-08-02T00:00:00Z"; self.assertEqual(review_price_evidence(d)["comparison_receipts"][0]["state"],"NOT_COMPARABLE")
    def test_duplicate_comparison(self):
        d=fixture(); d["comparisons"].append(copy.deepcopy(d["comparisons"][0])); self.assertRaises(ValueError,review_price_evidence,d)
    def test_self_comparison_not_comparable(self):
        d=fixture(); d["comparisons"][0]["right_observation_id"]="observation-left"; self.assertEqual(review_price_evidence(d)["comparison_receipts"][0]["state"],"NOT_COMPARABLE")
    def test_comparison_requires_scenario_lane(self):
        d=fixture(); d["policy"]["source_bindings"][1]["lane"]="approved_quote"; d["source_populations"][1]["lane"]="approved_quote"; d["observations"][1]["lane"]="approved_quote"; self.assertEqual(review_price_evidence(d)["comparison_receipts"][0]["state"],"NOT_COMPARABLE")
    def test_no_action_fields(self):
        output=render_review_output(review_price_evidence(fixture())).lower()
        for key in ('"recommendation":','"confidence":','"risk":','"rank":','"forecast":','"elasticity":','"optimal_price":','"arr_recovery":','"crm_write":','"coaching":'): self.assertNotIn(key,output)


if __name__ == "__main__": unittest.main()
