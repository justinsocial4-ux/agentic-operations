#!/usr/bin/env python3
"""Tests for deterministic event follow-up-plan evidence review."""

from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPEC = importlib.util.spec_from_file_location("event_plan_evidence", HERE / "event_plan_evidence.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def base_document() -> dict:
    governance = {
        "operations_approval_receipt_id": "receipt-operations-approval",
        "security_review_receipt_id": "receipt-security-review",
        "privacy_review_receipt_id": "receipt-privacy-review",
        "legal_review_receipt_id": "receipt-legal-review",
        "lawful_basis_receipt_id": "receipt-lawful-basis",
        "collection_notice_receipt_id": "receipt-collection-notice",
        "direct_marketing_notice_receipt_id": "receipt-direct-marketing-notice",
        "objection_path_receipt_id": "receipt-objection-path",
        "suppression_policy_receipt_id": "receipt-suppression-policy",
        "correction_access_path_receipt_id": "receipt-correction-access-path",
        "recipient_policy_receipt_id": "receipt-recipient-policy",
        "retention_policy_receipt_id": "receipt-retention-policy",
        "followup_policy_receipt_id": "receipt-followup-policy",
    }
    return {
        "review_declaration": {
            "review_id": "review-alpha",
            "policy_id": "policy-alpha",
            "policy_version": "version-one",
            "event_id": "event-alpha",
            "event_version": "version-one",
            "reviewed_at": "2026-07-10T18:05:00Z",
            "recipient_role_id": "role-plan-reviewer",
            "review_authorization_receipt_id": "receipt-review-authorization",
            "participant_ids": ["participant-alpha", "participant-beta"],
        },
        "policy": {
            "policy_id": "policy-alpha",
            "policy_version": "version-one",
            "effective_at": "2026-07-01T00:00:00Z",
            "expires_at": "2026-07-31T23:59:59Z",
            "cutoff_at": "2026-07-10T18:00:00Z",
            "timezone": "UTC",
            "approved_purpose": MODULE.PURPOSE,
            "owner_role_id": "role-marketing-owner",
            "human_reviewer_role_id": "role-plan-reviewer",
            **governance,
            "allowed_recipient_role_ids": ["role-followup-owner", "role-plan-reviewer"],
            "prohibited_uses": sorted(MODULE.REQUIRED_PROHIBITIONS),
            "source_bindings": [{
                "source_id": "source-event-plan",
                "source_version": "version-one",
                "source_kind": MODULE.SOURCE_KIND,
                "schema_id": "schema-event-plan",
                "schema_version": "version-one",
                "authorization_receipt_id": "receipt-source-authorization",
                "authorization_effective_at": "2026-07-01T00:00:00Z",
                "authorization_expires_at": "2026-07-31T23:59:59Z",
                "query_receipt_id": "receipt-source-query",
                "page_receipt_id": "receipt-source-pages",
                "pseudonymization_receipt_id": "receipt-source-pseudonymization",
            }],
            "event_contracts": [{
                "event_id": "event-alpha",
                "event_version": "version-one",
                "source_id": "source-event-plan",
                "source_version": "version-one",
                "starts_at": "2026-07-10T13:00:00Z",
                "ends_at": "2026-07-10T17:00:00Z",
                "event_receipt_id": "receipt-event-alpha",
                "participation_definition_receipt_id": "receipt-participation-definition",
                "capture_policy_receipt_id": "receipt-capture-policy",
            }],
            "route_contracts": [{
                "route_id": "route-human-supplied",
                "route_version": "version-one",
                "event_id": "event-alpha",
                "event_version": "version-one",
                "owner_role_id": "role-followup-owner",
                "channel_id": "channel-approved",
                "authorization_effective_at": "2026-07-01T00:00:00Z",
                "authorization_expires_at": "2026-07-31T23:59:59Z",
                "window_opens_at": "2026-07-10T18:10:00Z",
                "window_closes_at": "2026-07-11T18:10:00Z",
                "route_receipt_id": "receipt-route-contract",
                "authorization_receipt_id": "receipt-route-authorization",
                "channel_policy_receipt_id": "receipt-channel-policy",
                "owner_policy_receipt_id": "receipt-owner-policy",
                "timing_policy_receipt_id": "receipt-timing-policy",
            }],
        },
        "source_populations": [{
            "source_id": "source-event-plan",
            "source_version": "version-one",
            "population_receipt_id": "receipt-plan-population",
            "complete": True,
            "plan_receipt_ids": ["receipt-plan-alpha", "receipt-plan-beta"],
        }],
        "followup_plan": [
            {
                "participant_id": "participant-alpha",
                "source_id": "source-event-plan",
                "source_version": "version-one",
                "plan_receipt_id": "receipt-plan-alpha",
                "participation_state": "eligible",
                "participation_state_receipt_id": "receipt-state-alpha",
                "route_id": "route-human-supplied",
                "route_version": "version-one",
                "owner_role_id": "role-followup-owner",
                "channel_id": "channel-approved",
                "assignment_receipt_id": "receipt-assignment-alpha",
                "planned_at": "2026-07-10T18:15:00Z",
                "observed_at": "2026-07-10T14:00:00Z",
                "captured_at": "2026-07-10T14:05:00Z",
            },
            {
                "participant_id": "participant-beta",
                "source_id": "source-event-plan",
                "source_version": "version-one",
                "plan_receipt_id": "receipt-plan-beta",
                "participation_state": "suppressed",
                "participation_state_receipt_id": "receipt-state-beta",
                "route_id": None,
                "route_version": None,
                "owner_role_id": None,
                "channel_id": None,
                "assignment_receipt_id": None,
                "planned_at": None,
                "observed_at": "2026-07-10T15:00:00Z",
                "captured_at": "2026-07-10T15:05:00Z",
            },
        ],
    }


def review(doc: dict) -> dict:
    return MODULE.review_event_plan_evidence(doc)


class EventPlanEvidenceTests(unittest.TestCase):
    def assert_invalid(self, mutate) -> None:
        doc = base_document()
        mutate(doc)
        with self.assertRaises(ValueError):
            review(doc)

    def test_match_and_suppression(self):
        result = review(base_document())
        self.assertEqual(result["evidence_state"], "SUPPRESSED")
        self.assertEqual(result["participant_plan_reviews"][0]["evidence_state"], "CUSTOMER_EVENT_PLAN_EVIDENCE_MATCHED")
        self.assertEqual(result["participant_plan_reviews"][1]["evidence_state"], "SUPPRESSED")

    def test_unknown_route_nonmatch(self):
        doc = base_document()
        doc["followup_plan"][0]["route_id"] = "route-unknown"
        result = review(doc)
        self.assertEqual(result["participant_plan_reviews"][0]["evidence_state"], "CUSTOMER_EVENT_PLAN_EVIDENCE_NOT_MATCHED")
        self.assertIsNone(result["participant_plan_reviews"][0]["route_receipt"])

    def test_owner_mismatch_nonmatch(self):
        doc = base_document()
        doc["followup_plan"][0]["owner_role_id"] = "role-plan-reviewer"
        result = review(doc)
        self.assertEqual(result["participant_plan_reviews"][0]["evidence_state"], "CUSTOMER_EVENT_PLAN_EVIDENCE_NOT_MATCHED")

    def test_channel_mismatch_nonmatch(self):
        doc = base_document()
        doc["followup_plan"][0]["channel_id"] = "channel-other"
        self.assertEqual(review(doc)["participant_plan_reviews"][0]["evidence_state"], "CUSTOMER_EVENT_PLAN_EVIDENCE_NOT_MATCHED")

    def test_planned_outside_route_window_nonmatch(self):
        doc = base_document()
        doc["followup_plan"][0]["planned_at"] = "2026-07-12T18:15:00Z"
        self.assertEqual(review(doc)["participant_plan_reviews"][0]["evidence_state"], "CUSTOMER_EVENT_PLAN_EVIDENCE_NOT_MATCHED")

    def test_all_unresolved_states(self):
        expected = {
            "missing": "EVIDENCE_MISSING", "conflicting": "EVIDENCE_CONFLICT",
            "suppressed": "SUPPRESSED", "unauthorized": "UNAUTHORIZED",
        }
        for state, output in expected.items():
            with self.subTest(state=state):
                doc = base_document()
                doc["followup_plan"][0].update({
                    "participation_state": state, "route_id": None, "route_version": None,
                    "owner_role_id": None, "channel_id": None, "assignment_receipt_id": None,
                    "planned_at": None,
                })
                self.assertEqual(review(doc)["participant_plan_reviews"][0]["evidence_state"], output)

    def test_unresolved_precedence(self):
        doc = base_document()
        doc["followup_plan"][0].update({
            "participation_state": "unauthorized", "route_id": None, "route_version": None,
            "owner_role_id": None, "channel_id": None, "assignment_receipt_id": None,
            "planned_at": None,
        })
        self.assertEqual(review(doc)["evidence_state"], "UNAUTHORIZED")

    def test_all_actions_false(self):
        self.assertEqual(set(review(base_document())["action_authorization"].values()), {False})

    def test_exact_renderer_boundary(self):
        rendered = MODULE.render_review_output(review(base_document()))
        self.assertTrue(rendered.startswith("{"))
        self.assertTrue(rendered.endswith("}\n\n"))
        self.assertEqual(json.loads(rendered)["review_id"], "review-alpha")

    def test_no_ranking_or_contact_output(self):
        rendered = MODULE.render_review_output(review(base_document())).lower()
        for forbidden in ("tier 1", "high priority", "hot lead", "confidence", "buying stage", "send email", "write to crm"):
            self.assertNotIn(forbidden, rendered)

    def test_bundle_has_eleven_members(self):
        members = [path for path in ROOT.rglob("*") if path.is_file() and "__pycache__" not in path.parts]
        self.assertEqual(len(members), 11)

    def test_skill_routes_eight_references(self):
        skill = (ROOT / "SKILL.md").read_text()
        for name in (
            "scope_and_governance.md", "source_event_and_population.md",
            "route_and_assignment_contract.md", "privacy_identity_and_profiling.md",
            "output_and_action_boundary.md", "verification_sources.md", "failure_states.md",
            "construct_and_interpretation.md",
        ):
            self.assertIn(name, skill)

    def test_skill_exact_helper_rule(self):
        skill = (ROOT / "SKILL.md").read_text()
        self.assertIn("render_review_output(review_event_plan_evidence(document))", skill)
        self.assertIn("byte for byte", skill)


INVALID = {
    "extra_root_key": lambda d: d.update({"extra": True}),
    "wrong_purpose": lambda d: d["policy"].update({"approved_purpose": "event_activation"}),
    "bad_timezone": lambda d: d["policy"].update({"timezone": "Mars/Olympus"}),
    "expired_policy": lambda d: d["policy"].update({"expires_at": "2026-07-10T17:59:59Z"}),
    "review_before_cutoff": lambda d: d["review_declaration"].update({"reviewed_at": "2026-07-10T17:59:59Z"}),
    "unapproved_recipient": lambda d: d["review_declaration"].update({"recipient_role_id": "role-other"}),
    "recipient_not_reviewer": lambda d: d["review_declaration"].update({"recipient_role_id": "role-followup-owner"}),
    "reviewer_not_allowed": lambda d: d["policy"].update({"allowed_recipient_role_ids": ["role-followup-owner"]}),
    "missing_review_authorization": lambda d: d["review_declaration"].update({"review_authorization_receipt_id": None}),
    "duplicate_review_authorization": lambda d: d["review_declaration"].update({"review_authorization_receipt_id": d["policy"]["operations_approval_receipt_id"]}),
    "missing_prohibition": lambda d: d["policy"]["prohibited_uses"].remove("priority-ranking"),
    "duplicate_governance_receipt": lambda d: d["policy"].update({"security_review_receipt_id": d["policy"]["operations_approval_receipt_id"]}),
    "bad_source_kind": lambda d: d["policy"]["source_bindings"][0].update({"source_kind": "badge-api"}),
    "expired_source_auth": lambda d: d["policy"]["source_bindings"][0].update({"authorization_expires_at": "2026-07-10T17:59:59Z"}),
    "event_unknown_source": lambda d: d["policy"]["event_contracts"][0].update({"source_id": "source-other"}),
    "event_after_cutoff": lambda d: d["policy"]["event_contracts"][0].update({"ends_at": "2026-07-10T18:01:00Z"}),
    "duplicate_event": lambda d: d["policy"]["event_contracts"].append(copy.deepcopy(d["policy"]["event_contracts"][0])),
    "route_unknown_event": lambda d: d["policy"]["route_contracts"][0].update({"event_id": "event-other"}),
    "route_owner_not_recipient": lambda d: d["policy"]["route_contracts"][0].update({"owner_role_id": "role-other"}),
    "route_window_before_cutoff": lambda d: d["policy"]["route_contracts"][0].update({"window_opens_at": "2026-07-10T17:59:00Z"}),
    "route_auth_expires_early": lambda d: d["policy"]["route_contracts"][0].update({"authorization_expires_at": "2026-07-11T18:09:59Z"}),
    "duplicate_route_authorization_receipt": lambda d: d["policy"]["route_contracts"][0].update({"authorization_receipt_id": d["policy"]["route_contracts"][0]["route_receipt_id"]}),
    "route_after_policy_expiry": lambda d: d["policy"]["route_contracts"][0].update({"window_closes_at": "2026-08-01T00:00:00Z"}),
    "duplicate_route": lambda d: d["policy"]["route_contracts"].append(copy.deepcopy(d["policy"]["route_contracts"][0])),
    "incomplete_population": lambda d: d["source_populations"][0].update({"complete": False}),
    "missing_population_plan": lambda d: d["source_populations"][0]["plan_receipt_ids"].pop(),
    "extra_population_plan": lambda d: d["source_populations"][0]["plan_receipt_ids"].append("receipt-plan-extra"),
    "duplicate_population_plan": lambda d: d["source_populations"][0]["plan_receipt_ids"].append(d["source_populations"][0]["plan_receipt_ids"][0]),
    "missing_plan": lambda d: d["followup_plan"].pop(),
    "duplicate_plan": lambda d: d["followup_plan"].append(copy.deepcopy(d["followup_plan"][0])),
    "undeclared_participant": lambda d: d["followup_plan"][0].update({"participant_id": "participant-gamma"}),
    "direct_participant_id": lambda d: d["review_declaration"]["participant_ids"].__setitem__(0, "jane-smith"),
    "declaration_unknown_event": lambda d: d["review_declaration"].update({"event_id": "event-other"}),
    "plan_source_mismatch": lambda d: d["followup_plan"][0].update({"source_id": "source-other"}),
    "observation_before_event": lambda d: d["followup_plan"][0].update({"observed_at": "2026-07-10T12:59:59Z"}),
    "observation_after_event": lambda d: d["followup_plan"][0].update({"observed_at": "2026-07-10T17:00:01Z"}),
    "capture_before_observation": lambda d: d["followup_plan"][0].update({"captured_at": "2026-07-10T13:59:59Z"}),
    "capture_after_cutoff": lambda d: d["followup_plan"][0].update({"captured_at": "2026-07-10T18:00:01Z"}),
    "capture_before_source_auth": lambda d: d["policy"]["source_bindings"][0].update({"authorization_effective_at": "2026-07-10T14:06:00Z"}),
    "bad_participation_state": lambda d: d["followup_plan"][0].update({"participation_state": "hot"}),
    "duplicate_state_receipt": lambda d: d["followup_plan"][1].update({"participation_state_receipt_id": d["followup_plan"][0]["participation_state_receipt_id"]}),
    "eligible_missing_route": lambda d: d["followup_plan"][0].update({"route_id": None}),
    "eligible_missing_assignment": lambda d: d["followup_plan"][0].update({"assignment_receipt_id": None}),
    "planned_before_review": lambda d: d["followup_plan"][0].update({"planned_at": "2026-07-10T18:04:59Z"}),
    "suppressed_with_assignment": lambda d: d["followup_plan"][1].update({"route_id": "route-human-supplied", "route_version": "version-one"}),
}


def _make(mutate):
    def test(self):
        self.assert_invalid(mutate)
    return test


for _name, _mutate in INVALID.items():
    setattr(EventPlanEvidenceTests, f"test_reject_{_name}", _make(_mutate))


if __name__ == "__main__":
    unittest.main(verbosity=2)
