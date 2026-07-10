#!/usr/bin/env python3
import unittest
from decimal import Decimal

from onboarding_metrics import coverage, milestone_state, summarize_states


class OnboardingMetricsTests(unittest.TestCase):
    def test_due_date_and_on_time(self):
        self.assertEqual(milestone_state("2026-06-01", "2026-06-20", 5, "2026-06-06"), {"due_date": "2026-06-06", "completion_date": "2026-06-06", "delta_days": 0, "state": "COMPLETED_ON_TIME"})
    def test_early_completion(self): self.assertEqual(milestone_state("2026-06-01", "2026-06-20", 5, "2026-06-05")["delta_days"], -1)
    def test_late_completion(self):
        result = milestone_state("2026-06-01", "2026-06-20", 7, "2026-06-11")
        self.assertEqual((result["due_date"], result["delta_days"], result["state"]), ("2026-06-08", 3, "COMPLETED_LATE"))
    def test_pending(self):
        result = milestone_state("2026-06-01", "2026-06-20", 21)
        self.assertEqual((result["due_date"], result["delta_days"], result["state"]), ("2026-06-22", -2, "PENDING"))
    def test_due_today_pending(self): self.assertEqual(milestone_state("2026-06-01", "2026-06-06", 5)["state"], "PENDING")
    def test_due_not_recorded(self):
        result = milestone_state("2026-06-01", "2026-06-20", 14)
        self.assertEqual((result["due_date"], result["delta_days"], result["state"]), ("2026-06-15", 5, "DUE_NOT_RECORDED"))
    def test_unknown_overrides_calendar(self): self.assertEqual(milestone_state("2026-06-01", "2026-06-20", 14, evidence_available=False)["state"], "UNKNOWN_EVIDENCE")
    def test_pause_adjusts_due_date(self): self.assertEqual(milestone_state("2026-06-01", "2026-06-20", 5, approved_pause_days=3)["due_date"], "2026-06-09")
    def test_bad_expected_days(self):
        with self.assertRaises(ValueError): milestone_state("2026-06-01", "2026-06-20", -1)
    def test_bad_pause(self):
        with self.assertRaises(ValueError): milestone_state("2026-06-01", "2026-06-20", 5, approved_pause_days=True)
    def test_cutoff_before_start(self):
        with self.assertRaises(ValueError): milestone_state("2026-06-20", "2026-06-01", 5)
    def test_completion_before_start(self):
        with self.assertRaises(ValueError): milestone_state("2026-06-10", "2026-06-20", 5, "2026-06-01")
    def test_completion_after_cutoff(self):
        with self.assertRaises(ValueError): milestone_state("2026-06-01", "2026-06-20", 21, "2026-06-22")
    def test_unavailable_evidence_conflicts_with_completion(self):
        with self.assertRaises(ValueError): milestone_state("2026-06-01", "2026-06-20", 5, "2026-06-06", evidence_available=False)
    def test_bad_date(self):
        with self.assertRaises(ValueError): milestone_state("invalid-date", "2026-06-20", 5)
    def test_summary(self):
        result = summarize_states(["COMPLETED_ON_TIME", "COMPLETED_LATE", "PENDING", "UNKNOWN_EVIDENCE"])
        self.assertEqual((result["total"], result["PENDING"]), (4, 1))
    def test_bad_state(self):
        with self.assertRaises(ValueError): summarize_states(["AT_RISK"])
    def test_coverage(self): self.assertEqual(coverage(8, 10), Decimal("0.8"))
    def test_zero_coverage_unknown(self): self.assertIsNone(coverage(0, 0))
    def test_bad_coverage(self):
        with self.assertRaises(ValueError): coverage(11, 10)


if __name__ == "__main__": unittest.main()
