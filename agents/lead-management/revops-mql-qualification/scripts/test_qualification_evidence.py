#!/usr/bin/env python3
"""Adversarial tests for the deterministic qualification evidence helper."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qualification_evidence import render_review_output, review_qualification_evidence


PROHIBITIONS = [
    "account-health-inference", "alert", "archive-action", "behavioral-inference",
    "confidence-score", "contact-validity-inference", "conversion-prediction", "crm-read",
    "crm-write", "direct-identifier", "downstream-decision", "enrichment", "fit-inference",
    "intent-inference", "lead-score", "lifecycle-label", "message-send", "monitoring",
    "nurture-action", "outreach-action", "protected-trait", "publication", "ranking",
    "readiness-inference", "routing-action", "scheduling", "worker-data",
]


def fixture() -> dict:
    binding = {
        "source_id": "source-alpha", "source_version": "version-alpha",
        "source_kind": "customer-supplied-pseudonymous-condition-evidence",
        "schema_id": "schema-alpha", "schema_version": "version-alpha",
        "authorization_receipt_id": "receipt-authorization",
        "authorization_effective_at": "2026-07-01T00:00:00Z", "authorization_expires_at": None,
        "query_receipt_id": "receipt-query", "page_receipt_id": "receipt-page",
        "pseudonymization_receipt_id": "receipt-pseudonymization",
    }
    conditions = [
        {
            "condition_id": "condition-required", "condition_version": "version-alpha",
            "condition_kind": "required", "source_id": "source-alpha", "source_version": "version-alpha",
            "field_definition_receipt_id": "receipt-field-required",
            "condition_definition_receipt_id": "receipt-condition-required",
        },
        {
            "condition_id": "condition-disqualifying", "condition_version": "version-alpha",
            "condition_kind": "disqualifying", "source_id": "source-alpha", "source_version": "version-alpha",
            "field_definition_receipt_id": "receipt-field-disqualifying",
            "condition_definition_receipt_id": "receipt-condition-disqualifying",
        },
    ]
    observations = []
    for condition, state in ((conditions[0], "recorded-true"), (conditions[1], "recorded-false")):
        observations.append({
            "record_id": "record-alpha", "condition_id": condition["condition_id"],
            "condition_version": "version-alpha", "source_id": "source-alpha",
            "source_version": "version-alpha", "schema_id": "schema-alpha",
            "schema_version": "version-alpha", "authorization_receipt_id": "receipt-authorization",
            "query_receipt_id": "receipt-query", "page_receipt_id": "receipt-page",
            "pseudonymization_receipt_id": "receipt-pseudonymization",
            "population_receipt_id": "receipt-population",
            "field_definition_receipt_id": condition["field_definition_receipt_id"],
            "condition_definition_receipt_id": condition["condition_definition_receipt_id"],
            "evidence_receipt_id": f"receipt-evidence-{condition['condition_kind']}",
            "state": state, "observed_at": "2026-07-08T00:00:00Z", "captured_at": "2026-07-09T00:00:00Z",
        })
    return {
        "review_declaration": {
            "review_id": "review-alpha", "policy_id": "policy-alpha", "policy_version": "version-alpha",
            "reviewed_at": "2026-07-11T00:00:00Z", "recipient_role_id": "role-reviewer",
            "record_ids": ["record-alpha"],
        },
        "policy": {
            "policy_id": "policy-alpha", "policy_version": "version-alpha",
            "effective_at": "2026-07-01T00:00:00Z", "expires_at": None,
            "cutoff_at": "2026-07-10T00:00:00Z", "timezone": "America/Guayaquil",
            "approved_purpose": "pseudonymous_marketing_qualification_rule_evidence_review",
            "owner_role_id": "role-owner", "human_reviewer_role_id": "role-reviewer",
            "marketing_approval_receipt_id": "receipt-marketing", "sales_approval_receipt_id": "receipt-sales",
            "privacy_review_receipt_id": "receipt-privacy", "legal_review_receipt_id": "receipt-legal",
            "lawful_basis_receipt_id": "receipt-lawful-basis", "notice_program_receipt_id": "receipt-notice",
            "objection_path_receipt_id": "receipt-objection", "correction_path_receipt_id": "receipt-correction",
            "recipient_policy_receipt_id": "receipt-recipient", "retention_policy_receipt_id": "receipt-retention",
            "qualification_policy_receipt_id": "receipt-qualification-policy",
            "allowed_recipient_role_ids": ["role-reviewer"], "prohibited_uses": PROHIBITIONS,
            "source_bindings": [binding], "conditions": conditions,
        },
        "source_populations": [{
            "population_receipt_id": "receipt-population", "source_id": "source-alpha",
            "source_version": "version-alpha", "schema_id": "schema-alpha", "schema_version": "version-alpha",
            "authorization_receipt_id": "receipt-authorization", "query_receipt_id": "receipt-query",
            "page_receipt_id": "receipt-page", "pseudonymization_receipt_id": "receipt-pseudonymization",
            "complete": True, "record_ids": ["record-alpha"], "captured_at": "2026-07-09T12:00:00Z",
        }],
        "condition_observations": observations,
    }


class QualificationEvidenceTests(unittest.TestCase):
    def test_valid_document(self):
        result = review_qualification_evidence(fixture())
        self.assertEqual(result["record_receipts"][0]["state"], "CUSTOMER_POLICY_CONDITIONS_MET")
        self.assertFalse(result["lifecycle_label_authorized"])
        self.assertFalse(result["archive_action_authorized"])
        self.assertFalse(result["nurture_action_authorized"])
        self.assertFalse(result["routing_action_authorized"])
        self.assertFalse(result["outreach_action_authorized"])
        self.assertFalse(result["system_action_authorized"])
        self.assertFalse(result["downstream_decision_authorized"])
        self.assertFalse(result["publication_authorized"])

    def test_required_false_not_met(self):
        document = fixture(); document["condition_observations"][0]["state"] = "recorded-false"
        self.assertEqual(review_qualification_evidence(document)["record_receipts"][0]["state"], "CUSTOMER_POLICY_CONDITIONS_NOT_MET")

    def test_disqualifier_true_not_met(self):
        document = fixture(); document["condition_observations"][1]["state"] = "recorded-true"
        self.assertEqual(review_qualification_evidence(document)["record_receipts"][0]["state"], "CUSTOMER_POLICY_CONDITIONS_NOT_MET")

    def test_unresolved_precedence(self):
        expected = {"missing": "EVIDENCE_MISSING", "conflicting": "EVIDENCE_CONFLICT", "suppressed": "SUPPRESSED", "unauthorized": "UNAUTHORIZED"}
        for observed, result_state in expected.items():
            with self.subTest(observed=observed):
                document = fixture(); document["condition_observations"][0]["state"] = observed
                self.assertEqual(review_qualification_evidence(document)["record_receipts"][0]["state"], result_state)

    def test_render_exact(self):
        result = review_qualification_evidence(fixture())
        rendered = render_review_output(result)
        self.assertEqual(rendered, json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n\n")
        self.assertTrue(rendered.startswith("{")); self.assertTrue(rendered.endswith("}\n\n"))

    def test_input_order_does_not_change_output(self):
        first = fixture(); second = fixture()
        second["policy"]["conditions"].reverse(); second["condition_observations"].reverse()
        self.assertEqual(render_review_output(review_qualification_evidence(first)), render_review_output(review_qualification_evidence(second)))


def _delete_test(path: tuple[Any, ...]):
    def test(self):
        document = fixture(); cursor = document
        for key in path[:-1]: cursor = cursor[key]
        del cursor[path[-1]]
        with self.assertRaises(ValueError): review_qualification_evidence(document)
    return test


DELETE_PATHS = []
sample = fixture()
for key in sample: DELETE_PATHS.append((key,))
for key in sample["review_declaration"]: DELETE_PATHS.append(("review_declaration", key))
for key in sample["policy"]: DELETE_PATHS.append(("policy", key))
for key in sample["policy"]["source_bindings"][0]: DELETE_PATHS.append(("policy", "source_bindings", 0, key))
for key in sample["policy"]["conditions"][0]: DELETE_PATHS.append(("policy", "conditions", 0, key))
for key in sample["source_populations"][0]: DELETE_PATHS.append(("source_populations", 0, key))
for key in sample["condition_observations"][0]: DELETE_PATHS.append(("condition_observations", 0, key))
for index, path in enumerate(DELETE_PATHS, start=1):
    setattr(QualificationEvidenceTests, f"test_required_key_{index:03d}", _delete_test(path))


def _semantic_test(mutator):
    def test(self):
        document = fixture(); mutator(document)
        with self.assertRaises(ValueError): review_qualification_evidence(document)
    return test


SEMANTIC_MUTATORS = [
    lambda d: d.update(extra=True),
    lambda d: d["review_declaration"].update(extra=True),
    lambda d: d["policy"].update(extra=True),
    lambda d: d["policy"]["source_bindings"][0].update(extra=True),
    lambda d: d["policy"]["conditions"][0].update(extra=True),
    lambda d: d["source_populations"][0].update(extra=True),
    lambda d: d["condition_observations"][0].update(extra=True),
    lambda d: d["review_declaration"].update(review_id="Bad ID"),
    lambda d: d["review_declaration"].update(record_ids=["person-alpha"]),
    lambda d: d["review_declaration"].update(record_ids=["record-alpha", "record-alpha"]),
    lambda d: d["review_declaration"].update(reviewed_at="2026-07-11"),
    lambda d: d["review_declaration"].update(policy_id="policy-other"),
    lambda d: d["review_declaration"].update(recipient_role_id="role-other"),
    lambda d: d["policy"].update(approved_purpose="lead-scoring"),
    lambda d: d["policy"].update(timezone="Mars/Olympus"),
    lambda d: d["policy"].update(effective_at="2026-07-11T00:00:00Z"),
    lambda d: d["policy"].update(expires_at="2026-07-09T00:00:00Z"),
    lambda d: d["policy"].update(prohibited_uses=PROHIBITIONS[:-1]),
    lambda d: d["policy"].update(allowed_recipient_role_ids=[]),
    lambda d: d["policy"].update(marketing_approval_receipt_id="receipt-sales"),
    lambda d: d["policy"].update(source_bindings=[]),
    lambda d: d["policy"]["source_bindings"][0].update(source_kind="crm-live-read"),
    lambda d: d["policy"]["source_bindings"][0].update(authorization_effective_at="2026-07-11T00:00:00Z"),
    lambda d: d["policy"]["source_bindings"][0].update(authorization_expires_at="2026-07-09T00:00:00Z"),
    lambda d: d["policy"]["source_bindings"][0].update(authorization_expires_at="2026-07-10T12:00:00Z"),
    lambda d: d["policy"]["source_bindings"][0].update(query_receipt_id="receipt-authorization"),
    lambda d: d["policy"].update(conditions=[]),
    lambda d: d["policy"]["conditions"][0].update(condition_kind="score"),
    lambda d: d["policy"]["conditions"][0].update(source_id="source-other"),
    lambda d: d["policy"]["conditions"].append(copy.deepcopy(d["policy"]["conditions"][0])),
    lambda d: d["policy"]["conditions"][1].update(condition_definition_receipt_id="receipt-condition-required"),
    lambda d: d["source_populations"][0].update(complete=False),
    lambda d: d["source_populations"][0].update(record_ids=[]),
    lambda d: d["source_populations"][0].update(captured_at="2026-07-11T00:00:00Z"),
    lambda d: d["source_populations"][0].update(schema_id="schema-other"),
    lambda d: d["source_populations"].append(copy.deepcopy(d["source_populations"][0])),
    lambda d: d.update(source_populations=[]),
    lambda d: d["condition_observations"][0].update(record_id="record-other"),
    lambda d: d["condition_observations"][0].update(condition_id="condition-other"),
    lambda d: d["condition_observations"][0].update(source_id="source-other"),
    lambda d: d["condition_observations"][0].update(schema_id="schema-other"),
    lambda d: d["condition_observations"][0].update(population_receipt_id="receipt-other"),
    lambda d: d["condition_observations"][0].update(field_definition_receipt_id="receipt-other"),
    lambda d: d["condition_observations"][0].update(condition_definition_receipt_id="receipt-other"),
    lambda d: d["condition_observations"][0].update(evidence_receipt_id=d["condition_observations"][1]["evidence_receipt_id"]),
    lambda d: d["condition_observations"][0].update(state="high-intent"),
    lambda d: d["condition_observations"][0].update(observed_at="2026-07-12T00:00:00Z"),
    lambda d: d["condition_observations"][0].update(captured_at="2026-07-07T00:00:00Z"),
    lambda d: d["condition_observations"].pop(),
    lambda d: d["condition_observations"].append(copy.deepcopy(d["condition_observations"][0])),
]
for index, mutator in enumerate(SEMANTIC_MUTATORS, start=1):
    setattr(QualificationEvidenceTests, f"test_semantic_rejection_{index:03d}", _semantic_test(mutator))


if __name__ == "__main__":
    unittest.main()
