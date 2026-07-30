#!/usr/bin/env python3
import unittest
from decimal import Decimal

from event_review import action_gate, coverage, evaluate_lane, normalize


class EventReviewTests(unittest.TestCase):
    def setUp(self):
        self.rules = [
            {"rule_id": "r1", "lane_id": "review_now", "priority": 10, "response_hours": 4, "all_signals": ["attended", "explicit_meeting_request"]},
            {"rule_id": "r2", "lane_id": "standard_review", "priority": 20, "response_hours": 24, "all_signals": ["attended", "staff_conversation_recorded"]},
            {"rule_id": "r3", "lane_id": "evidence_review", "priority": 30, "response_hours": 48, "all_signals": ["attended"]},
        ]
        self.anchor = "2026-07-01T14:00:00+00:00"

    def test_normalize(self): self.assertEqual(normalize(" Explicit   Request "), "explicit request")
    def test_highest_priority_exact_rule(self):
        result = evaluate_lane(["ATTENDED", "EXPLICIT_MEETING_REQUEST"], self.rules, self.anchor)
        self.assertEqual((result["selected"]["rule_id"], result["selected"]["due_at"]), ("r1", "2026-07-01T18:00:00+00:00"))
    def test_conversation_rule(self):
        result = evaluate_lane(["attended", "staff_conversation_recorded"], self.rules, self.anchor)
        self.assertEqual(result["selected"]["lane_id"], "standard_review")
    def test_attendance_only_rule(self):
        self.assertEqual(evaluate_lane(["attended"], self.rules, self.anchor)["selected"]["lane_id"], "evidence_review")
    def test_no_policy_match(self):
        self.assertEqual(evaluate_lane(["registered"], self.rules, self.anchor)["status"], "NO_POLICY_MATCH")
    def test_optional_any_signal(self):
        rule = [{"rule_id": "r", "lane_id": "review", "priority": 1, "response_hours": 0, "all_signals": ["attended"], "any_signals": ["reply", "request"]}]
        self.assertEqual(evaluate_lane(["attended", "reply"], rule, self.anchor)["status"], "LANE_PREVIEW")
    def test_missing_any_signal_no_match(self):
        rule = [{"rule_id": "r", "lane_id": "review", "priority": 1, "response_hours": 0, "all_signals": ["attended"], "any_signals": ["reply"]}]
        self.assertEqual(evaluate_lane(["attended"], rule, self.anchor)["status"], "NO_POLICY_MATCH")
    def test_duplicate_signals_fail(self):
        with self.assertRaises(ValueError): evaluate_lane(["attended", "ATTENDED"], self.rules, self.anchor)
    def test_nontext_signal_fails(self):
        with self.assertRaises(ValueError): evaluate_lane(["attended", 1], self.rules, self.anchor)
    def test_duplicate_rule_id_fails(self):
        with self.assertRaises(ValueError): evaluate_lane(["attended"], self.rules + [dict(self.rules[0])], self.anchor)
    def test_duplicate_priority_fails(self):
        bad = [dict(self.rules[0]), dict(self.rules[1], priority=10)]
        with self.assertRaises(ValueError): evaluate_lane(["attended"], bad, self.anchor)
    def test_negative_hours_fail(self):
        with self.assertRaises(ValueError): evaluate_lane(["attended"], [dict(self.rules[0], response_hours=-1)], self.anchor)
    def test_boolean_hours_fail(self):
        with self.assertRaises(ValueError): evaluate_lane(["attended"], [dict(self.rules[0], response_hours=True)], self.anchor)
    def test_naive_timestamp_fails(self):
        with self.assertRaises(ValueError): evaluate_lane(["attended"], self.rules, "2026-07-01T14:00:00")
    def test_no_lane_means_no_action(self): self.assertEqual(action_gate("NO_POLICY_MATCH", "exact", "eligible", "none", "owner-1", True), "NO_POLICY_MATCH")
    def test_identity_review(self): self.assertEqual(action_gate("LANE_PREVIEW", "conflict", "eligible", "none", "owner-1", True), "IDENTITY_REVIEW")
    def test_suppression_blocks(self): self.assertEqual(action_gate("LANE_PREVIEW", "exact", "suppressed", "none", "owner-1", True), "CONTACT_BLOCKED")
    def test_unknown_contactability(self): self.assertEqual(action_gate("LANE_PREVIEW", "exact", "unknown", "none", "owner-1", True), "CONTACTABILITY_UNKNOWN")
    def test_active_enrollment_review(self): self.assertEqual(action_gate("LANE_PREVIEW", "exact", "eligible", "present", "owner-1", True), "ENROLLMENT_REVIEW")
    def test_unknown_enrollment(self): self.assertEqual(action_gate("LANE_PREVIEW", "exact", "eligible", "unknown", "owner-1", True), "ENROLLMENT_UNKNOWN")
    def test_owner_required(self): self.assertEqual(action_gate("LANE_PREVIEW", "exact", "eligible", "none", None, True), "OWNER_REQUIRED")
    def test_nontext_owner_fails(self):
        with self.assertRaises(ValueError): action_gate("LANE_PREVIEW", "exact", "eligible", "none", 7, True)
    def test_approval_required(self): self.assertEqual(action_gate("LANE_PREVIEW", "exact", "eligible", "none", "owner-1", False), "APPROVAL_REQUIRED")
    def test_preview_eligible_is_still_preview(self): self.assertEqual(action_gate("LANE_PREVIEW", "exact", "eligible", "none", "owner-1", True), "PREVIEW_ELIGIBLE")
    def test_bad_approval_fails(self):
        with self.assertRaises(ValueError): action_gate("LANE_PREVIEW", "exact", "eligible", "none", "owner-1", "yes")
    def test_coverage(self): self.assertEqual(coverage(3, 4), Decimal("0.75"))
    def test_zero_coverage_unknown(self): self.assertIsNone(coverage(0, 0))
    def test_bad_coverage_fails(self):
        with self.assertRaises(ValueError): coverage(5, 4)


if __name__ == "__main__":
    unittest.main()
