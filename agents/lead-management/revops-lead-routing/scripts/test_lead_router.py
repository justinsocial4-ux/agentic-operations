from __future__ import annotations

import unittest

from lead_router import calculate_capacity, capacity_state, escalation_decision, rank_candidates, route


def candidate(owner_id: str, **overrides: object) -> dict[str, object]:
    item: dict[str, object] = {
        "owner_id": owner_id,
        "active": True,
        "in_approved_pool": True,
        "excluded": False,
        "territory_conflict": False,
        "existing_account_owner": False,
        "territory_role": "general",
        "capacity_state": "Green",
        "vertical_specialist": False,
        "round_robin_position": 0,
    }
    item.update(overrides)
    return item


class LeadRouterTests(unittest.TestCase):
    def test_published_capacity_example_is_50_yellow(self) -> None:
        result = calculate_capacity(
            active_opportunities=6,
            average_active_opportunities=12,
            pipeline_amount=300_000,
            rep_quota=600_000,
            activities_7d=20,
            weekly_activity_target=40,
        )
        self.assertEqual(result["score"], 50.0)
        self.assertEqual(result["state"], "Yellow")

    def test_capacity_boundaries_do_not_overlap(self) -> None:
        self.assertEqual(capacity_state(49.99), "Green")
        self.assertEqual(capacity_state(50), "Yellow")
        self.assertEqual(capacity_state(84.99), "Yellow")
        self.assertEqual(capacity_state(85), "Red")
        self.assertEqual(capacity_state(99.99), "Red")
        self.assertEqual(capacity_state(100), "Critical")
        self.assertEqual(capacity_state(None), "Unknown")

    def test_components_are_capped(self) -> None:
        result = calculate_capacity(
            active_opportunities=100,
            average_active_opportunities=10,
            pipeline_amount=2_000_000,
            rep_quota=500_000,
            activities_7d=500,
            weekly_activity_target=40,
        )
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["state"], "Critical")

    def test_zero_denominator_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "denominator must be positive"):
            calculate_capacity(
                active_opportunities=1,
                average_active_opportunities=0,
                pipeline_amount=1,
                rep_quota=1,
                activities_7d=1,
                weekly_activity_target=1,
            )

    def test_account_owner_outranks_specialist(self) -> None:
        ranked = rank_candidates(
            [
                candidate("SPECIALIST", vertical_specialist=True, territory_role="primary"),
                candidate("OWNER", existing_account_owner=True, territory_role="secondary", capacity_state="Yellow"),
            ]
        )
        self.assertEqual(ranked[0]["owner_id"], "OWNER")

    def test_territory_precedes_capacity_and_specialty(self) -> None:
        ranked = rank_candidates(
            [
                candidate("GENERAL", territory_role="general", capacity_state="Green", vertical_specialist=True),
                candidate("PRIMARY", territory_role="primary", capacity_state="Yellow"),
            ]
        )
        self.assertEqual(ranked[0]["owner_id"], "PRIMARY")

    def test_critical_inactive_excluded_and_conflict_candidates_are_removed(self) -> None:
        ranked = rank_candidates(
            [
                candidate("CRITICAL", capacity_state="Critical"),
                candidate("INACTIVE", active=False),
                candidate("EXCLUDED", excluded=True),
                candidate("CONFLICT", territory_conflict=True),
                candidate("VALID"),
            ]
        )
        self.assertEqual([item["owner_id"] for item in ranked], ["VALID"])

    def test_round_robin_and_owner_id_are_stable_ties(self) -> None:
        ranked = rank_candidates(
            [
                candidate("B", round_robin_position=1),
                candidate("C", round_robin_position=0),
                candidate("A", round_robin_position=1),
            ]
        )
        self.assertEqual([item["owner_id"] for item in ranked], ["C", "A", "B"])

    def test_escalation_requires_critical_or_two_review_flags(self) -> None:
        self.assertFalse(escalation_decision(["STALE_CAPACITY"])["manual_review"])
        self.assertTrue(escalation_decision(["STALE_CAPACITY", "UNMAPPED_TERRITORY"])["manual_review"])
        self.assertTrue(escalation_decision(["ACCOUNT_TERRITORY_CONFLICT"])["manual_review"])

    def test_no_eligible_candidate_fails_to_manual_review(self) -> None:
        result = route([candidate("ONLY", capacity_state="Critical")])
        self.assertEqual(result["decision"], "MANUAL_REVIEW")
        self.assertIsNone(result["selected"])


if __name__ == "__main__":
    unittest.main()
