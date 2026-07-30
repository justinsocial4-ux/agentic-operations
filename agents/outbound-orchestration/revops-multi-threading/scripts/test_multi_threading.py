from __future__ import annotations

import unittest

from multi_threading import assess_coverage, candidate_score, engagement_status, rank_candidates


class MultiThreadingTests(unittest.TestCase):
    def test_engagement_boundaries(self) -> None:
        self.assertEqual(engagement_status(30), "ACTIVE")
        self.assertEqual(engagement_status(31), "COLD")
        self.assertEqual(engagement_status(90), "COLD")
        self.assertEqual(engagement_status(91), "DORMANT")
        self.assertEqual(engagement_status(None), "UNCONTACTED")
        self.assertEqual(engagement_status(2, activity_coverage_available=False), "UNKNOWN")

    def test_invalid_activity_age_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            engagement_status(-1)

    def test_worked_candidate_score(self) -> None:
        result = candidate_score({
            "role_fit": 1.0,
            "department_fit": 1.0,
            "seniority_fit": 1.0,
            "relationship_evidence": 0.8,
            "engagement_evidence": 0.2,
        })
        self.assertEqual(result["score"], 0.84)
        self.assertEqual(sum(result["contributions"].values()), 0.84)

    def test_missing_candidate_component_is_incomplete(self) -> None:
        result = candidate_score({"role_fit": 1.0})
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIsNone(result["score"])

    def test_invalid_candidate_component_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "0 to 1"):
            candidate_score({name: (2 if name == "role_fit" else 0) for name in (
                "role_fit", "department_fit", "seniority_fit", "relationship_evidence", "engagement_evidence"
            )})

    def test_worked_coverage_assessment(self) -> None:
        result = assess_coverage(
            ["Champion", "Economic Buyer", "Technical Buyer", "Budget Holder"],
            [
                {"contact_id": "Sarah", "role": "Champion", "evidence_level": "VERIFIED", "engagement_status": "ACTIVE"},
                {"contact_id": "Tom", "role": "Technical Buyer", "evidence_level": "VERIFIED", "engagement_status": "COLD"},
            ],
            late_stage=True,
        )
        self.assertEqual(result["status"], "URGENT_REVIEW")
        self.assertEqual(result["distinct_active_stakeholders"], 1)
        self.assertEqual(result["verified_active_roles"], ["Champion"])
        self.assertEqual(result["inactive_verified_roles"], ["Technical Buyer"])
        self.assertEqual(result["missing_roles"], ["Budget Holder", "Economic Buyer"])
        self.assertTrue(result["single_point_of_failure"])

    def test_inferred_role_does_not_become_verified(self) -> None:
        result = assess_coverage(
            ["Economic Buyer"],
            [{"contact_id": "Jen", "role": "Economic Buyer", "evidence_level": "INFERRED_CANDIDATE", "engagement_status": "ACTIVE"}],
            late_stage=True,
        )
        self.assertEqual(result["inferred_only_active_roles"], ["Economic Buyer"])
        self.assertEqual(result["missing_verified_active_roles"], ["Economic Buyer"])

    def test_unknown_role_does_not_become_inferred(self) -> None:
        result = assess_coverage(
            ["Economic Buyer"],
            [{"contact_id": "Jen", "role": "Economic Buyer", "evidence_level": "UNKNOWN", "engagement_status": "ACTIVE"}],
            late_stage=False,
        )
        self.assertEqual(result["inferred_only_active_roles"], [])
        self.assertEqual(result["missing_roles"], ["Economic Buyer"])

    def test_early_stage_single_point_requires_review(self) -> None:
        result = assess_coverage(
            ["Champion"],
            [{"contact_id": "A", "role": "Champion", "evidence_level": "VERIFIED", "engagement_status": "ACTIVE"}],
            late_stage=False,
        )
        self.assertEqual(result["status"], "REVIEW")
        self.assertTrue(result["single_point_of_failure"])

    def test_missing_activity_coverage_disables_single_point_claim(self) -> None:
        result = assess_coverage(
            ["Champion"],
            [{"contact_id": "A", "role": "Champion", "evidence_level": "VERIFIED", "engagement_status": "UNKNOWN"}],
            late_stage=True,
            activity_coverage_available=False,
        )
        self.assertEqual(result["status"], "DATA_GAP")
        self.assertIsNone(result["single_point_of_failure"])

    def test_missing_stage_policy_returns_data_gap(self) -> None:
        self.assertEqual(assess_coverage([], [], late_stage=False)["status"], "DATA_GAP")

    def test_candidate_ranking_is_stable(self) -> None:
        candidates = [
            {"contact_id": "B", "components": {"role_fit": 1, "department_fit": 1, "seniority_fit": 1, "relationship_evidence": 0.5, "engagement_evidence": 0.5}},
            {"contact_id": "A", "components": {"role_fit": 1, "department_fit": 1, "seniority_fit": 1, "relationship_evidence": 0.8, "engagement_evidence": 0.1}},
        ]
        ranked = rank_candidates(candidates)
        self.assertEqual([row["contact_id"] for row in ranked], ["A", "B"])


if __name__ == "__main__":
    unittest.main()
