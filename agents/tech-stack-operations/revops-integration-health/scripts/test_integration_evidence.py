#!/usr/bin/env python3
"""Tests for deterministic integration-observation evidence review."""

from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPEC = importlib.util.spec_from_file_location("integration_evidence", HERE / "integration_evidence.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


PROHIBITIONS = sorted(MODULE.REQUIRED_PROHIBITIONS)


def base_document() -> dict:
    lane_contracts = []
    for lane in MODULE.LANES:
        row = {
            "lane_id": lane,
            "lane_kind": lane,
            "definition_receipt_id": f"receipt-definition-{lane}",
            "expected_recorded_state": None,
            "max_age_seconds": None,
            "reconciliation_rule": None,
        }
        if lane == "source-endpoint":
            row["expected_recorded_state"] = "accepted"
        elif lane == "connector-job":
            row["expected_recorded_state"] = "succeeded"
        elif lane == "destination-endpoint":
            row["expected_recorded_state"] = "accepted"
        elif lane == "checkpoint":
            row["max_age_seconds"] = 600
        else:
            row["reconciliation_rule"] = "source-total-equals-target-total"
        lane_contracts.append(row)
    observations = []
    receipt_ids = []
    states = {
        "source-endpoint": "accepted",
        "connector-job": "succeeded",
        "destination-endpoint": "accepted",
    }
    for lane in MODULE.LANES:
        receipt = f"receipt-evidence-{lane}"
        receipt_ids.append(receipt)
        row = {
            "integration_id": "integration-alpha",
            "lane_id": lane,
            "lane_kind": lane,
            "source_id": "source-alpha",
            "source_version": "version-one",
            "evidence_receipt_id": receipt,
            "evidence_state": "recorded",
            "observed_at": "2026-07-11T11:56:00Z",
            "captured_at": "2026-07-11T11:57:00Z",
            "recorded_state": None,
            "recorded_state_receipt_id": None,
            "checkpoint_at": None,
            "checkpoint_receipt_id": None,
            "source_total": None,
            "source_total_receipt_id": None,
            "target_total": None,
            "target_total_receipt_id": None,
        }
        if lane in states:
            row["recorded_state"] = states[lane]
            row["recorded_state_receipt_id"] = f"receipt-value-{lane}"
        elif lane == "checkpoint":
            row["checkpoint_at"] = "2026-07-11T11:55:00Z"
            row["checkpoint_receipt_id"] = "receipt-value-checkpoint"
        else:
            row["source_total"] = 101
            row["source_total_receipt_id"] = "receipt-value-source-total"
            row["target_total"] = 101
            row["target_total_receipt_id"] = "receipt-value-target-total"
        observations.append(row)
    return {
        "review_declaration": {
            "review_id": "review-alpha",
            "policy_id": "policy-alpha",
            "policy_version": "version-one",
            "reviewed_at": "2026-07-11T12:05:00Z",
            "recipient_role_id": "role-integration-owner",
            "integration_ids": ["integration-alpha"],
        },
        "policy": {
            "policy_id": "policy-alpha",
            "policy_version": "version-one",
            "effective_at": "2026-07-01T00:00:00Z",
            "expires_at": "2026-12-31T23:59:59Z",
            "cutoff_at": "2026-07-11T12:00:00Z",
            "timezone": "UTC",
            "approved_purpose": MODULE.PURPOSE,
            "owner_role_id": "role-operations-owner",
            "human_reviewer_role_id": "role-integration-owner",
            "operations_approval_receipt_id": "receipt-operations-approval",
            "security_review_receipt_id": "receipt-security-review",
            "privacy_review_receipt_id": "receipt-privacy-review",
            "recipient_policy_receipt_id": "receipt-recipient-policy",
            "retention_policy_receipt_id": "receipt-retention-policy",
            "observation_policy_receipt_id": "receipt-observation-policy",
            "allowed_recipient_role_ids": ["role-integration-owner"],
            "prohibited_uses": list(PROHIBITIONS),
            "source_bindings": [{
                "source_id": "source-alpha",
                "source_version": "version-one",
                "source_kind": MODULE.SOURCE_KIND,
                "schema_id": "schema-integration-observation",
                "schema_version": "version-one",
                "authorization_receipt_id": "receipt-source-authorization",
                "authorization_effective_at": "2026-07-01T00:00:00Z",
                "authorization_expires_at": "2026-12-31T23:59:59Z",
                "query_receipt_id": "receipt-source-query",
                "page_receipt_id": "receipt-source-pages",
                "pseudonymization_receipt_id": "receipt-source-pseudonymization",
            }],
            "integration_contracts": [{
                "integration_id": "integration-alpha",
                "contract_id": "contract-alpha",
                "contract_version": "version-one",
                "contract_receipt_id": "receipt-contract-alpha",
                "lane_contracts": lane_contracts,
            }],
        },
        "source_populations": [{
            "source_id": "source-alpha",
            "source_version": "version-one",
            "population_receipt_id": "receipt-population-alpha",
            "complete": True,
            "observation_receipt_ids": receipt_ids,
        }],
        "observations": observations,
    }


def review(doc: dict) -> dict:
    return MODULE.review_integration_evidence(doc)


def lane(result: dict, lane_id: str) -> dict:
    return next(row for row in result["integration_reviews"][0]["lane_receipts"] if row["lane_id"] == lane_id)


class IntegrationEvidenceTests(unittest.TestCase):
    def assert_invalid(self, mutate) -> None:
        doc = base_document()
        mutate(doc)
        with self.assertRaises(ValueError):
            review(doc)

    def test_complete_match(self):
        result = review(base_document())
        self.assertEqual(result["integration_reviews"][0]["evidence_state"], "CONTRACT_OBSERVATION_MATCHED")

    def test_exact_renderer_terminal_boundary(self):
        rendered = MODULE.render_review_output(review(base_document()))
        self.assertTrue(rendered.startswith("{"))
        self.assertTrue(rendered.endswith("}\n\n"))
        self.assertEqual(json.loads(rendered)["review_id"], "review-alpha")

    def test_state_nonmatch(self):
        doc = base_document()
        doc["observations"][0]["recorded_state"] = "rejected"
        result = review(doc)
        self.assertEqual(lane(result, "source-endpoint")["evidence_state"], "CONTRACT_OBSERVATION_NOT_MATCHED")
        self.assertEqual(result["integration_reviews"][0]["evidence_state"], "CONTRACT_OBSERVATION_NOT_MATCHED")

    def test_checkpoint_match_math(self):
        values = lane(review(base_document()), "checkpoint")["values"]
        self.assertEqual(values, {"checkpoint_at": "2026-07-11T11:55:00Z", "checkpoint_receipt_id": "receipt-value-checkpoint", "maximum_age_seconds": 600, "observed_age_seconds": 300})

    def test_checkpoint_nonmatch(self):
        doc = base_document()
        doc["observations"][3]["checkpoint_at"] = "2026-07-11T11:40:00Z"
        self.assertEqual(lane(review(doc), "checkpoint")["evidence_state"], "CONTRACT_OBSERVATION_NOT_MATCHED")

    def test_reconciliation_match_math(self):
        values = lane(review(base_document()), "reconciliation")["values"]
        self.assertEqual(values["source_minus_target"], 0)

    def test_reconciliation_nonmatch_math(self):
        doc = base_document()
        doc["observations"][4]["target_total"] = 99
        values = lane(review(doc), "reconciliation")["values"]
        self.assertEqual(values["source_minus_target"], 2)
        self.assertEqual(lane(review(doc), "reconciliation")["evidence_state"], "CONTRACT_OBSERVATION_NOT_MATCHED")

    def test_all_actions_false(self):
        self.assertEqual(set(review(base_document())["action_authorization"].values()), {False})

    def test_no_health_or_cause_output(self):
        rendered = MODULE.render_review_output(review(base_document())).lower()
        for forbidden in ("healthy", "degraded", "critical", "root cause", "forecast impact", "recommended action"):
            self.assertNotIn(forbidden, rendered)

    def test_unresolved_precedence(self):
        doc = base_document()
        for index, state in enumerate(("missing", "conflicting", "suppressed", "unauthorized")):
            row = doc["observations"][index]
            row["evidence_state"] = state
            for field in ("recorded_state", "recorded_state_receipt_id", "checkpoint_at", "checkpoint_receipt_id", "source_total", "source_total_receipt_id", "target_total", "target_total_receipt_id"):
                row[field] = None
        self.assertEqual(review(doc)["integration_reviews"][0]["evidence_state"], "UNAUTHORIZED")

    def test_each_unresolved_lane(self):
        expected = {"missing": "EVIDENCE_MISSING", "conflicting": "EVIDENCE_CONFLICT", "suppressed": "SUPPRESSED", "unauthorized": "UNAUTHORIZED"}
        for state, output in expected.items():
            with self.subTest(state=state):
                doc = base_document()
                row = doc["observations"][0]
                row["evidence_state"] = state
                row["recorded_state"] = None
                row["recorded_state_receipt_id"] = None
                self.assertEqual(lane(review(doc), "source-endpoint")["evidence_state"], output)

    def test_skill_routes_all_references(self):
        skill = (ROOT / "SKILL.md").read_text()
        for name in (
            "scope_and_governance.md", "source_and_population.md", "observation_contract.md",
            "construct_and_interpretation.md", "privacy_and_security.md",
            "output_and_action_boundary.md", "verification_sources.md", "failure_states.md",
        ):
            self.assertIn(name, skill)

    def test_skill_exact_helper_rule(self):
        skill = (ROOT / "SKILL.md").read_text()
        self.assertIn("render_review_output(review_integration_evidence(document))", skill)
        self.assertIn("byte for byte", skill)

    def test_bundle_has_eleven_members(self):
        members = [p for p in ROOT.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
        self.assertEqual(len(members), 11)


INVALID_MUTATIONS = {
    "extra_root_key": lambda d: d.update({"extra": True}),
    "wrong_purpose": lambda d: d["policy"].update({"approved_purpose": "monitoring"}),
    "missing_prohibition": lambda d: d["policy"]["prohibited_uses"].remove("alert"),
    "unapproved_recipient": lambda d: d["review_declaration"].update({"recipient_role_id": "role-other"}),
    "bad_timezone": lambda d: d["policy"].update({"timezone": "Mars/Olympus"}),
    "expired_policy": lambda d: d["policy"].update({"expires_at": "2026-07-10T00:00:00Z"}),
    "review_before_cutoff": lambda d: d["review_declaration"].update({"reviewed_at": "2026-07-11T11:59:00Z"}),
    "wrong_source_kind": lambda d: d["policy"]["source_bindings"][0].update({"source_kind": "api"}),
    "expired_authorization": lambda d: d["policy"]["source_bindings"][0].update({"authorization_expires_at": "2026-07-10T00:00:00Z"}),
    "incomplete_population": lambda d: d["source_populations"][0].update({"complete": False}),
    "missing_population_receipt": lambda d: d["source_populations"][0]["observation_receipt_ids"].pop(),
    "extra_population_receipt": lambda d: d["source_populations"][0]["observation_receipt_ids"].append("receipt-extra"),
    "duplicate_population_receipt": lambda d: d["source_populations"][0]["observation_receipt_ids"].append(d["source_populations"][0]["observation_receipt_ids"][0]),
    "missing_observation": lambda d: d["observations"].pop(),
    "duplicate_lane": lambda d: d["observations"].append(copy.deepcopy(d["observations"][0])),
    "future_capture": lambda d: d["observations"][0].update({"captured_at": "2026-07-11T12:01:00Z"}),
    "observed_after_capture": lambda d: d["observations"][0].update({"observed_at": "2026-07-11T11:58:00Z", "captured_at": "2026-07-11T11:57:00Z"}),
    "direct_integration_name": lambda d: d["review_declaration"]["integration_ids"].__setitem__(0, "salesforce-prod"),
    "bad_lane_id": lambda d: d["observations"][0].update({"lane_id": "api-health"}),
    "bad_lane_kind": lambda d: d["observations"][0].update({"lane_kind": "api-health"}),
    "state_lane_has_count": lambda d: d["observations"][0].update({"source_total": 1}),
    "checkpoint_has_state": lambda d: d["observations"][3].update({"recorded_state": "recent"}),
    "reconciliation_has_checkpoint": lambda d: d["observations"][4].update({"checkpoint_at": "2026-07-11T11:55:00Z"}),
    "negative_source_total": lambda d: d["observations"][4].update({"source_total": -1}),
    "float_target_total": lambda d: d["observations"][4].update({"target_total": 1.0}),
    "unresolved_contains_value": lambda d: d["observations"][0].update({"evidence_state": "missing"}),
    "bad_evidence_state": lambda d: d["observations"][0].update({"evidence_state": "unknown"}),
    "duplicate_governance_receipt": lambda d: d["policy"].update({"security_review_receipt_id": d["policy"]["operations_approval_receipt_id"]}),
    "duplicate_source_receipt": lambda d: d["policy"]["source_bindings"][0].update({"query_receipt_id": d["policy"]["source_bindings"][0]["authorization_receipt_id"]}),
    "duplicate_definition_receipt": lambda d: d["policy"]["integration_contracts"][0]["lane_contracts"][1].update({"definition_receipt_id": d["policy"]["integration_contracts"][0]["lane_contracts"][0]["definition_receipt_id"]}),
    "missing_contract_lane": lambda d: d["policy"]["integration_contracts"][0]["lane_contracts"].pop(),
    "bad_checkpoint_contract": lambda d: d["policy"]["integration_contracts"][0]["lane_contracts"][3].update({"max_age_seconds": 0}),
    "bad_reconciliation_rule": lambda d: d["policy"]["integration_contracts"][0]["lane_contracts"][4].update({"reconciliation_rule": "close-enough"}),
    "health_state_contract": lambda d: d["policy"]["integration_contracts"][0]["lane_contracts"][0].update({"expected_recorded_state": "healthy"}),
    "health_state_observation": lambda d: d["observations"][0].update({"recorded_state": "critical"}),
    "capture_before_authorization": lambda d: d["observations"][0].update({"observed_at": "2026-06-30T23:58:00Z", "captured_at": "2026-06-30T23:59:00Z"}),
    "checkpoint_after_observation": lambda d: d["observations"][3].update({"checkpoint_at": "2026-07-11T11:56:30Z"}),
    "reused_value_receipt": lambda d: d["observations"][4].update({"target_total_receipt_id": d["observations"][4]["source_total_receipt_id"]}),
}


def _make_invalid_test(mutate):
    def test(self):
        self.assert_invalid(mutate)
    return test


for _name, _mutate in INVALID_MUTATIONS.items():
    setattr(IntegrationEvidenceTests, f"test_reject_{_name}", _make_invalid_test(_mutate))


if __name__ == "__main__":
    unittest.main(verbosity=2)
