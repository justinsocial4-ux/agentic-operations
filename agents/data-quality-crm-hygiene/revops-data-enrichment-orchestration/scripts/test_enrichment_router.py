from __future__ import annotations

import unittest

from enrichment_router import Candidate, confidence_tier, resolve_conflict, route_provider, score_missing_fields


class EnrichmentRouterTests(unittest.TestCase):
    def test_missing_field_weights_match_pilot(self) -> None:
        self.assertEqual(score_missing_fields(["email"]), {"score": 40, "priority": "low"})
        self.assertEqual(score_missing_fields(["email", "phone", "title"]), {"score": 85, "priority": "high"})
        self.assertEqual(score_missing_fields(["email", "phone", "title", "company"]), {"score": 100, "priority": "critical"})

    def test_duplicate_missing_field_is_not_double_counted(self) -> None:
        self.assertEqual(score_missing_fields(["email", "email"]), {"score": 40, "priority": "low"})

    def test_high_score_routes_by_accuracy_or_cost(self) -> None:
        self.assertEqual(route_provider(85, "accuracy")["providers"], ["Cleanlist"])
        self.assertEqual(route_provider(85, "cost")["providers"], ["Apollo"])

    def test_medium_and_low_routes_match_pilot(self) -> None:
        self.assertEqual(route_provider(70, "accuracy")["providers"], ["Clearbit", "Cognism"])
        self.assertEqual(route_provider(40, "cost")["providers"], ["cheapest_available"])

    def test_conflict_order_prefers_verified_then_newer(self) -> None:
        winner = resolve_conflict(
            [
                Candidate("old@example.com", True, "2026-01-01T00:00:00Z", 0.98, "Cleanlist"),
                Candidate("new@example.com", True, "2026-02-01T00:00:00Z", 0.80, "Apollo"),
                Candidate("majority@example.com", False, "2026-03-01T00:00:00Z", 0.99, "Provider A"),
                Candidate("majority@example.com", False, "2026-03-01T00:00:00Z", 0.99, "Provider B"),
            ]
        )
        self.assertEqual(winner.value, "new@example.com")

    def test_confidence_tiers_match_pilot(self) -> None:
        self.assertEqual(confidence_tier(98), "verified_or_multi_provider")
        self.assertEqual(confidence_tier(90), "high_accuracy_or_agreement")
        self.assertEqual(confidence_tier(80), "single_mid_accuracy")
        self.assertEqual(confidence_tier(60), "conflict_or_low_confidence")


if __name__ == "__main__":
    unittest.main()
