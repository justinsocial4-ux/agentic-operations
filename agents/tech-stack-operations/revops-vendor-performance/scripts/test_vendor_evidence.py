#!/usr/bin/env python3
import unittest
from decimal import Decimal

from vendor_evidence import assess_numeric, availability, currency_total, rate, summarize_states, validate_evidence


class VendorEvidenceTests(unittest.TestCase):
    def test_rate(self): self.assertEqual(rate(18, 20), Decimal("0.9"))
    def test_zero_denominator_is_unavailable(self): self.assertIsNone(rate(0, 0))
    def test_rate_numerator_too_large_fails(self):
        with self.assertRaises(ValueError): rate(21, 20)
    def test_rate_bool_fails(self):
        with self.assertRaises(ValueError): rate(True, 1)

    def test_availability_exact(self):
        result = availability("43200", "60", "90")
        self.assertEqual((result["eligible_minutes"], result["available_minutes"]), (Decimal("43140"), Decimal("43050")))
        self.assertEqual(result["availability_pct"], Decimal("43050") / Decimal("43140") * Decimal("100"))
    def test_availability_zero_clock_indeterminate(self):
        self.assertEqual(availability("60", "60", "0")["status"], "INDETERMINATE")
    def test_exclusions_over_total_fail(self):
        with self.assertRaises(ValueError): availability("10", "11", "0")
    def test_downtime_over_eligible_fails(self):
        with self.assertRaises(ValueError): availability("10", "1", "10")
    def test_float_minutes_fail(self):
        with self.assertRaises(ValueError): availability(10.0, "0", "1")

    def test_numeric_met(self): self.assertEqual(assess_numeric("99.95", "99.9", ">="), "MET")
    def test_numeric_not_met(self): self.assertEqual(assess_numeric("99.79", "99.9", ">="), "NOT_MET")
    def test_numeric_lower_is_better(self): self.assertEqual(assess_numeric("3", "4", "<="), "MET")
    def test_missing_is_indeterminate(self): self.assertEqual(assess_numeric(None, "4", "<="), "INDETERMINATE")
    def test_incomplete_is_indeterminate(self): self.assertEqual(assess_numeric("3", "4", "<=", complete=False), "INDETERMINATE")
    def test_not_applicable_precedes_missing(self): self.assertEqual(assess_numeric(None, None, ">=", applicable=False), "NOT_APPLICABLE")
    def test_conflict_precedes_value(self): self.assertEqual(assess_numeric("100", "99", ">=", conflicting=True), "CONFLICTING")
    def test_conflict_precedes_not_applicable(self): self.assertEqual(assess_numeric("100", "99", ">=", applicable=False, conflicting=True), "CONFLICTING")
    def test_invalid_comparator_fails(self):
        with self.assertRaises(ValueError): assess_numeric("1", "2", "~")
    def test_non_boolean_flag_fails(self):
        with self.assertRaises(ValueError): assess_numeric("1", "2", ">=", complete="yes")

    def evidence_rows(self):
        return [
            {"evidence_id": "E-1", "evidence_kind": "CONTRACTUAL", "source_id": "contract-1", "source_version": "v3", "extracted_at": "2026-07-10T12:00:00Z"},
            {"evidence_id": "E-2", "evidence_kind": "CUSTOMER_OBSERVED", "source_id": "monitor-1", "source_version": "snapshot-9", "extracted_at": "2026-07-10T12:01:00Z"},
        ]

    def test_valid_evidence(self): self.assertEqual(validate_evidence(self.evidence_rows())["evidence_count"], 2)
    def test_duplicate_evidence_fails(self):
        rows = self.evidence_rows()
        with self.assertRaises(ValueError): validate_evidence(rows + [dict(rows[0])])
    def test_bad_evidence_kind_fails(self):
        rows = self.evidence_rows()
        rows[0]["evidence_kind"] = "TRUSTED"
        with self.assertRaises(ValueError): validate_evidence(rows)
    def test_missing_provenance_fails(self):
        rows = self.evidence_rows()
        rows[0]["source_version"] = ""
        with self.assertRaises(ValueError): validate_evidence(rows)
    def test_unattributed_is_explicitly_allowed(self):
        rows = self.evidence_rows()
        rows[0]["evidence_kind"] = "UNATTRIBUTED"
        self.assertEqual(validate_evidence(rows)["status"], "VALID")

    def amount_rows(self):
        return [
            {"record_id": "I-1", "amount": "1000.25", "currency": "USD"},
            {"record_id": "I-2", "amount": "99.75", "currency": "usd"},
        ]

    def test_currency_total(self): self.assertEqual(currency_total(self.amount_rows(), "USD")["total"], Decimal("1100.00"))
    def test_empty_currency_rows_are_indeterminate(self):
        self.assertEqual(currency_total([], "USD"), {"status": "INDETERMINATE", "currency": "USD", "record_count": 0, "total": None})
    def test_mixed_currency_fails(self):
        rows = self.amount_rows()
        rows[1]["currency"] = "EUR"
        with self.assertRaisesRegex(ValueError, "MIXED_CURRENCY"): currency_total(rows, "USD")
    def test_duplicate_amount_fails(self):
        rows = self.amount_rows()
        with self.assertRaises(ValueError): currency_total(rows + [dict(rows[0])], "USD")
    def test_float_amount_fails(self):
        rows = self.amount_rows()
        rows[0]["amount"] = 1.2
        with self.assertRaises(ValueError): currency_total(rows, "USD")

    def assessment_rows(self):
        return [
            {"requirement_id": "R-1", "state": "NOT_MET"},
            {"requirement_id": "R-2", "state": "INDETERMINATE"},
            {"requirement_id": "R-3", "state": "MET"},
            {"requirement_id": "R-4", "state": "CONFLICTING"},
        ]

    def test_state_summary(self):
        result = summarize_states(self.assessment_rows())
        self.assertEqual((result["MET"], result["NOT_MET"], result["INDETERMINATE"], result["CONFLICTING"], result["NOT_APPLICABLE"]), (1, 1, 1, 1, 0))
    def test_state_summary_permutation_invariant(self):
        rows = self.assessment_rows()
        self.assertEqual(summarize_states(rows), summarize_states(list(reversed(rows))))
    def test_duplicate_requirement_fails(self):
        rows = self.assessment_rows()
        with self.assertRaises(ValueError): summarize_states(rows + [dict(rows[0])])
    def test_invalid_state_fails(self):
        rows = self.assessment_rows()
        rows[0]["state"] = "HEALTHY"
        with self.assertRaises(ValueError): summarize_states(rows)


if __name__ == "__main__":
    unittest.main()
