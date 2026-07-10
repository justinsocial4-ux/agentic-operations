#!/usr/bin/env python3
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from segment_evidence import BOUNDARY, main, render_review_output, review_segments, validate_policy


class SegmentEvidenceTests(unittest.TestCase):
    def policy(self, **changes):
        value = {"policy_id":"POLICY-IMS-03","version":"VERSION-IMS-03","purpose":"read-only segment outcome evidence comparison","cutoff":"2026-07-10T12:00:00Z","max_age_days":500,"source_evidence_policy_id":"SOURCE-POLICY","source_schema_id":"CRM-SCHEMA","source_schema_version":"SCHEMA-V1","outcome_mapping_id":"OUTCOME-MAP-V1","outcome_event_rule":"APPROVED_OUTCOME_OCCURRENCE","opportunity_identity_rule":"STABLE_OPPORTUNITY_ID_ONE_REVISION","segment_definition_id":"SEGMENT-DEFINITION-V1","segment_definition_version":"SEGMENT-V1","membership_mode":"EXCLUSIVE","period_timezone":"UTC","current_period_id":"PERIOD-CURRENT","comparison_period_id":"PERIOD-PRIOR","currency":"USD","amount_basis":"BOOKED_CONTRACT_VALUE","duration_begin_event":"APPROVED_QUALIFIED_AT","duration_stop_event":"APPROVED_OUTCOME_AT","comparison_policy_id":"COMPARISON-V1","rate_decimal_places":2,"workforce_policy_id":"WORKFORCE-NO-USE","owner_role":"POLICY-OWNER","reviewer_role":"REVIEWER-ROLE","approver_role":"APPROVER-ROLE","correction_path":"EVIDENCE-STEWARD","prohibited_uses":["ranking","forecast","crm-write","workforce-action"]}
        value.update(changes); return value

    def evidence(self):
        common={"source_id":"crm-snapshot","source_version":"SNAPSHOT-V1","schema_id":"CRM-SCHEMA","schema_version":"SCHEMA-V1","as_of":"2026-07-01T00:00:00Z","extracted_at":"2026-07-02T00:00:00Z","access_scope":"aggregate-read-only","policy_id":"SOURCE-POLICY"}
        return [{**common,"evidence_id":key} for key in ("E-DEFINITION","E-RECORD","E-MEMBERSHIP")]

    def periods(self):
        return [
            {"period_id":"PERIOD-PRIOR","label":"Approved comparison period","begin":"2026-01-01T00:00:00Z","end":"2026-01-31T00:00:00Z","evidence_id":"E-DEFINITION"},
            {"period_id":"PERIOD-CURRENT","label":"Approved current period","begin":"2026-02-01T00:00:00Z","end":"2026-03-03T00:00:00Z","evidence_id":"E-DEFINITION"},
        ]

    def segments(self, two=False):
        rows=[{"segment_id":"SEG-A","label":"Approved segment A","definition_receipt_id":"SEG-RECEIPT-A","evidence_id":"E-DEFINITION"}]
        if two: rows.append({"segment_id":"SEG-B","label":"Approved segment B","definition_receipt_id":"SEG-RECEIPT-B","evidence_id":"E-DEFINITION"})
        return rows

    def record(self, opportunity_id="OPP-1", period_id="PERIOD-PRIOR", outcome="WON", **changes):
        outcome_at="2026-01-15T00:00:00Z" if period_id=="PERIOD-PRIOR" else "2026-02-15T00:00:00Z"
        value={"opportunity_id":opportunity_id,"revision_id":"REV-1","period_id":period_id,"record_state":"AVAILABLE","outcome":outcome,"outcome_at":outcome_at,"segment_ids":["SEG-A"],"membership_evidence_id":"E-MEMBERSHIP","evidence_id":"E-RECORD","amount_state":"AVAILABLE","amount":"100.00","currency":"USD","amount_basis":"BOOKED_CONTRACT_VALUE","duration_state":"AVAILABLE","duration_begin_at":"2026-01-01T00:00:00Z" if period_id=="PERIOD-PRIOR" else "2026-02-01T00:00:00Z","duration_stop_at":"2026-01-01T00:01:40Z" if period_id=="PERIOD-PRIOR" else "2026-02-01T00:02:00Z"}
        value.update(changes); return value

    def records(self):
        return [
            self.record("OPP-P-W","PERIOD-PRIOR","WON",amount="100.00"),
            self.record("OPP-P-L","PERIOD-PRIOR","LOST",amount_state="UNAVAILABLE",amount=None,currency=None,amount_basis=None,duration_stop_at="2026-01-01T00:03:20Z"),
            self.record("OPP-C-W","PERIOD-CURRENT","WON",amount="150.00"),
            self.record("OPP-C-L","PERIOD-CURRENT","LOST",amount_state="UNAVAILABLE",amount=None,currency=None,amount_basis=None,duration_state="UNAVAILABLE",duration_begin_at=None,duration_stop_at=None),
        ]

    def document(self, **changes):
        value={"review_id":"REVIEW-IMS-03","policy":self.policy(),"evidence_rows":self.evidence(),"period_rows":self.periods(),"segment_rows":self.segments(),"opportunity_rows":self.records(),"approval_state":"APPROVAL_REQUIRED"}
        value.update(changes); return value

    def review(self, **changes): return review_segments(**self.document(**changes))

    def metric(self, review, period_id, segment_id="SEG-A"):
        return next(row for row in review["metric_results"] if row["segment_id"]==segment_id and row["period_id"]==period_id)

    def test_policy_valid(self): self.assertEqual(validate_policy(self.policy())["membership_mode"],"EXCLUSIVE")
    def test_policy_rejects_unknown(self):
        with self.assertRaises(ValueError): validate_policy({**self.policy(),"drift_threshold":10})
    def test_policy_rejects_bad_membership_mode(self):
        with self.assertRaises(ValueError): validate_policy(self.policy(membership_mode="FUZZY"))
    def test_exact_population_and_rate(self):
        row=self.metric(self.review(),"PERIOD-PRIOR"); self.assertEqual((row["closed_outcome_count"],row["won_count"],row["lost_count"],row["win_rate_pct"]),(2,1,1,"50.00"))
    def test_money_independent_of_lost_amount(self):
        row=self.metric(self.review(),"PERIOD-PRIOR"); self.assertEqual((row["money_state"],row["won_amount_total"],row["won_amount_median"]),("CALCULATED","100.00","100.00"))
    def test_duration_missing_does_not_erase_counts_or_money(self):
        row=self.metric(self.review(),"PERIOD-CURRENT"); self.assertEqual((row["population_state"],row["money_state"],row["duration_state"]),("CALCULATED","CALCULATED","SOURCE_REQUIRED"))
    def test_exact_comparison(self):
        row=self.review()["comparisons"][0]; self.assertEqual((row["win_rate_delta_pp"],row["won_amount_total_delta"],row["duration_comparison_state"]),("0.00","50.00","COMPARISON_UNAVAILABLE"))
    def test_zero_denominator(self):
        row=self.metric(self.review(opportunity_rows=[]),"PERIOD-CURRENT"); self.assertEqual((row["closed_outcome_count"],row["win_rate_pct"],row["population_reason_code"]),(0,None,"ZERO_DENOMINATOR"))
    def test_missing_won_amount(self):
        rows=self.records(); rows[2].update(amount_state="UNAVAILABLE",amount=None,currency=None,amount_basis=None)
        self.assertEqual(self.metric(self.review(opportunity_rows=rows),"PERIOD-CURRENT")["money_state"],"SOURCE_REQUIRED")
    def test_float_amount_rejected(self):
        rows=self.records(); rows[2]["amount"]=150.0
        with self.assertRaises(ValueError): self.review(opportunity_rows=rows)
    def test_currency_mismatch_conflicts_money_only(self):
        rows=self.records(); rows[2]["currency"]="EUR"; result=self.metric(self.review(opportunity_rows=rows),"PERIOD-CURRENT")
        self.assertEqual((result["population_state"],result["money_state"]),("CALCULATED","SOURCE_REQUIRED"))
    def test_negative_duration_conflicts_duration_only(self):
        rows=self.records(); rows[2]["duration_stop_at"]="2026-01-01T00:00:00Z"; result=self.metric(self.review(opportunity_rows=rows),"PERIOD-CURRENT")
        self.assertEqual((result["closed_outcome_count"],result["duration_state"]),(2,"SOURCE_REQUIRED"))
    def test_exclusive_membership_violation(self):
        rows=self.records(); rows[0]["segment_ids"]=["SEG-A","SEG-B"]; result=self.review(segment_rows=self.segments(True),opportunity_rows=rows)
        self.assertIn("EXCLUSIVE_MEMBERSHIP_VIOLATION",[row["reason_code"] for row in result["exception_queue"]])
    def test_overlapping_membership_is_per_segment_only(self):
        rows=[self.record(segment_ids=["SEG-A","SEG-B"])]
        result=self.review(policy=self.policy(membership_mode="OVERLAPPING"),segment_rows=self.segments(True),opportunity_rows=rows)
        self.assertEqual(result["membership_interpretation"],"PER_SEGMENT_ONLY_NO_CROSS_SEGMENT_TOTALS")
        self.assertEqual(self.metric(result,"PERIOD-PRIOR","SEG-B")["closed_outcome_count"],1)
    def test_unknown_segment_exception(self):
        rows=self.records(); rows[0]["segment_ids"]=["SEG-X"]
        self.assertIn("SEGMENT_MEMBERSHIP_INVALID",[row["reason_code"] for row in self.review(opportunity_rows=rows)["exception_queue"]])
    def test_duplicate_opportunity_excluded(self):
        rows=self.records()+[copy.deepcopy(self.records()[0])]; result=self.review(opportunity_rows=rows)
        self.assertEqual(self.metric(result,"PERIOD-PRIOR")["closed_outcome_count"],1)
        self.assertIn("DUPLICATE_OPPORTUNITY_ID",[row["reason_code"] for row in result["exception_queue"]])
    def test_out_of_period_exception(self):
        rows=self.records(); rows[0]["outcome_at"]="2026-04-01T00:00:00Z"
        self.assertIn("OUTCOME_OUTSIDE_PERIOD",[row["reason_code"] for row in self.review(opportunity_rows=rows)["exception_queue"]])
    def test_unknown_record_preserved(self):
        rows=self.records(); rows[0].update(record_state="UNKNOWN",outcome=None,outcome_at=None)
        self.assertIn("RECORD_NOT_AVAILABLE",[row["reason_code"] for row in self.review(opportunity_rows=rows)["exception_queue"]])
    def test_unregistered_record_evidence(self):
        rows=self.records(); rows[0]["evidence_id"]="E-X"
        self.assertIn("EVIDENCE_NOT_AVAILABLE",[row["reason_code"] for row in self.review(opportunity_rows=rows)["exception_queue"]])
    def test_stale_record_evidence(self):
        evidence=self.evidence(); evidence[1]["as_of"]="2020-01-01T00:00:00Z"; evidence[1]["extracted_at"]="2020-01-02T00:00:00Z"
        self.assertEqual(self.review(evidence_rows=evidence)["exception_queue"][0]["state"],"STALE")
    def test_future_record_evidence(self):
        evidence=self.evidence(); evidence[1]["as_of"]="2026-08-01T00:00:00Z"; evidence[1]["extracted_at"]="2026-08-02T00:00:00Z"
        self.assertEqual(self.review(evidence_rows=evidence)["exception_queue"][0]["state"],"CONFLICTING")
    def test_schema_mismatch(self):
        evidence=self.evidence(); evidence[1]["schema_version"]="WRONG"
        self.assertEqual(self.review(evidence_rows=evidence)["exception_queue"][0]["state"],"POLICY_REQUIRED")
    def test_source_policy_mismatch(self):
        evidence=self.evidence(); evidence[1]["policy_id"]="WRONG"
        self.assertEqual(self.review(evidence_rows=evidence)["exception_queue"][0]["state"],"POLICY_REQUIRED")
    def test_extraction_before_asof_rejected(self):
        evidence=self.evidence(); evidence[1]["extracted_at"]="2026-06-01T00:00:00Z"
        with self.assertRaises(ValueError): self.review(evidence_rows=evidence)
    def test_definition_evidence_required(self):
        periods=self.periods(); periods[0]["evidence_id"]="E-X"
        with self.assertRaises(ValueError): self.review(period_rows=periods)
    def test_period_overlap_rejected(self):
        periods=self.periods(); periods[1]["begin"]="2026-01-20T00:00:00Z"
        with self.assertRaises(ValueError): self.review(period_rows=periods)
    def test_current_period_must_follow_comparison(self):
        policy=self.policy(current_period_id="PERIOD-PRIOR",comparison_period_id="PERIOD-CURRENT")
        with self.assertRaises(ValueError): self.review(policy=policy)
    def test_period_beyond_cutoff_rejected(self):
        periods=self.periods(); periods[1].update(begin="2026-07-11T00:00:00Z",end="2026-08-10T00:00:00Z")
        with self.assertRaises(ValueError): self.review(period_rows=periods)
    def test_period_length_mismatch_blocks_comparison(self):
        periods=self.periods(); periods[1]["end"]="2026-03-02T00:00:00Z"; result=self.review(period_rows=periods)
        self.assertEqual(result["comparisons"][0]["comparison_state"],"COMPARISON_UNAVAILABLE")
    def test_win_rate_rounding_policy(self):
        rows=[self.record("W","PERIOD-PRIOR","WON"),self.record("L1","PERIOD-PRIOR","LOST"),self.record("L2","PERIOD-PRIOR","LOST")]
        self.assertEqual(self.metric(self.review(opportunity_rows=rows),"PERIOD-PRIOR")["win_rate_pct"],"33.33")
    def test_even_duration_median_uses_decimal(self):
        row=self.metric(self.review(),"PERIOD-PRIOR"); self.assertEqual(row["median_duration_seconds"],"150")
    def test_no_rank_forecast_alert_or_action(self):
        result=self.review(); self.assertEqual((result["ranked"],result["segment_selected"],result["forecast_authorized"],result["alert_authorized"],result["action_authorized"]),(False,False,False,False,False))
    def test_population_reconciliation_counts_unique_records(self):
        self.assertEqual(self.review()["population_reconciliation"],{"submitted_record_count":4,"included_unique_opportunity_count":4,"exception_opportunity_count":1})
    def test_sensitive_rep_field_rejected(self):
        rows=self.records(); rows[0]["rep_id"]="REP-1"
        with self.assertRaises(ValueError): self.review(opportunity_rows=rows)
    def test_unknown_win_rate_field_rejected(self):
        rows=self.records(); rows[0]["win_rate"]="0.5"
        with self.assertRaises(ValueError): self.review(opportunity_rows=rows)
    def test_approval_state_strict(self):
        with self.assertRaises(ValueError): self.review(approval_state="AUTO_APPROVED")
    def test_deterministic_record_order(self):
        self.assertEqual(self.review(),self.review(opportunity_rows=list(reversed(self.records()))))
    def test_inputs_not_mutated(self):
        document=self.document(); original=copy.deepcopy(document); review_segments(**document); self.assertEqual(document,original)
    def test_renderer_exact_and_boundary(self):
        rendered=render_review_output(self.review()); self.assertEqual(rendered[:9],"```json\n{"); self.assertTrue(rendered.endswith(BOUNDARY)); self.assertEqual(rendered.count(BOUNDARY),2)
    def test_no_adequacy_labels(self):
        rendered=render_review_output(self.review()).casefold()
        for phrase in ("small sample","large sample","enough data","limited data","insufficient data"):
            self.assertNotIn(phrase,rendered)
    def test_cli_equals_renderer(self):
        document=self.document()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"input.json"; path.write_text(json.dumps(document)); output=io.StringIO()
            with redirect_stdout(output): main([str(path)])
        self.assertEqual(output.getvalue().rstrip("\n"),render_review_output(self.review()))


if __name__ == "__main__": unittest.main()
