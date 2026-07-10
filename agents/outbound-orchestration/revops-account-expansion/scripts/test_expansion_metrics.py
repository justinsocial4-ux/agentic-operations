#!/usr/bin/env python3
import unittest
from decimal import Decimal

from expansion_metrics import evidence_coverage, evaluate_eligibility, ratio, renewal_days, score_candidate, seat_utilization, value_estimate


class ExpansionMetricsTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "adoption_min": "0.75",
            "utilization_min": "0.90",
            "renewal_min_days": 0,
            "renewal_max_days": 120,
            "health_required": True,
        }

    def test_feature_adoption(self):
        self.assertEqual(ratio(6, 8, "adopted", "eligible"), 0.75)

    def test_zero_denominator_is_unknown(self):
        self.assertIsNone(ratio(0, 0))

    def test_invalid_ratio_fails(self):
        with self.assertRaises(ValueError):
            ratio(9, 8)

    def test_seat_utilization(self):
        result = seat_utilization(90, 100)
        self.assertEqual(result["utilization"], Decimal("0.9"))
        self.assertEqual(result["unused_seats"], Decimal("10"))

    def test_seat_overage_stays_visible(self):
        result = seat_utilization(110, 100)
        self.assertEqual(result["utilization"], Decimal("1.1"))
        self.assertEqual(result["overage_users"], Decimal("10"))

    def test_zero_licensed_is_unknown(self):
        self.assertIsNone(seat_utilization(0, 0))

    def test_coverage(self):
        self.assertEqual(evidence_coverage(8, 10), Decimal("0.8"))

    def test_invalid_coverage_fails(self):
        with self.assertRaises(ValueError):
            evidence_coverage(11, 10)

    def test_renewal_days(self):
        self.assertEqual(renewal_days("2026-07-10", "2026-10-18"), 100)

    def test_invalid_date_fails(self):
        with self.assertRaises(ValueError):
            renewal_days("today", "2026-10-18")

    def test_complete_score(self):
        components = {"adoption": "0.75", "utilization": "0.90", "renewal": "1", "sponsor": "0"}
        weights = {"adoption": "0.35", "utilization": "0.35", "renewal": "0.20", "sponsor": "0.10"}
        self.assertEqual(score_candidate(components, weights), Decimal("0.7775"))

    def test_incomplete_score_fails(self):
        with self.assertRaises(ValueError):
            score_candidate({"adoption": 1}, {"adoption": 0.5, "usage": 0.5})

    def test_weights_must_total_one(self):
        with self.assertRaises(ValueError):
            score_candidate({"a": 1, "b": 1}, {"a": 0.4, "b": 0.5})

    def test_eligible_at_exact_boundaries(self):
        evidence = {"adoption": "0.75", "utilization": "0.90", "renewal_days": 120, "health_eligible": True}
        self.assertEqual(evaluate_eligibility(evidence, self.policy)["status"], "ELIGIBLE")

    def test_low_adoption_blocks_expansion(self):
        evidence = {"adoption": "0.50", "utilization": "0.95", "renewal_days": 30, "health_eligible": True}
        result = evaluate_eligibility(evidence, self.policy)
        self.assertEqual(result["status"], "NOT_ELIGIBLE")
        self.assertEqual(result["checks"]["adoption"], "FAIL")

    def test_missing_health_is_unknown(self):
        evidence = {"adoption": "0.80", "utilization": "0.95", "renewal_days": 30, "health_eligible": None}
        self.assertEqual(evaluate_eligibility(evidence, self.policy)["status"], "ELIGIBILITY_UNKNOWN")

    def test_verified_value(self):
        self.assertEqual(value_estimate(10, "125.50", "usd")["value"], "1255.00")

    def test_missing_currency_fails(self):
        with self.assertRaises(ValueError):
            value_estimate(1, 10, "")


if __name__ == "__main__":
    unittest.main()
