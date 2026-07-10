#!/usr/bin/env python3
import unittest
from decimal import Decimal

from stage_progression import classify_transition, coverage, dwell_result, episodes


class StageProgressionTests(unittest.TestCase):
    def setUp(self):
        self.stages = ["discovery", "qualification", "proposal", "negotiation"]
        self.events = [
            {"stage_id": "discovery", "entered_at": "2026-07-01T00:00:00Z"},
            {"stage_id": "qualification", "entered_at": "2026-07-06T00:00:00Z"},
            {"stage_id": "proposal", "entered_at": "2026-07-16T00:00:00Z"},
            {"stage_id": "qualification", "entered_at": "2026-07-20T00:00:00Z"},
            {"stage_id": "proposal", "entered_at": "2026-07-25T00:00:00Z"},
        ]

    def test_episode_days_and_reentry(self):
        result = episodes(self.events, "2026-08-14T00:00:00Z")
        self.assertEqual([row["days"] for row in result], [Decimal("5"), Decimal("10"), Decimal("4"), Decimal("5"), Decimal("20")])

    def test_after_cutoff_fails(self):
        with self.assertRaises(ValueError):
            episodes(self.events, "2026-07-10T00:00:00Z")

    def test_duplicate_time_fails(self):
        with self.assertRaises(ValueError):
            episodes(self.events + [{"stage_id": "proposal", "entered_at": "2026-07-25T00:00:00Z"}], "2026-08-14T00:00:00Z")

    def test_adjacent(self): self.assertEqual(classify_transition("discovery", "qualification", self.stages), "ADJACENT_FORWARD")
    def test_skip(self): self.assertEqual(classify_transition("discovery", "proposal", self.stages), "POLICY_SKIP")
    def test_allowed_skip(self): self.assertEqual(classify_transition("discovery", "proposal", self.stages, [("discovery", "proposal")]), "ALLOWED_TRANSITION")
    def test_regression(self): self.assertEqual(classify_transition("proposal", "qualification", self.stages), "REGRESSION")
    def test_unknown_stage(self): self.assertEqual(classify_transition("proposal", "legal", self.stages), "UNKNOWN_STAGE")
    def test_reentry(self): self.assertEqual(classify_transition("proposal", "proposal", self.stages), "REENTRY")

    def test_extended_dwell(self):
        result = dwell_result(20, 10, "1.5")
        self.assertEqual(result, {"ratio": Decimal("2"), "flagged": True, "label": "EXTENDED_DWELL"})

    def test_exact_threshold_flags(self): self.assertTrue(dwell_result(15, 10, "1.5")["flagged"])
    def test_rapid(self): self.assertEqual(dwell_result(4, 10, "0.5", "rapid")["label"], "RAPID_TRANSITION")
    def test_zero_benchmark_fails(self):
        with self.assertRaises(ValueError): dwell_result(10, 0, 2)
    def test_bad_direction_fails(self):
        with self.assertRaises(ValueError): dwell_result(10, 10, 2, "other")
    def test_coverage(self): self.assertEqual(coverage(8, 10), Decimal("0.8"))
    def test_bad_coverage_fails(self):
        with self.assertRaises(ValueError): coverage(11, 10)


if __name__ == "__main__": unittest.main()
