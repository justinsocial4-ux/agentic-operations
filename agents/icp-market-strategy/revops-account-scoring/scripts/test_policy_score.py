#!/usr/bin/env python3
import unittest
from decimal import Decimal
from policy_score import policy_gate, score_account


class PolicyScoreTests(unittest.TestCase):
    def setUp(self):
        self.policy = {"policy_id":"APS-7","version":"2","owner":"Morgan","effective_date":"2026-07-01","population_id":"POP-3","entity_level":"legal_account","cutoff":"2026-07-10T00:00:00Z","analysis_scope_status":"APPROVED","privacy_scope_status":"APPROVED","downstream_use_status":"APPROVED","feature_rules":[{"feature_id":"industry","component":"fit","min_points":"0","max_points":"20","missing_rule":"UNAVAILABLE"},{"feature_id":"geography","component":"fit","min_points":"0","max_points":"15","missing_rule":"ZERO"},{"feature_id":"meeting","component":"engagement","min_points":"0","max_points":"20","missing_rule":"UNAVAILABLE"},{"feature_id":"reply","component":"engagement","min_points":"0","max_points":"10","missing_rule":"FIXED","fixed_points":"2"}],"component_limits":{"fit":"35","engagement":"30"},"combined_weights":{"fit":"0.6","engagement":"0.4"},"thresholds":[{"label":"review_a","min_inclusive":"70","max_exclusive":None},{"label":"review_b","min_inclusive":"0","max_exclusive":"70"}]}
        self.evidence = [{"feature_id":"industry","status":"VERIFIED","points":"20"},{"feature_id":"geography","status":"VERIFIED","points":"15"},{"feature_id":"meeting","status":"VERIFIED","points":"12"},{"feature_id":"reply","status":"VERIFIED","points":"8"}]

    def test_gate_pass(self): self.assertEqual(policy_gate(self.policy)["status"], "POLICY_EVIDENCE_PRESENT")
    def test_gate_missing(self): self.assertEqual(policy_gate({})["status"], "POLICY_EVIDENCE_REQUIRED")
    def test_gate_blocked(self): self.assertEqual(policy_gate(dict(self.policy, downstream_use_status="DENIED"))["status"], "POLICY_SCOPE_NOT_APPROVED")
    def test_exact_components_and_combined(self):
        result=score_account(self.evidence,self.policy)
        self.assertEqual(result["component_scores"],{"fit":Decimal("1"),"engagement":Decimal("0.6666666666666666666666666667")})
        self.assertEqual(result["combined_policy_score"],Decimal("86.66666666666666666666666667"))
        self.assertEqual(result["policy_label"],"review_a")
    def test_unknown_unavailable_blocks_component(self):
        rows=[dict(x) for x in self.evidence]; rows[0]={"feature_id":"industry","status":"UNKNOWN","points":None}
        result=score_account(rows,self.policy); self.assertIsNone(result["component_scores"]["fit"]); self.assertIsNone(result["combined_policy_score"])
    def test_missing_row_applies_unavailable(self):
        result=score_account(self.evidence[1:],self.policy); self.assertIn("fit",result["unavailable_components"])
    def test_zero_missing_rule(self):
        rows=[x for x in self.evidence if x["feature_id"]!="geography"]
        result=score_account(rows,self.policy); receipt=next(x for x in result["feature_receipts"] if x["feature_id"]=="geography"); self.assertEqual((receipt["treatment"],receipt["points"]),("ZERO",Decimal("0")))
    def test_fixed_missing_rule(self):
        rows=[x for x in self.evidence if x["feature_id"]!="reply"]
        result=score_account(rows,self.policy); receipt=next(x for x in result["feature_receipts"] if x["feature_id"]=="reply"); self.assertEqual(receipt["points"],Decimal("2"))
    def test_conflict_blocks_component(self):
        rows=[dict(x) for x in self.evidence]; rows[2]={"feature_id":"meeting","status":"CONFLICT","points":None}
        result=score_account(rows,self.policy); self.assertEqual(result["status"],"FEATURE_CONFLICT_REVIEW"); self.assertEqual(result["conflict_features"],["meeting"])
    def test_unknown_with_points_rejected(self):
        rows=[dict(x) for x in self.evidence]; rows[0]={"feature_id":"industry","status":"UNKNOWN","points":"10"}
        with self.assertRaises(ValueError): score_account(rows,self.policy)
    def test_float_rejected(self):
        rows=[dict(x) for x in self.evidence]; rows[0]["points"]=20.0
        with self.assertRaises(ValueError): score_account(rows,self.policy)
    def test_out_of_bounds_rejected(self):
        rows=[dict(x) for x in self.evidence]; rows[0]["points"]="21"
        with self.assertRaises(ValueError): score_account(rows,self.policy)
    def test_duplicate_evidence_rejected(self):
        with self.assertRaises(ValueError): score_account(self.evidence+[dict(self.evidence[0])],self.policy)
    def test_unapproved_feature_rejected(self):
        with self.assertRaises(ValueError): score_account(self.evidence+[{"feature_id":"intent","status":"VERIFIED","points":"1"}],self.policy)
    def test_duplicate_rule_rejected(self):
        policy=dict(self.policy,feature_rules=self.policy["feature_rules"]+[dict(self.policy["feature_rules"][0])])
        with self.assertRaises(ValueError): score_account(self.evidence,policy)
    def test_bad_component_rejected(self):
        rules=[dict(x) for x in self.policy["feature_rules"]]; rules[0]["component"]="priority"
        with self.assertRaises(ValueError): score_account(self.evidence,dict(self.policy,feature_rules=rules))
    def test_bad_missing_rule_rejected(self):
        rules=[dict(x) for x in self.policy["feature_rules"]]; rules[0]["missing_rule"]="NEUTRAL"
        with self.assertRaises(ValueError): score_account(self.evidence,dict(self.policy,feature_rules=rules))
    def test_fixed_outside_bounds_rejected(self):
        rules=[dict(x) for x in self.policy["feature_rules"]]; rules[3]["fixed_points"]="99"
        with self.assertRaises(ValueError): score_account(self.evidence,dict(self.policy,feature_rules=rules))
    def test_zero_outside_bounds_rejected(self):
        rules=[dict(x) for x in self.policy["feature_rules"]]; rules[1]["min_points"]="1"
        with self.assertRaises(ValueError): score_account(self.evidence,dict(self.policy,feature_rules=rules))
    def test_bad_weights_rejected(self):
        with self.assertRaises(ValueError): score_account(self.evidence,dict(self.policy,combined_weights={"fit":"0.7","engagement":"0.4"}))
    def test_no_weights_means_no_combined(self): self.assertIsNone(score_account(self.evidence,dict(self.policy,combined_weights=None))["combined_policy_score"])
    def test_no_thresholds_means_no_label(self): self.assertIsNone(score_account(self.evidence,dict(self.policy,thresholds=None))["policy_label"])
    def test_threshold_gap_means_no_label(self):
        policy=dict(self.policy,thresholds=[{"label":"x","min_inclusive":"90","max_exclusive":None}])
        self.assertIsNone(score_account(self.evidence,policy)["policy_label"])
    def test_overlapping_thresholds_rejected(self):
        policy=dict(self.policy,thresholds=[{"label":"x","min_inclusive":"0","max_exclusive":None},{"label":"y","min_inclusive":"0","max_exclusive":None}])
        with self.assertRaises(ValueError): score_account(self.evidence,policy)
    def test_component_limit_overflow_rejected(self):
        with self.assertRaises(ValueError): score_account(self.evidence,dict(self.policy,component_limits={"fit":"34","engagement":"30"}))
    def test_latent_threshold_overlap_rejected(self):
        policy=dict(self.policy,thresholds=[{"label":"x","min_inclusive":"0","max_exclusive":"50"},{"label":"y","min_inclusive":"40","max_exclusive":"70"},{"label":"z","min_inclusive":"70","max_exclusive":None}])
        with self.assertRaises(ValueError): score_account(self.evidence,policy)
    def test_invalid_threshold_range_rejected(self):
        policy=dict(self.policy,thresholds=[{"label":"x","min_inclusive":"70","max_exclusive":"60"}])
        with self.assertRaises(ValueError): score_account(self.evidence,policy)
    def test_nonlist_thresholds_rejected(self):
        with self.assertRaises(ValueError): score_account(self.evidence,dict(self.policy,thresholds={}))
    def test_blocked_policy_does_not_score(self): self.assertEqual(score_account(self.evidence,dict(self.policy,analysis_scope_status="DENIED"))["status"],"POLICY_SCOPE_NOT_APPROVED")

if __name__ == "__main__": unittest.main()
