#!/usr/bin/env python3
import unittest
from decimal import Decimal

from icp_metrics import coverage, segment_metrics


class ICPMetricsTests(unittest.TestCase):
    def test_overall(self): self.assertEqual(segment_metrics(60, 40)["win_rate"], 0.6)
    def test_segment_difference(self):
        result = segment_metrics(12, 3, baseline_won=60, baseline_total=100)
        self.assertEqual(
            (result["total"], result["rate_denominator"], result["win_rate"], round(result["difference_pp"], 6)),
            (15, 15, 0.8, 20.0),
        )
    def test_other_is_visible_but_not_in_win_rate(self):
        result = segment_metrics(6, 3, 1)
        self.assertEqual((result["total"], result["rate_denominator"], result["win_rate"]), (10, 9, 2 / 3))
    def test_other_only_has_no_win_rate(self):
        result = segment_metrics(0, 0, 4)
        self.assertEqual((result["total"], result["rate_denominator"], result["win_rate"], result["wilson"]), (4, 0, None, None))
    def test_zero_total_unknown(self): self.assertIsNone(segment_metrics(0, 0)["win_rate"])
    def test_wilson_bounds(self):
        low, high = segment_metrics(12, 3)["wilson"]
        self.assertTrue(0 <= low < 0.8 < high <= 1)
    def test_bad_count(self):
        with self.assertRaises(ValueError): segment_metrics(-1, 2)
    def test_bool_count(self):
        with self.assertRaises(ValueError): segment_metrics(True, 2)
    def test_partial_baseline_fails(self):
        with self.assertRaises(ValueError): segment_metrics(1, 1, baseline_won=1)
    def test_zero_baseline_fails(self):
        with self.assertRaises(ValueError): segment_metrics(1, 1, baseline_won=0, baseline_total=0)
    def test_won_exceeds_baseline_fails(self):
        with self.assertRaises(ValueError): segment_metrics(1, 1, baseline_won=3, baseline_total=2)
    def test_nonfinite_z_fails(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                segment_metrics(1, 1, z=value)
    def test_nonpositive_z_fails(self):
        for value in (0, -1, True, "1.96"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                segment_metrics(1, 1, z=value)
    def test_coverage(self): self.assertEqual(coverage(80, 100), Decimal("0.8"))
    def test_zero_coverage_unknown(self): self.assertIsNone(coverage(0, 0))
    def test_bad_coverage(self):
        with self.assertRaises(ValueError): coverage(11, 10)


if __name__ == "__main__": unittest.main()
