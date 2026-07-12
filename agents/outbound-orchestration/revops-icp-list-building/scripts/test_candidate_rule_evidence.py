#!/usr/bin/env python3
"""Adversarial tests for the candidate-rule evidence helper."""

from __future__ import annotations

import copy
import json
import unittest

from candidate_rule_evidence import REQUIRED_PROHIBITIONS, render_review_output, review_candidate_evidence


def base_document() -> dict:
    candidate_ids = ["candidate-alpha", "candidate-beta"]
    rules = [
        {
            "rule_id": "rule-industry-code", "rule_version": "version-one",
            "rule_effective_at": "2026-07-01T00:00:00Z", "rule_expires_at": None,
            "source_id": "source-customer-crm", "source_version": "version-one",
            "source_kind": "customer-supplied-pseudonymous-candidate-observation",
            "schema_id": "schema-candidate-observation", "schema_version": "version-one",
            "field_definition_id": "definition-industry-code", "value_kind": "code",
            "unit_id": None, "denominator_definition_id": None, "rule_operator": "in",
            "rule_threshold_values": ["source-code-02", "source-code-01"],
            "window_starts_at": "2026-07-01T00:00:00Z", "window_ends_at": "2026-07-10T23:59:59Z",
            "authorization_effective_at": "2026-07-01T00:00:00Z", "authorization_expires_at": None,
            "declared_candidate_ids": candidate_ids,
            "source_authorization_receipt_id": "receipt-rule-industry-source-auth",
            "field_definition_receipt_id": "receipt-rule-industry-definition",
            "denominator_definition_receipt_id": None,
            "rule_receipt_id": "receipt-rule-industry-contract",
            "rule_approval_receipt_id": "receipt-rule-industry-approval",
            "population_receipt_id": "receipt-rule-industry-population",
            "completeness_receipt_id": "receipt-rule-industry-completeness",
            "privacy_receipt_id": "receipt-rule-industry-privacy",
            "source_documentation_receipt_id": "receipt-rule-industry-source-doc",
        },
        {
            "rule_id": "rule-revenue-percentage", "rule_version": "version-one",
            "rule_effective_at": "2026-07-01T00:00:00Z", "rule_expires_at": None,
            "source_id": "source-customer-crm", "source_version": "version-one",
            "source_kind": "customer-supplied-pseudonymous-candidate-observation",
            "schema_id": "schema-candidate-observation", "schema_version": "version-one",
            "field_definition_id": "definition-revenue-percentage", "value_kind": "percentage",
            "unit_id": "unit-percent", "denominator_definition_id": "definition-candidate-population",
            "rule_operator": "gte", "rule_threshold_values": ["70"],
            "window_starts_at": "2026-07-01T00:00:00Z", "window_ends_at": "2026-07-10T23:59:59Z",
            "authorization_effective_at": "2026-07-01T00:00:00Z", "authorization_expires_at": None,
            "declared_candidate_ids": candidate_ids,
            "source_authorization_receipt_id": "receipt-rule-revenue-source-auth",
            "field_definition_receipt_id": "receipt-rule-revenue-definition",
            "denominator_definition_receipt_id": "receipt-rule-revenue-denominator",
            "rule_receipt_id": "receipt-rule-revenue-contract",
            "rule_approval_receipt_id": "receipt-rule-revenue-approval",
            "population_receipt_id": "receipt-rule-revenue-population",
            "completeness_receipt_id": "receipt-rule-revenue-completeness",
            "privacy_receipt_id": "receipt-rule-revenue-privacy",
            "source_documentation_receipt_id": "receipt-rule-revenue-source-doc",
        },
    ]

    def observation(candidate: str, rule: dict, state: str, value, observed_at):
        suffix = f"{candidate.removeprefix('candidate-')}-{rule['rule_id'].removeprefix('rule-')}"
        return {
            "candidate_id": candidate, "rule_id": rule["rule_id"], "source_id": rule["source_id"],
            "source_version": rule["source_version"], "source_kind": rule["source_kind"],
            "schema_id": rule["schema_id"], "schema_version": rule["schema_version"],
            "field_definition_id": rule["field_definition_id"], "value_kind": rule["value_kind"],
            "unit_id": rule["unit_id"], "denominator_definition_id": rule["denominator_definition_id"],
            "observed_at": observed_at, "evidence_state": state, "value": value,
            "capture_authorization_receipt_id": f"receipt-observation-{suffix}-auth",
            "capture_receipt_id": f"receipt-observation-{suffix}-capture",
            "candidate_binding_receipt_id": f"receipt-observation-{suffix}-binding",
            "privacy_receipt_id": f"receipt-observation-{suffix}-privacy",
        }

    policy_receipts = {
        "operations_approval_receipt_id": "receipt-policy-operations",
        "security_review_receipt_id": "receipt-policy-security",
        "privacy_review_receipt_id": "receipt-policy-privacy",
        "legal_review_receipt_id": "receipt-policy-legal",
        "collection_policy_receipt_id": "receipt-policy-collection",
        "lawful_basis_review_receipt_id": "receipt-policy-lawful-basis",
        "notice_policy_receipt_id": "receipt-policy-notice",
        "objection_policy_receipt_id": "receipt-policy-objection",
        "suppression_policy_receipt_id": "receipt-policy-suppression",
        "correction_access_policy_receipt_id": "receipt-policy-correction-access",
        "recipient_policy_receipt_id": "receipt-policy-recipient",
        "retention_policy_receipt_id": "receipt-policy-retention",
        "pseudonymization_policy_receipt_id": "receipt-policy-pseudonymization",
        "rule_policy_receipt_id": "receipt-policy-rules",
        "population_policy_receipt_id": "receipt-policy-population",
        "review_authorization_receipt_id": "receipt-policy-review-auth",
    }
    return {
        "schema_version": "candidate-rule-evidence-v1", "review_id": "review-example-one",
        "policy": {
            "policy_id": "policy-prospect-review", "policy_version": "version-one",
            "effective_at": "2026-07-01T00:00:00Z", "expires_at": None,
            "cutoff_at": "2026-07-11T00:00:00Z", "timezone": "America/Guayaquil",
            "approved_purpose": "pseudonymous_candidate_rule_evidence_review",
            "owner_role_id": "role-revops-owner", "human_reviewer_role_id": "role-human-reviewer",
            "actual_recipient_role_id": "role-human-reviewer",
            "review_authorization_effective_at": "2026-07-01T00:00:00Z",
            "review_authorization_expires_at": None,
            **policy_receipts,
            "allowed_recipient_role_ids": ["role-human-reviewer"],
            "prohibited_uses": sorted(REQUIRED_PROHIBITIONS), "rule_contracts": rules,
        },
        "candidate_population": {
            "population_id": "population-prospect-candidates", "declared_candidate_ids": candidate_ids,
            "packet_generated_at": "2026-07-10T23:59:59Z",
            "assigned_reviewer_role_id": "role-human-reviewer",
            "packet_receipt_id": "receipt-population-packet",
            "population_receipt_id": "receipt-population-contract",
            "completeness_receipt_id": "receipt-population-completeness",
            "pseudonymization_receipt_id": "receipt-population-pseudonymization",
            "review_assignment_receipt_id": "receipt-population-review-assignment",
        },
        "candidates": [
            {"candidate_id": "candidate-alpha", "observations": [
                observation("candidate-alpha", rules[0], "available", "source-code-01", "2026-07-10T12:00:00Z"),
                observation("candidate-alpha", rules[1], "available", "75", "2026-07-10T12:00:00Z"),
            ]},
            {"candidate_id": "candidate-beta", "observations": [
                observation("candidate-beta", rules[0], "available", "source-code-03", "2026-07-10T12:00:00Z"),
                observation("candidate-beta", rules[1], "missing", None, None),
            ]},
        ],
    }


def set_path(document: dict, path: tuple, value) -> None:
    cursor = document
    for part in path[:-1]:
        cursor = cursor[part]
    cursor[path[-1]] = value


class CandidateEvidenceTests(unittest.TestCase):
    def test_matched_not_met_and_missing(self):
        result = review_candidate_evidence(base_document())
        self.assertEqual(result["candidates"][0]["candidate_state"], "ALL_CUSTOMER_RULE_CONDITIONS_MET")
        self.assertEqual(result["candidates"][1]["candidate_state"], "EVIDENCE_MISSING")
        self.assertEqual(result["review_state"], "EVIDENCE_MISSING")

    def test_exact_renderer_and_r2(self):
        rendered = render_review_output(review_candidate_evidence(base_document()))
        self.assertTrue(rendered.startswith("{"))
        self.assertTrue(rendered.endswith("}\n\n"))
        self.assertEqual(rendered.count('"observed_value": "75"'), 1)
        self.assertEqual(rendered.count('"rule_threshold_values": [\n        "70"'), 1)
        self.assertNotIn("confidence", rendered.lower())
        self.assertNotIn("ready", rendered.lower())

    def test_all_action_flags_false(self):
        self.assertTrue(all(value is False for value in review_candidate_evidence(base_document())["action_flags"].values()))

    def test_numeric_condition_not_met(self):
        doc = base_document()
        doc["candidates"][0]["observations"][1]["value"] = "69"
        result = review_candidate_evidence(doc)
        self.assertEqual(result["candidates"][0]["candidate_state"], "AT_LEAST_ONE_CUSTOMER_RULE_CONDITION_NOT_MET")

    def test_code_not_in(self):
        doc = base_document()
        doc["policy"]["rule_contracts"][0]["rule_operator"] = "not-in"
        result = review_candidate_evidence(doc)
        self.assertEqual(result["candidates"][0]["rule_evidence"][0]["condition_state"], "CUSTOMER_RULE_CONDITION_NOT_MET")

    def test_permutation_invariant(self):
        doc = base_document()
        expected = render_review_output(review_candidate_evidence(doc))
        doc["candidates"].reverse()
        doc["candidate_population"]["declared_candidate_ids"].reverse()
        doc["policy"]["rule_contracts"].reverse()
        for candidate in doc["candidates"]:
            candidate["observations"].reverse()
        for rule in doc["policy"]["rule_contracts"]:
            rule["declared_candidate_ids"].reverse()
            rule["rule_threshold_values"].reverse()
        self.assertEqual(render_review_output(review_candidate_evidence(doc)), expected)

    def test_unmatched_binding_hides_value(self):
        doc = base_document()
        doc["candidates"][0]["observations"][0]["schema_version"] = "version-two"
        result = review_candidate_evidence(doc)
        evidence = result["candidates"][0]["rule_evidence"][0]
        self.assertEqual(evidence["evidence_state"], "SOURCE_OBSERVATION_EVIDENCE_NOT_MATCHED")
        self.assertIsNone(evidence["observed_value"])

    def test_unauthorized_precedence(self):
        doc = base_document()
        observation = doc["candidates"][1]["observations"][1]
        observation["evidence_state"] = "unauthorized"
        result = review_candidate_evidence(doc)
        self.assertEqual(result["review_state"], "UNAUTHORIZED")

    def test_suppressed_precedes_conflict_and_missing(self):
        doc = base_document()
        doc["candidates"][0]["observations"][0].update(evidence_state="suppressed", value=None, observed_at=None)
        doc["candidates"][0]["observations"][1].update(evidence_state="conflicting", value=None, observed_at=None)
        self.assertEqual(review_candidate_evidence(doc)["review_state"], "SUPPRESSED")

    def test_output_is_valid_json_without_terminal_blank(self):
        rendered = render_review_output(review_candidate_evidence(base_document()))
        parsed = json.loads(rendered)
        self.assertEqual(parsed["review_id"], "review-example-one")


SIMPLE_REJECTIONS = {
    "bad_schema": (("schema_version",), "other-v1"),
    "bad_review_id": (("review_id",), "Review One"),
    "bad_purpose": (("policy", "approved_purpose"), "prospect_scoring"),
    "bad_timezone": (("policy", "timezone"), "Mars/Olympus"),
    "late_policy": (("policy", "effective_at"), "2026-07-05T00:00:00Z"),
    "expired_policy": (("policy", "expires_at"), "2026-07-10T00:00:00Z"),
    "late_review_auth": (("policy", "review_authorization_effective_at"), "2026-07-12T00:00:00Z"),
    "expired_review_auth": (("policy", "review_authorization_expires_at"), "2026-07-10T00:00:00Z"),
    "bad_owner": (("policy", "owner_role_id"), "owner-one"),
    "bad_reviewer": (("policy", "human_reviewer_role_id"), "reviewer-one"),
    "wrong_actual_recipient": (("policy", "actual_recipient_role_id"), "role-other"),
    "empty_recipients": (("policy", "allowed_recipient_role_ids"), []),
    "duplicate_recipients": (("policy", "allowed_recipient_role_ids"), ["role-human-reviewer", "role-human-reviewer"]),
    "bad_rule_id": (("policy", "rule_contracts", 0, "rule_id"), "industry-rule"),
    "bad_rule_kind": (("policy", "rule_contracts", 0, "value_kind"), "text"),
    "bad_code_operator": (("policy", "rule_contracts", 0, "rule_operator"), "eq"),
    "bad_numeric_operator": (("policy", "rule_contracts", 1, "rule_operator"), "in"),
    "empty_thresholds": (("policy", "rule_contracts", 0, "rule_threshold_values"), []),
    "duplicate_thresholds": (("policy", "rule_contracts", 0, "rule_threshold_values"), ["source-code-01", "source-code-01"]),
    "multiple_numeric_thresholds": (("policy", "rule_contracts", 1, "rule_threshold_values"), ["70", "80"]),
    "bad_numeric_threshold": (("policy", "rule_contracts", 1, "rule_threshold_values"), ["070"]),
    "percentage_over_hundred": (("policy", "rule_contracts", 1, "rule_threshold_values"), ["101"]),
    "code_with_unit": (("policy", "rule_contracts", 0, "unit_id"), "unit-code"),
    "numeric_without_unit": (("policy", "rule_contracts", 1, "unit_id"), None),
    "late_rule": (("policy", "rule_contracts", 0, "rule_effective_at"), "2026-07-02T00:00:00Z"),
    "expired_rule": (("policy", "rule_contracts", 0, "rule_expires_at"), "2026-07-09T00:00:00Z"),
    "reversed_window": (("policy", "rule_contracts", 0, "window_starts_at"), "2026-07-11T00:00:00Z"),
    "late_source_auth": (("policy", "rule_contracts", 0, "authorization_effective_at"), "2026-07-02T00:00:00Z"),
    "expired_source_auth": (("policy", "rule_contracts", 0, "authorization_expires_at"), "2026-07-09T00:00:00Z"),
    "empty_rule_population": (("policy", "rule_contracts", 0, "declared_candidate_ids"), []),
    "rule_population_mismatch": (("policy", "rule_contracts", 0, "declared_candidate_ids"), ["candidate-alpha"]),
    "empty_population": (("candidate_population", "declared_candidate_ids"), []),
    "duplicate_population": (("candidate_population", "declared_candidate_ids"), ["candidate-alpha", "candidate-alpha"]),
    "bad_population_id": (("candidate_population", "population_id"), "prospects"),
    "early_packet": (("candidate_population", "packet_generated_at"), "2026-07-10T23:59:58Z"),
    "future_packet": (("candidate_population", "packet_generated_at"), "2026-07-12T00:00:00Z"),
    "wrong_assigned_reviewer": (("candidate_population", "assigned_reviewer_role_id"), "role-other"),
    "candidate_binding_mismatch": (("candidates", 0, "observations", 0, "candidate_id"), "candidate-beta"),
    "unknown_rule": (("candidates", 0, "observations", 0, "rule_id"), "rule-unknown"),
    "bad_evidence_state": (("candidates", 0, "observations", 0, "evidence_state"), "cached"),
    "bad_observed_time": (("candidates", 0, "observations", 0, "observed_at"), "2026-07-10"),
    "future_observation": (("candidates", 0, "observations", 0, "observed_at"), "2026-07-12T00:00:00Z"),
    "prewindow_observation": (("candidates", 0, "observations", 0, "observed_at"), "2026-06-30T23:59:59Z"),
    "bad_code_value": (("candidates", 0, "observations", 0, "value"), "Software"),
    "bad_decimal_value": (("candidates", 0, "observations", 1, "value"), "75.0000000000"),
    "percentage_value_over_hundred": (("candidates", 0, "observations", 1, "value"), "101"),
    "bad_candidate_id": (("candidates", 0, "candidate_id"), "account-alpha"),
}


def make_simple_rejection(path, value):
    def test(self):
        doc = base_document()
        set_path(doc, path, value)
        with self.assertRaises(ValueError):
            review_candidate_evidence(doc)
    return test


for case_name, (case_path, case_value) in SIMPLE_REJECTIONS.items():
    setattr(CandidateEvidenceTests, f"test_reject_{case_name}", make_simple_rejection(case_path, case_value))


def make_custom_rejection(mutator):
    def test(self):
        doc = base_document()
        mutator(doc)
        with self.assertRaises(ValueError):
            review_candidate_evidence(doc)
    return test


CUSTOM_REJECTIONS = {
    "extra_root_key": lambda d: d.update(identity="forbidden"),
    "missing_policy_key": lambda d: d["policy"].pop("legal_review_receipt_id"),
    "extra_policy_key": lambda d: d["policy"].update(company_name="forbidden"),
    "missing_prohibition": lambda d: d["policy"]["prohibited_uses"].remove("ranking"),
    "duplicate_policy_receipt": lambda d: d["policy"].update(security_review_receipt_id=d["policy"]["operations_approval_receipt_id"]),
    "no_rules": lambda d: d["policy"].update(rule_contracts=[]),
    "missing_candidate": lambda d: d["candidates"].pop(),
    "extra_candidate": lambda d: d["candidates"].append({"candidate_id": "candidate-gamma", "observations": []}),
    "duplicate_candidate": lambda d: d["candidates"].append(copy.deepcopy(d["candidates"][0])),
    "extra_candidate_key": lambda d: d["candidates"][0].update(email="forbidden@example.com"),
    "extra_observation_key": lambda d: d["candidates"][0]["observations"][0].update(company="forbidden"),
    "missing_observation": lambda d: d["candidates"][0]["observations"].pop(),
    "duplicate_observation": lambda d: d["candidates"][0]["observations"].append(copy.deepcopy(d["candidates"][0]["observations"][0])),
    "unresolved_with_value": lambda d: d["candidates"][1]["observations"][1].update(value="75"),
    "unresolved_with_timestamp": lambda d: d["candidates"][1]["observations"][1].update(observed_at="2026-07-10T12:00:00Z"),
    "duplicate_observation_receipt": lambda d: d["candidates"][0]["observations"][1].update(capture_receipt_id=d["candidates"][0]["observations"][0]["capture_receipt_id"]),
    "nonpercentage_denominator": lambda d: d["policy"]["rule_contracts"][0].update(denominator_definition_id="definition-population"),
    "nonpercentage_denominator_receipt": lambda d: d["policy"]["rule_contracts"][0].update(denominator_definition_receipt_id="receipt-rule-industry-denominator"),
    "percentage_missing_denominator": lambda d: d["policy"]["rule_contracts"][1].update(denominator_definition_id=None),
    "percentage_missing_denominator_receipt": lambda d: d["policy"]["rule_contracts"][1].update(denominator_definition_receipt_id=None),
}

for case_name, mutator in CUSTOM_REJECTIONS.items():
    setattr(CandidateEvidenceTests, f"test_reject_{case_name}", make_custom_rejection(mutator))


if __name__ == "__main__":
    unittest.main(verbosity=2)
