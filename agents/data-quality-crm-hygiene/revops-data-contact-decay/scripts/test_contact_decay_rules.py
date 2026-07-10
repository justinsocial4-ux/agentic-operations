from __future__ import annotations

import unittest

from contact_decay_rules import classify, score_contact


class ContactDecayRulesTests(unittest.TestCase):
    def test_frozen_worked_example(self) -> None:
        result = score_contact({
            "email_engagement": 60,
            "phone_engagement": 35,
            "title_staleness": 20,
            "company_departure": 0,
            "overall_engagement": 60,
        })
        self.assertEqual(result["raw_score"], 38.75)
        self.assertEqual(result["display_score"], 39)
        self.assertEqual(result["tier"], "DECAYING")
        self.assertEqual(result["route"], "RE_ENGAGE")

    def test_contributions_match_frozen_weights(self) -> None:
        result = score_contact({
            "email_engagement": 60,
            "phone_engagement": 35,
            "title_staleness": 20,
            "company_departure": 0,
            "overall_engagement": 60,
        })
        self.assertEqual(result["contributions"], {
            "email_engagement": 21.0,
            "phone_engagement": 8.75,
            "title_staleness": 3.0,
            "company_departure": 0.0,
            "overall_engagement": 6.0,
        })

    def test_all_tier_boundaries(self) -> None:
        expected = {
            0: ("ACTIVE", "MONITOR"),
            30: ("ACTIVE", "MONITOR"),
            31: ("DECAYING", "RE_ENGAGE"),
            60: ("DECAYING", "RE_ENGAGE"),
            61: ("STALE", "ENRICH_AND_DECIDE"),
            85: ("STALE", "ENRICH_AND_DECIDE"),
            86: ("ARCHIVED_CANDIDATE", "ARCHIVE_RECOMMEND"),
            100: ("ARCHIVED_CANDIDATE", "ARCHIVE_RECOMMEND"),
        }
        for score, result in expected.items():
            with self.subTest(score=score):
                self.assertEqual(classify(score), result)

    def test_half_up_rounding(self) -> None:
        result = score_contact({name: 30.5 for name in (
            "email_engagement",
            "phone_engagement",
            "title_staleness",
            "company_departure",
            "overall_engagement",
        )})
        self.assertEqual(result["raw_score"], 30.5)
        self.assertEqual(result["display_score"], 31)

    def test_archival_route_requires_approval(self) -> None:
        result = score_contact({name: 100 for name in (
            "email_engagement",
            "phone_engagement",
            "title_staleness",
            "company_departure",
            "overall_engagement",
        )})
        self.assertTrue(result["requires_explicit_approval"])

    def test_non_archival_route_does_not_set_archive_approval_flag(self) -> None:
        result = score_contact({name: 60 for name in (
            "email_engagement",
            "phone_engagement",
            "title_staleness",
            "company_departure",
            "overall_engagement",
        )})
        self.assertFalse(result["requires_explicit_approval"])

    def test_missing_signal_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly"):
            score_contact({"email_engagement": 60})

    def test_extra_signal_fails_closed(self) -> None:
        signals = {name: 0 for name in (
            "email_engagement",
            "phone_engagement",
            "title_staleness",
            "company_departure",
            "overall_engagement",
        )}
        signals["unknown"] = 0
        with self.assertRaisesRegex(ValueError, "extra"):
            score_contact(signals)

    def test_out_of_range_and_nonfinite_values_fail_closed(self) -> None:
        baseline = {
            "email_engagement": 0,
            "phone_engagement": 0,
            "title_staleness": 0,
            "company_departure": 0,
            "overall_engagement": 0,
        }
        for invalid in (-1, 101, float("nan"), float("inf"), True):
            with self.subTest(invalid=invalid):
                signals = dict(baseline)
                signals["email_engagement"] = invalid
                with self.assertRaisesRegex(ValueError, "0 to 100"):
                    score_contact(signals)


if __name__ == "__main__":
    unittest.main()
