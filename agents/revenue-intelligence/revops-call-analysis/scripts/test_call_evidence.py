#!/usr/bin/env python3
import unittest
from decimal import Decimal

from call_evidence import annotation_receipt, policy_gate, transcript_receipt


class CallEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "recording_policy_id": "rec-v3",
            "analysis_use_policy_id": "use-v2",
            "requester_access_id": "access-17",
            "redaction_policy_id": "redact-v4",
            "retention_policy_id": "retain-v1",
            "downstream_use_policy_id": "downstream-v5",
            "policy_owner": "privacy-owner-2",
            "recording_scope_status": "APPROVED",
            "analysis_use_status": "APPROVED",
            "requester_access_status": "APPROVED",
            "redaction_scope_status": "APPROVED",
            "retention_handling_status": "APPROVED",
            "downstream_use_status": "APPROVED",
        }
        self.segments = [
            {"segment_id": "s1", "speaker_id": "rep-7", "start_ms": 60000, "end_ms": 90000, "text": "What budget has been approved?", "status": "verified"},
            {"segment_id": "s2", "speaker_id": "buyer-2", "start_ms": 100000, "end_ms": 130000, "text": "Our approved budget is capped at forty thousand.", "status": "verified"},
            {"segment_id": "s3", "speaker_id": "rep-7", "start_ms": 500000, "end_ms": 520000, "text": "I will send the security packet Friday.", "status": "verified"},
        ]

    def test_policy_gate_passes_complete_receipt(self):
        self.assertEqual(policy_gate(self.policy)["status"], "POLICY_EVIDENCE_PRESENT")

    def test_policy_gate_lists_missing_fields(self):
        result = policy_gate({"recording_policy_id": "rec-v3"})
        self.assertEqual(result["status"], "POLICY_EVIDENCE_REQUIRED")
        self.assertIn("requester_access_id", result["missing_fields"])

    def test_policy_gate_rejects_non_object(self):
        with self.assertRaises(ValueError): policy_gate([])

    def test_policy_gate_blocks_nonapproved_scope(self):
        result = policy_gate(dict(self.policy, downstream_use_status="DENIED"))
        self.assertEqual(result["status"], "POLICY_SCOPE_NOT_APPROVED")
        self.assertEqual(result["blocked_fields"], ["downstream_use_status"])

    def test_transcript_exact_coverage_and_speaker_time(self):
        result = transcript_receipt(self.segments, 600000, ["rep-7", "buyer-2"])
        self.assertEqual(result["union_coverage_ms"], 80000)
        self.assertEqual(result["speaker_ms"], {"buyer-2": 30000, "rep-7": 50000})
        self.assertEqual(result["coverage_ratio"], Decimal("0.1333333333333333333333333333"))

    def test_transcript_speaker_shares(self):
        result = transcript_receipt(self.segments, 600000, ["rep-7", "buyer-2"])
        self.assertEqual(result["speaker_share_of_segment_time"]["rep-7"], Decimal("0.625"))

    def test_transcript_unknown_speaker_requires_review(self):
        result = transcript_receipt(self.segments, 600000, ["rep-7"])
        self.assertEqual((result["speaker_status"], result["unknown_speaker_ids"]), ("SPEAKER_MAPPING_REVIEW", ["buyer-2"]))

    def test_transcript_overlap_is_disclosed(self):
        rows = self.segments[:2] + [{"segment_id": "s4", "speaker_id": "rep-7", "start_ms": 120000, "end_ms": 140000, "text": "Understood.", "status": "verified"}]
        result = transcript_receipt(rows, 600000, ["rep-7", "buyer-2"])
        self.assertEqual(result["overlap_ms"], 10000)

    def test_transcript_uncertain_and_redacted_time(self):
        rows = [dict(self.segments[0], status="uncertain"), dict(self.segments[1], status="redacted")]
        result = transcript_receipt(rows, 600000, ["rep-7", "buyer-2"])
        self.assertEqual((result["uncertain_segment_ms"], result["redacted_segment_ms"]), (30000, 30000))

    def test_transcript_duplicate_segment_fails(self):
        with self.assertRaises(ValueError): transcript_receipt(self.segments + [dict(self.segments[0])], 600000, ["rep-7", "buyer-2"])

    def test_transcript_out_of_bounds_fails(self):
        with self.assertRaises(ValueError): transcript_receipt([dict(self.segments[0], end_ms=700000)], 600000, ["rep-7"])

    def test_transcript_reverse_span_fails(self):
        with self.assertRaises(ValueError): transcript_receipt([dict(self.segments[0], start_ms=90000, end_ms=60000)], 600000, ["rep-7"])

    def test_transcript_bool_timestamp_fails(self):
        with self.assertRaises(ValueError): transcript_receipt([dict(self.segments[0], start_ms=False)], 600000, ["rep-7"])

    def test_transcript_empty_text_fails(self):
        with self.assertRaises(ValueError): transcript_receipt([dict(self.segments[0], text=" ")], 600000, ["rep-7"])

    def test_transcript_bad_status_fails(self):
        with self.assertRaises(ValueError): transcript_receipt([dict(self.segments[0], status="good")], 600000, ["rep-7"])

    def test_empty_transcript_is_explicit(self):
        result = transcript_receipt([], 600000, [])
        self.assertEqual((result["union_coverage_ms"], result["uncovered_ms"]), (0, 600000))

    def test_annotation_exact_quote_and_category(self):
        rows = [{"annotation_id": "a1", "segment_id": "s2", "category_id": "budget_constraint", "speaker_id": "buyer-2", "quote": "budget is capped at forty thousand", "review_status": "HUMAN_VERIFIED", "reviewer_id": "reviewer-4"}]
        result = annotation_receipt(rows, self.segments, ["budget_constraint"])
        self.assertEqual((result["status"], result["counts_by_category"]), ("ANNOTATIONS_REVIEWED", {"budget_constraint": 1}))
        self.assertEqual(result["human_verified_counts_by_category"], {"budget_constraint": 1})

    def test_model_candidate_requires_review(self):
        rows = [{"annotation_id": "a1", "segment_id": "s2", "category_id": "budget_constraint", "speaker_id": "buyer-2", "quote": "budget is capped", "review_status": "MODEL_CANDIDATE", "reviewer_id": None}]
        self.assertEqual(annotation_receipt(rows, self.segments, ["budget_constraint"])["status"], "ANNOTATION_REVIEW_REQUIRED")

    def test_annotation_nonexact_quote_fails(self):
        rows = [{"annotation_id": "a1", "segment_id": "s2", "category_id": "budget_constraint", "speaker_id": "buyer-2", "quote": "Budget about $40k", "review_status": "MODEL_CANDIDATE", "reviewer_id": None}]
        with self.assertRaises(ValueError): annotation_receipt(rows, self.segments, ["budget_constraint"])

    def test_annotation_unapproved_category_fails(self):
        rows = [{"annotation_id": "a1", "segment_id": "s2", "category_id": "high_risk", "speaker_id": "buyer-2", "quote": "approved budget", "review_status": "MODEL_CANDIDATE", "reviewer_id": None}]
        with self.assertRaisesRegex(ValueError, "TAXONOMY_REQUIRED"): annotation_receipt(rows, self.segments, ["budget_constraint"])

    def test_annotation_speaker_mismatch_fails(self):
        rows = [{"annotation_id": "a1", "segment_id": "s2", "category_id": "budget_constraint", "speaker_id": "rep-7", "quote": "approved budget", "review_status": "MODEL_CANDIDATE", "reviewer_id": None}]
        with self.assertRaises(ValueError): annotation_receipt(rows, self.segments, ["budget_constraint"])

    def test_human_verified_requires_reviewer(self):
        rows = [{"annotation_id": "a1", "segment_id": "s2", "category_id": "budget_constraint", "speaker_id": "buyer-2", "quote": "approved budget", "review_status": "HUMAN_VERIFIED", "reviewer_id": None}]
        with self.assertRaises(ValueError): annotation_receipt(rows, self.segments, ["budget_constraint"])

    def test_annotation_duplicate_id_fails(self):
        row = {"annotation_id": "a1", "segment_id": "s2", "category_id": "budget_constraint", "speaker_id": "buyer-2", "quote": "approved budget", "review_status": "MODEL_CANDIDATE", "reviewer_id": None}
        with self.assertRaises(ValueError): annotation_receipt([row, dict(row)], self.segments, ["budget_constraint"])

    def test_annotation_missing_segment_fails(self):
        rows = [{"annotation_id": "a1", "segment_id": "missing", "category_id": "budget_constraint", "speaker_id": "buyer-2", "quote": "approved budget", "review_status": "MODEL_CANDIDATE", "reviewer_id": None}]
        with self.assertRaises(ValueError): annotation_receipt(rows, self.segments, ["budget_constraint"])

    def test_rejected_annotation_is_counted_not_silenced(self):
        rows = [{"annotation_id": "a1", "segment_id": "s2", "category_id": "budget_constraint", "speaker_id": "buyer-2", "quote": "approved budget", "review_status": "REJECTED", "reviewer_id": "reviewer-4"}]
        result = annotation_receipt(rows, self.segments, ["budget_constraint"])
        self.assertEqual(result["counts_by_review_status"], {"REJECTED": 1})
        self.assertEqual(result["human_verified_counts_by_category"], {})

    def test_rejected_annotation_requires_reviewer(self):
        rows = [{"annotation_id": "a1", "segment_id": "s2", "category_id": "budget_constraint", "speaker_id": "buyer-2", "quote": "approved budget", "review_status": "REJECTED", "reviewer_id": None}]
        with self.assertRaises(ValueError): annotation_receipt(rows, self.segments, ["budget_constraint"])

    def test_redacted_segment_cannot_support_annotation(self):
        redacted = [dict(self.segments[1], status="redacted")]
        rows = [{"annotation_id": "a1", "segment_id": "s2", "category_id": "budget_constraint", "speaker_id": "buyer-2", "quote": "approved budget", "review_status": "MODEL_CANDIDATE", "reviewer_id": None}]
        with self.assertRaises(ValueError): annotation_receipt(rows, redacted, ["budget_constraint"])

    def test_uncertain_segment_cannot_be_human_verified(self):
        uncertain = [dict(self.segments[1], status="uncertain")]
        rows = [{"annotation_id": "a1", "segment_id": "s2", "category_id": "budget_constraint", "speaker_id": "buyer-2", "quote": "approved budget", "review_status": "HUMAN_VERIFIED", "reviewer_id": "reviewer-4"}]
        with self.assertRaises(ValueError): annotation_receipt(rows, uncertain, ["budget_constraint"])


if __name__ == "__main__":
    unittest.main()
