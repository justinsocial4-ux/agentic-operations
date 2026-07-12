#!/usr/bin/env python3
"""Tests for deterministic enrichment route-plan evidence review."""

from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPEC = importlib.util.spec_from_file_location("route_evidence", HERE / "route_evidence.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def provider(provider_id: str, contract_version: str, field_id: str, unit_cost: str) -> dict:
    suffix = provider_id.removeprefix("provider-")
    return {
        "provider_id": provider_id,
        "contract_id": f"contract-{suffix}",
        "contract_version": contract_version,
        "authorization_effective_at": "2026-07-01T00:00:00Z",
        "authorization_expires_at": "2026-12-31T23:59:59Z",
        "contract_receipt_id": f"receipt-{suffix}-contract",
        "authorization_receipt_id": f"receipt-{suffix}-authorization",
        "terms_receipt_id": f"receipt-{suffix}-terms",
        "geography_receipt_id": f"receipt-{suffix}-geography",
        "field_support_receipt_id": f"receipt-{suffix}-field-support",
        "price_receipt_id": f"receipt-{suffix}-price",
        "geography_scope_id": "geography-north-america",
        "charge_unit": "per-route-assignment",
        "currency": "USD",
        "unit_cost": unit_cost,
        "supported_fields": [{"field_id": field_id, "field_version": "version-one"}],
    }


def base_document() -> dict:
    governance = {
        "operations_approval_receipt_id": "receipt-operations-approval",
        "security_review_receipt_id": "receipt-security-review",
        "privacy_review_receipt_id": "receipt-privacy-review",
        "legal_review_receipt_id": "receipt-legal-review",
        "lawful_basis_receipt_id": "receipt-lawful-basis",
        "notice_receipt_id": "receipt-notice",
        "objection_path_receipt_id": "receipt-objection-path",
        "suppression_policy_receipt_id": "receipt-suppression-policy",
        "correction_path_receipt_id": "receipt-correction-path",
        "recipient_policy_receipt_id": "receipt-recipient-policy",
        "retention_policy_receipt_id": "receipt-retention-policy",
        "route_policy_receipt_id": "receipt-route-policy",
    }
    return {
        "review_declaration": {
            "review_id": "review-alpha",
            "policy_id": "policy-alpha",
            "policy_version": "version-one",
            "reviewed_at": "2026-07-11T12:05:00Z",
            "recipient_role_id": "role-route-reviewer",
            "record_ids": ["record-alpha", "record-beta"],
            "requested_fields": [
                {"record_id": "record-alpha", "fields": [{"field_id": "field-email", "field_version": "version-one"}]},
                {"record_id": "record-beta", "fields": [{"field_id": "field-phone", "field_version": "version-one"}]},
            ],
        },
        "policy": {
            "policy_id": "policy-alpha",
            "policy_version": "version-one",
            "effective_at": "2026-07-01T00:00:00Z",
            "expires_at": "2026-12-31T23:59:59Z",
            "cutoff_at": "2026-07-11T12:00:00Z",
            "timezone": "UTC",
            "approved_purpose": MODULE.PURPOSE,
            "currency": "USD",
            "owner_role_id": "role-operations-owner",
            "human_reviewer_role_id": "role-route-reviewer",
            **governance,
            "allowed_recipient_role_ids": ["role-route-reviewer"],
            "prohibited_uses": sorted(MODULE.REQUIRED_PROHIBITIONS),
            "source_bindings": [{
                "source_id": "source-route-plan",
                "source_version": "version-one",
                "source_kind": MODULE.SOURCE_KIND,
                "schema_id": "schema-route-plan",
                "schema_version": "version-one",
                "authorization_receipt_id": "receipt-source-authorization",
                "authorization_effective_at": "2026-07-01T00:00:00Z",
                "authorization_expires_at": "2026-12-31T23:59:59Z",
                "query_receipt_id": "receipt-source-query",
                "page_receipt_id": "receipt-source-pages",
                "pseudonymization_receipt_id": "receipt-source-pseudonymization",
            }],
            "field_definitions": [
                {
                    "field_id": "field-email", "field_version": "version-one",
                    "definition_receipt_id": "receipt-email-definition",
                    "purpose_receipt_id": "receipt-email-purpose",
                    "minimization_receipt_id": "receipt-email-minimization",
                    "field_policy_receipt_id": "receipt-email-policy",
                },
                {
                    "field_id": "field-phone", "field_version": "version-one",
                    "definition_receipt_id": "receipt-phone-definition",
                    "purpose_receipt_id": "receipt-phone-purpose",
                    "minimization_receipt_id": "receipt-phone-minimization",
                    "field_policy_receipt_id": "receipt-phone-policy",
                },
            ],
            "provider_contracts": [
                provider("provider-alpha", "version-one", "field-email", "0.125"),
                provider("provider-beta", "version-one", "field-phone", "0.250"),
            ],
        },
        "source_populations": [{
            "source_id": "source-route-plan", "source_version": "version-one",
            "population_receipt_id": "receipt-route-population", "complete": True,
            "route_receipt_ids": ["receipt-route-alpha-email", "receipt-route-beta-phone"],
        }],
        "route_plan": [
            {
                "record_id": "record-alpha", "field_id": "field-email", "field_version": "version-one",
                "source_id": "source-route-plan", "source_version": "version-one",
                "route_receipt_id": "receipt-route-alpha-email", "request_state": "eligible",
                "request_state_receipt_id": "receipt-state-alpha-email",
                "provider_id": "provider-alpha", "provider_contract_version": "version-one",
                "assignment_receipt_id": "receipt-assignment-alpha-email",
                "geography_scope_id": "geography-north-america",
                "observed_at": "2026-07-11T11:56:00Z", "captured_at": "2026-07-11T11:57:00Z",
            },
            {
                "record_id": "record-beta", "field_id": "field-phone", "field_version": "version-one",
                "source_id": "source-route-plan", "source_version": "version-one",
                "route_receipt_id": "receipt-route-beta-phone", "request_state": "suppressed",
                "request_state_receipt_id": "receipt-state-beta-phone",
                "provider_id": None, "provider_contract_version": None,
                "assignment_receipt_id": None, "geography_scope_id": None,
                "observed_at": "2026-07-11T11:56:00Z", "captured_at": "2026-07-11T11:57:00Z",
            },
        ],
    }


def review(doc: dict) -> dict:
    return MODULE.review_route_evidence(doc)


class RouteEvidenceTests(unittest.TestCase):
    def assert_invalid(self, mutate) -> None:
        doc = base_document()
        mutate(doc)
        with self.assertRaises(ValueError):
            review(doc)

    def test_match_and_suppression(self):
        result = review(base_document())
        self.assertEqual(result["evidence_state"], "SUPPRESSED")
        self.assertEqual(result["route_reviews"][0]["evidence_state"], "CUSTOMER_ROUTE_EVIDENCE_MATCHED")
        self.assertEqual(result["route_reviews"][1]["evidence_state"], "SUPPRESSED")

    def test_exact_decimal_charges(self):
        result = review(base_document())
        self.assertEqual(result["aggregate_planned_charge_receipt"], {"currency": "USD", "planned_charge": "0.125"})
        route_charge = result["route_reviews"][0]["planned_charge_basis_receipt"]
        self.assertEqual(route_charge, {"charge_unit": "per-route-assignment", "currency": "USD", "included_in_aggregate": True})
        self.assertNotIn("planned_charge", route_charge)

    def test_unsupported_supplied_provider_nonmatch(self):
        doc = base_document()
        doc["route_plan"][0]["provider_id"] = "provider-beta"
        result = review(doc)
        self.assertEqual(result["route_reviews"][0]["evidence_state"], "CUSTOMER_ROUTE_EVIDENCE_NOT_MATCHED")
        self.assertIsNone(result["route_reviews"][0]["planned_charge_basis_receipt"])

    def test_unknown_provider_nonmatch(self):
        doc = base_document()
        doc["route_plan"][0]["provider_id"] = "provider-unknown"
        result = review(doc)
        self.assertEqual(result["route_reviews"][0]["evidence_state"], "CUSTOMER_ROUTE_EVIDENCE_NOT_MATCHED")

    def test_geography_mismatch_nonmatch(self):
        doc = base_document()
        doc["route_plan"][0]["geography_scope_id"] = "geography-europe"
        self.assertEqual(review(doc)["route_reviews"][0]["evidence_state"], "CUSTOMER_ROUTE_EVIDENCE_NOT_MATCHED")

    def test_all_unresolved_states(self):
        expected = {"missing": "EVIDENCE_MISSING", "conflicting": "EVIDENCE_CONFLICT", "suppressed": "SUPPRESSED", "unauthorized": "UNAUTHORIZED"}
        for state, output in expected.items():
            with self.subTest(state=state):
                doc = base_document()
                doc["route_plan"][0].update({"request_state": state, "provider_id": None, "provider_contract_version": None, "assignment_receipt_id": None, "geography_scope_id": None})
                self.assertEqual(review(doc)["route_reviews"][0]["evidence_state"], output)

    def test_unresolved_precedence(self):
        doc = base_document()
        doc["route_plan"][0].update({"request_state": "unauthorized", "provider_id": None, "provider_contract_version": None, "assignment_receipt_id": None, "geography_scope_id": None})
        self.assertEqual(review(doc)["evidence_state"], "UNAUTHORIZED")

    def test_all_actions_false(self):
        self.assertEqual(set(review(base_document())["action_authorization"].values()), {False})

    def test_exact_renderer_boundary(self):
        rendered = MODULE.render_review_output(review(base_document()))
        self.assertTrue(rendered.startswith("{"))
        self.assertTrue(rendered.endswith("}\n\n"))
        self.assertEqual(json.loads(rendered)["review_id"], "review-alpha")

    def test_no_provider_recommendation_output(self):
        rendered = MODULE.render_review_output(review(base_document())).lower()
        for forbidden in ("optimal", "recommended provider", "confidence", "accuracy", "write to crm", "send outreach"):
            self.assertNotIn(forbidden, rendered)

    def test_bundle_has_eleven_members(self):
        members = [path for path in ROOT.rglob("*") if path.is_file() and "__pycache__" not in path.parts]
        self.assertEqual(len(members), 11)

    def test_skill_routes_eight_references(self):
        skill = (ROOT / "SKILL.md").read_text()
        for name in (
            "scope_and_governance.md", "source_and_population.md", "field_and_route_contract.md",
            "provider_and_charge_contract.md", "privacy_and_identity.md", "output_and_action_boundary.md",
            "verification_sources.md", "failure_states.md",
        ):
            self.assertIn(name, skill)

    def test_skill_exact_helper_rule(self):
        skill = (ROOT / "SKILL.md").read_text()
        self.assertIn("render_review_output(review_route_evidence(document))", skill)
        self.assertIn("byte for byte", skill)


INVALID = {
    "extra_root_key": lambda d: d.update({"extra": True}),
    "wrong_purpose": lambda d: d["policy"].update({"approved_purpose": "enrichment"}),
    "bad_currency": lambda d: d["policy"].update({"currency": "usd"}),
    "bad_timezone": lambda d: d["policy"].update({"timezone": "Mars/Olympus"}),
    "expired_policy": lambda d: d["policy"].update({"expires_at": "2026-07-10T00:00:00Z"}),
    "review_before_cutoff": lambda d: d["review_declaration"].update({"reviewed_at": "2026-07-11T11:59:00Z"}),
    "unapproved_recipient": lambda d: d["review_declaration"].update({"recipient_role_id": "role-other"}),
    "missing_prohibition": lambda d: d["policy"]["prohibited_uses"].remove("provider-ranking"),
    "duplicate_governance_receipt": lambda d: d["policy"].update({"security_review_receipt_id": d["policy"]["operations_approval_receipt_id"]}),
    "bad_source_kind": lambda d: d["policy"]["source_bindings"][0].update({"source_kind": "api"}),
    "expired_source_auth": lambda d: d["policy"]["source_bindings"][0].update({"authorization_expires_at": "2026-07-10T00:00:00Z"}),
    "capture_before_source_auth": lambda d: d["route_plan"][0].update({"observed_at": "2026-06-30T23:58:00Z", "captured_at": "2026-06-30T23:59:00Z"}),
    "future_capture": lambda d: d["route_plan"][0].update({"captured_at": "2026-07-11T12:01:00Z"}),
    "observed_after_capture": lambda d: d["route_plan"][0].update({"observed_at": "2026-07-11T11:58:00Z"}),
    "incomplete_population": lambda d: d["source_populations"][0].update({"complete": False}),
    "missing_population_route": lambda d: d["source_populations"][0]["route_receipt_ids"].pop(),
    "extra_population_route": lambda d: d["source_populations"][0]["route_receipt_ids"].append("receipt-route-extra"),
    "duplicate_population_route": lambda d: d["source_populations"][0]["route_receipt_ids"].append(d["source_populations"][0]["route_receipt_ids"][0]),
    "missing_route": lambda d: d["route_plan"].pop(),
    "duplicate_route": lambda d: d["route_plan"].append(copy.deepcopy(d["route_plan"][0])),
    "undeclared_record": lambda d: d["route_plan"][0].update({"record_id": "record-gamma"}),
    "undeclared_field": lambda d: d["route_plan"][0].update({"field_id": "field-title"}),
    "direct_record_id": lambda d: d["review_declaration"]["record_ids"].__setitem__(0, "john-smith"),
    "direct_provider_id": lambda d: d["policy"]["provider_contracts"][0].update({"provider_id": "apollo"}),
    "bad_money_float": lambda d: d["policy"]["provider_contracts"][0].update({"unit_cost": 0.125}),
    "negative_money": lambda d: d["policy"]["provider_contracts"][0].update({"unit_cost": "-0.125"}),
    "wrong_charge_unit": lambda d: d["policy"]["provider_contracts"][0].update({"charge_unit": "per-match"}),
    "provider_currency_mismatch": lambda d: d["policy"]["provider_contracts"][0].update({"currency": "EUR"}),
    "expired_provider_auth": lambda d: d["policy"]["provider_contracts"][0].update({"authorization_expires_at": "2026-07-10T00:00:00Z"}),
    "unsupported_contract_field": lambda d: d["policy"]["provider_contracts"][0]["supported_fields"][0].update({"field_id": "field-title"}),
    "duplicate_field_definition": lambda d: d["policy"]["field_definitions"].append(copy.deepcopy(d["policy"]["field_definitions"][0])),
    "missing_requested_record": lambda d: d["review_declaration"]["requested_fields"].pop(),
    "duplicate_requested_field": lambda d: d["review_declaration"]["requested_fields"][0]["fields"].append(copy.deepcopy(d["review_declaration"]["requested_fields"][0]["fields"][0])),
    "eligible_without_provider": lambda d: d["route_plan"][0].update({"provider_id": None, "provider_contract_version": None, "assignment_receipt_id": None, "geography_scope_id": None}),
    "suppressed_with_provider": lambda d: d["route_plan"][1].update({"provider_id": "provider-beta", "provider_contract_version": "version-one"}),
    "bad_request_state": lambda d: d["route_plan"][0].update({"request_state": "ready"}),
    "duplicate_state_receipt": lambda d: d["route_plan"][1].update({"request_state_receipt_id": d["route_plan"][0]["request_state_receipt_id"]}),
    "missing_assignment_receipt": lambda d: d["route_plan"][0].update({"assignment_receipt_id": None}),
}


def _make(mutate):
    def test(self):
        self.assert_invalid(mutate)
    return test


for _name, _mutate in INVALID.items():
    setattr(RouteEvidenceTests, f"test_reject_{_name}", _make(_mutate))


if __name__ == "__main__":
    unittest.main(verbosity=2)
