#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import unittest

from deliverability_evidence import (
    REQUIRED_PROHIBITIONS,
    render_review_output,
    review_deliverability_evidence,
)


def fixture() -> dict:
    receipts = iter(f"receipt-r{i}" for i in range(1, 100))

    def receipt() -> str:
        return next(receipts)

    def lane(lane_id: str, kind: str, provider: str, observation_id: str, value_kind: str, unit: str, denominator: str | None) -> dict:
        return {
            "lane_id": lane_id, "lane_kind": kind, "provider_id": provider,
            "source_id": f"source-{provider[9:]}", "source_version": "v1", "source_kind": "customer-supplied-pseudonymous-deliverability-observation",
            "schema_id": f"schema-{provider[9:]}", "schema_version": "v1",
            "metric_definition_id": f"definition-{kind}", "value_kind": value_kind, "unit_id": unit,
            "denominator_definition_id": denominator, "window_starts_at": "2026-07-01T00:00:00Z",
            "window_ends_at": "2026-07-10T23:59:59Z", "authorization_effective_at": "2026-06-01T00:00:00Z",
            "authorization_expires_at": "2026-12-31T23:59:59Z", "declared_observation_ids": [observation_id],
            "source_authorization_receipt_id": receipt(), "metric_definition_receipt_id": receipt(),
            "denominator_definition_receipt_id": receipt(), "population_receipt_id": receipt(),
            "completeness_receipt_id": receipt(), "privacy_receipt_id": receipt(),
            "source_documentation_receipt_id": receipt(),
        }

    lane_one = lane("lane-gmail-complaint", "complaint-ratio", "provider-gmail", "observation-one", "percentage", "unit-percent", "definition-inbox-denominator")
    lane_two = lane("lane-seed-placement", "placement-test-ratio", "provider-seedtest", "observation-two", "percentage", "unit-percent", "definition-seed-denominator")
    policy_receipts = [receipt() for _ in range(10)]
    policy = {
        "policy_id": "policy-deliverability", "policy_version": "v1",
        "effective_at": "2026-06-01T00:00:00Z", "expires_at": "2026-12-31T23:59:59Z",
        "cutoff_at": "2026-07-12T12:00:00Z", "timezone": "America/Guayaquil",
        "approved_purpose": "pseudonymous_email_deliverability_observation_evidence_review",
        "owner_role_id": "role-email-owner", "human_reviewer_role_id": "role-human-reviewer",
        "actual_recipient_role_id": "role-human-reviewer",
        "review_authorization_effective_at": "2026-07-01T00:00:00Z",
        "review_authorization_expires_at": "2026-07-31T23:59:59Z",
        "operations_approval_receipt_id": policy_receipts[0], "security_review_receipt_id": policy_receipts[1],
        "privacy_review_receipt_id": policy_receipts[2], "legal_review_receipt_id": policy_receipts[3],
        "collection_policy_receipt_id": policy_receipts[4], "recipient_policy_receipt_id": policy_receipts[5],
        "retention_policy_receipt_id": policy_receipts[6], "review_authorization_receipt_id": policy_receipts[7],
        "pseudonymization_policy_receipt_id": policy_receipts[8], "source_separation_policy_receipt_id": policy_receipts[9],
        "allowed_recipient_role_ids": ["role-human-reviewer"],
        "prohibited_uses": sorted(REQUIRED_PROHIBITIONS), "lane_contracts": [lane_one, lane_two],
    }

    def observation(lane_row: dict, observation_id: str, state: str, value: str | None) -> dict:
        return {
            "observation_id": observation_id, "lane_id": lane_row["lane_id"], "provider_id": lane_row["provider_id"],
            "source_id": lane_row["source_id"], "source_version": lane_row["source_version"],
            "schema_id": lane_row["schema_id"], "schema_version": lane_row["schema_version"],
            "metric_definition_id": lane_row["metric_definition_id"], "value_kind": lane_row["value_kind"],
            "unit_id": lane_row["unit_id"], "denominator_definition_id": lane_row["denominator_definition_id"],
            "observed_at": "2026-07-10T12:00:00Z", "evidence_state": state, "source_value": value,
            "capture_authorization_receipt_id": receipt(), "observation_receipt_id": receipt(), "state_receipt_id": receipt(),
        }

    return {
        "review_id": "review-deliverability", "review_version": "v1", "policy": policy,
        "declared_observation_ids": ["observation-one", "observation-two"],
        "observations": [observation(lane_one, "observation-one", "observed", "0.08"), observation(lane_two, "observation-two", "suppressed", None)],
        "packet_receipt_id": receipt(),
    }


class DeliverabilityEvidenceTests(unittest.TestCase):
    def test_happy_and_suppressed(self):
        result = review_deliverability_evidence(fixture())
        self.assertEqual(result["review_receipt"]["review_status"], "SUPPRESSED")
        self.assertEqual(result["observation_receipts"][0]["source_value"], "0.08")
        self.assertIsNone(result["observation_receipts"][1]["source_value"])
        self.assertTrue(all(value is False for key, value in result["action_boundary"].items() if key.endswith("_authorized")))

    def test_exact_renderer(self):
        rendered = render_review_output(review_deliverability_evidence(fixture()))
        self.assertTrue(rendered.startswith("{"))
        self.assertTrue(rendered.endswith("}\n\n"))
        self.assertEqual(json.loads(rendered)["review_receipt"]["review_id"], "review-deliverability")
        self.assertEqual(rendered.count("0.08"), 1)

    def test_permutation_invariant(self):
        doc = fixture()
        expected = render_review_output(review_deliverability_evidence(doc))
        doc["observations"].reverse()
        doc["declared_observation_ids"].reverse()
        doc["policy"]["lane_contracts"].reverse()
        self.assertEqual(render_review_output(review_deliverability_evidence(doc)), expected)

    def test_unmatched_binding_hides_value(self):
        doc = fixture()
        doc["observations"][0]["provider_id"] = "provider-yahoo"
        result = review_deliverability_evidence(doc)
        row = result["observation_receipts"][0]
        self.assertEqual(row["evidence_status"], "SOURCE_OBSERVATION_EVIDENCE_NOT_MATCHED")
        self.assertIsNone(row["source_value"])

    def test_precedence(self):
        doc = fixture()
        doc["observations"][0]["evidence_state"] = "unauthorized"
        doc["observations"][0]["source_value"] = None
        self.assertEqual(review_deliverability_evidence(doc)["review_receipt"]["review_status"], "UNAUTHORIZED")


def mutate(path: tuple, value):
    def test(self):
        doc = fixture()
        target = doc
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        with self.assertRaises(ValueError):
            review_deliverability_evidence(doc)
    return test


MUTATIONS = {
    "wrong_purpose": (("policy", "approved_purpose"), "monitor-email"),
    "bad_timezone": (("policy", "timezone"), "Mars/Base"),
    "late_policy": (("policy", "effective_at"), "2026-08-01T00:00:00Z"),
    "expired_policy": (("policy", "expires_at"), "2026-07-01T00:00:00Z"),
    "late_review_auth": (("policy", "review_authorization_effective_at"), "2026-08-01T00:00:00Z"),
    "expired_review_auth": (("policy", "review_authorization_expires_at"), "2026-07-01T00:00:00Z"),
    "wrong_recipient": (("policy", "actual_recipient_role_id"), "role-email-owner"),
    "missing_prohibition": (("policy", "prohibited_uses"), sorted(REQUIRED_PROHIBITIONS - {"dns-change"})),
    "bad_lane_kind": (("policy", "lane_contracts", 0, "lane_kind"), "health-score"),
    "bad_source_kind": (("policy", "lane_contracts", 0, "source_kind"), "live-api"),
    "bad_value_kind": (("policy", "lane_contracts", 0, "value_kind"), "float"),
    "incompatible_value_kind": (("policy", "lane_contracts", 0, "value_kind"), "count"),
    "ratio_no_denominator": (("policy", "lane_contracts", 0, "denominator_definition_id"), None),
    "late_lane_window": (("policy", "lane_contracts", 0, "window_ends_at"), "2026-07-13T00:00:00Z"),
    "reversed_lane_window": (("policy", "lane_contracts", 0, "window_starts_at"), "2026-07-11T00:00:00Z"),
    "late_lane_auth": (("policy", "lane_contracts", 0, "authorization_effective_at"), "2026-07-02T00:00:00Z"),
    "short_lane_auth": (("policy", "lane_contracts", 0, "authorization_expires_at"), "2026-07-05T00:00:00Z"),
    "empty_lane_population": (("policy", "lane_contracts", 0, "declared_observation_ids"), []),
    "document_population_missing": (("declared_observation_ids",), ["observation-one"]),
    "unknown_lane": (("observations", 0, "lane_id"), "lane-unknown"),
    "future_observation": (("observations", 0, "observed_at"), "2026-07-13T00:00:00Z"),
    "prewindow_observation": (("observations", 0, "observed_at"), "2026-06-30T23:59:59Z"),
    "bad_state": (("observations", 0, "evidence_state"), "estimated"),
    "negative_value": (("observations", 0, "source_value"), "-0.1"),
    "noncanonical_value": (("observations", 0, "source_value"), ".08"),
    "too_large_percentage": (("observations", 0, "source_value"), "100.1"),
    "too_precise_percentage": (("observations", 0, "source_value"), "0.1234567890"),
    "wrong_source": (("observations", 0, "source_id"), "BAD SOURCE"),
    "wrong_schema": (("observations", 0, "schema_id"), "BAD SCHEMA"),
    "wrong_definition": (("observations", 0, "metric_definition_id"), "BAD DEFINITION"),
    "wrong_unit": (("observations", 0, "unit_id"), "BAD UNIT"),
    "unresolved_with_value": (("observations", 1, "source_value"), "0"),
    "bad_review_id": (("review_id",), "Review 1"),
    "bad_packet_receipt": (("packet_receipt_id",), "packet-one"),
}

for name, (path, value) in MUTATIONS.items():
    setattr(DeliverabilityEvidenceTests, f"test_reject_{name}", mutate(path, value))


class StructuralTests(unittest.TestCase):
    def test_extra_document_key(self):
        doc = fixture(); doc["extra"] = True
        with self.assertRaises(ValueError): review_deliverability_evidence(doc)

    def test_extra_policy_key(self):
        doc = fixture(); doc["policy"]["extra"] = True
        with self.assertRaises(ValueError): review_deliverability_evidence(doc)

    def test_extra_lane_key(self):
        doc = fixture(); doc["policy"]["lane_contracts"][0]["extra"] = True
        with self.assertRaises(ValueError): review_deliverability_evidence(doc)

    def test_extra_observation_key(self):
        doc = fixture(); doc["observations"][0]["extra"] = True
        with self.assertRaises(ValueError): review_deliverability_evidence(doc)

    def test_duplicate_observation(self):
        doc = fixture(); doc["observations"][1] = copy.deepcopy(doc["observations"][0])
        with self.assertRaises(ValueError): review_deliverability_evidence(doc)

    def test_incomplete_packet(self):
        doc = fixture(); doc["observations"].pop()
        with self.assertRaises(ValueError): review_deliverability_evidence(doc)

    def test_extra_packet_row(self):
        doc = fixture(); extra = copy.deepcopy(doc["observations"][0]); extra["observation_id"] = "observation-extra"; extra["observation_receipt_id"] = "receipt-extra-a"; extra["capture_authorization_receipt_id"] = "receipt-extra-b"; extra["state_receipt_id"] = "receipt-extra-c"; doc["observations"].append(extra)
        with self.assertRaises(ValueError): review_deliverability_evidence(doc)

    def test_duplicate_receipt(self):
        doc = fixture(); doc["observations"][0]["state_receipt_id"] = doc["observations"][0]["observation_receipt_id"]
        with self.assertRaises(ValueError): review_deliverability_evidence(doc)

    def test_missing_state(self):
        doc = fixture(); doc["observations"][0]["evidence_state"] = "missing"; doc["observations"][0]["source_value"] = None; doc["observations"][1]["evidence_state"] = "observed"; doc["observations"][1]["source_value"] = "92.5"
        self.assertEqual(review_deliverability_evidence(doc)["review_receipt"]["review_status"], "EVIDENCE_MISSING")

    def test_conflicting_state(self):
        doc = fixture(); doc["observations"][0]["evidence_state"] = "conflicting"; doc["observations"][0]["source_value"] = None
        self.assertEqual(review_deliverability_evidence(doc)["review_receipt"]["review_status"], "SUPPRESSED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
