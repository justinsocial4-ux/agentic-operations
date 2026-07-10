#!/usr/bin/env python3
import unittest

from forecast_metrics import backtest_metrics, category_rollup, coverage, delta, money, validate_scenarios, weighted_expectation


class ForecastMetricsTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"category": "Commit", "amount": "100000", "currency": "USD", "probability": "0.8"},
            {"category": "Commit", "amount": "50000", "currency": "USD", "probability": "0.8"},
            {"category": "Best case", "amount": "80000", "currency": "USD", "probability": "0.5"},
            {"category": "Pipeline", "amount": "120000", "currency": "USD", "probability": "0.25"},
            {"category": "Pipeline", "amount": "60000", "currency": "USD", "probability": "0.25"},
            {"category": "Not forecasted", "amount": "40000", "currency": "USD", "probability": "0.1"},
            {"category": "Closed won", "amount": "30000", "currency": "USD", "probability": "1"},
        ]

    def test_category_rollup(self):
        result = category_rollup(self.rows)
        self.assertEqual(result["total"], "480000")
        self.assertEqual(result["categories"]["Commit"], {"count": 2, "amount": "150000"})

    def test_weighted_expectation(self):
        self.assertEqual(weighted_expectation(self.rows)["weighted_expectation"], "239000.00")

    def test_mixed_currency_fails(self):
        rows = self.rows + [{"category": "Commit", "amount": 1, "currency": "EUR"}]
        with self.assertRaises(ValueError):
            category_rollup(rows)

    def test_missing_category_fails(self):
        with self.assertRaises(ValueError):
            category_rollup([{"category": "", "amount": 1, "currency": "USD"}])

    def test_invalid_probability_fails(self):
        with self.assertRaises(ValueError):
            weighted_expectation([{"amount": 1, "currency": "USD", "probability": 1.1}])

    def test_negative_money_fails(self):
        with self.assertRaises(ValueError):
            money(-1)

    def test_delta(self):
        self.assertEqual(delta("120", "100"), {"absolute": "20", "relative": "0.2"})

    def test_zero_prior_relative_unknown(self):
        self.assertIsNone(delta("10", "0")["relative"])

    def test_scenario_order(self):
        self.assertEqual(validate_scenarios(80, 100, 130)["base"], "100")

    def test_bad_scenario_order_fails(self):
        with self.assertRaises(ValueError):
            validate_scenarios(120, 100, 130)

    def test_coverage(self):
        self.assertEqual(coverage(8, 10), 0.8)

    def test_invalid_coverage(self):
        with self.assertRaises(ValueError):
            coverage(11, 10)

    def test_backtest(self):
        result = backtest_metrics([110, 80, 0], [100, 100, 0])
        self.assertEqual(result["period_count"], 3)
        self.assertEqual(result["mae"], "10")
        self.assertEqual(result["wape"], "0.15")
        self.assertEqual(result["aggregate_bias"], "-0.05")
        self.assertEqual(result["errors"], ["10", "-20", "0"])

    def test_zero_actual_percentage_metrics_unknown(self):
        result = backtest_metrics([10, 0], [0, 0])
        self.assertIsNone(result["wape"])
        self.assertIsNone(result["aggregate_bias"])

    def test_backtest_length_mismatch_fails(self):
        with self.assertRaises(ValueError):
            backtest_metrics([1], [1, 2])


if __name__ == "__main__":
    unittest.main()
