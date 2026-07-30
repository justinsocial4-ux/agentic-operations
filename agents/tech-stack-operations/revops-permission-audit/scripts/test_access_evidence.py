#!/usr/bin/env python3
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from access_evidence import BOUNDARY, main, render_review_output, review_access, validate_policy


class AccessEvidenceTests(unittest.TestCase):
    def policy(self, **changes):
        value={"policy_id":"POLICY","version":"V1","purpose":"read-only observed entitlement review","cutoff":"2026-07-10T12:00:00Z","max_age_days":30,"source_policy_id":"SOURCE-POLICY","population_policy_id":"POP-POLICY","system_id":"SYSTEM","source_schema_id":"SCHEMA","source_schema_version":"S1","entitlement_namespace_id":"NAMESPACE","entitlement_namespace_version":"N1","observed_access_semantics":"OBSERVED_ASSIGNMENTS_ONLY","account_type_policy_id":"TYPE-POLICY","access_rule_policy_id":"RULE-POLICY","authorization_policy_id":"AUTH-POLICY","exception_policy_id":"EXCEPTION-POLICY","activity_policy_id":"ACTIVITY-POLICY","activity_threshold_days":30,"activity_eligible_account_types":["INDIVIDUAL"],"control_context_id":"CONTROL-CONTEXT","privacy_policy_id":"PRIVACY-POLICY","workforce_policy_id":"WORKFORCE-POLICY","owner_role":"POLICY-OWNER","reviewer_role":"REVIEWER","approver_role":"APPROVER","correction_path":"EVIDENCE-STEWARD","prohibited_uses":["access-write","compliance-verdict","workforce-action"]}
        value.update(changes); return value

    def evidence(self):
        common={"system_id":"SYSTEM","source_id":"SOURCE","source_version":"SNAPSHOT-1","schema_id":"SCHEMA","schema_version":"S1","as_of":"2026-07-01T00:00:00Z","extracted_at":"2026-07-02T00:00:00Z","access_scope":"pseudonymous-read-only","policy_id":"SOURCE-POLICY"}
        return [{**common,"evidence_id":key} for key in ("E-ACCOUNT","E-IDENTITY","E-AUTH","E-ACTIVITY","E-EXCEPTION","E-POLICY")]

    def rule(self, **changes):
        value={"rule_id":"RULE-A","policy_id":"RULE-POLICY","entitlement_namespace_id":"NAMESPACE","entitlement_namespace_version":"N1","account_type":"INDIVIDUAL","required_entitlement_ids":["READ"],"allowed_entitlement_ids":["READ","WRITE"],"prohibited_entitlement_ids":["ADMIN"],"evidence_id":"E-POLICY"}
        value.update(changes); return value

    def account(self, account_id="ACCOUNT-A", **changes):
        value={"account_id":account_id,"subject_id":"SUBJECT-A","identity_state":"VERIFIED","account_type":"INDIVIDUAL","account_type_policy_id":"TYPE-POLICY","rule_id":"RULE-A","entitlement_namespace_id":"NAMESPACE","entitlement_namespace_version":"N1","platform_state":"ACTIVE","authorization_state":"AUTHORIZED","authorization_policy_id":"AUTH-POLICY","observed_entitlement_ids":["READ"],"assignment_count":1,"activity_state":"AVAILABLE","activity_policy_id":"ACTIVITY-POLICY","last_activity_at":"2026-07-01T00:00:00Z","evidence_id":"E-ACCOUNT","identity_evidence_id":"E-IDENTITY","authorization_evidence_id":"E-AUTH","activity_evidence_id":"E-ACTIVITY"}
        value.update(changes); return value

    def exception(self, **changes):
        value={"account_id":"ACCOUNT-A","entitlement_id":"ADMIN","state":"APPROVED","policy_id":"EXCEPTION-POLICY","entitlement_namespace_id":"NAMESPACE","entitlement_namespace_version":"N1","begin_at":"2026-07-01T00:00:00Z","expires_at":"2026-08-01T00:00:00Z","approval_receipt_id":"APPROVAL-A","evidence_id":"E-EXCEPTION"}
        value.update(changes); return value

    def population(self, accounts=None, **changes):
        accounts=[self.account()] if accounts is None else accounts
        value={"receipt_id":"POPULATION-A","policy_id":"POP-POLICY","system_id":"SYSTEM","declared_account_count":len(accounts),"declared_assignment_count":sum(row["assignment_count"] for row in accounts),"declared_entitlement_occurrence_count":sum(len(row["observed_entitlement_ids"]) for row in accounts),"evidence_id":"E-POLICY"}
        value.update(changes); return value

    def document(self, **changes):
        accounts=changes.pop("account_rows",[self.account()])
        value={"review_id":"REVIEW-A","policy":self.policy(),"evidence_rows":self.evidence(),"population_receipt":self.population(accounts),"rule_rows":[self.rule()],"account_rows":accounts,"exception_rows":[],"approval_state":"APPROVAL_REQUIRED"}
        value.update(changes); return value

    def review(self, **changes): return review_access(**self.document(**changes))
    def result(self, **changes): return self.review(**changes)["account_results"][0]

    def test_policy_valid(self): self.assertEqual(validate_policy(self.policy())["system_id"],"SYSTEM")
    def test_policy_unknown_field_rejected(self):
        with self.assertRaises(ValueError): validate_policy({**self.policy(),"severity_threshold":2})
    def test_observed_semantics_fixed(self):
        with self.assertRaises(ValueError): validate_policy(self.policy(observed_access_semantics="EFFECTIVE_ACCESS"))
    def test_match(self): self.assertEqual(self.result()["entitlement_result"]["state"],"MATCHED")
    def test_required_missing(self): self.assertEqual(self.result(account_rows=[self.account(observed_entitlement_ids=[])])["entitlement_result"]["required_missing"],["READ"])
    def test_prohibited_observed(self): self.assertEqual(self.result(account_rows=[self.account(observed_entitlement_ids=["READ","ADMIN"])])["entitlement_result"]["prohibited_observed"],["ADMIN"])
    def test_outside_allowed(self): self.assertEqual(self.result(account_rows=[self.account(observed_entitlement_ids=["READ","EXPORT"])])["entitlement_result"]["outside_allowed"],["EXPORT"])
    def test_active_exception_covers_difference(self):
        account=self.account(observed_entitlement_ids=["READ","ADMIN"]); result=self.review(account_rows=[account],exception_rows=[self.exception()])
        self.assertEqual((result["account_results"][0]["entitlement_result"]["state"],result["exception_receipts"][0]["exception_result_state"]),("MATCHED_WITH_ACTIVE_EXCEPTION","ACTIVE"))
    def test_expired_exception_visible_and_not_covering(self):
        account=self.account(observed_entitlement_ids=["READ","ADMIN"]); result=self.review(account_rows=[account],exception_rows=[self.exception(expires_at="2026-07-05T00:00:00Z")])
        self.assertEqual((result["account_results"][0]["entitlement_result"]["state"],result["exception_receipts"][0]["exception_result_state"]),("DIFFERENCE_FOUND","EXPIRED"))
    def test_stale_exception_evidence_preserved(self):
        evidence=self.evidence(); evidence[4].update(as_of="2020-01-01T00:00:00Z",extracted_at="2020-01-02T00:00:00Z"); account=self.account(observed_entitlement_ids=["READ","ADMIN"])
        self.assertEqual(self.review(evidence_rows=evidence,account_rows=[account],exception_rows=[self.exception()])["exception_receipts"][0]["exception_result_state"],"STALE")
    def test_exception_unknown_account_rejected(self):
        with self.assertRaises(ValueError): self.review(exception_rows=[self.exception(account_id="ACCOUNT-X")])
    def test_exception_unobserved_entitlement_rejected(self):
        with self.assertRaises(ValueError): self.review(exception_rows=[self.exception()])
    def test_duplicate_exception_rejected(self):
        account=self.account(observed_entitlement_ids=["READ","ADMIN"])
        with self.assertRaises(ValueError): self.review(account_rows=[account],exception_rows=[self.exception(),self.exception()])
    def test_population_reconciled(self): self.assertEqual(self.review()["population_reconciliation"]["state"],"RECONCILED")
    def test_receipt_is_self_contained(self):
        result=self.review(); account=result["account_results"][0]
        self.assertEqual((result["population_reconciliation"]["receipt_id"],result["access_rules"][0]["rule_id"],account["observed_entitlement_ids"],account["evidence_ids"]["authorization"]),("POPULATION-A","RULE-A",["READ"],"E-AUTH"))
    def test_population_incomplete_blocks_entitlement_conclusion(self):
        population=self.population(declared_account_count=2); result=self.review(population_receipt=population)
        self.assertEqual((result["population_reconciliation"]["state"],result["account_results"][0]["entitlement_result"]["state"]),("POPULATION_INCOMPLETE","POPULATION_INCOMPLETE"))
    def test_population_policy_mismatch(self):
        with self.assertRaises(ValueError): self.review(population_receipt=self.population(policy_id="WRONG"))
    def test_population_system_mismatch(self):
        with self.assertRaises(ValueError): self.review(population_receipt=self.population(system_id="WRONG"))
    def test_account_source_coverage_state(self):
        evidence=self.evidence(); evidence[0].update(as_of="2020-01-01T00:00:00Z",extracted_at="2020-01-02T00:00:00Z")
        self.assertEqual(self.review(evidence_rows=evidence)["population_reconciliation"]["account_source_coverage_state"],"SOURCE_REQUIRED")
    def test_identity_unavailable_independent(self): self.assertEqual(self.result(account_rows=[self.account(identity_state="UNAVAILABLE")])["identity_result_state"],"UNAVAILABLE")
    def test_authorization_conflict(self): self.assertEqual(self.result(account_rows=[self.account(authorization_state="REVOKED")])["authorization_result_state"],"STATE_CONFLICT")
    def test_unknown_authorization_unresolved(self): self.assertEqual(self.result(account_rows=[self.account(authorization_state="UNKNOWN")])["authorization_result_state"],"AUTHORIZATION_UNRESOLVED")
    def test_unknown_platform_unresolved(self): self.assertEqual(self.result(account_rows=[self.account(platform_state="UNKNOWN")])["authorization_result_state"],"AUTHORIZATION_UNRESOLVED")
    def test_stale_authorization_evidence_preserved(self):
        evidence=self.evidence(); evidence[2].update(as_of="2020-01-01T00:00:00Z",extracted_at="2020-01-02T00:00:00Z")
        self.assertEqual(self.result(evidence_rows=evidence)["authorization_result_state"],"STALE")
    def test_activity_within(self): self.assertEqual(self.result()["activity_result_state"],"WITHIN_THRESHOLD")
    def test_activity_exceeded(self): self.assertEqual(self.result(account_rows=[self.account(last_activity_at="2026-05-01T00:00:00Z")])["activity_result_state"],"THRESHOLD_EXCEEDED")
    def test_activity_missing(self): self.assertEqual(self.result(account_rows=[self.account(activity_state="UNAVAILABLE",last_activity_at=None)])["activity_result_state"],"SOURCE_REQUIRED")
    def test_activity_future_conflict(self): self.assertEqual(self.result(account_rows=[self.account(last_activity_at="2026-08-01T00:00:00Z")])["activity_result_state"],"CONFLICTING")
    def test_nonavailable_activity_cannot_hide_timestamp(self):
        with self.assertRaises(ValueError): self.review(account_rows=[self.account(activity_state="UNAVAILABLE")])
    def test_activity_not_applicable(self):
        rule=self.rule(account_type="SERVICE"); account=self.account(account_type="SERVICE")
        self.assertEqual(self.result(rule_rows=[rule],account_rows=[account])["activity_result_state"],"NOT_APPLICABLE")
    def test_duplicate_account_rejected(self):
        accounts=[self.account(),self.account()]
        with self.assertRaises(ValueError): self.review(account_rows=accounts)
    def test_duplicate_observed_entitlement_rejected(self):
        with self.assertRaises(ValueError): self.review(account_rows=[self.account(observed_entitlement_ids=["READ","READ"])])
    def test_rule_overlap_rejected(self):
        with self.assertRaises(ValueError): self.review(rule_rows=[self.rule(prohibited_entitlement_ids=["READ"])])
    def test_rule_required_must_be_allowed(self):
        with self.assertRaises(ValueError): self.review(rule_rows=[self.rule(required_entitlement_ids=["ADMIN"])])
    def test_rule_namespace_mismatch_rejected(self):
        with self.assertRaises(ValueError): self.review(rule_rows=[self.rule(entitlement_namespace_version="WRONG")])
    def test_namespace_mismatch_rejected(self):
        with self.assertRaises(ValueError): self.review(account_rows=[self.account(entitlement_namespace_version="WRONG")])
    def test_lane_policy_mismatch_rejected(self):
        with self.assertRaises(ValueError): self.review(account_rows=[self.account(activity_policy_id="WRONG")])
    def test_evidence_system_mismatch_blocks_lane(self):
        evidence=self.evidence(); evidence[0]["system_id"]="WRONG"
        self.assertEqual(self.result(evidence_rows=evidence)["entitlement_result"]["state"],"POLICY_REQUIRED")
    def test_exception_namespace_mismatch_rejected(self):
        account=self.account(observed_entitlement_ids=["READ","ADMIN"])
        with self.assertRaises(ValueError): self.review(account_rows=[account],exception_rows=[self.exception(entitlement_namespace_version="WRONG")])
    def test_exception_queue_contains_independent_lanes(self):
        account=self.account(authorization_state="UNKNOWN",activity_state="UNAVAILABLE",last_activity_at=None,observed_entitlement_ids=["READ","ADMIN"])
        lanes=[row["lane"] for row in self.review(account_rows=[account])["exception_queue"]]
        self.assertEqual(lanes,["ACTIVITY","AUTHORIZATION","ENTITLEMENT"])
    def test_direct_identifier_key_rejected(self):
        account=self.account(); account["email"]="redacted"
        with self.assertRaises(ValueError): self.review(account_rows=[account])
    def test_direct_identifier_value_rejected(self):
        account=self.account(subject_id="person@example.test")
        with self.assertRaises(ValueError): self.review(account_rows=[account])
    def test_no_verdict_score_or_action(self):
        result=self.review(); self.assertEqual((result["ranked"],result["compliance_verdict_authorized"],result["risk_score_authorized"],result["savings_score_authorized"],result["access_action_authorized"],result["workforce_action_authorized"]),(False,False,False,False,False,False))
    def test_approval_state_strict(self):
        with self.assertRaises(ValueError): self.review(approval_state="AUTO_APPROVED")
    def test_deterministic_order(self):
        accounts=[self.account("ACCOUNT-B",subject_id="SUBJECT-B"),self.account()]; population=self.population(accounts)
        first=self.review(account_rows=accounts,population_receipt=population); second=self.review(account_rows=list(reversed(accounts)),population_receipt=population)
        self.assertEqual(first,second)
    def test_inputs_not_mutated(self):
        document=self.document(); original=copy.deepcopy(document); review_access(**document); self.assertEqual(document,original)
    def test_renderer_exact_boundary(self):
        rendered=render_review_output(self.review()); self.assertEqual(rendered[:9],"```json\n{"); self.assertTrue(rendered.endswith(BOUNDARY)); self.assertEqual(rendered.count(BOUNDARY),2)
    def test_no_adequacy_or_severity_labels(self):
        rendered=render_review_output(self.review()).casefold()
        for phrase in ("small sample","large sample","enough data","limited data","insufficient data","critical finding","high severity"):
            self.assertNotIn(phrase,rendered)
    def test_cli_equals_renderer(self):
        document=self.document()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"input.json"; path.write_text(json.dumps(document)); output=io.StringIO()
            with redirect_stdout(output): main([str(path)])
        self.assertEqual(output.getvalue().rstrip("\n"),render_review_output(self.review()))


if __name__=="__main__": unittest.main()
