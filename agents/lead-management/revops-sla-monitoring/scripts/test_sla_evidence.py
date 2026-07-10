#!/usr/bin/env python3
import json
import unittest
from copy import deepcopy
from decimal import Decimal

from sla_evidence import BOUNDARY, evaluate, reject_sensitive_fields, render_report_json, validate_evidence, validate_policy


class SlaEvidenceTests(unittest.TestCase):
    def policy(self, **overrides):
        value = {"policy_id":"SLA-1","version":"v2","purpose":"read-only SLA evidence review","start_event_type":"RECORD_ACCEPTED","qualifying_event_types":["HUMAN_CALL","HUMAN_EMAIL"],"clock_type":"CONTINUOUS","target_seconds":600,"timezone":"UTC","exclusion_policy_id":"EX-1","denominator_policy_id":"DEN-1","workforce_policy_id":"WORK-1","owner":"sla-policy-owner","reviewer":"sla-reviewer","approver":"named-approver","correction_path":"evidence-steward","prohibited_uses":["crm-write","workforce-action"]}
        value.update(overrides); return value

    def evidence(self):
        common={"extracted_at":"2026-07-10T12:00:00Z","as_of":"2026-07-10T11:59:59Z","policy_id":"SRC-1","access_scope":"pseudonymous-read-only"}
        return [
            {**common,"evidence_id":"E-1","source_id":"crm-snapshot","source_version":"s7"},
            {**common,"evidence_id":"E-CALL","source_id":"call-log","source_version":"v3"},
            {**common,"evidence_id":"E-EMAIL","source_id":"email-log","source_version":"v4"},
        ]

    def records(self):
        return [
            {"record_id":"REC-A","start_at":"2026-07-10T10:00:00Z","start_event_type":"RECORD_ACCEPTED","owner_id":"OWNER-X","evidence_ids":["E-1"]},
            {"record_id":"REC-B","start_at":"2026-07-10T10:00:00Z","start_event_type":"RECORD_ACCEPTED","owner_id":"OWNER-Y","evidence_ids":["E-1"]},
            {"record_id":"REC-C","start_at":"2026-07-10T11:55:00Z","start_event_type":"RECORD_ACCEPTED","owner_id":"OWNER-Z","evidence_ids":["E-1"]},
        ]

    def events(self):
        return [
            {"event_id":"EV-A","record_id":"REC-A","event_type":"HUMAN_CALL","occurred_at":"2026-07-10T10:08:00Z","created_at":"2026-07-10T10:09:00Z","association_evidence_id":"E-1","source_id":"call-log","source_version":"v3","evidence_id":"E-CALL"},
            {"event_id":"EV-B","record_id":"REC-B","event_type":"HUMAN_EMAIL","occurred_at":"2026-07-10T10:12:00Z","created_at":"2026-07-10T10:13:00Z","association_evidence_id":"E-1","source_id":"email-log","source_version":"v4","evidence_id":"E-EMAIL"},
        ]

    def report(self, **overrides):
        values = dict(review_id="REV-1", cutoff="2026-07-10T12:00:00Z", policy=self.policy(), evidence_rows=self.evidence(), record_rows=self.records(), event_rows=self.events())
        values.update(overrides); return evaluate(**values)

    def test_policy_valid(self): self.assertEqual(validate_policy(self.policy())["clock_type"], "CONTINUOUS")
    def test_policy_requires_unique_events(self):
        with self.assertRaises(ValueError): validate_policy(self.policy(qualifying_event_types=["HUMAN_CALL","HUMAN_CALL"]))
    def test_policy_rejects_float_target(self):
        with self.assertRaises(ValueError): validate_policy(self.policy(target_seconds=1.5))
    def test_continuous_clock_requires_utc(self):
        with self.assertRaises(ValueError): validate_policy(self.policy(timezone="America/New_York"))
    def test_sensitive_field_rejected(self):
        with self.assertRaises(ValueError): reject_sensitive_fields({"rep_email":"person@example.test"})
    def test_evidence_valid(self): self.assertEqual(validate_evidence(self.evidence())[0]["evidence_id"], "E-1")
    def test_duplicate_evidence_rejected(self):
        with self.assertRaises(ValueError): validate_evidence(self.evidence()*2)
    def test_offset_timestamp_accepted(self):
        rows=self.evidence(); rows[0]["as_of"]="2026-07-10T08:00:00-04:00"
        self.assertEqual(validate_evidence(rows)[0]["evidence_id"], "E-1")
    def test_naive_timestamp_rejected(self):
        rows=self.evidence(); rows[0]["as_of"]="2026-07-10T08:00:00"
        with self.assertRaises(ValueError): validate_evidence(rows)
    def test_met_breached_pending_states(self):
        result=self.report()
        self.assertEqual([row["state"] for row in result["results"]],["MET","BREACHED","PENDING"])
    def test_due_time_exact(self): self.assertEqual(self.report()["results"][0]["due_at"],"2026-07-10T10:10:00Z")
    def test_occurrence_not_creation_controls(self):
        events=self.events(); events[0]["occurred_at"]="2026-07-10T10:08:00Z"; events[0]["created_at"]="2026-07-10T10:30:00Z"
        self.assertEqual(self.report(event_rows=events)["results"][0]["state"],"MET")
    def test_unapproved_event_type_ignored(self):
        events=self.events(); events[0]["event_type"]="BACKGROUND_SYNC"
        self.assertEqual(self.report(event_rows=events)["results"][0]["state"],"BREACHED")
    def test_earliest_qualifying_event_selected(self):
        events=self.events()+[{**self.events()[0],"event_id":"EV-A2","occurred_at":"2026-07-10T10:09:00Z"}]
        self.assertEqual(self.report(event_rows=events)["results"][0]["stop_event"]["event_id"],"EV-A")
    def test_duplicate_event_rejected(self):
        with self.assertRaises(ValueError): self.report(event_rows=self.events()*2)
    def test_event_before_start_enters_conflict_queue(self):
        events=self.events(); events[0]["occurred_at"]="2026-07-10T09:59:00Z"
        result=self.report(event_rows=events)
        self.assertEqual(result["conflict_queue"][0]["reason_code"],"EVENT_BEFORE_START")
    def test_unregistered_event_evidence_enters_conflict_queue(self):
        events=self.events(); events[0]["evidence_id"]="E-X"
        self.assertEqual(self.report(event_rows=events)["conflict_queue"][0]["reason_code"],"EVENT_EVIDENCE_NOT_REGISTERED")
    def test_event_source_mismatch_enters_conflict_queue(self):
        events=self.events(); events[0]["source_version"]="v999"
        self.assertEqual(self.report(event_rows=events)["conflict_queue"][0]["reason_code"],"EVENT_SOURCE_MISMATCH")
    def test_event_after_cutoff_does_not_count(self):
        events=self.events(); events[0]["occurred_at"]="2026-07-10T12:01:00Z"; events[0]["created_at"]="2026-07-10T12:02:00Z"
        result=self.report(event_rows=events)
        self.assertEqual((result["results"][0]["state"],result["conflict_queue"][0]["reason_code"]),("BREACHED","EVENT_AFTER_CUTOFF"))
    def test_event_created_after_cutoff_does_not_count(self):
        events=self.events(); events[0]["created_at"]="2026-07-10T12:01:00Z"
        result=self.report(event_rows=events)
        self.assertEqual((result["results"][0]["state"],result["conflict_queue"][0]["reason_code"]),("BREACHED","EVENT_CREATED_AFTER_CUTOFF"))
    def test_unknown_event_record_visible(self):
        events=self.events()+[{**self.events()[0],"event_id":"EV-X","record_id":"REC-X"}]
        self.assertEqual(self.report(event_rows=events)["unknown_event_record_ids"],["REC-X"])
    def test_unregistered_record_evidence_source_required(self):
        rows=self.records(); rows[0]["evidence_ids"]=["E-X"]
        self.assertEqual(self.report(record_rows=rows)["results"][0]["state"],"SOURCE_REQUIRED")
    def test_start_type_mismatch_policy_required(self):
        rows=self.records(); rows[0]["start_event_type"]="CREATED"
        self.assertEqual(self.report(record_rows=rows)["results"][0]["state"],"POLICY_REQUIRED")
    def test_start_after_cutoff_conflicting(self):
        rows=self.records(); rows[0]["start_at"]="2026-07-10T13:00:00Z"
        self.assertEqual(self.report(record_rows=rows)["results"][0]["state"],"CONFLICTING")
    def test_exclusion_preserved(self):
        excluded=[{"record_id":"REC-C","reason_code":"TEST_RECORD","evidence_id":"E-1","policy_id":"EX-1"}]
        result=self.report(excluded_rows=excluded)
        self.assertEqual((result["results"][2]["state"],result["summary"]["excluded_count"]),("EXCLUDED",1))
    def test_unknown_exclusion_rejected(self):
        with self.assertRaises(ValueError): self.report(excluded_rows=[{"record_id":"REC-X","reason_code":"TEST","evidence_id":"E-1","policy_id":"EX-1"}])
    def test_unregistered_exclusion_evidence_not_applied(self):
        excluded=[{"record_id":"REC-C","reason_code":"TEST_RECORD","evidence_id":"E-X","policy_id":"EX-1"}]
        self.assertEqual(self.report(excluded_rows=excluded)["results"][2]["state"],"SOURCE_REQUIRED")
    def test_wrong_exclusion_policy_not_applied(self):
        excluded=[{"record_id":"REC-C","reason_code":"TEST_RECORD","evidence_id":"E-1","policy_id":"EX-X"}]
        self.assertEqual(self.report(excluded_rows=excluded)["results"][2]["state"],"POLICY_REQUIRED")
    def test_summary_denominator_excludes_pending(self):
        summary=self.report()["summary"]
        self.assertEqual((summary["resolved_denominator"],summary["met_rate"]),(2,Decimal("0.5")))
    def test_zero_denominator_rate_none(self):
        rows=[{"record_id":"REC-P","start_at":"2026-07-10T11:55:00Z","start_event_type":"RECORD_ACCEPTED","owner_id":"OWNER-P","evidence_ids":["E-1"]}]
        summary=self.report(record_rows=rows,event_rows=[])["summary"]
        self.assertEqual((summary["resolved_denominator"],summary["met_rate"]),(0,None))
    def test_calendar_receipt_required(self):
        self.assertEqual(self.report(policy=self.policy(clock_type="SUPPLIED_CALENDAR"))["results"][0]["state"],"POLICY_REQUIRED")
    def calendar_receipts(self):
        return [{"record_id":record,"due_at":"2026-07-10T10:10:00Z" if record!="REC-C" else "2026-07-10T12:05:00Z","calendar_id":"CAL-1","calendar_version":"v9","calculator_id":"calendar-engine","computed_at":"2026-07-10T09:00:00Z","evidence_id":"E-1"} for record in ("REC-A","REC-B","REC-C")]
    def test_calendar_receipt_used(self):
        result=self.report(policy=self.policy(clock_type="SUPPLIED_CALENDAR"),calendar_due_receipts=self.calendar_receipts())
        self.assertEqual(result["results"][0]["calendar_due_receipt"]["calendar_id"],"CAL-1")
    def test_duplicate_calendar_receipt_rejected(self):
        rows=self.calendar_receipts(); rows.append(deepcopy(rows[0]))
        with self.assertRaises(ValueError): self.report(policy=self.policy(clock_type="SUPPLIED_CALENDAR"),calendar_due_receipts=rows)
    def test_calendar_due_before_start_conflicting(self):
        rows=self.calendar_receipts(); rows[0]["due_at"]="2026-07-10T09:59:00Z"
        self.assertEqual(self.report(policy=self.policy(clock_type="SUPPLIED_CALENDAR"),calendar_due_receipts=rows)["results"][0]["state"],"CONFLICTING")
    def test_event_rows_must_be_list(self):
        with self.assertRaises(ValueError): self.report(event_rows={})
    def test_report_has_no_action(self):
        result=self.report()
        self.assertEqual((result["ranked"],result["action_authorized"],result["boundary"]),(False,False,BOUNDARY))
    def test_results_are_deterministic(self):
        first=self.report(record_rows=list(reversed(self.records())),event_rows=list(reversed(self.events())))
        second=self.report()
        self.assertEqual(first,second)
    def test_inputs_not_mutated(self):
        rows=self.records(); original=deepcopy(rows); self.report(record_rows=rows)
        self.assertEqual(rows,original)
    def test_renderer_preserves_decimal_and_keys(self):
        rendered=json.loads(render_report_json(self.report()))
        self.assertEqual(rendered["summary"]["met_rate"],"0.5")
        self.assertEqual(rendered["results"][0]["record_id"],"REC-A")
    def test_renderer_rejects_non_object(self):
        with self.assertRaises(ValueError): render_report_json([])
    def test_unsupported_approval_state_rejected(self):
        with self.assertRaises(ValueError): self.report(approval_state="AUTO_APPROVED")


if __name__ == "__main__": unittest.main()
