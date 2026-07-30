#!/usr/bin/env python3
import unittest
from decimal import Decimal

from sequence_router import coverage, evaluate_eligibility, exact_map, match_sequences, normalize, resolve_enrollment


class SequenceRouterTests(unittest.TestCase):
    def setUp(self):
        self.evidence = {"qualified": True, "contactable": True, "suppressed": False, "do_not_contact": False, "hard_bounce": False, "owner_in_scope": True, "cooldown_clear": True, "frequency_clear": True, "active_enrollment_ids": []}
        self.profile = {"persona": "revenue_leader", "vertical": "saas", "engagement": "demo_request"}
        self.library = [{"sequence_id": "seq-7", "name": "Revenue Leader SaaS Demo", "active": True, "workspace": "team-a", "priority": 10, "target_personas": ["revenue_leader"], "target_verticals": ["saas"], "target_engagements": ["demo_request"], "wildcard_allowed": {}}]

    def test_normalize(self): self.assertEqual(normalize(" VP   SALES "), "vp sales")
    def test_exact_mapping(self): self.assertEqual(exact_map("VP Sales", {"vp sales": "revenue_leader"}), "revenue_leader")
    def test_missing_mapping_unknown(self): self.assertIsNone(exact_map(None, {"vp sales": "revenue_leader"}))
    def test_no_fuzzy_mapping(self): self.assertIsNone(exact_map("Vice President Sales", {"vp sales": "revenue_leader"}))
    def test_duplicate_normalized_key_fails(self):
        with self.assertRaises(ValueError): exact_map("a", {"A": "x", " a ": "y"})
    def test_eligible(self): self.assertEqual(evaluate_eligibility(self.evidence)["status"], "ELIGIBLE")
    def test_suppression_blocks(self):
        evidence = dict(self.evidence, suppressed=True)
        self.assertEqual(evaluate_eligibility(evidence)["status"], "INELIGIBLE")
    def test_active_enrollment_preserved_for_reconciliation(self):
        evidence = dict(self.evidence, active_enrollment_ids=["seq-old"])
        result = evaluate_eligibility(evidence)
        self.assertEqual(result["status"], "ELIGIBLE")
        self.assertEqual(result["checks"]["active_enrollment"], "PRESENT")
    def test_missing_contactability_unknown(self):
        evidence = dict(self.evidence, contactable=None)
        self.assertEqual(evaluate_eligibility(evidence)["status"], "ELIGIBILITY_UNKNOWN")
    def test_unique_match(self): self.assertEqual(match_sequences(self.profile, self.library, "team-a")["recommended"]["sequence_id"], "seq-7")
    def test_wrong_workspace_no_match(self): self.assertEqual(match_sequences(self.profile, self.library, "team-b")["status"], "NO_MATCH")
    def test_inactive_no_match(self):
        library = [dict(self.library[0], active=False)]
        self.assertEqual(match_sequences(self.profile, library, "team-a")["status"], "NO_MATCH")
    def test_missing_dimension_no_fallback(self):
        profile = dict(self.profile, engagement=None)
        self.assertEqual(match_sequences(profile, self.library, "team-a")["status"], "MAPPING_REQUIRED")
    def test_explicit_wildcard(self):
        library = [dict(self.library[0], target_verticals=["*"], wildcard_allowed={"vertical": True})]
        self.assertEqual(match_sequences(self.profile, library, "team-a")["status"], "RECOMMENDED_PREVIEW")
    def test_unapproved_wildcard_no_match(self):
        library = [dict(self.library[0], target_verticals=["*"], wildcard_allowed={"vertical": False})]
        self.assertEqual(match_sequences(self.profile, library, "team-a")["status"], "NO_MATCH")
    def test_tied_priority_ambiguous(self):
        other = dict(self.library[0], sequence_id="seq-8", name="Other")
        self.assertEqual(match_sequences(self.profile, self.library + [other], "team-a")["status"], "AMBIGUOUS_MATCH")
    def test_lower_priority_number_wins(self):
        other = dict(self.library[0], sequence_id="seq-8", name="Other", priority=20)
        self.assertEqual(match_sequences(self.profile, self.library + [other], "team-a")["recommended"]["sequence_id"], "seq-7")
    def test_duplicate_sequence_id_fails(self):
        with self.assertRaises(ValueError): match_sequences(self.profile, self.library + [dict(self.library[0])], "team-a")
    def test_non_integer_priority_fails(self):
        with self.assertRaises(ValueError): match_sequences(self.profile, [dict(self.library[0], priority=10.5)], "team-a")
    def test_clear_enrollment(self): self.assertEqual(resolve_enrollment("seq-7", []), "CLEAR_TO_PREVIEW")
    def test_same_enrollment_no_change(self): self.assertEqual(resolve_enrollment("seq-7", ["SEQ-7"]), "NO_CHANGE")
    def test_other_enrollment_conflict(self): self.assertEqual(resolve_enrollment("seq-7", ["seq-old"]), "ENROLLMENT_CONFLICT")
    def test_coverage(self): self.assertEqual(coverage(9, 10), Decimal("0.9"))
    def test_bad_coverage_fails(self):
        with self.assertRaises(ValueError): coverage(11, 10)


if __name__ == "__main__": unittest.main()
