#!/usr/bin/env python3

import copy
import json
import unittest

from signal_evidence import REQUIRED_PROHIBITIONS, render_review_output, review_signal_evidence


def fixture():
    binding = {
        "source_id": "source-observations",
        "source_version": "snapshot-alpha",
        "source_kind": "customer-supplied-pseudonymous-signal-evidence",
        "schema_id": "schema-signal",
        "schema_version": "schema-alpha",
        "authorization_id": "authorization-alpha",
        "authorization_effective_at": "2026-07-01T00:00:00Z",
        "authorization_expires_at": None,
        "collection_authority_receipt_id": "collection-alpha",
        "purpose_compatibility_receipt_id": "purpose-alpha",
        "notice_receipt_id": "notice-alpha",
        "objection_sync_receipt_id": "objection-sync-alpha",
        "retention_receipt_id": "retention-alpha",
        "allowed_event_type_ids": ["pricing-page-observation", "review-site-observation"],
    }
    population = {
        "population_receipt_id": "population-alpha",
        "source_id": "source-observations",
        "source_version": "snapshot-alpha",
        "source_kind": "customer-supplied-pseudonymous-signal-evidence",
        "schema_id": "schema-signal",
        "schema_version": "schema-alpha",
        "authorization_id": "authorization-alpha",
        "complete": True,
        "observation_ids": ["observation-alpha", "observation-beta", "observation-gamma"],
        "observed_at": "2026-07-10T10:00:00Z",
        "captured_at": "2026-07-10T12:00:00Z",
    }
    common = {
        "population_receipt_id": "population-alpha",
        "source_id": "source-observations",
        "source_version": "snapshot-alpha",
        "source_kind": "customer-supplied-pseudonymous-signal-evidence",
        "schema_id": "schema-signal",
        "schema_version": "schema-alpha",
        "authorization_id": "authorization-alpha",
        "captured_at": "2026-07-10T12:00:00Z",
    }
    return {
        "review_id": "review-alpha",
        "policy": {
            "policy_id": "policy-alpha",
            "policy_version": "version-alpha",
            "owner_role_id": "policy-owner",
            "human_reviewer_role_id": "human-reviewer",
            "effective_at": "2026-07-01T00:00:00Z",
            "expires_at": None,
            "cutoff_at": "2026-07-11T00:00:00Z",
            "observation_window_start": "2026-07-01T00:00:00Z",
            "observation_window_end": "2026-07-10T23:59:59Z",
            "timezone": "America/Guayaquil",
            "approved_purpose": "pseudonymous_inbound_signal_evidence_review",
            "prohibited_uses": sorted(REQUIRED_PROHIBITIONS),
            "correction_path": "submit a new correction receipt",
            "objection_path": "submit an objection to the named human reviewer",
            "privacy_review_receipt_id": "privacy-alpha",
            "marketing_review_receipt_id": "marketing-alpha",
            "notice_program_receipt_id": "notice-program-alpha",
            "classification_rules": [
                {
                    "rule_id": "rule-pricing",
                    "event_type_id": "pricing-page-observation",
                    "max_age_seconds": 172800,
                    "matched_state": "OBSERVED_WITHIN_RULE_WINDOW",
                    "stale_state": "OBSERVED_OUTSIDE_RULE_WINDOW",
                },
                {
                    "rule_id": "rule-review",
                    "event_type_id": "review-site-observation",
                    "max_age_seconds": 604800,
                    "matched_state": "OBSERVED_WITHIN_RULE_WINDOW",
                    "stale_state": "OBSERVED_OUTSIDE_RULE_WINDOW",
                },
            ],
            "source_bindings": [binding],
        },
        "source_populations": [population],
        "observations": [
            {
                **common,
                "observation_id": "observation-alpha",
                "pseudonymous_organization_id": "anonymous-org-alpha",
                "event_type_id": "pricing-page-observation",
                "evidence_state": "observed",
                "occurred_at": "2026-07-10T10:00:00Z",
                "evidence_receipt_ids": ["event-alpha"],
            },
            {
                **common,
                "observation_id": "observation-beta",
                "pseudonymous_organization_id": "anonymous-org-beta",
                "event_type_id": "review-site-observation",
                "evidence_state": "missing",
                "occurred_at": None,
                "evidence_receipt_ids": [],
            },
            {
                **common,
                "observation_id": "observation-gamma",
                "pseudonymous_organization_id": "anonymous-org-gamma",
                "event_type_id": "pricing-page-observation",
                "evidence_state": "suppressed",
                "occurred_at": None,
                "evidence_receipt_ids": ["suppression-alpha"],
            },
        ],
    }


class SignalEvidenceTests(unittest.TestCase):
    def review(self, value=None):
        return review_signal_evidence(fixture() if value is None else value)

    def test_happy_path_states(self):
        states = [row["event_receipt"]["result_state"] for row in self.review()["observation_receipts"]]
        self.assertEqual(states, ["OBSERVED_WITHIN_RULE_WINDOW", "EVIDENCE_MISSING", "SUPPRESSED"])

    def test_summary_counts_once(self):
        self.assertEqual(self.review()["state_summary"], {
            "EVIDENCE_MISSING": 1, "OBSERVED_WITHIN_RULE_WINDOW": 1, "SUPPRESSED": 1,
        })

    def test_no_inference_or_action(self):
        result = self.review()
        self.assertFalse(result["inference_authorized"]); self.assertFalse(result["action_authorized"])
        self.assertTrue(all(not row["inference_authorized"] and not row["action_authorized"] for row in result["observation_receipts"]))

    def test_human_review_required(self):
        self.assertEqual(self.review()["review_state"], "HUMAN_REVIEW_REQUIRED")

    def test_exact_renderer(self):
        rendered = render_review_output(self.review())
        self.assertTrue(rendered.startswith("{")); self.assertTrue(rendered.endswith("}\n\n"))
        self.assertEqual(json.loads(rendered), self.review())

    def test_deterministic_renderer(self):
        self.assertEqual(render_review_output(self.review()), render_review_output(self.review()))

    def test_observations_sorted(self):
        data = fixture(); data["observations"].reverse()
        self.assertEqual([x["observation_id"] for x in self.review(data)["observation_receipts"]],
                         ["observation-alpha", "observation-beta", "observation-gamma"])

    def test_stale_rule_state(self):
        data = fixture(); data["observations"][0]["occurred_at"] = "2026-07-08T00:00:00Z"
        self.assertEqual(self.review(data)["observation_receipts"][0]["event_receipt"]["result_state"],
                         "OBSERVED_OUTSIDE_RULE_WINDOW")

    def test_exact_boundary_is_within(self):
        data = fixture(); data["observations"][0]["occurred_at"] = "2026-07-09T00:00:00Z"
        self.assertEqual(self.review(data)["observation_receipts"][0]["event_receipt"]["result_state"],
                         "OBSERVED_WITHIN_RULE_WINDOW")

    def test_conflict_preserved(self):
        data = fixture(); row = data["observations"][1]
        row["evidence_state"] = "conflicting"; row["evidence_receipt_ids"] = ["conflict-a", "conflict-b"]
        self.assertEqual(self.review(data)["observation_receipts"][1]["event_receipt"]["result_state"], "EVIDENCE_CONFLICT")

    def test_unauthorized_preserved(self):
        data = fixture(); row = data["observations"][1]
        row["evidence_state"] = "unauthorized"; row["evidence_receipt_ids"] = ["control-alpha"]
        self.assertEqual(self.review(data)["observation_receipts"][1]["event_receipt"]["result_state"], "UNAUTHORIZED")

    def test_direct_organization_identifier_rejected(self):
        data = fixture(); data["observations"][0]["pseudonymous_organization_id"] = "acme-corporation"
        self.assertRaises(ValueError, self.review, data)

    def test_email_rejected_as_extra_field(self):
        data = fixture(); data["observations"][0]["email"] = "person@example.test"
        self.assertRaises(ValueError, self.review, data)

    def test_domain_rejected_as_extra_field(self):
        data = fixture(); data["observations"][0]["domain"] = "example.test"
        self.assertRaises(ValueError, self.review, data)

    def test_ip_rejected_as_extra_field(self):
        data = fixture(); data["observations"][0]["ip_address"] = "192.0.2.1"
        self.assertRaises(ValueError, self.review, data)

    def test_score_rejected_as_extra_field(self):
        data = fixture(); data["observations"][0]["intent_score"] = 0.9
        self.assertRaises(ValueError, self.review, data)

    def test_recommendation_rejected_as_extra_field(self):
        data = fixture(); data["observations"][0]["recommended_action"] = "contact"
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_observation_rejected(self):
        data = fixture(); data["observations"].append(copy.deepcopy(data["observations"][0]))
        self.assertRaises(ValueError, self.review, data)

    def test_missing_observation_rejected(self):
        data = fixture(); data["observations"].pop()
        self.assertRaises(ValueError, self.review, data)

    def test_extra_observation_rejected(self):
        data = fixture(); data["source_populations"][0]["observation_ids"].pop()
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_declared_observation_rejected(self):
        data = fixture(); data["source_populations"][0]["observation_ids"].append("observation-alpha")
        self.assertRaises(ValueError, self.review, data)

    def test_incomplete_population_rejected(self):
        data = fixture(); data["source_populations"][0]["complete"] = False
        self.assertRaises(ValueError, self.review, data)

    def test_empty_population_rejected(self):
        data = fixture(); data["source_populations"][0]["observation_ids"] = []; data["observations"] = []
        self.assertRaises(ValueError, self.review, data)

    def test_unapproved_event_rejected(self):
        data = fixture(); data["observations"][0]["event_type_id"] = "unapproved-mail-event"
        self.assertRaises(ValueError, self.review, data)

    def test_missing_state_rejects_receipt(self):
        data = fixture(); data["observations"][1]["evidence_receipt_ids"] = ["invented"]
        self.assertRaises(ValueError, self.review, data)

    def test_missing_state_rejects_occurrence(self):
        data = fixture(); data["observations"][1]["occurred_at"] = "2026-07-10T00:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_observed_requires_receipt(self):
        data = fixture(); data["observations"][0]["evidence_receipt_ids"] = []
        self.assertRaises(ValueError, self.review, data)

    def test_observed_rejects_multiple_receipts(self):
        data = fixture(); data["observations"][0]["evidence_receipt_ids"] = ["a", "b"]
        self.assertRaises(ValueError, self.review, data)

    def test_conflict_requires_two_receipts(self):
        data = fixture(); row = data["observations"][1]; row["evidence_state"] = "conflicting"; row["evidence_receipt_ids"] = ["one"]
        self.assertRaises(ValueError, self.review, data)

    def test_suppressed_requires_receipt(self):
        data = fixture(); data["observations"][2]["evidence_receipt_ids"] = []
        self.assertRaises(ValueError, self.review, data)

    def test_occurrence_after_capture_rejected(self):
        data = fixture(); data["observations"][0]["occurred_at"] = "2026-07-10T13:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_occurrence_outside_window_rejected(self):
        data = fixture(); data["observations"][0]["occurred_at"] = "2026-06-30T23:59:59Z"
        self.assertRaises(ValueError, self.review, data)

    def test_future_capture_rejected(self):
        data = fixture(); data["source_populations"][0]["captured_at"] = "2026-07-12T00:00:00Z"
        for row in data["observations"]: row["captured_at"] = "2026-07-12T00:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_capture_mismatch_rejected(self):
        data = fixture(); data["observations"][0]["captured_at"] = "2026-07-10T12:00:01Z"
        self.assertRaises(ValueError, self.review, data)

    def test_bad_timezone_rejected(self):
        data = fixture(); data["policy"]["timezone"] = "Mars/Base"
        self.assertRaises(ValueError, self.review, data)

    def test_wrong_purpose_rejected(self):
        data = fixture(); data["policy"]["approved_purpose"] = "target-people"
        self.assertRaises(ValueError, self.review, data)

    def test_missing_prohibition_rejected(self):
        data = fixture(); data["policy"]["prohibited_uses"].remove("buying-intent-inference")
        self.assertRaises(ValueError, self.review, data)

    def test_expired_policy_rejected(self):
        data = fixture(); data["policy"]["expires_at"] = "2026-07-10T00:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_expired_authorization_rejected(self):
        data = fixture(); data["policy"]["source_bindings"][0]["authorization_expires_at"] = "2026-07-10T00:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_authorization_after_window_start_rejected(self):
        data = fixture(); data["policy"]["source_bindings"][0]["authorization_effective_at"] = "2026-07-02T00:00:00Z"
        self.assertRaises(ValueError, self.review, data)

    def test_rule_without_source_event_rejected_only_if_binding_unknown(self):
        data = fixture(); data["policy"]["source_bindings"][0]["allowed_event_type_ids"].append("unknown-event")
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_event_rule_rejected(self):
        data = fixture(); data["policy"]["classification_rules"].append(copy.deepcopy(data["policy"]["classification_rules"][0]))
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_rule_id_across_event_types_rejected(self):
        data = fixture(); data["policy"]["classification_rules"][1]["rule_id"] = "rule-pricing"
        self.assertRaises(ValueError, self.review, data)

    def test_bad_rule_state_rejected(self):
        data = fixture(); data["policy"]["classification_rules"][0]["matched_state"] = "HIGH_INTENT"
        self.assertRaises(ValueError, self.review, data)

    def test_float_rule_window_rejected(self):
        data = fixture(); data["policy"]["classification_rules"][0]["max_age_seconds"] = 1.5
        self.assertRaises(ValueError, self.review, data)

    def test_negative_rule_window_rejected(self):
        data = fixture(); data["policy"]["classification_rules"][0]["max_age_seconds"] = -1
        self.assertRaises(ValueError, self.review, data)

    def test_unknown_root_key_rejected(self):
        data = fixture(); data["send_alert"] = True
        self.assertRaises(ValueError, self.review, data)

    def test_unknown_policy_key_rejected(self):
        data = fixture(); data["policy"]["default_intent_score"] = 0.8
        self.assertRaises(ValueError, self.review, data)

    def test_unknown_binding_key_rejected(self):
        data = fixture(); data["policy"]["source_bindings"][0]["vendor_claim"] = "compliant"
        self.assertRaises(ValueError, self.review, data)

    def test_duplicate_evidence_receipts_rejected(self):
        data = fixture(); data["observations"][0]["evidence_receipt_ids"] = ["event-alpha", "event-alpha"]
        self.assertRaises(ValueError, self.review, data)

    def test_non_utc_timestamp_rejected(self):
        data = fixture(); data["observations"][0]["occurred_at"] = "2026-07-10T10:00:00-05:00"
        self.assertRaises(ValueError, self.review, data)

    def test_source_lineage_mismatch_rejected(self):
        data = fixture(); data["observations"][0]["schema_version"] = "schema-beta"
        self.assertRaises(ValueError, self.review, data)

    def test_population_lineage_mismatch_rejected(self):
        data = fixture(); data["source_populations"][0]["authorization_id"] = "authorization-beta"
        self.assertRaises(ValueError, self.review, data)

    def test_source_kind_rejected(self):
        data = fixture(); data["policy"]["source_bindings"][0]["source_kind"] = "vendor-intent-score"
        self.assertRaises(ValueError, self.review, data)

    def test_required_receipts_are_rendered(self):
        source = self.review()["observation_receipts"][0]["source_receipt"]
        self.assertEqual(set(source), {
            "population_receipt_id", "source_id", "source_version", "schema_id", "schema_version",
            "authorization_id", "collection_authority_receipt_id", "purpose_compatibility_receipt_id",
            "notice_receipt_id", "objection_sync_receipt_id", "retention_receipt_id",
        })

    def test_full_source_binding_is_rendered(self):
        binding = self.review()["policy_receipt"]["source_bindings"][0]
        self.assertEqual(binding["authorization_effective_at"], "2026-07-01T00:00:00Z")
        self.assertEqual(binding["allowed_event_type_ids"], ["pricing-page-observation", "review-site-observation"])

    def test_duplicate_complete_population_for_binding_rejected(self):
        data = fixture(); second = copy.deepcopy(data["source_populations"][0])
        second["population_receipt_id"] = "population-beta"
        second["observation_ids"] = ["observation-delta"]
        data["source_populations"].append(second)
        self.assertRaises(ValueError, self.review, data)

    def test_no_forbidden_output_terms(self):
        rendered = render_review_output(self.review()).lower()
        for term in ("high intent", "low intent", "recommended contact", "email address", "account rank", "confidence score"):
            self.assertNotIn(term, rendered)


if __name__ == "__main__":
    unittest.main()
