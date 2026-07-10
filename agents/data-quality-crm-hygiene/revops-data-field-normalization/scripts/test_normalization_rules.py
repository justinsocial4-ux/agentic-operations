from __future__ import annotations

import unittest

from normalization_rules import bulk_plan, confidence_tier, jaro_winkler, score_mapping


class NormalizationRulesTests(unittest.TestCase):
    def test_smoke_example_is_point_92_high_auto_map(self) -> None:
        result = score_mapping(similarity=0.82, company_context=True, frequency=100, user_threshold=0.85)
        self.assertEqual(result["confidence"], 0.92)
        self.assertEqual(result["tier"], "HIGH")
        self.assertTrue(result["auto_map"])

    def test_frequency_boost_starts_at_one_hundred(self) -> None:
        self.assertEqual(score_mapping(similarity=0.82, frequency=99)["confidence"], 0.82)
        self.assertEqual(score_mapping(similarity=0.82, frequency=100)["confidence"], 0.87)

    def test_similarity_below_point_75_gets_no_base_credit(self) -> None:
        result = score_mapping(similarity=0.74, company_context=True, frequency=100)
        self.assertEqual(result["confidence"], 0.10)
        self.assertEqual(result["tier"], "REJECT")

    def test_confidence_is_capped_at_one(self) -> None:
        self.assertEqual(score_mapping(similarity=1, company_context=True, frequency=100)["confidence"], 1.0)

    def test_tier_boundaries(self) -> None:
        self.assertEqual(confidence_tier(0.90), "HIGH")
        self.assertEqual(confidence_tier(0.80), "MEDIUM")
        self.assertEqual(confidence_tier(0.70), "LOW")
        self.assertEqual(confidence_tier(0.69), "REJECT")

    def test_user_threshold_controls_eligibility(self) -> None:
        result = score_mapping(similarity=0.88, user_threshold=0.90)
        self.assertFalse(result["eligible_for_apply"])
        self.assertFalse(result["auto_map"])

    def test_invalid_inputs_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            score_mapping(similarity=1.1)
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            score_mapping(similarity=0.8, frequency=-1)

    def test_jaro_winkler_is_deterministic(self) -> None:
        self.assertEqual(jaro_winkler("Sales Manager", "Sales Manager"), 1.0)
        self.assertGreater(jaro_winkler("Vice President Sales", "Vice Pres Sales"), 0.75)

    def test_bulk_plan_separates_updates_and_skips(self) -> None:
        result = bulk_plan([
            {"id": "A", "original_value": "VP Sales", "confidence": 0.92},
            {"id": "B", "original_value": "Sales", "confidence": 0.65},
        ])
        self.assertEqual([row["id"] for row in result["updates"]], ["A"])
        self.assertEqual([row["id"] for row in result["skipped"]], ["B"])
        self.assertTrue(result["requires_explicit_approval"])

    def test_bulk_audit_fields_preserve_original_and_score(self) -> None:
        result = bulk_plan([{"id": "A", "original_value": "VP Sales", "confidence": 0.92}])
        audit = result["updates"][0]["audit_fields"]
        self.assertEqual(audit["original_value"], "VP Sales")
        self.assertEqual(audit["confidence_score"], 0.92)


if __name__ == "__main__":
    unittest.main()
