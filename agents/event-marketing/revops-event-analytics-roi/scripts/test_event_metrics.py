#!/usr/bin/env python3
import unittest
from decimal import Decimal

from event_metrics import attribution_rollup, benchmark, cost_per, coverage, return_metrics


class EventMetricsTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"opportunity_id": "o1", "amount": "200000", "currency": "USD", "credit": "0.5", "state": "active_pipeline"},
            {"opportunity_id": "o2", "amount": "100000", "currency": "USD", "credit": "0.25", "state": "closed_won"},
            {"opportunity_id": "o3", "amount": "80000", "currency": "USD", "credit": "0.5", "state": "closed_lost"},
        ]

    def test_coverage(self): self.assertEqual(coverage(120, 150), Decimal("0.8"))
    def test_zero_coverage_unknown(self): self.assertIsNone(coverage(0, 0))
    def test_bad_coverage_fails(self):
        with self.assertRaises(ValueError): coverage(151, 150)
    def test_cost_per(self): self.assertEqual(cost_per("100000", 200), Decimal("500"))
    def test_cost_per_zero_unknown(self): self.assertIsNone(cost_per("100000", 0))
    def test_float_cost_fails(self):
        with self.assertRaises(ValueError): cost_per(1.2, 2)
    def test_bool_count_fails(self):
        with self.assertRaises(ValueError): cost_per("1", True)
    def test_rollup_totals(self):
        result = attribution_rollup(self.rows, "USD")
        self.assertEqual((result["crm_amount_total"], result["attributed_amount_total"]), (Decimal("380000"), Decimal("165000")))
    def test_rollup_states(self):
        result = attribution_rollup(self.rows, "USD")
        self.assertEqual(result["attributed_amount_by_state"]["closed_lost"], Decimal("40000"))
    def test_duplicate_opportunity_fails(self):
        with self.assertRaises(ValueError): attribution_rollup(self.rows + [dict(self.rows[0])], "USD")
    def test_mixed_currency_fails(self):
        rows = [dict(self.rows[0], currency="EUR")]
        with self.assertRaisesRegex(ValueError, "MIXED_CURRENCY"): attribution_rollup(rows, "USD")
    def test_credit_over_one_fails(self):
        with self.assertRaises(ValueError): attribution_rollup([dict(self.rows[0], credit="1.1")], "USD")
    def test_invalid_state_fails(self):
        with self.assertRaises(ValueError): attribution_rollup([dict(self.rows[0], state="won")], "USD")
    def test_benefit_required(self):
        self.assertEqual(return_metrics("100000", "USD")["status"], "BENEFIT_BASIS_REQUIRED")
    def test_finance_approval_required(self):
        self.assertEqual(return_metrics("100000", "USD", "130000", "USD")["status"], "FINANCE_APPROVAL_REQUIRED")
    def test_finance_return_not_incremental(self):
        result = return_metrics("100000", "USD", "130000", "USD", True, False)
        self.assertEqual((result["status"], result["finance_defined_return"], result["incremental_roi"]), ("INCREMENTAL_ROI_UNAVAILABLE", Decimal("0.3"), None))
    def test_incremental_roi(self):
        result = return_metrics("100000", "USD", "130000", "USD", True, True)
        self.assertEqual(result["incremental_roi"], Decimal("0.3"))
    def test_return_mixed_currency_fails(self):
        with self.assertRaisesRegex(ValueError, "MIXED_CURRENCY"): return_metrics("100000", "USD", "130000", "EUR", True, True)
    def test_benefit_currency_required(self):
        with self.assertRaises(ValueError): return_metrics("100000", "USD", "130000", None, True, False)
    def test_zero_cost_fails(self):
        with self.assertRaises(ValueError): return_metrics("0", "USD", "1", "USD", True, True)
    def test_lower_is_better_benchmark(self):
        result = benchmark(Decimal("666.6666666666666666666666667"), ["700", "600", "800", "500"], "lower_is_better")
        self.assertEqual((result["median"], result["performance_percentile"]), (Decimal("650"), Decimal("0.5")))
    def test_higher_is_better_benchmark(self):
        result = benchmark("7", ["5", "6", "8", "9"], "higher_is_better")
        self.assertEqual(result["performance_percentile"], Decimal("0.5"))
    def test_invalid_direction_fails(self):
        with self.assertRaises(ValueError): benchmark("1", ["1"], "high")
    def test_empty_peers_fail(self):
        with self.assertRaises(ValueError): benchmark("1", [], "higher_is_better")
    def test_nonfinite_peer_fails(self):
        with self.assertRaises(ValueError): benchmark("1", ["NaN"], "higher_is_better")


if __name__ == "__main__":
    unittest.main()
