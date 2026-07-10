from __future__ import annotations

import unittest

from lead_account_matcher import (
    confidence_bucket,
    employee_count_match,
    jaro_winkler,
    normalize_company,
    normalize_domain,
    phonetic_match,
    rank_candidates,
    score_match,
    soundex,
)


class LeadAccountMatcherTests(unittest.TestCase):
    def test_normalization(self) -> None:
        self.assertEqual(normalize_company(" Acme Corporation "), "acme")
        self.assertEqual(normalize_domain("https://www.Acme.com/path"), "acme.com")

    def test_jaro_winkler_and_phonetic_helpers(self) -> None:
        self.assertEqual(jaro_winkler("Acme Corp", "Acme Corporation"), 1.0)
        self.assertEqual(soundex("Robert"), "R163")
        self.assertEqual(phonetic_match("Acme", "ACM"), 0.5)

    def test_employee_count_tolerance(self) -> None:
        self.assertEqual(employee_count_match(500, 480), 1.0)
        self.assertEqual(employee_count_match(500, 700), 0.0)
        self.assertEqual(employee_count_match(None, 480), 0.0)

    def test_published_example_is_94_point_3_high(self) -> None:
        result = score_match(
            name_similarity=0.92,
            domain_match=1,
            employee_count_match=1,
            location_match=1,
            phonetic_match=0.5,
        )
        self.assertEqual(result["score"], 94.3)
        self.assertEqual(result["bucket"], "HIGH")
        self.assertEqual(result["recommended_action"], "AUTO_ASSOCIATE_AFTER_APPROVAL")

    def test_old_ambiguous_prose_components_are_low_not_medium(self) -> None:
        result = score_match(
            name_similarity=0.88,
            domain_match=0,
            employee_count_match=1,
            location_match=1,
            phonetic_match=0.5,
        )
        self.assertEqual(result["score"], 62.7)
        self.assertEqual(result["bucket"], "LOW")

    def test_bucket_boundaries(self) -> None:
        self.assertEqual(confidence_bucket(90), "HIGH")
        self.assertEqual(confidence_bucket(75), "MEDIUM")
        self.assertEqual(confidence_bucket(74.99), "LOW")

    def test_invalid_threshold_order_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "review < auto"):
            confidence_bucket(80, auto_threshold=75, review_threshold=90)

    def test_component_out_of_range_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "phonetic_match"):
            score_match(
                name_similarity=1,
                domain_match=1,
                employee_count_match=1,
                location_match=1,
                phonetic_match=1,
            )

    def test_candidate_tie_break_order(self) -> None:
        ranked = rank_candidates(
            [
                {"account_id": "B", "score": 90, "exact_name_match": False, "domain_match": True, "employee_count_delta": 0.01},
                {"account_id": "A", "score": 90, "exact_name_match": True, "domain_match": False, "employee_count_delta": 0.20},
            ]
        )
        self.assertEqual(ranked[0]["account_id"], "A")


if __name__ == "__main__":
    unittest.main()
