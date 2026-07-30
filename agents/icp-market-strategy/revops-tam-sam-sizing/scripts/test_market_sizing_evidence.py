#!/usr/bin/env python3
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from market_sizing_evidence import BOUNDARY, main, reject_sensitive_fields, render_review_output, review_market, validate_policy


class MarketSizingEvidenceTests(unittest.TestCase):
    def policy(self, **changes):
        value={"policy_id":"POLICY-ALPHA","version":"VERSION-ALPHA","purpose":"read-only market-size evidence review","cutoff":"2026-07-10T12:00:00Z","target_count_unit":"FIRM","coverage_definition":"PAID_EMPLOYER_FIRMS","taxonomy_id":"NAICS","taxonomy_version":"2022","geography_scheme_id":"FIPS","currency":"USD","price_period":"ANNUAL","price_basis":"CUSTOMER_APPROVED_ANNUAL_PRICE","freshness_policy_id":"FRESH-ALPHA","max_age_days":500,"aggregation_policy_id":"AGG-ALPHA","disjoint_aggregation_status":"VERIFIED_DISJOINT","disjoint_receipt_id":"DISJOINT-ALPHA","disjoint_evidence_id":"E-DISJOINT","serviceability_policy_id":"SERVICE-ALPHA","obtainability_policy_id":"OBTAIN-ALPHA","owner_role":"POLICY-OWNER","reviewer_role":"REVIEWER-ROLE","approver_role":"APPROVER-ROLE","correction_path":"EVIDENCE-STEWARD","prohibited_uses":["market-selection","forecast","crm-write"]}
        value.update(changes); return value

    def evidence(self):
        common={"dataset_year":"2022","as_of":"2026-07-01T00:00:00Z","extracted_at":"2026-07-02T00:00:00Z","access_scope":"aggregate-read-only","policy_id":"SOURCE-ALPHA"}
        return [{**common,"evidence_id":"E-UNIVERSE","source_id":"official-firm-table","source_version":"table-alpha"},{**common,"evidence_id":"E-PRICE","source_id":"finance-price-table","source_version":"price-alpha"},{**common,"evidence_id":"E-SERVICE","source_id":"serviceability-register","source_version":"service-alpha"},{**common,"evidence_id":"E-OBTAIN","source_id":"scenario-register","source_version":"scenario-alpha"},{**common,"evidence_id":"E-DISJOINT","source_id":"overlap-audit","source_version":"audit-alpha"}]

    def universe(self, segment_id="SEG-A", **changes):
        value={"segment_id":segment_id,"label":"Software firms in approved geography","geography_id":"GEO-A","taxonomy_code":"5415","count_state":"AVAILABLE","total_count":100,"count_unit":"FIRM","coverage_definition":"PAID_EMPLOYER_FIRMS","taxonomy_id":"NAICS","taxonomy_version":"2022","geography_scheme_id":"FIPS","evidence_id":"E-UNIVERSE"}
        value.update(changes); return value

    def price(self, segment_id="SEG-A", **changes):
        value={"segment_id":segment_id,"price_state":"AVAILABLE","price_per_unit":"2500.50","currency":"USD","period":"ANNUAL","basis":"CUSTOMER_APPROVED_ANNUAL_PRICE","evidence_id":"E-PRICE"}
        value.update(changes); return value

    def service(self, segment_id="SEG-A", **changes):
        value={"segment_id":segment_id,"state":"AVAILABLE","serviceable_count":60,"policy_id":"SERVICE-ALPHA","receipt_id":"SERVICE-RECEIPT-A","evidence_id":"E-SERVICE"}
        value.update(changes); return value

    def obtain(self, segment_id="SEG-A", **changes):
        value={"segment_id":segment_id,"state":"AVAILABLE","fraction":"0.10","horizon":"CUSTOMER_APPROVED_HORIZON","policy_id":"OBTAIN-ALPHA","receipt_id":"OBTAIN-RECEIPT-A","evidence_id":"E-OBTAIN"}
        value.update(changes); return value

    def review(self, **changes):
        values={"review_id":"REVIEW-ALPHA","policy":self.policy(),"evidence_rows":self.evidence(),"universe_rows":[self.universe()],"price_rows":[self.price()],"serviceability_rows":[self.service()],"obtainability_rows":[self.obtain()]}
        values.update(changes); return review_market(**values)

    def test_policy_valid(self): self.assertEqual(validate_policy(self.policy())["target_count_unit"],"FIRM")
    def test_disjoint_receipt_required(self):
        with self.assertRaises(ValueError): validate_policy(self.policy(disjoint_receipt_id=None))
    def test_not_verified_disallows_receipt(self):
        with self.assertRaises(ValueError): validate_policy(self.policy(disjoint_aggregation_status="NOT_VERIFIED"))
    def test_policy_rejects_unknown_fields(self):
        with self.assertRaises(ValueError): validate_policy({**self.policy(),"market_share":"0.05"})
    def test_sensitive_field_rejected(self):
        with self.assertRaises(ValueError): reject_sensitive_fields({"person_email":"x@example.test"})
    def test_exact_single_segment_values(self):
        result=self.review()["segment_results"][0]
        self.assertEqual(str(result["total_addressable_scenario_value"]),"250050.00")
        self.assertEqual(str(result["serviceable_addressable_scenario_value"]),"150030.00")
        self.assertEqual(str(result["obtainable_scenario_value"]),"15003.0000")
        self.assertEqual(result["obtainable_interpretation"],"SCENARIO_NOT_FORECAST")
    def test_single_segment_not_reprinted(self): self.assertEqual(self.review()["aggregation"]["state"],"SINGLE_SEGMENT_NOT_REPRINTED")
    def test_suppressed_count_preserved(self):
        result=self.review(universe_rows=[self.universe(count_state="SUPPRESSED",total_count=None)])["segment_results"][0]
        self.assertEqual((result["state"],result["total_addressable_scenario_value"]),("SUPPRESSED",None))
    def test_nonavailable_count_cannot_have_value(self):
        with self.assertRaises(ValueError): self.review(universe_rows=[self.universe(count_state="UNAVAILABLE")])
    def test_missing_price_is_source_required(self):
        self.assertEqual(self.review(price_rows=[])["segment_results"][0]["reason_code"],"PRICE_REQUIRED")
    def test_float_price_rejected(self):
        with self.assertRaises(ValueError): self.review(price_rows=[self.price(price_per_unit=2.5)])
    def test_price_currency_mismatch(self):
        self.assertEqual(self.review(price_rows=[self.price(currency="EUR")])["segment_results"][0]["reason_code"],"PRICE_POLICY_MISMATCH")
    def test_count_unit_mismatch(self):
        result=self.review(universe_rows=[self.universe(count_unit="ESTABLISHMENT")])["segment_results"][0]
        self.assertEqual((result["state"],result["reason_code"]),("POLICY_REQUIRED","UNIVERSE_POLICY_MISMATCH"))
    def test_coverage_mismatch_visible(self):
        result=self.review(universe_rows=[self.universe(coverage_definition="ESTABLISHMENTS")])["exception_queue"][0]
        self.assertIn("coverage_definition",result["mismatched_fields"])
    def test_unregistered_universe_evidence(self):
        result=self.review(universe_rows=[self.universe(evidence_id="E-X")])["segment_results"][0]
        self.assertEqual(result["state"],"SOURCE_REQUIRED")
    def test_future_evidence_conflicting(self):
        rows=self.evidence(); rows[0]["as_of"]="2026-07-11T00:00:00Z"; rows[0]["extracted_at"]="2026-07-11T01:00:00Z"
        self.assertEqual(self.review(evidence_rows=rows)["segment_results"][0]["state"],"CONFLICTING")
    def test_stale_evidence(self):
        self.assertEqual(self.review(policy=self.policy(max_age_days=1))["segment_results"][0]["state"],"STALE")
    def test_extraction_before_asof_rejected(self):
        rows=self.evidence(); rows[0]["extracted_at"]="2026-06-30T00:00:00Z"
        with self.assertRaises(ValueError): self.review(evidence_rows=rows)
    def test_duplicate_evidence_rejected(self):
        with self.assertRaises(ValueError): self.review(evidence_rows=self.evidence()+[copy.deepcopy(self.evidence()[0])])
    def test_serviceable_count_bounded(self):
        result=self.review(serviceability_rows=[self.service(serviceable_count=101)])["segment_results"][0]
        self.assertEqual((result["state"],result["serviceability_result_state"],result["serviceability_reason_code"]),("CALCULATED","CONFLICTING","SERVICEABLE_COUNT_EXCEEDS_TOTAL"))
        self.assertEqual(str(result["total_addressable_scenario_value"]),"250050.00")
    def test_serviceability_policy_mismatch(self):
        self.assertEqual(self.review(serviceability_rows=[self.service(policy_id="WRONG")])["segment_results"][0]["serviceability_result_state"],"POLICY_REQUIRED")
    def test_stale_service_evidence_stays_stale(self):
        rows=self.evidence(); rows[2]["as_of"]="2020-01-01T00:00:00Z"; rows[2]["extracted_at"]="2020-01-02T00:00:00Z"
        self.assertEqual(self.review(evidence_rows=rows)["segment_results"][0]["serviceability_result_state"],"STALE")
    def test_obtainability_requires_service(self):
        result=self.review(serviceability_rows=[])["segment_results"][0]
        self.assertEqual(result["obtainability_reason_code"],"SERVICEABLE_VALUE_REQUIRED_FOR_OBTAINABLE")
    def test_fraction_bounded(self):
        with self.assertRaises(ValueError): self.review(obtainability_rows=[self.obtain(fraction="1.01")])
    def test_win_rate_not_an_input(self):
        row=self.obtain(); row["win_rate"]= "0.5"
        with self.assertRaises(ValueError): self.review(obtainability_rows=[row])
    def test_unknown_scenario_segment_rejected(self):
        with self.assertRaises(ValueError): self.review(price_rows=[self.price("SEG-X")])
    def test_duplicate_segment_rejected(self):
        with self.assertRaises(ValueError): self.review(universe_rows=[self.universe(),self.universe()])
    def test_verified_disjoint_aggregation(self):
        result=self.review(universe_rows=[self.universe("SEG-A"),self.universe("SEG-B",total_count=20)],price_rows=[self.price("SEG-A"),self.price("SEG-B")],serviceability_rows=[self.service("SEG-A"),self.service("SEG-B",serviceable_count=10)],obtainability_rows=[self.obtain("SEG-A"),self.obtain("SEG-B")])["aggregation"]
        self.assertEqual((result["state"],str(result["total_addressable_value"])),("VERIFIED_DISJOINT_AGGREGATION","300060.00"))
    def test_unverified_disjoint_blocks_aggregation(self):
        policy=self.policy(disjoint_aggregation_status="NOT_VERIFIED",disjoint_receipt_id=None,disjoint_evidence_id=None)
        result=self.review(policy=policy,universe_rows=[self.universe("SEG-A"),self.universe("SEG-B")],price_rows=[self.price("SEG-A"),self.price("SEG-B")],serviceability_rows=[],obtainability_rows=[])["aggregation"]
        self.assertEqual(result["state"],"AGGREGATION_UNAVAILABLE")
    def test_unresolved_segment_blocks_aggregation(self):
        result=self.review(universe_rows=[self.universe("SEG-A"),self.universe("SEG-B",count_state="SUPPRESSED",total_count=None)],price_rows=[self.price("SEG-A"),self.price("SEG-B")],serviceability_rows=[],obtainability_rows=[])["aggregation"]
        self.assertEqual(result["reason_code"],"TOTAL_LANE_UNRESOLVED")
    def test_invalid_disjoint_evidence_blocks_aggregation(self):
        result=self.review(policy=self.policy(disjoint_evidence_id="E-X"),universe_rows=[self.universe("SEG-A"),self.universe("SEG-B")],price_rows=[self.price("SEG-A"),self.price("SEG-B")],serviceability_rows=[],obtainability_rows=[])["aggregation"]
        self.assertEqual(result["reason_code"],"DISJOINTNESS_EVIDENCE_INVALID")
    def test_service_conflict_does_not_erase_total_aggregation(self):
        result=self.review(universe_rows=[self.universe("SEG-A"),self.universe("SEG-B",total_count=20)],price_rows=[self.price("SEG-A"),self.price("SEG-B")],serviceability_rows=[self.service("SEG-A",state="CONFLICT",serviceable_count=None),self.service("SEG-B",serviceable_count=10)],obtainability_rows=[])["aggregation"]
        self.assertEqual(str(result["total_addressable_value"]),"300060.00")
        self.assertEqual(result["serviceability_aggregation_state"],"AGGREGATION_UNAVAILABLE")
    def test_no_rank_forecast_or_action(self):
        result=self.review(); self.assertEqual((result["ranked"],result["market_selected"],result["forecast_authorized"],result["action_authorized"]),(False,False,False,False))
    def test_approval_state_strict(self):
        with self.assertRaises(ValueError): self.review(approval_state="AUTO_APPROVED")
    def test_inputs_not_mutated(self):
        policy=self.policy(); original=copy.deepcopy(policy); self.review(policy=policy); self.assertEqual(policy,original)
    def test_deterministic_order(self):
        a=self.universe("SEG-A"); b=self.universe("SEG-B"); pa=self.price("SEG-A"); pb=self.price("SEG-B")
        first=self.review(universe_rows=[b,a],price_rows=[pb,pa],serviceability_rows=[],obtainability_rows=[])
        second=self.review(universe_rows=[a,b],price_rows=[pa,pb],serviceability_rows=[],obtainability_rows=[])
        self.assertEqual(first,second)
    def test_renderer_exact_and_boundary(self):
        rendered=render_review_output(self.review())
        self.assertTrue(rendered.startswith("```json\n{")); self.assertTrue(rendered.endswith(BOUNDARY)); self.assertEqual(rendered.count(BOUNDARY),2)
        parsed=json.loads(rendered.split("```json\n",1)[1].split("\n```",1)[0]); self.assertEqual(parsed["segment_results"][0]["total_addressable_scenario_value"],"250050.00")
    def test_renderer_rejects_nonobject(self):
        with self.assertRaises(ValueError): render_review_output([])
    def test_no_adequacy_labels_in_output(self):
        rendered=render_review_output(self.review()).casefold()
        for phrase in ("small cohort","large cohort","enough data","limited data","insufficient data"):
            self.assertNotIn(phrase,rendered)
    def test_cli_output_equals_renderer(self):
        document={"review_id":"REVIEW-ALPHA","policy":self.policy(),"evidence_rows":self.evidence(),"universe_rows":[self.universe()],"price_rows":[self.price()],"serviceability_rows":[self.service()],"obtainability_rows":[self.obtain()]}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"input.json"; path.write_text(json.dumps(document))
            output=io.StringIO()
            with redirect_stdout(output): main([str(path)])
        self.assertEqual(output.getvalue().rstrip("\n"),render_review_output(self.review()))


if __name__ == "__main__": unittest.main()
