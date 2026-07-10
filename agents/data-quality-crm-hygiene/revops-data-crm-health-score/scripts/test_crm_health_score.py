from __future__ import annotations

import unittest

from crm_health_score import DEFAULT_WEIGHTS, composite_score, dimension_score, tier, trend


SCORES = {
    "completeness": 90,
    "accuracy": 80,
    "duplicates": 95,
    "freshness": 65,
    "consistency": 85,
    "connectivity": 80,
}


class CrmHealthScoreTests(unittest.TestCase):
    def test_completeness_and_accuracy_boundaries(self) -> None:
        self.assertEqual(dimension_score("completeness", 90), 90)
        self.assertEqual(dimension_score("completeness", 89.9), 80)
        self.assertEqual(dimension_score("accuracy", 80), 80)
        self.assertEqual(dimension_score("accuracy", 69.9), 50)

    def test_duplicate_boundaries_use_lower_rate_as_better(self) -> None:
        self.assertEqual(dimension_score("duplicates", 2.99), 95)
        self.assertEqual(dimension_score("duplicates", 3), 90)
        self.assertEqual(dimension_score("duplicates", 20), 50)
        self.assertEqual(dimension_score("duplicates", 20.01), 25)

    def test_freshness_consistency_and_connectivity_boundaries(self) -> None:
        self.assertEqual(dimension_score("freshness", 35), 35)
        self.assertEqual(dimension_score("consistency", 95), 85)
        self.assertEqual(dimension_score("consistency", 95.01), 95)
        self.assertEqual(dimension_score("connectivity", 95), 80)
        self.assertEqual(dimension_score("connectivity", 95.01), 90)

    def test_composite_matches_frozen_weights(self) -> None:
        result = composite_score(SCORES)
        self.assertEqual(result["score"], 82.75)
        self.assertEqual(result["tier"], "GOOD")
        self.assertEqual(result["weights"], DEFAULT_WEIGHTS)

    def test_custom_weights_must_sum_to_one(self) -> None:
        with self.assertRaisesRegex(ValueError, "sum to 1"):
            composite_score(SCORES, {name: 0.20 for name in SCORES})

    def test_all_six_dimensions_are_required(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing: connectivity"):
            composite_score({name: value for name, value in SCORES.items() if name != "connectivity"})

    def test_tiers_match_pilot(self) -> None:
        self.assertEqual(tier(85), "EXCELLENT")
        self.assertEqual(tier(75), "GOOD")
        self.assertEqual(tier(65), "AVERAGE")
        self.assertEqual(tier(50), "POOR")
        self.assertEqual(tier(49.99), "CRITICAL")

    def test_trend_reports_deltas_rate_and_biggest_mover(self) -> None:
        previous = dict(SCORES)
        current = dict(SCORES, completeness=96, freshness=69)
        result = trend(current, previous, periods=2)
        self.assertEqual(result["direction"], "improving")
        self.assertEqual(result["dimension_deltas"]["completeness"], 6)
        self.assertEqual(result["biggest_movers"][0], ("completeness", 6.0))
        self.assertEqual(result["rate_per_period"], result["delta"] / 2)


if __name__ == "__main__":
    unittest.main()
