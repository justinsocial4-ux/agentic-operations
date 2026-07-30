#!/usr/bin/env python3

import copy
import unittest

from selection_preview import BOUNDARY, build_preview, render_preview_output


def policy(**changes):
    value = {
        "policy_id": "ASP-12",
        "version": "3",
        "owner": "Morgan Lee",
        "effective_date": "2026-07-01",
        "candidate_population_id": "POP-ABM-Q3",
        "candidate_population_receipt_id": "pop-receipt-7",
        "candidate_population_status": "COMPLETE",
        "candidate_count": 0,
        "cutoff": "2026-07-10T00:00:00Z",
        "purpose": "NEW_ADDITIONS_PREVIEW",
        "entity_level": "legal_account",
        "capacity": 2,
        "reviewer": "Quinn Hale",
        "action_approval_status": "NOT_APPROVED",
        "proposed_use": "review possible Q3 ABM additions",
        "records_system": "fictional CRM account records",
        "reversal_path": "discard preview; no state changed",
        "score_policy_id": "APS-7",
        "score_policy_version": "2",
        "model_card_status": "NOT_PRESENT",
        "construct_validation_status": "NOT_PRESENT",
        "mature_outcome_cohort_status": "NOT_PRESENT",
        "calibration_status": "NOT_PRESENT",
        "uncertainty_analysis_status": "NOT_PRESENT",
        "prospective_evaluation_status": "NOT_PRESENT",
        "treatment_design_status": "NOT_PRESENT",
        "causal_evidence_status": "NOT_PRESENT",
        "predictive_approval_status": "NOT_PRESENT",
        "identity_policy_status": "APPROVED",
        "eligibility_policy_status": "APPROVED",
        "selection_policy_status": "APPROVED",
        "privacy_scope_status": "APPROVED",
        "downstream_use_status": "APPROVED",
    }
    value.update(changes)
    return value


def candidate(account_id, score="80", **changes):
    value = {
        "account_id": account_id,
        "population_membership_status": "VERIFIED_MEMBER",
        "population_membership_receipt_id": "membership-" + account_id,
        "identity_status": "RESOLVED",
        "identity_receipt_id": "identity-" + account_id,
        "eligibility_status": "VERIFIED_ELIGIBLE",
        "eligibility_receipt_id": "eligibility-" + account_id,
        "score_status": "AVAILABLE",
        "score": score,
        "score_receipt_id": "score-" + account_id,
        "score_policy_id": "APS-7",
        "score_policy_version": "2",
        "evidence_cutoff": "2026-07-09T00:00:00Z",
        "segment_receipt_id": "segment-" + account_id,
    }
    value.update(changes)
    return value


def document(candidates, selected_policy=None):
    selected = copy.deepcopy(selected_policy or policy())
    selected["candidate_count"] = len(candidates)
    return {"policy": selected, "candidates": candidates}


class SelectionPreviewTests(unittest.TestCase):
    def test_global_selection(self):
        result = build_preview(document([candidate("a", "91"), candidate("b", "82"), candidate("c", "70")]))
        self.assertEqual(result["status"], "SELECTION_PREVIEW_AVAILABLE")
        self.assertEqual(result["selection_account_ids"], ["a", "b"])
        dispositions = {row["account_id"]: row["disposition"] for row in result["candidate_receipts"]}
        self.assertEqual(dispositions, {"a": "SELECTED_PREVIEW", "b": "SELECTED_PREVIEW", "c": "NOT_SELECTED_CAPACITY"})

    def test_boundary_tie_blocks_final_list(self):
        result = build_preview(document([candidate("a", "91"), candidate("b", "74"), candidate("c", "74")]))
        self.assertEqual(result["status"], "BOUNDARY_TIE_REVIEW_REQUIRED")
        self.assertEqual(result["selection_account_ids"], [])
        self.assertEqual(result["provisional_above_boundary"], ["a"])
        self.assertCountEqual(result["review_account_ids"], ["b", "c"])
        dispositions = {row["account_id"]: row["disposition"] for row in result["candidate_receipts"]}
        self.assertEqual(dispositions["a"], "PROVISIONAL_ABOVE_BOUNDARY")
        self.assertEqual(dispositions["b"], "BOUNDARY_TIE_REVIEW")

    def test_unknown_identity_blocks(self):
        row = candidate("a", "91", identity_status="UNKNOWN")
        result = build_preview(document([row]))
        self.assertEqual(result["status"], "CANDIDATE_EVIDENCE_REVIEW_REQUIRED")

    def test_unknown_population_membership_blocks(self):
        row = candidate("a", population_membership_status="UNKNOWN")
        result = build_preview(document([row]))
        self.assertEqual(result["candidate_receipts"][0]["disposition"], "POPULATION_MEMBERSHIP_REVIEW_REQUIRED")

    def test_ambiguous_identity_blocks(self):
        row = candidate("a", "91", identity_status="AMBIGUOUS")
        self.assertEqual(build_preview(document([row]))["candidate_receipts"][0]["disposition"], "IDENTITY_REVIEW_REQUIRED")

    def test_unknown_eligibility_blocks(self):
        row = candidate("a", "91", eligibility_status="UNKNOWN")
        self.assertEqual(build_preview(document([row]))["candidate_receipts"][0]["disposition"], "ELIGIBILITY_REVIEW_REQUIRED")

    def test_verified_ineligible_excludes_without_blocking(self):
        rows = [candidate("a", "91", eligibility_status="VERIFIED_INELIGIBLE"), candidate("b", "82")]
        result = build_preview(document(rows))
        self.assertEqual(result["selection_account_ids"], ["b"])
        self.assertEqual(result["status"], "SELECTION_PREVIEW_AVAILABLE_CAPACITY_UNFILLED")

    def test_unknown_score_blocks(self):
        row = candidate("a", None, score_status="UNKNOWN")
        result = build_preview(document([row]))
        self.assertEqual(result["candidate_receipts"][0]["disposition"], "SCORE_EVIDENCE_REVIEW_REQUIRED")

    def test_nonavailable_score_cannot_carry_points(self):
        row = candidate("a", "50", score_status="CONFLICT")
        with self.assertRaises(ValueError):
            build_preview(document([row]))

    def test_available_score_cannot_be_null(self):
        with self.assertRaises(ValueError):
            build_preview(document([candidate("a", None)]))

    def test_float_score_rejected(self):
        with self.assertRaises(ValueError):
            build_preview(document([candidate("a", 80.5)]))

    def test_nonfinite_score_rejected(self):
        with self.assertRaises(ValueError):
            build_preview(document([candidate("a", "NaN")]))

    def test_out_of_bounds_score_rejected(self):
        with self.assertRaises(ValueError):
            build_preview(document([candidate("a", "101")]))

    def test_score_policy_conflict_blocks(self):
        row = candidate("a", "80", score_policy_version="1")
        result = build_preview(document([row]))
        self.assertEqual(result["candidate_receipts"][0]["disposition"], "SCORE_POLICY_CONFLICT")

    def test_post_cutoff_evidence_blocks(self):
        row = candidate("a", "80", evidence_cutoff="2026-07-11T00:00:00Z")
        self.assertEqual(build_preview(document([row]))["candidate_receipts"][0]["disposition"], "EVIDENCE_AFTER_CUTOFF")

    def test_post_cutoff_ineligible_evidence_still_blocks(self):
        row = candidate("a", "80", eligibility_status="VERIFIED_INELIGIBLE", evidence_cutoff="2026-07-11T00:00:00Z")
        self.assertEqual(build_preview(document([row]))["candidate_receipts"][0]["disposition"], "EVIDENCE_AFTER_CUTOFF")

    def test_pre_effective_evidence_blocks(self):
        row = candidate("a", "80", evidence_cutoff="2026-06-30T23:59:59Z")
        self.assertEqual(build_preview(document([row]))["candidate_receipts"][0]["disposition"], "EVIDENCE_BEFORE_POLICY_EFFECTIVE")

    def test_missing_trace_receipt_rejected(self):
        row = candidate("a")
        del row["score_receipt_id"]
        with self.assertRaises(ValueError):
            build_preview(document([row]))

    def test_timezone_required(self):
        row = candidate("a", "80", evidence_cutoff="2026-07-09T00:00:00")
        with self.assertRaises(ValueError):
            build_preview(document([row]))

    def test_non_utc_timestamp_rejected(self):
        row = candidate("a", "80", evidence_cutoff="2026-07-09T01:00:00+01:00")
        with self.assertRaises(ValueError):
            build_preview(document([row]))

    def test_duplicate_account_rejected(self):
        with self.assertRaises(ValueError):
            build_preview(document([candidate("a"), candidate("a")]))

    def test_policy_approval_blocks(self):
        selected = policy(privacy_scope_status="PENDING")
        result = build_preview(document([candidate("a")], selected))
        self.assertEqual(result["gate"], "POLICY_APPROVAL_REQUIRED")
        self.assertEqual(result["candidate_receipts"], [])

    def test_population_incomplete_blocks(self):
        selected = policy(candidate_population_status="INCOMPLETE")
        result = build_preview(document([candidate("a")], selected))
        self.assertEqual(result["status"], "CANDIDATE_POPULATION_INCOMPLETE")

    def test_population_count_mismatch_blocks(self):
        payload = document([candidate("a")])
        payload["policy"]["candidate_count"] = 2
        self.assertEqual(build_preview(payload)["status"], "CANDIDATE_POPULATION_COUNT_MISMATCH")

    def test_policy_missing_field_rejected(self):
        selected = policy()
        del selected["owner"]
        with self.assertRaises(ValueError):
            build_preview(document([], selected))

    def test_invalid_purpose_rejected(self):
        with self.assertRaises(ValueError):
            build_preview(document([], policy(purpose="EXECUTE")))

    def test_invalid_policy_state_rejected(self):
        with self.assertRaises(ValueError):
            build_preview(document([], policy(selection_policy_status="TYPO")))

    def test_policy_effective_after_cutoff_rejected(self):
        with self.assertRaises(ValueError):
            build_preview(document([], policy(effective_date="2026-07-11")))

    def test_non_legal_entity_rejected(self):
        with self.assertRaises(ValueError):
            build_preview(document([], policy(entity_level="contact")))

    def test_capacity_boolean_rejected(self):
        with self.assertRaises(ValueError):
            build_preview(document([], policy(capacity=True)))

    def test_zero_capacity_is_valid(self):
        result = build_preview(document([candidate("a")], policy(capacity=0)))
        self.assertEqual(result["selection_account_ids"], [])
        self.assertEqual(result["status"], "SELECTION_PREVIEW_AVAILABLE")

    def test_segment_selection(self):
        selected = policy(capacity=3, segment_field="region", segment_slots={"NA": 2, "EMEA": 1})
        rows = [
            candidate("a", "90", segment_status="VERIFIED", segment="NA"),
            candidate("b", "80", segment_status="VERIFIED", segment="NA"),
            candidate("c", "70", segment_status="VERIFIED", segment="NA"),
            candidate("d", "60", segment_status="VERIFIED", segment="EMEA"),
        ]
        result = build_preview(document(rows, selected))
        self.assertEqual(result["selection_account_ids"], ["a", "b", "d"])

    def test_segment_boundary_tie_blocks(self):
        selected = policy(capacity=1, segment_field="region", segment_slots={"NA": 1})
        rows = [candidate("a", "80", segment_status="VERIFIED", segment="NA"), candidate("b", "80", segment_status="VERIFIED", segment="NA")]
        self.assertEqual(build_preview(document(rows, selected))["status"], "BOUNDARY_TIE_REVIEW_REQUIRED")

    def test_segment_receipt_required(self):
        selected = policy(capacity=1, segment_field="region", segment_slots={"NA": 1})
        row = candidate("a", "80", segment_status="VERIFIED", segment="NA")
        del row["segment_receipt_id"]
        with self.assertRaises(ValueError):
            build_preview(document([row], selected))

    def test_segment_slots_must_sum_to_capacity(self):
        with self.assertRaises(ValueError):
            build_preview(document([], policy(capacity=3, segment_field="region", segment_slots={"NA": 1})))

    def test_segment_pair_required(self):
        with self.assertRaises(ValueError):
            build_preview(document([], policy(segment_field="region")))

    def test_unknown_segment_blocks(self):
        selected = policy(capacity=1, segment_field="region", segment_slots={"NA": 1})
        row = candidate("a", "80", segment_status="UNKNOWN", segment=None)
        result = build_preview(document([row], selected))
        self.assertEqual(result["candidate_receipts"][0]["disposition"], "SEGMENT_REVIEW_REQUIRED")

    def test_unrecognized_segment_blocks(self):
        selected = policy(capacity=1, segment_field="region", segment_slots={"NA": 1})
        row = candidate("a", "80", segment_status="VERIFIED", segment="APAC")
        result = build_preview(document([row], selected))
        self.assertEqual(result["candidate_receipts"][0]["disposition"], "SEGMENT_POLICY_CONFLICT")

    def test_unfilled_segment_slots_are_not_redistributed(self):
        selected = policy(capacity=3, segment_field="region", segment_slots={"NA": 1, "EMEA": 2})
        rows = [candidate("a", "90", segment_status="VERIFIED", segment="NA"), candidate("b", "80", segment_status="VERIFIED", segment="NA")]
        result = build_preview(document(rows, selected))
        self.assertEqual(result["selection_account_ids"], ["a"])
        self.assertEqual(result["status"], "SELECTION_PREVIEW_AVAILABLE_CAPACITY_UNFILLED")
        dispositions = {row["account_id"]: row["disposition"] for row in result["candidate_receipts"]}
        self.assertEqual(dispositions["b"], "NOT_SELECTED_CAPACITY")

    def test_approved_action_does_not_execute(self):
        result = build_preview(document([candidate("a")], policy(action_approval_status="APPROVED")))
        self.assertEqual(result["execution_state"], "OUT_OF_SCOPE")
        self.assertEqual(result["boundary"], BOUNDARY)

    def test_equal_score_display_is_deterministic_without_membership_tiebreak(self):
        rows = [candidate("b", "80"), candidate("a", "80")]
        result = build_preview(document(rows))
        self.assertEqual(result["selection_account_ids"], ["a", "b"])
        self.assertIn("DISPLAY_ONLY", result["capacity_receipts"][0]["presentation_order"])

    def test_input_not_mutated(self):
        payload = document([candidate("a")])
        original = copy.deepcopy(payload)
        build_preview(payload)
        self.assertEqual(payload, original)

    def test_validation_receipt_is_helper_owned(self):
        result=build_preview(document([candidate("a")]))
        self.assertEqual(result["validation_receipt"]["model_card_status"],"NOT_PRESENT")
        self.assertEqual(result["validation_receipt"]["interpretation"],"POLICY_ARITHMETIC_ONLY")
        self.assertFalse(result["action_authorized"])
        self.assertNotIn("model_card_status",result["policy_receipt"])
        self.assertNotIn("segment_slots",result["policy_receipt"])

    def test_invalid_validation_state_rejected(self):
        with self.assertRaises(ValueError):
            build_preview(document([candidate("a")], policy(model_card_status="NONE")))

    def test_exact_output_renderer(self):
        rendered=render_preview_output(build_preview(document([candidate("a")])))
        self.assertTrue(rendered.startswith("```json\n{"))
        self.assertTrue(rendered.endswith(BOUNDARY))
        self.assertEqual(rendered.count(BOUNDARY),2)

    def test_renderer_rejects_nonobject(self):
        with self.assertRaises(ValueError): render_preview_output([])

    def test_segment_bucket_count_printed_once(self):
        selected=policy(capacity=3,segment_field="region",segment_slots={"NA":2,"EMEA":1})
        rows=[candidate("acct-a","91",segment_status="VERIFIED",segment="NA"),candidate("acct-b","74",segment_status="VERIFIED",segment="NA"),candidate("acct-c","74",segment_status="VERIFIED",segment="NA"),candidate("acct-d","80",segment_status="VERIFIED",segment="EMEA"),candidate("acct-e","60",segment_status="VERIFIED",segment="EMEA")]
        rendered=render_preview_output(build_preview(document(rows,selected)))
        self.assertEqual(rendered.count('"rankable_count": 3'),1)
        self.assertNotIn("actually",rendered.casefold())
        for word in ("small cohort","large cohort","enough data","limited data","insufficient data"):
            self.assertNotIn(word,rendered.casefold())


if __name__ == "__main__":
    unittest.main()
