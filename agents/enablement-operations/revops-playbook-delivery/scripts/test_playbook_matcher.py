#!/usr/bin/env python3
import unittest
from decimal import Decimal

from playbook_matcher import catalog_eligibility, coverage, match_catalog, normalize


class PlaybookMatcherTests(unittest.TestCase):
    def setUp(self):
        self.context = {"stage": "negotiation", "competitor": "acme_crm", "vertical": "healthcare", "objection": "pricing"}
        self.base = {"playbook_id": "pb-acme", "version": "3", "title": "Acme CRM Competitive Guide", "owner": "enablement", "approved": True, "active": True, "valid_from": "2026-01-01", "valid_to": "2026-12-31", "superseded": False, "workspace": "sales-a", "access_groups": ["field-sales"], "criteria": {"stage": ["negotiation"], "competitor": ["acme_crm"]}, "priority": 10}

    def test_normalize(self): self.assertEqual(normalize(" ACME   CRM "), "acme crm")
    def test_eligible(self): self.assertTrue(catalog_eligibility(self.base, "2026-07-10", ["field-sales"])["eligible"])
    def test_unapproved(self): self.assertIn("UNAPPROVED", catalog_eligibility(dict(self.base, approved=False), "2026-07-10", ["field-sales"])["reasons"])
    def test_inactive(self): self.assertIn("INACTIVE", catalog_eligibility(dict(self.base, active=False), "2026-07-10", ["field-sales"])["reasons"])
    def test_superseded(self): self.assertIn("SUPERSEDED", catalog_eligibility(dict(self.base, superseded=True), "2026-07-10", ["field-sales"])["reasons"])
    def test_outside_dates(self): self.assertIn("OUTSIDE_ACTIVE_DATES", catalog_eligibility(self.base, "2027-01-01", ["field-sales"])["reasons"])
    def test_access_denied(self): self.assertIn("ACCESS_DENIED", catalog_eligibility(self.base, "2026-07-10", ["support"])["reasons"])
    def test_unique_match(self): self.assertEqual(match_catalog(self.context, [self.base], "2026-07-10", ["field-sales"], "sales-a")["status"], "RECOMMENDED_PREVIEW")
    def test_wrong_workspace_excluded(self): self.assertEqual(match_catalog(self.context, [self.base], "2026-07-10", ["field-sales"], "sales-b")["status"], "NO_MATCH")
    def test_nonmatching_criteria(self): self.assertEqual(match_catalog(dict(self.context, competitor="other"), [self.base], "2026-07-10", ["field-sales"], "sales-a")["status"], "NO_MATCH")
    def test_missing_required_context(self): self.assertEqual(match_catalog({"stage": "negotiation"}, [self.base], "2026-07-10", ["field-sales"], "sales-a")["status"], "CONTEXT_REQUIRED")
    def test_priority_selects_unique_best(self):
        second = dict(self.base, playbook_id="pb-price", title="Pricing", priority=20, criteria={"stage": ["negotiation"], "objection": ["pricing"]})
        self.assertEqual(match_catalog(self.context, [self.base, second], "2026-07-10", ["field-sales"], "sales-a")["recommended"]["playbook_id"], "pb-acme")
    def test_tied_priority_ambiguous(self):
        second = dict(self.base, playbook_id="pb-price", title="Pricing")
        self.assertEqual(match_catalog(self.context, [self.base, second], "2026-07-10", ["field-sales"], "sales-a")["status"], "AMBIGUOUS_MATCH")
    def test_duplicate_id_fails(self):
        with self.assertRaises(ValueError): match_catalog(self.context, [self.base, dict(self.base)], "2026-07-10", ["field-sales"], "sales-a")
    def test_bad_priority_fails(self):
        with self.assertRaises(ValueError): catalog_eligibility(dict(self.base, priority=1.5), "2026-07-10", ["field-sales"])
    def test_bad_date_fails(self):
        with self.assertRaises(ValueError): catalog_eligibility(dict(self.base, valid_to="soon"), "2026-07-10", ["field-sales"])
    def test_reversed_dates_fail(self):
        with self.assertRaises(ValueError): catalog_eligibility(dict(self.base, valid_from="2026-12-31", valid_to="2026-01-01"), "2026-07-10", ["field-sales"])
    def test_empty_access_group_fails(self):
        with self.assertRaises(ValueError): catalog_eligibility(dict(self.base, access_groups=[""]), "2026-07-10", [""])
    def test_empty_criteria_value_fails(self):
        bad = dict(self.base, criteria={"stage": [""]})
        with self.assertRaises(ValueError): match_catalog(self.context, [bad], "2026-07-10", ["field-sales"], "sales-a")
    def test_coverage(self): self.assertEqual(coverage(8, 10), Decimal("0.8"))
    def test_bad_coverage_fails(self):
        with self.assertRaises(ValueError): coverage(11, 10)


if __name__ == "__main__": unittest.main()
