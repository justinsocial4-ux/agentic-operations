#!/usr/bin/env python3
"""Adversarial tests for the coaching-record evidence helper."""

from __future__ import annotations

import copy
import json
import unittest

from coaching_record_evidence import (
    LANE_IDS,
    REQUIRED_PROHIBITIONS,
    render_review_output,
    review_coaching_records,
)


def fixture() -> dict:
    lanes = [
        {"lane_id": lane_id, "state": "present", "receipt_id": f"receipt-{lane_id}"}
        for lane_id in sorted(LANE_IDS)
    ]
    record = {
        "record_id": "record-alpha",
        "anonymous_subject_id": "anonymous-worker-alpha",
        "anonymous_coach_id": "anonymous-coach-alpha",
        "rule_id": "rule-record-evidence",
        "source_id": "source-coaching-export",
        "source_version": "version-one",
        "source_kind": "customer-authored-pseudonymous-coaching-record",
        "schema_id": "schema-coaching-record",
        "schema_version": "version-one",
        "authorization_receipt_id": "authorization-coaching-source",
        "observation_receipt_id": "observation-alpha",
        "observed_at": "2026-07-10T10:00:00Z",
        "captured_at": "2026-07-10T11:00:00Z",
        "recipient_role_ids": ["role-authorized-reviewer"],
        "retention_rule_id": "retention-rule-alpha",
        "evidence_lanes": lanes,
    }
    for lane in record["evidence_lanes"]:
        if lane["lane_id"] == "source-observation":
            lane["receipt_id"] = "observation-alpha"
    return {
        "review_id": "review-alpha",
        "policy": {
            "policy_id": "policy-coaching-evidence",
            "policy_version": "version-one",
            "owner_role_id": "role-policy-owner",
            "human_reviewer_role_id": "role-human-reviewer",
            "effective_at": "2026-07-01T00:00:00Z",
            "expires_at": "2026-12-31T23:59:59Z",
            "cutoff_at": "2026-07-11T12:00:00Z",
            "timezone": "America/Guayaquil",
            "approved_purpose": "pseudonymous_coaching_record_evidence_review",
            "workforce_review_receipt_id": "receipt-workforce-review",
            "privacy_review_receipt_id": "receipt-privacy-review",
            "worker_notice_program_receipt_id": "receipt-worker-notice-program",
            "worker_access_path_receipt_id": "receipt-worker-access-path",
            "worker_response_path_receipt_id": "receipt-worker-response-path",
            "correction_path_receipt_id": "receipt-correction-path",
            "appeal_path_receipt_id": "receipt-appeal-path",
            "recipient_policy_receipt_id": "receipt-recipient-policy",
            "retention_policy_receipt_id": "receipt-retention-policy",
            "retention_rule_id": "retention-rule-alpha",
            "allowed_recipient_role_ids": ["role-authorized-reviewer"],
            "prohibited_uses": sorted(REQUIRED_PROHIBITIONS),
            "evidence_rule": {
                "rule_id": "rule-record-evidence",
                "required_lane_ids": sorted(LANE_IDS),
                "matched_state": "RULE_MATCHED",
            },
            "source_bindings": [{
                "source_id": "source-coaching-export",
                "source_version": "version-one",
                "source_kind": "customer-authored-pseudonymous-coaching-record",
                "schema_id": "schema-coaching-record",
                "schema_version": "version-one",
                "authorization_receipt_id": "authorization-coaching-source",
                "authorization_effective_at": "2026-07-01T00:00:00Z",
                "authorization_expires_at": "2026-12-31T23:59:59Z",
            }],
        },
        "population": {
            "population_receipt_id": "population-alpha",
            "complete": True,
            "record_ids": ["record-alpha"],
            "observed_at": "2026-07-10T12:00:00Z",
            "captured_at": "2026-07-10T13:00:00Z",
        },
        "records": [record],
    }


class CoachingRecordEvidenceTests(unittest.TestCase):
    def assert_invalid(self, mutate) -> None:
        doc = fixture()
        mutate(doc)
        with self.assertRaises(ValueError):
            review_coaching_records(doc)

    def test_happy_path(self):
        result = review_coaching_records(fixture())
        self.assertEqual(result["records"][0]["evidence_state"], "RULE_MATCHED")
        self.assertEqual(result["state_summary"], [{"state": "RULE_MATCHED", "record_count": 1}])
        self.assertFalse(result["coaching_authorized"])
        self.assertFalse(result["worker_judgment_authorized"])
        self.assertFalse(result["action_authorized"])

    def test_render_is_deterministic_and_exact(self):
        result = review_coaching_records(fixture())
        first = render_review_output(result)
        second = render_review_output(result)
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("{"))
        self.assertTrue(first.endswith("}\n\n"))
        self.assertEqual(json.loads(first), result)

    def test_missing_lane_state(self):
        doc = fixture()
        doc["records"][0]["evidence_lanes"][0].update(state="missing", receipt_id=None)
        self.assertEqual(review_coaching_records(doc)["records"][0]["evidence_state"], "EVIDENCE_MISSING")

    def test_conflict_precedes_missing(self):
        doc = fixture()
        doc["records"][0]["evidence_lanes"][0].update(state="missing", receipt_id=None)
        doc["records"][0]["evidence_lanes"][1].update(state="conflicting", receipt_id=None)
        self.assertEqual(review_coaching_records(doc)["records"][0]["evidence_state"], "EVIDENCE_CONFLICT")

    def test_unauthorized_precedes_conflict(self):
        doc = fixture()
        doc["records"][0]["evidence_lanes"][0].update(state="conflicting", receipt_id=None)
        doc["records"][0]["evidence_lanes"][1].update(state="unauthorized", receipt_id=None)
        self.assertEqual(review_coaching_records(doc)["records"][0]["evidence_state"], "UNAUTHORIZED")

    def test_suppressed_state(self):
        doc = fixture()
        doc["records"][0]["evidence_lanes"][0].update(state="suppressed", receipt_id=None)
        self.assertEqual(review_coaching_records(doc)["records"][0]["evidence_state"], "SUPPRESSED")

    def test_unknown_root_key_rejected(self):
        self.assert_invalid(lambda d: d.update({"notes": "forbidden"}))

    def test_unknown_record_key_rejected(self):
        self.assert_invalid(lambda d: d["records"][0].update({"win_rate": 0.5}))

    def test_direct_worker_name_rejected(self):
        self.assert_invalid(lambda d: d["records"][0].update({"worker_name": "Person"}))

    def test_subject_prefix_required(self):
        self.assert_invalid(lambda d: d["records"][0].update(anonymous_subject_id="worker-alpha"))

    def test_coach_prefix_required(self):
        self.assert_invalid(lambda d: d["records"][0].update(anonymous_coach_id="coach-alpha"))

    def test_complete_population_required(self):
        self.assert_invalid(lambda d: d["population"].update(complete=False))

    def test_empty_population_rejected(self):
        self.assert_invalid(lambda d: d["population"].update(record_ids=[]))

    def test_duplicate_population_id_rejected(self):
        self.assert_invalid(lambda d: d["population"].update(record_ids=["record-alpha", "record-alpha"]))

    def test_extra_record_rejected(self):
        def mutate(d):
            extra = copy.deepcopy(d["records"][0])
            extra["record_id"] = "record-beta"
            d["records"].append(extra)
        self.assert_invalid(mutate)

    def test_missing_declared_record_rejected(self):
        self.assert_invalid(lambda d: d["population"]["record_ids"].append("record-beta"))

    def test_duplicate_record_rejected(self):
        self.assert_invalid(lambda d: d["records"].append(copy.deepcopy(d["records"][0])))

    def test_wrong_rule_rejected(self):
        self.assert_invalid(lambda d: d["records"][0].update(rule_id="rule-other"))

    def test_missing_required_lane_rejected(self):
        self.assert_invalid(lambda d: d["records"][0]["evidence_lanes"].pop())

    def test_duplicate_lane_rejected(self):
        self.assert_invalid(lambda d: d["records"][0]["evidence_lanes"].append(copy.deepcopy(d["records"][0]["evidence_lanes"][0])))

    def test_unknown_lane_rejected(self):
        self.assert_invalid(lambda d: d["records"][0]["evidence_lanes"][0].update(lane_id="performance"))

    def test_unknown_lane_state_rejected(self):
        self.assert_invalid(lambda d: d["records"][0]["evidence_lanes"][0].update(state="good"))

    def test_present_lane_requires_receipt(self):
        self.assert_invalid(lambda d: d["records"][0]["evidence_lanes"][0].update(receipt_id=None))

    def test_unresolved_lane_forbids_receipt(self):
        self.assert_invalid(lambda d: d["records"][0]["evidence_lanes"][0].update(state="missing"))

    def test_missing_prohibition_rejected(self):
        self.assert_invalid(lambda d: d["policy"]["prohibited_uses"].remove("worker-ranking"))

    def test_wrong_purpose_rejected(self):
        self.assert_invalid(lambda d: d["policy"].update(approved_purpose="coaching-generation"))

    def test_expired_policy_rejected(self):
        self.assert_invalid(lambda d: d["policy"].update(expires_at="2026-07-10T00:00:00Z"))

    def test_invalid_timezone_rejected(self):
        self.assert_invalid(lambda d: d["policy"].update(timezone="Mars/Olympus"))

    def test_missing_governance_receipt_rejected(self):
        self.assert_invalid(lambda d: d["policy"].update(privacy_review_receipt_id=None))

    def test_governance_receipts_must_be_separate(self):
        self.assert_invalid(lambda d: d["policy"].update(privacy_review_receipt_id=d["policy"]["workforce_review_receipt_id"]))

    def test_rule_must_require_all_lanes(self):
        self.assert_invalid(lambda d: d["policy"]["evidence_rule"]["required_lane_ids"].pop())

    def test_wrong_matched_state_rejected(self):
        self.assert_invalid(lambda d: d["policy"]["evidence_rule"].update(matched_state="COMPLETE"))

    def test_unapproved_source_rejected(self):
        self.assert_invalid(lambda d: d["records"][0].update(source_id="source-other"))

    def test_source_schema_conflict_rejected(self):
        self.assert_invalid(lambda d: d["records"][0].update(schema_id="schema-other"))

    def test_source_authorization_conflict_rejected(self):
        self.assert_invalid(lambda d: d["records"][0].update(authorization_receipt_id="authorization-other"))

    def test_observation_before_authorization_rejected(self):
        self.assert_invalid(lambda d: d["records"][0].update(observed_at="2026-06-30T10:00:00Z"))

    def test_observation_before_policy_rejected(self):
        self.assert_invalid(lambda d: d["policy"].update(effective_at="2026-07-10T10:30:00Z"))

    def test_capture_before_observation_rejected(self):
        self.assert_invalid(lambda d: d["records"][0].update(captured_at="2026-07-10T09:00:00Z"))

    def test_future_population_rejected(self):
        self.assert_invalid(lambda d: d["population"].update(captured_at="2026-07-12T13:00:00Z"))

    def test_unapproved_recipient_rejected(self):
        self.assert_invalid(lambda d: d["records"][0].update(recipient_role_ids=["role-sales-manager"]))

    def test_empty_recipient_list_rejected(self):
        self.assert_invalid(lambda d: d["records"][0].update(recipient_role_ids=[]))

    def test_retention_rule_must_match_policy(self):
        self.assert_invalid(lambda d: d["records"][0].update(retention_rule_id="retention-rule-other"))

    def test_lane_receipts_must_be_separate(self):
        def mutate(d):
            d["records"][0]["evidence_lanes"][1]["receipt_id"] = d["records"][0]["evidence_lanes"][0]["receipt_id"]
        self.assert_invalid(mutate)

    def test_source_lane_binds_observation_receipt(self):
        def mutate(d):
            for lane in d["records"][0]["evidence_lanes"]:
                if lane["lane_id"] == "source-observation":
                    lane["receipt_id"] = "observation-other"
        self.assert_invalid(mutate)

    def test_output_has_no_forbidden_inference_keys(self):
        rendered = render_review_output(review_coaching_records(fixture())).lower()
        for token in ('"recommendation"', '"score"', '"rank"', '"performance"', '"sentiment"', '"win_rate"'):
            self.assertNotIn(token, rendered)

    def test_two_record_summary_counts_once(self):
        doc = fixture()
        second = copy.deepcopy(doc["records"][0])
        second["record_id"] = "record-beta"
        second["anonymous_subject_id"] = "anonymous-worker-beta"
        second["observation_receipt_id"] = "observation-beta"
        for lane in second["evidence_lanes"]:
            if lane["lane_id"] == "source-observation":
                lane["receipt_id"] = "observation-beta"
        second["evidence_lanes"][0].update(state="missing", receipt_id=None)
        doc["records"].append(second)
        doc["population"]["record_ids"].append("record-beta")
        result = review_coaching_records(doc)
        self.assertEqual(result["state_summary"], [
            {"state": "EVIDENCE_MISSING", "record_count": 1},
            {"state": "RULE_MATCHED", "record_count": 1},
        ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
