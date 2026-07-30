from __future__ import annotations

import unittest

from pipeline_health import activity_points, score_health, stage_age_points, stall_status, status


class PipelineHealthTests(unittest.TestCase):
    def test_published_example_is_64_green(self) -> None:
        result = score_health(
            fields={"stage": True, "amount": True, "close_date": True, "next_step": False},
            days_since_activity=16,
            activity_source_available=True,
            days_in_stage=24,
            expected_stage_days=30,
        )
        self.assertEqual(result["raw_points"], 64)
        self.assertEqual(result["evidence_coverage"], 100)
        self.assertEqual(result["health_score"], 64.0)
        self.assertEqual(result["health_status"], "Green")

    def test_activity_boundaries(self) -> None:
        self.assertEqual(activity_points(6.99, source_available=True), (30, 30))
        self.assertEqual(activity_points(7, source_available=True), (22, 30))
        self.assertEqual(activity_points(14, source_available=True), (14, 30))
        self.assertEqual(activity_points(21, source_available=True), (7, 30))
        self.assertEqual(activity_points(30, source_available=True), (0, 30))

    def test_stage_age_boundaries(self) -> None:
        self.assertEqual(stage_age_points(15, 30), (30, 30))
        self.assertEqual(stage_age_points(30, 30), (20, 30))
        self.assertEqual(stage_age_points(45, 30), (10, 30))
        self.assertEqual(stage_age_points(45.01, 30), (0, 30))

    def test_zero_expected_days_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be positive"):
            stage_age_points(1, 0)

    def test_low_coverage_is_unknown_even_with_perfect_available_signals(self) -> None:
        result = score_health(
            fields={"stage": True, "amount": True, "close_date": True, "next_step": True},
            days_since_activity=None,
            activity_source_available=False,
            days_in_stage=None,
            expected_stage_days=None,
        )
        self.assertEqual(result["health_score"], 100.0)
        self.assertEqual(result["evidence_coverage"], 40)
        self.assertEqual(result["health_status"], "Unknown")

    def test_status_boundaries(self) -> None:
        self.assertEqual(status(60, 80), "Green")
        self.assertEqual(status(59.9, 80), "Yellow")
        self.assertEqual(status(40, 80), "Yellow")
        self.assertEqual(status(39.9, 80), "Red")
        self.assertEqual(status(100, 79), "Unknown")

    def test_stall_threshold_is_inclusive(self) -> None:
        result = stall_status(
            stage="Proposal",
            days_since_activity=21,
            activity_source_available=True,
            deal_age_days=40,
        )
        self.assertEqual(result["status"], "STALLED")
        self.assertEqual(result["severity"], "ALERT")

    def test_pending_signature_stall_is_critical(self) -> None:
        result = stall_status(
            stage="Pending Signature",
            days_since_activity=14,
            activity_source_available=True,
            deal_age_days=20,
        )
        self.assertEqual(result["severity"], "CRITICAL")

    def test_new_deal_grace_suppresses_stall(self) -> None:
        result = stall_status(
            stage="Pending Signature",
            days_since_activity=None,
            activity_source_available=True,
            deal_age_days=5,
        )
        self.assertEqual(result["basis"], "new_deal_grace")
        self.assertEqual(result["status"], "NOT_STALLED")

    def test_missing_activity_source_is_unknown_not_modified_date_fallback(self) -> None:
        result = stall_status(
            stage="Negotiation",
            days_since_activity=None,
            activity_source_available=False,
            deal_age_days=100,
        )
        self.assertEqual(result["status"], "STALL_UNKNOWN")
        self.assertEqual(result["basis"], "activity_unavailable")


if __name__ == "__main__":
    unittest.main()
