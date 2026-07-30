#!/usr/bin/env python3
"""Adversarial tests for certification-assignment evidence review."""

from __future__ import annotations

import copy
import json
import unittest

from certification_evidence import (
    REQUIRED_PROHIBITIONS,
    render_review_output,
    review_certification_evidence,
)


def fixture() -> dict:
    assignment = {
        "assignment_id": "assignment-alpha",
        "anonymous_worker_id": "anonymous-worker-alpha",
        "anonymous_group_id": "anonymous-group-alpha",
        "certification_id": "certification-product-alpha",
        "rule_id": "rule-certification-state",
        "due_at": "2026-08-01T00:00:00Z",
        "no_due_date_rule": False,
        "assignment_source_id": "source-assignment-export",
        "assignment_source_version": "version-one",
        "assignment_source_kind": "customer-supplied-pseudonymous-assignment-evidence",
        "assignment_schema_id": "schema-assignment",
        "assignment_schema_version": "version-one",
        "assignment_authorization_receipt_id": "authorization-assignment",
        "assignment_receipt_id": "receipt-assignment-alpha",
        "assigned_at": "2026-07-02T09:00:00Z",
        "assignment_captured_at": "2026-07-02T10:00:00Z",
        "completion_source_id": "source-completion-export",
        "completion_source_version": "version-one",
        "completion_source_kind": "customer-supplied-pseudonymous-completion-evidence",
        "completion_schema_id": "schema-completion",
        "completion_schema_version": "version-one",
        "completion_authorization_receipt_id": "authorization-completion",
        "completion_observation_receipt_id": "receipt-completion-alpha",
        "completion_state": "recorded-incomplete",
        "completed_at": None,
        "completion_observed_at": "2026-07-11T12:00:00Z",
        "completion_captured_at": "2026-07-11T12:30:00Z",
        "recipient_role_ids": ["role-authorized-reviewer"],
        "retention_rule_id": "retention-rule-alpha",
    }
    return {
        "review_id": "review-alpha",
        "policy": {
            "policy_id": "policy-certification-evidence",
            "policy_version": "version-one",
            "owner_role_id": "role-policy-owner",
            "human_reviewer_role_id": "role-human-reviewer",
            "effective_at": "2026-07-01T00:00:00Z",
            "expires_at": "2026-12-31T23:59:59Z",
            "cutoff_at": "2026-07-11T12:00:00Z",
            "reviewed_at": "2026-07-11T14:00:00Z",
            "timezone": "America/Guayaquil",
            "approved_purpose": "pseudonymous_certification_assignment_evidence_review",
            "workforce_review_receipt_id": "receipt-workforce-review",
            "privacy_review_receipt_id": "receipt-privacy-review",
            "worker_notice_program_receipt_id": "receipt-worker-notice-program",
            "worker_access_path_receipt_id": "receipt-worker-access-path",
            "worker_response_path_receipt_id": "receipt-worker-response-path",
            "correction_path_receipt_id": "receipt-correction-path",
            "appeal_path_receipt_id": "receipt-appeal-path",
            "recipient_policy_receipt_id": "receipt-recipient-policy",
            "retention_policy_receipt_id": "receipt-retention-policy",
            "assignment_policy_receipt_id": "receipt-assignment-policy",
            "retention_rule_id": "retention-rule-alpha",
            "allowed_recipient_role_ids": ["role-authorized-reviewer"],
            "prohibited_uses": sorted(REQUIRED_PROHIBITIONS),
            "assignment_rules": [{
                "anonymous_group_id": "anonymous-group-alpha",
                "certification_id": "certification-product-alpha",
            }],
            "state_rule": {
                "rule_id": "rule-certification-state",
                "recorded_complete_state": "RECORDED_COMPLETE_BY_CUTOFF",
                "recorded_incomplete_due_at_or_before_state": "RECORDED_INCOMPLETE_DUE_AT_OR_BEFORE_CUTOFF",
                "recorded_incomplete_due_after_state": "RECORDED_INCOMPLETE_DUE_AFTER_CUTOFF",
                "no_due_date_rule_state": "NO_DUE_DATE_RULE",
            },
            "source_bindings": [
                {
                    "source_id": "source-assignment-export",
                    "source_version": "version-one",
                    "source_kind": "customer-supplied-pseudonymous-assignment-evidence",
                    "schema_id": "schema-assignment",
                    "schema_version": "version-one",
                    "authorization_receipt_id": "authorization-assignment",
                    "authorization_effective_at": "2026-07-01T00:00:00Z",
                    "authorization_expires_at": "2026-12-31T23:59:59Z",
                },
                {
                    "source_id": "source-completion-export",
                    "source_version": "version-one",
                    "source_kind": "customer-supplied-pseudonymous-completion-evidence",
                    "schema_id": "schema-completion",
                    "schema_version": "version-one",
                    "authorization_receipt_id": "authorization-completion",
                    "authorization_effective_at": "2026-07-01T00:00:00Z",
                    "authorization_expires_at": "2026-12-31T23:59:59Z",
                },
            ],
        },
        "population": {
            "population_receipt_id": "population-alpha",
            "complete": True,
            "assignment_ids": ["assignment-alpha"],
            "observed_at": "2026-07-11T12:00:00Z",
            "captured_at": "2026-07-11T13:00:00Z",
        },
        "assignments": [assignment],
    }


class CertificationEvidenceTests(unittest.TestCase):
    def assert_invalid(self, mutate) -> None:
        document = fixture()
        mutate(document)
        with self.assertRaises(ValueError):
            review_certification_evidence(document)

    def test_recorded_incomplete_due_after(self):
        result = review_certification_evidence(fixture())
        self.assertEqual(result["assignments"][0]["evidence_state"], "RECORDED_INCOMPLETE_DUE_AFTER_CUTOFF")
        self.assertEqual(result["state_summary"], [{"state": "RECORDED_INCOMPLETE_DUE_AFTER_CUTOFF", "assignment_count": 1}])
        self.assertFalse(result["compliance_authorized"])
        self.assertFalse(result["worker_judgment_authorized"])
        self.assertFalse(result["action_authorized"])

    def test_recorded_incomplete_due_at_cutoff(self):
        document = fixture()
        document["assignments"][0]["due_at"] = document["policy"]["cutoff_at"]
        state = review_certification_evidence(document)["assignments"][0]["evidence_state"]
        self.assertEqual(state, "RECORDED_INCOMPLETE_DUE_AT_OR_BEFORE_CUTOFF")

    def test_recorded_incomplete_due_before(self):
        document = fixture()
        document["assignments"][0]["due_at"] = "2026-07-10T12:00:00Z"
        state = review_certification_evidence(document)["assignments"][0]["evidence_state"]
        self.assertEqual(state, "RECORDED_INCOMPLETE_DUE_AT_OR_BEFORE_CUTOFF")

    def test_no_due_date_rule(self):
        document = fixture()
        document["assignments"][0].update(due_at=None, no_due_date_rule=True)
        state = review_certification_evidence(document)["assignments"][0]["evidence_state"]
        self.assertEqual(state, "NO_DUE_DATE_RULE")

    def test_recorded_complete(self):
        document = fixture()
        document["assignments"][0].update(
            completion_state="recorded-complete", completed_at="2026-07-10T09:00:00Z"
        )
        state = review_certification_evidence(document)["assignments"][0]["evidence_state"]
        self.assertEqual(state, "RECORDED_COMPLETE_BY_CUTOFF")

    def test_unresolved_states(self):
        expected = {
            "missing": "EVIDENCE_MISSING",
            "conflicting": "EVIDENCE_CONFLICT",
            "suppressed": "SUPPRESSED",
            "unauthorized": "UNAUTHORIZED",
        }
        for input_state, output_state in expected.items():
            with self.subTest(input_state=input_state):
                document = fixture()
                document["assignments"][0].update(
                    completion_state=input_state,
                    completion_observation_receipt_id=None,
                    completed_at=None,
                )
                state = review_certification_evidence(document)["assignments"][0]["evidence_state"]
                self.assertEqual(state, output_state)

    def test_render_is_deterministic_and_exact(self):
        result = review_certification_evidence(fixture())
        first = render_review_output(result)
        self.assertEqual(first, render_review_output(result))
        self.assertTrue(first.startswith("{"))
        self.assertTrue(first.endswith("}\n\n"))
        self.assertEqual(json.loads(first), result)

    def test_unknown_root_key_rejected(self):
        self.assert_invalid(lambda d: d.update({"notes": "forbidden"}))

    def test_unknown_assignment_key_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update({"worker_name": "Person"}))

    def test_performance_field_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update({"quota_attainment": 0.5}))

    def test_worker_prefix_required(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(anonymous_worker_id="worker-alpha"))

    def test_group_prefix_required(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(anonymous_group_id="group-alpha"))

    def test_complete_population_required(self):
        self.assert_invalid(lambda d: d["population"].update(complete=False))

    def test_empty_population_rejected(self):
        self.assert_invalid(lambda d: d["population"].update(assignment_ids=[]))

    def test_duplicate_population_id_rejected(self):
        self.assert_invalid(lambda d: d["population"].update(assignment_ids=["assignment-alpha", "assignment-alpha"]))

    def test_extra_assignment_rejected(self):
        def mutate(d):
            extra = copy.deepcopy(d["assignments"][0])
            extra["assignment_id"] = "assignment-beta"
            extra["assignment_receipt_id"] = "receipt-assignment-beta"
            extra["completion_observation_receipt_id"] = "receipt-completion-beta"
            d["assignments"].append(extra)
        self.assert_invalid(mutate)

    def test_missing_declared_assignment_rejected(self):
        self.assert_invalid(lambda d: d["population"]["assignment_ids"].append("assignment-beta"))

    def test_duplicate_assignment_rejected(self):
        self.assert_invalid(lambda d: d["assignments"].append(copy.deepcopy(d["assignments"][0])))

    def test_wrong_rule_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(rule_id="rule-other"))

    def test_wrong_purpose_rejected(self):
        self.assert_invalid(lambda d: d["policy"].update(approved_purpose="worker-compliance"))

    def test_missing_prohibition_rejected(self):
        self.assert_invalid(lambda d: d["policy"]["prohibited_uses"].remove("worker-monitoring"))

    def test_governance_receipts_must_be_separate(self):
        self.assert_invalid(lambda d: d["policy"].update(privacy_review_receipt_id=d["policy"]["workforce_review_receipt_id"]))

    def test_invalid_timezone_rejected(self):
        self.assert_invalid(lambda d: d["policy"].update(timezone="Mars/Olympus"))

    def test_expired_policy_rejected(self):
        self.assert_invalid(lambda d: d["policy"].update(expires_at="2026-07-11T13:00:00Z"))

    def test_cutoff_after_review_rejected(self):
        self.assert_invalid(lambda d: d["policy"].update(reviewed_at="2026-07-11T11:00:00Z"))

    def test_wrong_exact_state_rejected(self):
        self.assert_invalid(lambda d: d["policy"]["state_rule"].update(recorded_complete_state="COMPLETE"))

    def test_assignment_rule_required(self):
        self.assert_invalid(lambda d: d["policy"].update(assignment_rules=[]))

    def test_duplicate_assignment_rule_rejected(self):
        self.assert_invalid(lambda d: d["policy"]["assignment_rules"].append(copy.deepcopy(d["policy"]["assignment_rules"][0])))

    def test_group_certification_pair_must_be_approved(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(certification_id="certification-other"))

    def test_both_source_kinds_required(self):
        self.assert_invalid(lambda d: d["policy"]["source_bindings"].pop())

    def test_duplicate_source_binding_rejected(self):
        self.assert_invalid(lambda d: d["policy"]["source_bindings"].append(copy.deepcopy(d["policy"]["source_bindings"][0])))

    def test_unapproved_assignment_source_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(assignment_source_id="source-other"))

    def test_unapproved_completion_source_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(completion_source_id="source-other"))

    def test_assignment_schema_conflict_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(assignment_schema_id="schema-other"))

    def test_completion_authorization_conflict_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(completion_authorization_receipt_id="authorization-other"))

    def test_assignment_before_policy_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(assigned_at="2026-06-30T09:00:00Z"))

    def test_assignment_capture_before_assignment_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(assignment_captured_at="2026-07-02T08:00:00Z"))

    def test_population_observation_must_equal_cutoff(self):
        self.assert_invalid(lambda d: d["population"].update(observed_at="2026-07-11T11:59:59Z"))

    def test_population_capture_after_review_rejected(self):
        self.assert_invalid(lambda d: d["population"].update(captured_at="2026-07-11T14:00:01Z"))

    def test_completion_observation_must_equal_cutoff(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(completion_observed_at="2026-07-11T11:59:59Z"))

    def test_completion_capture_after_population_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(completion_captured_at="2026-07-11T13:00:01Z"))

    def test_due_rule_conflict_with_null_due(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(due_at=None))

    def test_due_rule_conflict_with_present_due(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(no_due_date_rule=True))

    def test_due_before_assignment_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(due_at="2026-07-02T08:59:59Z"))

    def test_recorded_complete_requires_completed_at(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(completion_state="recorded-complete"))

    def test_completion_before_assignment_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(
            completion_state="recorded-complete", completed_at="2026-07-02T08:00:00Z"
        ))

    def test_completion_after_cutoff_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(
            completion_state="recorded-complete", completed_at="2026-07-11T12:00:01Z"
        ))

    def test_recorded_incomplete_forbids_completed_at(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(completed_at="2026-07-10T09:00:00Z"))

    def test_unresolved_evidence_forbids_receipt(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(completion_state="missing"))

    def test_unresolved_evidence_forbids_completed_at(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(
            completion_state="missing", completion_observation_receipt_id=None, completed_at="2026-07-10T09:00:00Z"
        ))

    def test_completion_receipt_cannot_be_reused(self):
        def mutate(d):
            second = copy.deepcopy(d["assignments"][0])
            second["assignment_id"] = "assignment-beta"
            second["assignment_receipt_id"] = "receipt-assignment-beta"
            d["assignments"].append(second)
            d["population"]["assignment_ids"].append("assignment-beta")
        self.assert_invalid(mutate)

    def test_assignment_receipt_cannot_be_reused(self):
        def mutate(d):
            second = copy.deepcopy(d["assignments"][0])
            second["assignment_id"] = "assignment-beta"
            second["completion_observation_receipt_id"] = "receipt-completion-beta"
            d["assignments"].append(second)
            d["population"]["assignment_ids"].append("assignment-beta")
        self.assert_invalid(mutate)

    def test_unapproved_recipient_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(recipient_role_ids=["role-manager"]))

    def test_empty_recipient_rejected(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(recipient_role_ids=[]))

    def test_retention_rule_must_match_policy(self):
        self.assert_invalid(lambda d: d["assignments"][0].update(retention_rule_id="retention-rule-other"))

    def test_output_has_no_forbidden_inference_keys(self):
        rendered = render_review_output(review_certification_evidence(fixture())).lower()
        for token in ('"worker_name"', '"email"', '"manager"', '"score"', '"priority"', '"compliant"', '"ready"'):
            self.assertNotIn(token, rendered)

    def test_three_state_summary_counts_once(self):
        document = fixture()
        complete = copy.deepcopy(document["assignments"][0])
        complete.update(
            assignment_id="assignment-beta",
            anonymous_worker_id="anonymous-worker-beta",
            assignment_receipt_id="receipt-assignment-beta",
            completion_observation_receipt_id="receipt-completion-beta",
            completion_state="recorded-complete",
            completed_at="2026-07-10T09:00:00Z",
        )
        missing = copy.deepcopy(document["assignments"][0])
        missing.update(
            assignment_id="assignment-gamma",
            anonymous_worker_id="anonymous-worker-gamma",
            assignment_receipt_id="receipt-assignment-gamma",
            completion_observation_receipt_id=None,
            completion_state="missing",
            completed_at=None,
        )
        document["assignments"].extend([complete, missing])
        document["population"]["assignment_ids"].extend(["assignment-beta", "assignment-gamma"])
        result = review_certification_evidence(document)
        self.assertEqual(result["state_summary"], [
            {"state": "EVIDENCE_MISSING", "assignment_count": 1},
            {"state": "RECORDED_COMPLETE_BY_CUTOFF", "assignment_count": 1},
            {"state": "RECORDED_INCOMPLETE_DUE_AFTER_CUTOFF", "assignment_count": 1},
        ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
