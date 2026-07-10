from __future__ import annotations

import unittest

from deduplication_rules import choose_master, confidence_tier, jaro_winkler, metaphone, score_pair


class DeduplicationRulesTests(unittest.TestCase):
    def test_published_example_is_96_point_65(self) -> None:
        result = score_pair(email=0.95, phone=1, name=0.92, company=1)
        self.assertEqual(result["score"], 96.65)
        self.assertEqual(result["tier"], "SAFE_AUTO_MERGE")

    def test_other_published_examples(self) -> None:
        self.assertEqual(score_pair(email=1, phone=0, name=0.9, company=0)["score"], 53.0)
        self.assertEqual(score_pair(email=0, phone=1, name=0, company=0)["score"], 35.0)

    def test_tier_boundaries(self) -> None:
        self.assertEqual(confidence_tier(95), "SAFE_AUTO_MERGE")
        self.assertEqual(confidence_tier(85), "REVIEW_RECOMMENDED")
        self.assertEqual(confidence_tier(70), "MANUAL_REVIEW")
        self.assertEqual(confidence_tier(69.99), "DO_NOT_MERGE")

    def test_invalid_signal_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            score_pair(email=1.1, phone=0, name=0, company=0)

    def test_name_helpers(self) -> None:
        self.assertGreater(jaro_winkler("Jonathan", "Jonathon"), 0.85)
        self.assertEqual(metaphone("Smith"), metaphone("Smyth"))

    def test_verified_email_decides_master_first(self) -> None:
        result = choose_master({"verified_email": True}, {"verified_email": False, "verified_phone": True})
        self.assertEqual(result, {"master": "A", "reason": "verified_email"})

    def test_verified_phone_is_second(self) -> None:
        result = choose_master({"verified_phone": False}, {"verified_phone": True})
        self.assertEqual(result, {"master": "B", "reason": "verified_phone"})

    def test_activity_rule_requires_high_vs_low(self) -> None:
        result = choose_master({"activities_90d": 10}, {"activities_90d": 4})
        self.assertEqual(result, {"master": "A", "reason": "activity_count"})

    def test_older_record_wins_at_thirty_day_difference(self) -> None:
        result = choose_master({"created_epoch_days": 100}, {"created_epoch_days": 130})
        self.assertEqual(result, {"master": "A", "reason": "creation_date"})

    def test_completeness_then_modified_tie_break(self) -> None:
        self.assertEqual(choose_master({"completeness": 0.85}, {"completeness": 0.70})["master"], "A")
        self.assertEqual(choose_master({"modified_epoch": 1}, {"modified_epoch": 2})["master"], "B")


if __name__ == "__main__":
    unittest.main()
