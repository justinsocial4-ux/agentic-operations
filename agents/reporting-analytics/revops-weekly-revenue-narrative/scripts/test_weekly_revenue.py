from __future__ import annotations

import unittest

from weekly_revenue import close_date_slip, deal_risk, percent_delta, velocity_signal, weekly_metrics


class WeeklyRevenueTests(unittest.TestCase):
    def test_percent_delta(self) -> None:
        self.assertEqual(percent_delta(120000, 100000), {"status": "PERCENT", "percent": 20.0})
        self.assertEqual(percent_delta(1, 0), {"status": "NEW", "percent": None})
        self.assertEqual(percent_delta(0, 0), {"status": "UNCHANGED_ZERO", "percent": None})

    def test_worked_risk_is_high(self) -> None:
        result = deal_risk(days_in_stage=30, median_stage_days=10, days_since_activity=20)
        self.assertEqual(result["stage_multiplier"], 3.0)
        self.assertEqual(result["stall_score"], 1.0)
        self.assertEqual(result["silence_score"], 1.0)
        self.assertEqual(result["composite_score"], 1.0)
        self.assertEqual(result["risk_level"], "HIGH")

    def test_risk_boundaries(self) -> None:
        medium = deal_risk(days_in_stage=20, median_stage_days=10, days_since_activity=6)
        self.assertEqual(medium["composite_score"], 0.3)
        self.assertEqual(medium["risk_level"], "LOW")
        high = deal_risk(days_in_stage=30, median_stage_days=10, days_since_activity=13)
        self.assertEqual(high["composite_score"], 0.8)
        self.assertEqual(high["risk_level"], "HIGH")

    def test_missing_risk_evidence_stays_unknown(self) -> None:
        result = deal_risk(days_in_stage=None, median_stage_days=None, days_since_activity=20)
        self.assertEqual(result["risk_level"], "UNKNOWN")
        self.assertIsNone(result["composite_score"])
        self.assertEqual(result["missing"], ["stage_history"])

    def test_zero_stage_median_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            deal_risk(days_in_stage=4, median_stage_days=0, days_since_activity=2)

    def test_close_date_slip(self) -> None:
        self.assertEqual(close_date_slip("2026-07-01", "2026-07-10"), {"status": "SLIPPED", "slip_days": 9, "urgent": True})
        self.assertEqual(close_date_slip("2026-07-10", "2026-07-01"), {"status": "NOT_SLIPPED", "slip_days": 0, "urgent": False})
        self.assertEqual(close_date_slip(None, "2026-07-01")["status"], "UNKNOWN")

    def test_velocity_states(self) -> None:
        self.assertEqual(velocity_signal(5, [1, 2])["status"], "INSUFFICIENT_HISTORY")
        self.assertEqual(velocity_signal(5, [3] * 8)["status"], "NO_VARIANCE_BASELINE")
        self.assertEqual(velocity_signal(20, [2, 3, 4, 3, 2, 4, 3, 3])["status"], "SURGE")
        self.assertEqual(velocity_signal(0, [10, 11, 9, 10, 12, 8, 11, 9])["status"], "SLOWDOWN")

    def test_weekly_metrics_and_half_open_boundary(self) -> None:
        records = [
            {"id": "W1", "amount": 70000, "currency": "USD", "is_closed": True, "is_won": True, "close_date": "2026-07-08", "created_date": "2026-06-01"},
            {"id": "W2", "amount": 50000, "currency": "USD", "is_closed": True, "is_won": True, "close_date": "2026-07-09", "created_date": "2026-07-09"},
            {"id": "L1", "amount": 30000, "currency": "USD", "is_closed": True, "is_won": False, "close_date": "2026-07-10", "created_date": "2026-06-01"},
            {"id": "O1", "amount": 500000, "currency": "USD", "is_closed": False, "is_won": False, "close_date": "2026-08-01", "created_date": "2026-07-13"},
            {"id": "NEXT", "amount": 999, "currency": "USD", "is_closed": True, "is_won": True, "close_date": "2026-07-13", "created_date": "2026-06-01"},
        ]
        result = weekly_metrics(records, "2026-07-06", "2026-07-13")
        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["closed_won_count"], 2)
        self.assertEqual(result["closed_won_amount"], 120000.0)
        self.assertEqual(result["closed_lost_count"], 1)
        self.assertEqual(result["closed_lost_amount"], 30000.0)
        self.assertEqual(result["win_rate_percent"], 66.67)
        self.assertEqual(result["open_pipeline_amount"], 500000.0)
        self.assertEqual(result["new_deal_count"], 1)

    def test_no_closed_deals_has_unknown_win_rate(self) -> None:
        records = [{"id": "O1", "amount": 5, "currency": "USD", "is_closed": False, "is_won": False, "close_date": "2026-08-01", "created_date": "2026-06-01"}]
        self.assertIsNone(weekly_metrics(records, "2026-07-06", "2026-07-13")["win_rate_percent"])

    def test_invalid_amount_and_outcome_fail_closed(self) -> None:
        bad_amount = [{"id": "X", "amount": -1, "currency": "USD", "is_closed": False, "is_won": False, "close_date": "2026-08-01", "created_date": "2026-06-01"}]
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            weekly_metrics(bad_amount, "2026-07-06", "2026-07-13")
        bad_state = [{"id": "X", "amount": 1, "currency": "USD", "is_closed": "no", "is_won": False, "close_date": "2026-08-01", "created_date": "2026-06-01"}]
        with self.assertRaisesRegex(ValueError, "booleans"):
            weekly_metrics(bad_state, "2026-07-06", "2026-07-13")

    def test_missing_amount_and_mixed_currency_fail_closed(self) -> None:
        missing_amount = [{"id": "X", "currency": "USD", "is_closed": False, "is_won": False, "close_date": "2026-08-01", "created_date": "2026-06-01"}]
        with self.assertRaisesRegex(ValueError, "amount is required"):
            weekly_metrics(missing_amount, "2026-07-06", "2026-07-13")
        mixed = [
            {"id": "A", "amount": 1, "currency": "USD", "is_closed": False, "is_won": False, "close_date": "2026-08-01", "created_date": "2026-06-01"},
            {"id": "B", "amount": 1, "currency": "EUR", "is_closed": False, "is_won": False, "close_date": "2026-08-01", "created_date": "2026-06-01"},
        ]
        with self.assertRaisesRegex(ValueError, "mixed currencies"):
            weekly_metrics(mixed, "2026-07-06", "2026-07-13")

    def test_fractional_velocity_count_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "integers"):
            velocity_signal(1.5, [1] * 8)


if __name__ == "__main__":
    unittest.main()
