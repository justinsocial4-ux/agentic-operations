#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import unittest

from pipeline_evidence import REQUIRED_PROHIBITIONS, render_review_output, review_pipeline_evidence


def fixture() -> dict:
    receipts = iter(f"receipt-p{i}" for i in range(1, 120))

    def receipt() -> str:
        return next(receipts)

    def lane(lane_id: str, kind: str, platform: str, observation_id: str, value_kind: str, unit: str, denominator: str | None, operator: str, threshold: str) -> dict:
        return {
            "lane_id": lane_id, "observation_kind": kind, "platform_id": platform,
            "source_id": f"source-{platform[9:]}", "source_version": "v1",
            "source_kind": "customer-supplied-pseudonymous-pipeline-observation",
            "schema_id": f"schema-{platform[9:]}", "schema_version": "v1",
            "field_definition_id": f"definition-{kind}", "value_kind": value_kind,
            "unit_id": unit, "denominator_definition_id": denominator,
            "rule_id": f"rule-{kind}", "rule_version": "v1",
            "rule_effective_at": "2026-06-01T00:00:00Z", "rule_expires_at": "2026-12-31T23:59:59Z",
            "rule_operator": operator, "rule_threshold_value": threshold,
            "window_starts_at": "2026-07-01T00:00:00Z", "window_ends_at": "2026-07-10T23:59:59Z",
            "authorization_effective_at": "2026-06-01T00:00:00Z", "authorization_expires_at": "2026-12-31T23:59:59Z",
            "declared_observation_ids": [observation_id], "source_authorization_receipt_id": receipt(),
            "field_definition_receipt_id": receipt(), "denominator_definition_receipt_id": receipt(),
            "rule_receipt_id": receipt(), "rule_approval_receipt_id": receipt(),
            "population_receipt_id": receipt(), "completeness_receipt_id": receipt(),
            "privacy_receipt_id": receipt(), "source_documentation_receipt_id": receipt(),
        }

    lane_one = lane("lane-fivetran-state", "connection-update-state", "platform-fivetran", "observation-one", "code", "unit-source-code", None, "eq", "source-code-01")
    lane_two = lane("lane-dbt-freshness", "source-freshness-duration", "platform-dbt", "observation-two", "duration", "unit-hours", None, "lte", "12")
    policy_receipts = [receipt() for _ in range(11)]
    policy = {
        "policy_id": "policy-pipeline", "policy_version": "v1",
        "effective_at": "2026-06-01T00:00:00Z", "expires_at": "2026-12-31T23:59:59Z",
        "cutoff_at": "2026-07-12T12:00:00Z", "timezone": "America/Guayaquil",
        "approved_purpose": "pseudonymous_pipeline_observation_rule_evidence_review",
        "owner_role_id": "role-data-owner", "human_reviewer_role_id": "role-human-reviewer",
        "actual_recipient_role_id": "role-human-reviewer",
        "review_authorization_effective_at": "2026-07-01T00:00:00Z",
        "review_authorization_expires_at": "2026-07-31T23:59:59Z",
        "operations_approval_receipt_id": policy_receipts[0], "security_review_receipt_id": policy_receipts[1],
        "privacy_review_receipt_id": policy_receipts[2], "legal_review_receipt_id": policy_receipts[3],
        "collection_policy_receipt_id": policy_receipts[4], "recipient_policy_receipt_id": policy_receipts[5],
        "retention_policy_receipt_id": policy_receipts[6], "review_authorization_receipt_id": policy_receipts[7],
        "pseudonymization_policy_receipt_id": policy_receipts[8], "rule_policy_receipt_id": policy_receipts[9],
        "platform_separation_policy_receipt_id": policy_receipts[10],
        "allowed_recipient_role_ids": ["role-human-reviewer"],
        "prohibited_uses": sorted(REQUIRED_PROHIBITIONS), "lane_contracts": [lane_one, lane_two],
    }

    def observation(lane_row: dict, observation_id: str, state: str, value: str | None) -> dict:
        return {
            "observation_id": observation_id, "lane_id": lane_row["lane_id"], "platform_id": lane_row["platform_id"],
            "source_id": lane_row["source_id"], "source_version": lane_row["source_version"],
            "schema_id": lane_row["schema_id"], "schema_version": lane_row["schema_version"],
            "field_definition_id": lane_row["field_definition_id"], "value_kind": lane_row["value_kind"],
            "unit_id": lane_row["unit_id"], "denominator_definition_id": lane_row["denominator_definition_id"],
            "rule_id": lane_row["rule_id"], "observed_at": "2026-07-10T12:00:00Z",
            "evidence_state": state, "source_value": value,
            "capture_authorization_receipt_id": receipt(), "observation_receipt_id": receipt(), "state_receipt_id": receipt(),
        }

    return {
        "review_id": "review-pipeline", "review_version": "v1", "policy": policy,
        "declared_observation_ids": ["observation-one", "observation-two"],
        "observations": [observation(lane_one, "observation-one", "observed", "source-code-01"), observation(lane_two, "observation-two", "missing", None)],
        "packet_receipt_id": receipt(),
    }


class PipelineEvidenceTests(unittest.TestCase):
    def test_matched_and_missing(self):
        result = review_pipeline_evidence(fixture())
        self.assertEqual(result["review_receipt"]["review_status"], "EVIDENCE_MISSING")
        self.assertEqual(result["observation_receipts"][0]["rule_condition_status"], "CUSTOMER_RULE_CONDITION_MET")
        self.assertIsNone(result["observation_receipts"][1]["source_value"])
        self.assertTrue(all(value is False for key, value in result["action_boundary"].items() if key.endswith("_authorized")))

    def test_exact_renderer_and_r2(self):
        rendered = render_review_output(review_pipeline_evidence(fixture()))
        self.assertTrue(rendered.startswith("{")); self.assertTrue(rendered.endswith("}\n\n"))
        self.assertEqual(rendered.count('"12"'), 1)
        self.assertEqual(rendered.count('"source-code-01"'), 2)  # one rule threshold, one observation value
        self.assertEqual(json.loads(rendered)["review_receipt"]["review_id"], "review-pipeline")

    def test_permutation_invariant(self):
        doc = fixture(); expected = render_review_output(review_pipeline_evidence(doc))
        doc["observations"].reverse(); doc["declared_observation_ids"].reverse(); doc["policy"]["lane_contracts"].reverse()
        self.assertEqual(render_review_output(review_pipeline_evidence(doc)), expected)

    def test_numeric_condition_not_met(self):
        doc = fixture(); doc["observations"][1]["evidence_state"] = "observed"; doc["observations"][1]["source_value"] = "13"
        result = review_pipeline_evidence(doc)
        row = next(item for item in result["observation_receipts"] if item["observation_id"] == "observation-two")
        self.assertEqual(row["rule_condition_status"], "CUSTOMER_RULE_CONDITION_NOT_MET")

    def test_unmatched_binding_hides_value(self):
        doc = fixture(); doc["observations"][0]["platform_id"] = "platform-dbt"
        row = review_pipeline_evidence(doc)["observation_receipts"][0]
        self.assertEqual(row["evidence_status"], "SOURCE_OBSERVATION_EVIDENCE_NOT_MATCHED")
        self.assertIsNone(row["source_value"]); self.assertIsNone(row["rule_condition_status"])

    def test_precedence(self):
        doc = fixture(); doc["observations"][0]["evidence_state"] = "unauthorized"; doc["observations"][0]["source_value"] = None
        self.assertEqual(review_pipeline_evidence(doc)["review_receipt"]["review_status"], "UNAUTHORIZED")


def mutate(path: tuple, value):
    def test(self):
        doc = fixture(); target = doc
        for key in path[:-1]: target = target[key]
        target[path[-1]] = value
        with self.assertRaises(ValueError): review_pipeline_evidence(doc)
    return test


MUTATIONS = {
    "wrong_purpose": (("policy", "approved_purpose"), "monitor-pipeline"),
    "bad_timezone": (("policy", "timezone"), "Mars/Base"),
    "late_policy": (("policy", "effective_at"), "2026-08-01T00:00:00Z"),
    "expired_policy": (("policy", "expires_at"), "2026-07-01T00:00:00Z"),
    "late_review_auth": (("policy", "review_authorization_effective_at"), "2026-08-01T00:00:00Z"),
    "expired_review_auth": (("policy", "review_authorization_expires_at"), "2026-07-01T00:00:00Z"),
    "wrong_recipient": (("policy", "actual_recipient_role_id"), "role-data-owner"),
    "missing_prohibition": (("policy", "prohibited_uses"), sorted(REQUIRED_PROHIBITIONS - {"retry-action"})),
    "bad_kind": (("policy", "lane_contracts", 0, "observation_kind"), "health-score"),
    "bad_value_kind": (("policy", "lane_contracts", 0, "value_kind"), "float"),
    "incompatible_value_kind": (("policy", "lane_contracts", 0, "value_kind"), "count"),
    "bad_source_kind": (("policy", "lane_contracts", 0, "source_kind"), "live-api"),
    "ratio_no_denominator": (("policy", "lane_contracts", 0, "observation_kind"), "rate-limit-ratio"),
    "bad_token_operator": (("policy", "lane_contracts", 0, "rule_operator"), "gt"),
    "bad_code": (("policy", "lane_contracts", 0, "rule_threshold_value"), "source-code-delayed"),
    "late_window": (("policy", "lane_contracts", 0, "window_ends_at"), "2026-07-13T00:00:00Z"),
    "reversed_window": (("policy", "lane_contracts", 0, "window_starts_at"), "2026-07-11T00:00:00Z"),
    "late_lane_auth": (("policy", "lane_contracts", 0, "authorization_effective_at"), "2026-07-02T00:00:00Z"),
    "short_lane_auth": (("policy", "lane_contracts", 0, "authorization_expires_at"), "2026-07-05T00:00:00Z"),
    "late_rule": (("policy", "lane_contracts", 0, "rule_effective_at"), "2026-07-02T00:00:00Z"),
    "expired_rule": (("policy", "lane_contracts", 0, "rule_expires_at"), "2026-07-05T00:00:00Z"),
    "empty_population": (("policy", "lane_contracts", 0, "declared_observation_ids"), []),
    "document_population_missing": (("declared_observation_ids",), ["observation-one"]),
    "unknown_lane": (("observations", 0, "lane_id"), "lane-unknown"),
    "future_observation": (("observations", 0, "observed_at"), "2026-07-13T00:00:00Z"),
    "prewindow_observation": (("observations", 0, "observed_at"), "2026-06-30T23:59:59Z"),
    "bad_state": (("observations", 0, "evidence_state"), "estimated"),
    "bad_source_code": (("observations", 0, "source_value"), "source-code-up"),
    "wrong_source": (("observations", 0, "source_id"), "BAD SOURCE"),
    "wrong_schema": (("observations", 0, "schema_id"), "BAD SCHEMA"),
    "wrong_definition": (("observations", 0, "field_definition_id"), "BAD DEFINITION"),
    "wrong_unit": (("observations", 0, "unit_id"), "BAD UNIT"),
    "wrong_rule": (("observations", 0, "rule_id"), "BAD RULE"),
    "unresolved_with_value": (("observations", 1, "source_value"), "0"),
    "bad_review_id": (("review_id",), "Review 1"),
    "bad_packet_receipt": (("packet_receipt_id",), "packet-one"),
}

for name, (path, value) in MUTATIONS.items():
    setattr(PipelineEvidenceTests, f"test_reject_{name}", mutate(path, value))


class StructuralTests(unittest.TestCase):
    def test_extra_document_key(self):
        doc = fixture(); doc["extra"] = True
        with self.assertRaises(ValueError): review_pipeline_evidence(doc)

    def test_extra_policy_key(self):
        doc = fixture(); doc["policy"]["extra"] = True
        with self.assertRaises(ValueError): review_pipeline_evidence(doc)

    def test_extra_lane_key(self):
        doc = fixture(); doc["policy"]["lane_contracts"][0]["extra"] = True
        with self.assertRaises(ValueError): review_pipeline_evidence(doc)

    def test_extra_observation_key(self):
        doc = fixture(); doc["observations"][0]["extra"] = True
        with self.assertRaises(ValueError): review_pipeline_evidence(doc)

    def test_duplicate_observation(self):
        doc = fixture(); doc["observations"][1] = copy.deepcopy(doc["observations"][0])
        with self.assertRaises(ValueError): review_pipeline_evidence(doc)

    def test_incomplete_packet(self):
        doc = fixture(); doc["observations"].pop()
        with self.assertRaises(ValueError): review_pipeline_evidence(doc)

    def test_extra_packet_row(self):
        doc = fixture(); extra = copy.deepcopy(doc["observations"][0]); extra["observation_id"] = "observation-extra"; extra["capture_authorization_receipt_id"] = "receipt-extra-a"; extra["observation_receipt_id"] = "receipt-extra-b"; extra["state_receipt_id"] = "receipt-extra-c"; doc["observations"].append(extra)
        with self.assertRaises(ValueError): review_pipeline_evidence(doc)

    def test_duplicate_receipt(self):
        doc = fixture(); doc["observations"][0]["state_receipt_id"] = doc["observations"][0]["observation_receipt_id"]
        with self.assertRaises(ValueError): review_pipeline_evidence(doc)

    def test_suppressed_state(self):
        doc = fixture(); doc["observations"][0]["evidence_state"] = "suppressed"; doc["observations"][0]["source_value"] = None
        self.assertEqual(review_pipeline_evidence(doc)["review_receipt"]["review_status"], "SUPPRESSED")

    def test_conflict_precedes_missing(self):
        doc = fixture(); doc["observations"][0]["evidence_state"] = "conflicting"; doc["observations"][0]["source_value"] = None
        self.assertEqual(review_pipeline_evidence(doc)["review_receipt"]["review_status"], "EVIDENCE_CONFLICT")


if __name__ == "__main__": unittest.main(verbosity=2)
