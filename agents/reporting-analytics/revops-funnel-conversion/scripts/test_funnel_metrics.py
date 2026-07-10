#!/usr/bin/env python3
import math
import unittest

from funnel_metrics import build_funnel_report, compare_rates, distribution_summary, rate, render_funnel_json, target_comparison, transition_summary, validate_ordered_reach, wilson_interval


class FunnelMetricsTests(unittest.TestCase):
    def report(self, **overrides):
        values={"report_id":"REPORT-ALPHA","policy_id":"FP-7","cutoff":"UTC-CUTOFF","stages":["Lead","MQL","SQL","Opportunity","Closed Won"],"reach_counts":[100,48,20,9,2],"transition_rows":[{"from_stage":"Lead","to_stage":"MQL","entered":100,"mature":80,"advanced":48},{"from_stage":"MQL","to_stage":"SQL","entered":48,"mature":40,"advanced":20},{"from_stage":"SQL","to_stage":"Opportunity","entered":20,"mature":15,"advanced":9},{"from_stage":"Opportunity","to_stage":"Closed Won","entered":9,"mature":5,"advanced":2}]}
        values.update(overrides); return build_funnel_report(**values)
    def test_transition_keeps_pending_out(self):
        result = transition_summary(100, 80, 48)
        self.assertEqual(result["pending_not_mature"], 20)
        self.assertEqual(result["not_advanced_by_deadline"], 32)
        self.assertEqual(result["conversion_rate"], 0.6)

    def test_zero_mature(self):
        result = transition_summary(10, 0, 0)
        self.assertEqual(result["status"], "INSUFFICIENT_MATURE_COHORT")
        self.assertIsNone(result["conversion_rate"])

    def test_mature_cannot_exceed_entered(self):
        with self.assertRaises(ValueError):
            transition_summary(10, 11, 1)

    def test_advanced_cannot_exceed_mature(self):
        with self.assertRaises(ValueError):
            transition_summary(10, 5, 6)

    def test_ordered_reach(self):
        self.assertTrue(validate_ordered_reach([100, 48, 20, 9, 2]))

    def test_ordered_reach_rejects_increase(self):
        with self.assertRaises(ValueError):
            validate_ordered_reach([100, 48, 50])

    def test_rate_zero_denominator(self):
        self.assertIsNone(rate(0, 0))

    def test_wilson_contains_rate(self):
        low, high = wilson_interval(48, 80)
        self.assertLess(low, 0.6)
        self.assertGreater(high, 0.6)

    def test_invalid_wilson_z(self):
        with self.assertRaises(ValueError):
            wilson_interval(1, 2, 0)

    def test_rate_comparison(self):
        result = compare_rates(48, 80, 40, 80)
        self.assertAlmostEqual(result["absolute_difference"], 0.1)
        self.assertAlmostEqual(result["relative_difference"], 0.2)

    def test_zero_baseline_relative_unknown(self):
        self.assertIsNone(compare_rates(1, 10, 0, 10)["relative_difference"])

    def test_distribution(self):
        result = distribution_summary([5, 10, 15, 20, 25, 30, 35, 40, 45])
        self.assertEqual(result, {"count": 9, "median": 25.0, "p75": 35.0, "p90": 41.0})

    def test_empty_distribution(self):
        self.assertEqual(distribution_summary([]), {"count": 0, "median": None, "p75": None, "p90": None})

    def test_invalid_distribution(self):
        with self.assertRaises(ValueError):
            distribution_summary([1, math.nan])

    def test_target_difference_only(self):
        result = target_comparison(0.4, 0.5)
        self.assertAlmostEqual(result["difference_percentage_points"], -10.0)

    def test_invalid_target(self):
        with self.assertRaises(ValueError):
            target_comparison(0.4, 1.1)

    def test_exact_report_states_and_minimum(self):
        result=self.report()
        self.assertEqual(result["transitions"][0]["conversion_rate"],"0.600000")
        self.assertEqual(result["transitions"][3]["pending_not_mature"],4)
        self.assertEqual(result["minimum_point_estimate"]["bottleneck_state"],"TARGET_NOT_APPROVED")
        self.assertNotIn("conversion_rate",result["minimum_point_estimate"])
        self.assertNotIn("entered",result["transitions"][0])
        self.assertNotIn("advanced",result["transitions"][0])

    def test_report_end_to_end_fails_closed(self):
        self.assertEqual(self.report()["end_to_end_conversion"]["state"],"POLICY_REQUIRED")

    def test_report_has_no_action_or_adequacy_label(self):
        result=self.report()
        self.assertFalse(result["action_authorized"])
        self.assertFalse(result["validation"]["adequacy_label_applied"])
        rendered=render_funnel_json(result).casefold()
        for word in ("small cohort","large cohort","enough data","limited data","insufficient data"):
            self.assertNotIn(word,rendered)

    def test_report_rejects_transition_reach_mismatch(self):
        rows=[{"from_stage":"Lead","to_stage":"MQL","entered":100,"mature":80,"advanced":47},{"from_stage":"MQL","to_stage":"SQL","entered":48,"mature":40,"advanced":20},{"from_stage":"SQL","to_stage":"Opportunity","entered":20,"mature":15,"advanced":9},{"from_stage":"Opportunity","to_stage":"Closed Won","entered":9,"mature":5,"advanced":2}]
        with self.assertRaises(ValueError): self.report(transition_rows=rows)

    def test_report_rejects_nonadjacent_transition(self):
        rows=[dict(row) for row in self.report()["transitions"]]
        for row in rows:
            for key in ("pending_not_mature","not_advanced_by_deadline","conversion_rate","wilson95","state"):
                row.pop(key)
        rows[0]["to_stage"]="SQL"
        with self.assertRaises(ValueError): self.report(transition_rows=rows)

    def test_renderer_is_deterministic(self):
        self.assertEqual(render_funnel_json(self.report()),render_funnel_json(self.report()))

    def test_renderer_rejects_nonobject(self):
        with self.assertRaises(ValueError): render_funnel_json([])


if __name__ == "__main__":
    unittest.main()
