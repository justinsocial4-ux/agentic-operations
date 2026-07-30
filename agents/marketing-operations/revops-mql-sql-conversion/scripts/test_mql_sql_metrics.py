#!/usr/bin/env python3
import math
import unittest

from mql_sql_metrics import compare_rates, rate, rejection_summary, summarize_funnel, velocity_summary, wilson_interval


class MetricsTests(unittest.TestCase):
    def test_rate(self):
        self.assertEqual(rate(42, 70), 0.6)

    def test_zero_denominator_is_unknown(self):
        self.assertIsNone(rate(0, 0))

    def test_invalid_rate_fails(self):
        with self.assertRaises(ValueError):
            rate(2, 1)

    def test_funnel_keeps_pending_out(self):
        result = summarize_funnel(100, 70, 42, 18, 10)
        self.assertEqual(result["pending_not_mature"], 30)
        self.assertEqual(result["converted_rate"], 0.6)

    def test_funnel_reconciles(self):
        with self.assertRaises(ValueError):
            summarize_funnel(100, 70, 42, 18, 9)

    def test_no_mature_cohort(self):
        result = summarize_funnel(30, 0, 0, 0, 0)
        self.assertEqual(result["status"], "INSUFFICIENT_MATURE_COHORT")

    def test_wilson(self):
        low, high = wilson_interval(42, 70)
        self.assertLess(low, 0.6)
        self.assertGreater(high, 0.6)

    def test_invalid_z(self):
        with self.assertRaises(ValueError):
            wilson_interval(1, 2, 0)

    def test_comparison(self):
        result = compare_rates(42, 70, 36, 70)
        self.assertAlmostEqual(result["absolute_difference"], 0.08571428571428574)
        self.assertAlmostEqual(result["relative_difference"], 1 / 6)

    def test_zero_baseline_relative_unknown(self):
        self.assertIsNone(compare_rates(2, 10, 0, 10)["relative_difference"])

    def test_rejection_denominators(self):
        reasons = ["Bad fit"] * 9 + ["No response"] * 6
        result = rejection_summary(reasons, 18)
        self.assertAlmostEqual(result["capture_rate"], 15 / 18)
        self.assertEqual(result["unknown_reason"], 3)
        self.assertEqual(result["rows"][0]["share_all_rejections"], 0.5)
        self.assertEqual(result["rows"][0]["share_captured_reasons"], 0.6)

    def test_velocity(self):
        result = velocity_summary([1, 2, 3, 4])
        self.assertEqual(result, {"count": 4, "median_days": 2.5, "p75_days": 3.25})

    def test_velocity_invalid(self):
        with self.assertRaises(ValueError):
            velocity_summary([1, math.nan])


if __name__ == "__main__":
    unittest.main()
