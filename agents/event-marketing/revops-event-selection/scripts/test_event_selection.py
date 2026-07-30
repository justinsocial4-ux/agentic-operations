#!/usr/bin/env python3

import copy
import json
import unittest

from event_selection import BOUNDARY, build_selection, render_selection_output


def fixture():
    policy = {
        "policy_id": "POL-EVENT", "version": "2", "owner": "OWNER-1", "reviewer": "REVIEWER-1",
        "effective_date": "2026-07-01", "cutoff": "2026-07-10T12:00:00Z",
        "purpose": "EVENT_CRITERIA_COMPARISON", "candidate_population_id": "POP-1",
        "candidate_population_receipt_id": "POP-R-1", "candidate_population_status": "COMPLETE",
        "candidate_count": 3, "source_id": "SRC-1", "source_version": "3",
        "schema_id": "SCHEMA-1", "schema_version": "4", "currency": "USD", "cost_basis": "SPONSORSHIP_QUOTE",
        "accepted_cost_statuses": ["APPROVED_QUOTE"], "capacity": 2,
        "tie_rule": "NO_AUTOMATIC_TIE_BREAK", "action_approval_status": "NOT_APPROVED",
        "proposed_use": "HUMAN_EVENT_PORTFOLIO_REVIEW", "records_system": "SYS-1",
        "correction_path": "CORRECTION-1", "prohibited_uses": ["AUTOMATIC_SPONSORSHIP"],
        "identity_policy_status": "APPROVED", "criteria_policy_status": "APPROVED",
        "cost_policy_status": "APPROVED", "privacy_policy_status": "APPROVED",
        "downstream_use_status": "APPROVED",
        "criteria": [
            {"criterion_id": "C1", "definition": "Approved organization overlap rule", "evidence_rule_id": "ER-1", "required": True, "weight": "60"},
            {"criterion_id": "C2", "definition": "Approved event-format rule", "evidence_rule_id": "ER-2", "required": False, "weight": "40"},
        ],
    }

    def event(event_id, c1="MATCHED", c2="MATCHED"):
        return {
            "event_id": event_id, "population_membership_status": "VERIFIED_MEMBER",
            "population_membership_receipt_id": f"MEM-{event_id}", "identity_status": "RESOLVED",
            "identity_receipt_id": f"ID-{event_id}", "source_id": "SRC-1", "source_version": "3",
            "schema_id": "SCHEMA-1", "schema_version": "4", "extraction_id": f"EXT-{event_id}",
            "evidence_cutoff": "2026-07-10T11:00:00Z", "evidence_population_status": "COMPLETE",
            "evidence_population_receipt_id": f"EPOP-{event_id}", "event_begin_date": "2026-09-01",
            "event_end_date": "2026-09-03", "cost_status": "APPROVED_QUOTE", "cost_amount": "25000.00",
            "currency": "USD", "cost_basis": "SPONSORSHIP_QUOTE", "cost_receipt_id": f"COST-{event_id}",
            "evidence_organization_count": 2,
            "organization_receipts": [
                {"organization_id": f"ORG-{event_id}-1", "identity_status": "RESOLVED", "identity_receipt_id": f"OID-{event_id}-1"},
                {"organization_id": f"ORG-{event_id}-2", "identity_status": "RESOLVED", "identity_receipt_id": f"OID-{event_id}-2"},
            ],
            "criterion_evidence": [
                {"criterion_id": "C1", "state": c1, "evidence_receipt_id": f"C1-{event_id}", "evidence_rule_id": "ER-1"},
                {"criterion_id": "C2", "state": c2, "evidence_receipt_id": f"C2-{event_id}", "evidence_rule_id": "ER-2"},
            ],
        }

    return {"policy": policy, "events": [event("E1"), event("E2", c2="NOT_MATCHED"), event("E3", c1="NOT_MATCHED")]}


class EventSelectionTests(unittest.TestCase):
    def test_happy_path(self):
        result = build_selection(fixture())
        self.assertEqual(result["selection_event_ids"], ["E1", "E2"])
        self.assertEqual(result["gate"], "READY_FOR_HUMAN_REVIEW")
        self.assertFalse(result["action_authorized"])

    def test_exact_scores(self):
        result = build_selection(fixture())
        scores = {row["event_id"]: row["policy_score"] for row in result["event_receipts"]}
        self.assertEqual(scores, {"E1": "100", "E2": "60", "E3": "40"})

    def test_required_nonmatch_excluded(self):
        result = build_selection(fixture())
        row = next(item for item in result["event_receipts"] if item["event_id"] == "E3")
        self.assertEqual(row["disposition"], "REQUIRED_CRITERION_NOT_MATCHED")

    def test_policy_not_approved(self):
        data = fixture(); data["policy"]["privacy_policy_status"] = "PENDING"
        self.assertEqual(build_selection(data)["gate"], "POLICY_REQUIRED")

    def test_population_status_incomplete(self):
        data = fixture(); data["policy"]["candidate_population_status"] = "INCOMPLETE"
        self.assertEqual(build_selection(data)["gate"], "POPULATION_INCOMPLETE")

    def test_population_count_mismatch(self):
        data = fixture(); data["policy"]["candidate_count"] = 4
        self.assertEqual(build_selection(data)["gate"], "POPULATION_INCOMPLETE")

    def test_duplicate_event_rejected(self):
        data = fixture(); data["events"][1]["event_id"] = "E1"
        with self.assertRaisesRegex(ValueError, "duplicate event_id"): build_selection(data)

    def test_unknown_policy_field_rejected(self):
        data = fixture(); data["policy"]["forecast_model"] = "X"
        with self.assertRaisesRegex(ValueError, "unsupported fields"): build_selection(data)

    def test_unknown_event_field_rejected(self):
        data = fixture(); data["events"][0]["predicted_value"] = "1"
        with self.assertRaisesRegex(ValueError, "unsupported fields"): build_selection(data)

    def test_forbidden_email_rejected(self):
        data = fixture(); data["events"][0]["attendee_email"] = "person@example.com"
        with self.assertRaisesRegex(ValueError, "prohibited"): build_selection(data)

    def test_forbidden_prediction_rejected(self):
        data = fixture(); data["events"][0]["predicted_pipeline"] = "1"
        with self.assertRaisesRegex(ValueError, "prohibited"): build_selection(data)

    def test_nonpseudonymous_org_rejected(self):
        data = fixture(); data["events"][0]["organization_receipts"][0]["organization_id"] = "person@example.com"
        with self.assertRaisesRegex(ValueError, "pseudonymous"): build_selection(data)

    def test_duplicate_org_rejected(self):
        data = fixture(); data["events"][0]["organization_receipts"][1]["organization_id"] = data["events"][0]["organization_receipts"][0]["organization_id"]
        with self.assertRaisesRegex(ValueError, "duplicate organization"): build_selection(data)

    def test_identity_ambiguous_unresolved(self):
        data = fixture(); data["events"][0]["identity_status"] = "AMBIGUOUS"
        result = build_selection(data)
        self.assertEqual(result["gate"], "EVIDENCE_REVIEW")
        self.assertIn("E1", result["review_event_ids"])

    def test_organization_identity_unknown_unresolved(self):
        data = fixture(); data["events"][0]["organization_receipts"][0]["identity_status"] = "UNKNOWN"
        result = build_selection(data)
        self.assertEqual(result["gate"], "EVIDENCE_REVIEW")
        self.assertIn("E1", result["review_event_ids"])

    def test_organization_count_mismatch_rejected(self):
        data = fixture(); data["events"][0]["evidence_organization_count"] = 3
        with self.assertRaisesRegex(ValueError, "does not reconcile"): build_selection(data)

    def test_membership_unknown_preserved(self):
        data = fixture(); data["events"][0]["population_membership_status"] = "UNKNOWN"
        result = build_selection(data)
        row = next(item for item in result["event_receipts"] if item["event_id"] == "E1")
        self.assertEqual(row["disposition"], "POPULATION_MEMBERSHIP_REVIEW")

    def test_source_conflict(self):
        data = fixture(); data["events"][0]["source_version"] = "OLD"
        self.assertEqual(build_selection(data)["gate"], "EVIDENCE_REVIEW")

    def test_schema_conflict(self):
        data = fixture(); data["events"][0]["schema_version"] = "OLD"
        self.assertEqual(build_selection(data)["gate"], "EVIDENCE_REVIEW")

    def test_future_evidence(self):
        data = fixture(); data["events"][0]["evidence_cutoff"] = "2026-07-10T13:00:00Z"
        self.assertEqual(build_selection(data)["gate"], "EVIDENCE_REVIEW")

    def test_pre_policy_evidence(self):
        data = fixture(); data["events"][0]["evidence_cutoff"] = "2026-06-30T23:00:00Z"
        self.assertEqual(build_selection(data)["gate"], "EVIDENCE_REVIEW")

    def test_non_utc_rejected(self):
        data = fixture(); data["events"][0]["evidence_cutoff"] = "2026-07-10T06:00:00-05:00"
        with self.assertRaisesRegex(ValueError, "use UTC"): build_selection(data)

    def test_incomplete_event_population(self):
        data = fixture(); data["events"][0]["evidence_population_status"] = "INCOMPLETE"
        self.assertEqual(build_selection(data)["gate"], "EVIDENCE_REVIEW")

    def test_unapproved_cost(self):
        data = fixture(); data["events"][0]["cost_status"] = "UNAVAILABLE"; data["events"][0]["cost_amount"] = None
        self.assertEqual(build_selection(data)["gate"], "EVIDENCE_REVIEW")

    def test_float_cost_rejected(self):
        data = fixture(); data["events"][0]["cost_amount"] = 25000.0
        with self.assertRaisesRegex(ValueError, "decimal string"): build_selection(data)

    def test_mixed_currency(self):
        data = fixture(); data["events"][0]["currency"] = "EUR"
        self.assertEqual(build_selection(data)["gate"], "EVIDENCE_REVIEW")

    def test_cost_basis_conflict(self):
        data = fixture(); data["events"][0]["cost_basis"] = "ESTIMATE"
        self.assertEqual(build_selection(data)["gate"], "EVIDENCE_REVIEW")

    def test_duplicate_accepted_cost_status_rejected(self):
        data = fixture(); data["policy"]["accepted_cost_statuses"] = ["APPROVED_QUOTE", "APPROVED_QUOTE"]
        with self.assertRaisesRegex(ValueError, "contains duplicates"): build_selection(data)

    def test_date_order_rejected(self):
        data = fixture(); data["events"][0]["event_end_date"] = "2026-08-31"
        with self.assertRaisesRegex(ValueError, "precedes begin"): build_selection(data)

    def test_unknown_criterion_rejected(self):
        data = fixture(); data["events"][0]["criterion_evidence"][0]["criterion_id"] = "C9"
        with self.assertRaisesRegex(ValueError, "unknown criterion"): build_selection(data)

    def test_missing_criterion_rejected(self):
        data = fixture(); data["events"][0]["criterion_evidence"].pop()
        with self.assertRaisesRegex(ValueError, "every policy criterion"): build_selection(data)

    def test_rule_conflict_rejected(self):
        data = fixture(); data["events"][0]["criterion_evidence"][0]["evidence_rule_id"] = "OTHER"
        with self.assertRaisesRegex(ValueError, "conflicts with policy"): build_selection(data)

    def test_unknown_criterion_state_unresolved(self):
        data = fixture(); data["events"][0]["criterion_evidence"][1]["state"] = "UNKNOWN"
        result = build_selection(data)
        self.assertEqual(result["gate"], "EVIDENCE_REVIEW")
        self.assertEqual(result["selection_event_ids"], [])

    def test_weights_must_total_100(self):
        data = fixture(); data["policy"]["criteria"][1]["weight"] = "39"
        with self.assertRaisesRegex(ValueError, "exactly 100"): build_selection(data)

    def test_unapproved_adequacy_label_rejected(self):
        data = fixture(); data["policy"]["criteria"][0]["definition"] = "High organization overlap"
        with self.assertRaisesRegex(ValueError, "unapproved adequacy label"): build_selection(data)

    def test_float_weight_rejected(self):
        data = fixture(); data["policy"]["criteria"][0]["weight"] = 60.0
        with self.assertRaisesRegex(ValueError, "decimal string"): build_selection(data)

    def test_duplicate_criterion_definition_rejected(self):
        data = fixture(); data["policy"]["criteria"][1]["criterion_id"] = "C1"
        with self.assertRaisesRegex(ValueError, "duplicate criterion_id"): build_selection(data)

    def test_boundary_tie(self):
        data = fixture(); data["policy"]["capacity"] = 1
        data["events"][1]["criterion_evidence"][1]["state"] = "MATCHED"
        result = build_selection(data)
        self.assertEqual(result["gate"], "BOUNDARY_TIE_REVIEW")
        self.assertEqual(result["selection_event_ids"], [])
        self.assertEqual(result["review_event_ids"], ["E1", "E2"])

    def test_zero_capacity(self):
        data = fixture(); data["policy"]["capacity"] = 0
        result = build_selection(data)
        self.assertEqual(result["selection_event_ids"], [])
        self.assertEqual(result["capacity_receipt"]["unfilled_slots"], 0)

    def test_unfilled_capacity(self):
        data = fixture(); data["policy"]["capacity"] = 5
        result = build_selection(data)
        self.assertEqual(result["capacity_receipt"]["filled_slots"], 2)
        self.assertEqual(result["capacity_receipt"]["unfilled_slots"], 3)

    def test_deterministic_input_order(self):
        first = fixture(); second = copy.deepcopy(first); second["events"].reverse()
        self.assertEqual(render_selection_output(build_selection(first)), render_selection_output(build_selection(second)))

    def test_renderer_is_single_json_and_boundary(self):
        output = render_selection_output(build_selection(fixture()))
        self.assertTrue(output.startswith("```json\n"))
        self.assertTrue(output.endswith(BOUNDARY))
        self.assertEqual(output.count("```json"), 1)
        json.loads(output.split("```json\n", 1)[1].split("\n```", 1)[0])

    def test_prohibited_conclusions_and_no_action(self):
        result = build_selection(fixture())
        self.assertIn("ROI", result["prohibited_conclusions"])
        self.assertIn("EXPECTED_PIPELINE", result["prohibited_conclusions"])
        self.assertFalse(result["action_authorized"])
        self.assertEqual(result["boundary"], BOUNDARY)


if __name__ == "__main__":
    unittest.main(verbosity=2)
