#!/usr/bin/env python3

import copy
import json
import unittest

from deal_evidence import BOUNDARY, render_review_output, review_deals


def fixture():
    policy = {
        "policy_id":"POL-DEAL","version":"V1","purpose":"DEAL_EVIDENCE_REVIEW","owner":"OWNER-1","reviewer":"REVIEWER-1",
        "effective_date":"2026-07-01","cutoff":"2026-07-10T12:00:00Z","timezone":"UTC","population_policy_id":"POP-POL",
        "source_id":"SRC-CURRENT","source_version":"SV1","schema_id":"SCHEMA-DEAL","schema_version":"SC1",
        "stage_history_source_id":"SRC-STAGE","stage_history_source_version":"ST1","activity_source_id":"SRC-ACTIVITY",
        "activity_source_version":"ACT1","pipeline_id":"PIPE-1","open_stage_ids":["STAGE-A","STAGE-B"],
        "terminal_stage_ids":["WON","LOST"],"stage_threshold_days":{"STAGE-A":20,"STAGE-B":30},
        "activity_threshold_days":14,"qualifying_activity_types":["BUYER_CALL","BUYER_EMAIL","BUYER_MEETING"],
        "activity_occurrence_rule_id":"ACT-OCC","activity_association_rule_id":"ACT-ASSOC","amount_basis":"CRM_PIPELINE_AMOUNT",
        "currency":"USD","identity_policy_status":"APPROVED","stage_policy_status":"APPROVED",
        "activity_policy_status":"APPROVED","amount_policy_status":"APPROVED","privacy_policy_status":"APPROVED",
        "workforce_policy_status":"APPROVED","downstream_use_status":"APPROVED","action_approval_status":"NOT_APPROVED",
        "correction_path":"STEWARD-1","prohibited_uses":["COACHING","FORECAST","WORKFORCE_ACTION"],
    }
    population = {"receipt_id":"POP-R1","policy_id":"POP-POL","population_status":"COMPLETE","declared_deal_count":2,
                  "source_id":"SRC-CURRENT","source_version":"SV1","schema_id":"SCHEMA-DEAL","schema_version":"SC1","extraction_id":"EXT-POP"}
    def deal(deal_id):
        return {
            "deal_id":deal_id,"account_id":f"ACCOUNT-{deal_id}","owner_id":f"OWNER-{deal_id}",
            "population_membership_status":"VERIFIED_MEMBER","population_membership_receipt_id":f"MEM-{deal_id}",
            "source_id":"SRC-CURRENT","source_version":"SV1","schema_id":"SCHEMA-DEAL","schema_version":"SC1",
            "extraction_id":f"EXT-{deal_id}","evidence_cutoff":"2026-07-10T12:00:00Z","pipeline_id":"PIPE-1",
            "current_stage_id":"STAGE-A","current_state_receipt_id":f"CURRENT-{deal_id}","stage_entry_state":"AVAILABLE",
            "current_stage_entered_at":"2026-07-01T12:00:00Z","stage_history_source_id":"SRC-STAGE",
            "stage_history_source_version":"ST1","stage_history_receipt_id":f"STAGE-{deal_id}","close_date_state":"AVAILABLE",
            "close_date":"2026-07-31","close_date_receipt_id":f"CLOSE-{deal_id}","activity_population_state":"COMPLETE",
            "activity_population_receipt_id":f"ACT-POP-{deal_id}","activity_state":"AVAILABLE","last_activity_at":"2026-07-08T12:00:00Z",
            "last_activity_type":"BUYER_MEETING","activity_source_id":"SRC-ACTIVITY","activity_source_version":"ACT1",
            "activity_occurrence_rule_id":"ACT-OCC","activity_association_rule_id":"ACT-ASSOC",
            "activity_receipt_id":f"ACT-{deal_id}","amount_state":"AVAILABLE","amount":"125000.00","currency":"USD",
            "amount_basis":"CRM_PIPELINE_AMOUNT","amount_receipt_id":f"AMOUNT-{deal_id}",
        }
    return {"review_id":"REVIEW-1","policy":policy,"population_receipt":population,"deals":[deal("D1"),deal("D2")]}


class DealEvidenceTests(unittest.TestCase):
    def test_happy_path(self):
        result=review_deals(fixture()); self.assertEqual(result["review_deal_ids"],[]); self.assertFalse(result["action_authorized"])

    def test_stage_threshold(self):
        data=fixture(); data["deals"][0]["current_stage_entered_at"]="2026-06-01T12:00:00Z"
        result=review_deals(data); self.assertIn("D1",result["review_deal_ids"]); self.assertIn("STAGE_THRESHOLD_EXCEEDED",result["deal_receipts"][0]["review_reasons"])

    def test_activity_threshold(self):
        data=fixture(); data["deals"][0]["last_activity_at"]="2026-06-01T12:00:00Z"
        self.assertIn("ACTIVITY_THRESHOLD_EXCEEDED",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_past_close_date(self):
        data=fixture(); data["deals"][0]["close_date"]="2026-07-09"
        self.assertIn("DATE_BEFORE_CUTOFF",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_stage_unavailable(self):
        data=fixture(); d=data["deals"][0]; d["stage_entry_state"]="UNAVAILABLE"; d["current_stage_entered_at"]=None
        self.assertIn("STAGE_ENTRY_UNAVAILABLE",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_stage_conflict(self):
        data=fixture(); d=data["deals"][0]; d["stage_entry_state"]="CONFLICT"; d["current_stage_entered_at"]=None
        self.assertIn("STAGE_HISTORY_CONFLICT",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_no_activity(self):
        data=fixture(); d=data["deals"][0]; d["activity_state"]="NO_QUALIFYING_ACTIVITY_RECORDED"; d["last_activity_at"]=None; d["last_activity_type"]=None
        self.assertIn("NO_QUALIFYING_ACTIVITY_RECORDED",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_activity_unavailable(self):
        data=fixture(); d=data["deals"][0]; d["activity_population_state"]="INCOMPLETE"; d["activity_state"]="EVIDENCE_UNAVAILABLE"; d["last_activity_at"]=None; d["last_activity_type"]=None
        self.assertIn("ACTIVITY_EVIDENCE_UNAVAILABLE",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_amount_unavailable_not_zero(self):
        data=fixture(); d=data["deals"][0]; d["amount_state"]="UNAVAILABLE"; d["amount"]=None
        row=review_deals(data)["deal_receipts"][0]; self.assertIsNone(row["amount_lane"]["amount"]); self.assertIn("AMOUNT_UNAVAILABLE",row["review_reasons"])

    def test_zero_amount_preserved(self):
        data=fixture(); data["deals"][0]["amount"]="0"
        self.assertEqual(review_deals(data)["deal_receipts"][0]["amount_lane"]["amount"],"0")

    def test_currency_conflict(self):
        data=fixture(); data["deals"][0]["currency"]="EUR"
        self.assertIn("CURRENCY_CONFLICT",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_amount_basis_conflict(self):
        data=fixture(); data["deals"][0]["amount_basis"]="ARR"
        self.assertIn("AMOUNT_BASIS_CONFLICT",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_float_amount_rejected(self):
        data=fixture(); data["deals"][0]["amount"]=1.2
        with self.assertRaisesRegex(ValueError,"decimal string"): review_deals(data)

    def test_duplicate_deal_rejected(self):
        data=fixture(); data["deals"][1]["deal_id"]="D1"
        with self.assertRaisesRegex(ValueError,"duplicate deal_id"): review_deals(data)

    def test_population_count_mismatch(self):
        data=fixture(); data["population_receipt"]["declared_deal_count"]=3
        self.assertEqual(review_deals(data)["gate"],"POPULATION_INCOMPLETE")

    def test_population_incomplete(self):
        data=fixture(); data["population_receipt"]["population_status"]="INCOMPLETE"
        self.assertEqual(review_deals(data)["gate"],"POPULATION_INCOMPLETE")

    def test_population_binding_conflict(self):
        data=fixture(); data["population_receipt"]["source_version"]="OLD"
        self.assertEqual(review_deals(data)["gate"],"POPULATION_INCOMPLETE")

    def test_policy_not_approved(self):
        data=fixture(); data["policy"]["workforce_policy_status"]="PENDING"
        self.assertEqual(review_deals(data)["gate"],"POLICY_REQUIRED")

    def test_membership_conflict_reviewed(self):
        data=fixture(); data["deals"][0]["population_membership_status"]="CONFLICT"
        self.assertIn("POPULATION_MEMBERSHIP_REVIEW",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_terminal_stage_in_open_population(self):
        data=fixture(); data["deals"][0]["current_stage_id"]="WON"
        self.assertIn("CURRENT_STAGE_NOT_OPEN",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_source_conflict(self):
        data=fixture(); data["deals"][0]["source_version"]="OLD"
        self.assertIn("SOURCE_POLICY_CONFLICT",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_stage_source_conflict(self):
        data=fixture(); data["deals"][0]["stage_history_source_version"]="OLD"
        row=review_deals(data)["deal_receipts"][0]; self.assertIn("STAGE_HISTORY_SOURCE_CONFLICT",row["review_reasons"]); self.assertIsNone(row["stage_lane"]["elapsed_days"])

    def test_activity_source_conflict(self):
        data=fixture(); data["deals"][0]["activity_source_version"]="OLD"
        row=review_deals(data)["deal_receipts"][0]; self.assertIn("ACTIVITY_SOURCE_CONFLICT",row["review_reasons"]); self.assertIsNone(row["activity_lane"]["elapsed_days"])

    def test_activity_rule_conflict(self):
        data=fixture(); data["deals"][0]["activity_association_rule_id"]="OTHER"
        row=review_deals(data)["deal_receipts"][0]; self.assertIn("ACTIVITY_SOURCE_CONFLICT",row["review_reasons"]); self.assertIsNone(row["activity_lane"]["elapsed_days"])

    def test_current_source_conflict_disables_derived_current_lanes(self):
        data=fixture(); data["deals"][0]["source_version"]="OLD"
        row=review_deals(data)["deal_receipts"][0]; self.assertIsNone(row["stage_lane"]["elapsed_days"]); self.assertEqual(row["close_date_lane"]["result"],"CURRENT_STATE_SOURCE_CONFLICT"); self.assertEqual(row["amount_lane"]["result"],"CURRENT_STATE_SOURCE_CONFLICT")

    def test_future_evidence(self):
        data=fixture(); data["deals"][0]["evidence_cutoff"]="2026-07-10T13:00:00Z"
        self.assertIn("SOURCE_POLICY_CONFLICT",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_pre_policy_evidence(self):
        data=fixture(); data["deals"][0]["evidence_cutoff"]="2026-06-30T12:00:00Z"; data["deals"][0]["current_stage_entered_at"]="2026-06-01T12:00:00Z"; data["deals"][0]["last_activity_at"]="2026-06-29T12:00:00Z"
        self.assertIn("SOURCE_POLICY_CONFLICT",review_deals(data)["deal_receipts"][0]["review_reasons"])

    def test_stage_entry_after_cutoff_rejected(self):
        data=fixture(); data["deals"][0]["current_stage_entered_at"]="2026-07-11T00:00:00Z"
        with self.assertRaisesRegex(ValueError,"after evidence cutoff"): review_deals(data)

    def test_activity_after_cutoff_rejected(self):
        data=fixture(); data["deals"][0]["last_activity_at"]="2026-07-11T00:00:00Z"
        with self.assertRaisesRegex(ValueError,"after evidence cutoff"): review_deals(data)

    def test_unqualified_activity_type_rejected(self):
        data=fixture(); data["deals"][0]["last_activity_type"]="TASK_CREATED"
        with self.assertRaisesRegex(ValueError,"not policy-qualified"): review_deals(data)

    def test_unavailable_activity_cannot_have_timestamp(self):
        data=fixture(); data["deals"][0]["activity_state"]="EVIDENCE_UNAVAILABLE"
        with self.assertRaisesRegex(ValueError,"null occurrence"): review_deals(data)

    def test_unavailable_stage_cannot_have_timestamp(self):
        data=fixture(); data["deals"][0]["stage_entry_state"]="UNAVAILABLE"
        with self.assertRaisesRegex(ValueError,"null timestamp"): review_deals(data)

    def test_unavailable_close_cannot_have_date(self):
        data=fixture(); data["deals"][0]["close_date_state"]="UNAVAILABLE"
        with self.assertRaisesRegex(ValueError,"must be null"): review_deals(data)

    def test_unavailable_amount_cannot_have_value(self):
        data=fixture(); data["deals"][0]["amount_state"]="UNAVAILABLE"
        with self.assertRaisesRegex(ValueError,"must be null"): review_deals(data)

    def test_non_utc_rejected(self):
        data=fixture(); data["deals"][0]["evidence_cutoff"]="2026-07-10T07:00:00-05:00"
        with self.assertRaisesRegex(ValueError,"use UTC"): review_deals(data)

    def test_open_terminal_overlap_rejected(self):
        data=fixture(); data["policy"]["terminal_stage_ids"].append("STAGE-A")
        with self.assertRaisesRegex(ValueError,"disjoint"): review_deals(data)

    def test_threshold_coverage_rejected(self):
        data=fixture(); del data["policy"]["stage_threshold_days"]["STAGE-B"]
        with self.assertRaisesRegex(ValueError,"cover every active stage"): review_deals(data)

    def test_duplicate_policy_list_rejected(self):
        data=fixture(); data["policy"]["qualifying_activity_types"].append("BUYER_CALL")
        with self.assertRaisesRegex(ValueError,"duplicates"): review_deals(data)

    def test_forbidden_name_rejected(self):
        data=fixture(); data["deals"][0]["owner_name"]="Person"
        with self.assertRaisesRegex(ValueError,"prohibited"): review_deals(data)

    def test_forbidden_probability_rejected(self):
        data=fixture(); data["deals"][0]["probability"]="0.5"
        with self.assertRaisesRegex(ValueError,"prohibited"): review_deals(data)

    def test_nonpseudonymous_id_rejected(self):
        data=fixture(); data["deals"][0]["owner_id"]="person@example.com"
        with self.assertRaisesRegex(ValueError,"pseudonymous"): review_deals(data)

    def test_unknown_field_rejected(self):
        data=fixture(); data["policy"]["risk_threshold"]="1"
        with self.assertRaisesRegex(ValueError,"unsupported fields"): review_deals(data)

    def test_unranked_deterministic_review_set(self):
        first=fixture(); first["deals"][0]["close_date"]="2026-07-09"; second=copy.deepcopy(first); second["deals"].reverse()
        self.assertEqual(render_review_output(review_deals(first)),render_review_output(review_deals(second)))

    def test_renderer_single_artifact(self):
        output=render_review_output(review_deals(fixture())); self.assertTrue(output.startswith("```json\n")); self.assertTrue(output.endswith(BOUNDARY)); self.assertEqual(output.count("```json"),1); json.loads(output.split("```json\n",1)[1].split("\n```",1)[0])

    def test_prohibited_conclusions(self):
        result=review_deals(fixture()); self.assertIn("CLOSE_PROBABILITY",result["prohibited_conclusions"]); self.assertIn("SELLER_PERFORMANCE",result["prohibited_conclusions"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
