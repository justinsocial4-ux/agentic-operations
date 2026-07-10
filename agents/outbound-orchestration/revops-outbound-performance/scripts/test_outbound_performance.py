from __future__ import annotations

import unittest

from outbound_performance import benjamini_hochberg, cluster_subjects, compare_proportions, jaro_winkler, rate_summary


class OutboundPerformanceTests(unittest.TestCase):
    def test_worked_example(self) -> None:
        comparison = compare_proportions(20, 200, 8, 200)
        self.assertEqual(comparison["rate_a"], 0.10)
        self.assertEqual(comparison["rate_b"], 0.04)
        self.assertEqual(comparison["absolute_difference"], 0.06)
        self.assertEqual(comparison["relative_lift"], 1.5)
        self.assertEqual(comparison["p_value_two_sided"], 0.018694)

    def test_wilson_interval_and_zero_denominator(self) -> None:
        summary = rate_summary(20, 200)
        self.assertEqual(summary["rate"], 0.10)
        self.assertLess(summary["wilson_low"], 0.10)
        self.assertGreater(summary["wilson_high"], 0.10)
        self.assertIsNone(rate_summary(0, 0)["rate"])
        with self.assertRaisesRegex(ValueError, "positive finite"):
            rate_summary(1, 2, z=0)

    def test_zero_baseline_has_no_relative_lift(self) -> None:
        self.assertIsNone(compare_proportions(2, 10, 0, 10)["relative_lift"])

    def test_invalid_counts_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "0 <="):
            rate_summary(3, 2)
        with self.assertRaisesRegex(ValueError, "integers"):
            rate_summary(1.5, 2)
        with self.assertRaisesRegex(ValueError, "positive"):
            compare_proportions(0, 0, 1, 2)

    def test_benjamini_hochberg_preserves_order(self) -> None:
        self.assertEqual(benjamini_hochberg([0.01, 0.04, 0.03, 0.20]), [0.04, 0.053333, 0.053333, 0.20])

    def test_invalid_p_value_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "0 to 1"):
            benjamini_hochberg([1.2])

    def test_subject_similarity_is_normalized(self) -> None:
        self.assertEqual(jaro_winkler("Q2 Budget Planning", "q2 budget-planning!"), 1.0)
        self.assertLess(jaro_winkler("Budget planning", "Unsubscribe now"), 0.90)

    def test_subject_clusters_are_reviewable(self) -> None:
        clusters = cluster_subjects(["Q2 budget planning", "Q2 budget-planning!", "Unsubscribe now"])
        merged = next(item for item in clusters if item["canonical"] == "q2 budget planning")
        self.assertEqual(merged["touches"], 2)
        self.assertEqual(len(merged["original_variants"]), 2)
        self.assertTrue(merged["requires_review"])

    def test_invalid_similarity_threshold_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            cluster_subjects(["a"], threshold=1.1)


if __name__ == "__main__":
    unittest.main()
