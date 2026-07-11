#!/usr/bin/env python3

import copy, json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from quote_configuration import BOUNDARY, render_review_output, review_quote_configuration


def fixture():
    return {
        "policy": {
            "policy_id":"policy-alpha","policy_version":"version-alpha","owner_id":"owner-alpha","human_reviewer_role_id":"reviewer-alpha",
            "effective_at":"2026-07-01T00:00:00Z","expires_at":None,"cutoff_at":"2026-07-11T00:00:00Z","timezone":"America/Guayaquil",
            "approved_purpose":"quote_configuration_evidence_review",
            "prohibited_uses":["product-recommendation","price-recommendation","approval-action","customer-send","crm-write","legal-determination","finance-determination","workforce-action"],
            "correction_path":"submit-correction-receipt",
            "catalog_binding":{"catalog_id":"catalog-alpha","catalog_version":"catalog-version-alpha","pricebook_id":"pricebook-alpha","pricebook_version":"pricebook-version-alpha"},
            "calculation_policy":{"discount_scale":"4","discount_rounding":"ROUND_HALF_EVEN"},
            "source_bindings":[{"record_type":"catalog","source_id":"source-catalog","schema_version":"schema-catalog"},{"record_type":"quote","source_id":"source-quote","schema_version":"schema-quote"},{"record_type":"approval","source_id":"source-approval","schema_version":"schema-approval"}],
            "rules":[
                {"rule_id":"rule-discount","rule_type":"numeric","precedence":10,"observation_label":"review-observation-discount","human_review_role_id":"reviewer-finance","fact_id":"fact:line-alpha:discount-percent","operator":"le","threshold":"20","unit":"percent","basis":"net-unit-price","currency":"USD","billing_period":"one-time"},
                {"rule_id":"rule-requires","rule_type":"requires_item","precedence":10,"observation_label":"record-observation-requirement","human_review_role_id":"reviewer-product","left_item_id":"item-alpha","right_item_id":"item-beta"},
                {"rule_id":"rule-quantity","rule_type":"quantity","precedence":10,"observation_label":"review-observation-quantity","human_review_role_id":"reviewer-product","item_id":"item-alpha","operator":"ge","threshold":"2","unit":"seat"},
                {"rule_id":"rule-process","rule_type":"approval_observation","precedence":10,"observation_label":"record-observation-process","human_review_role_id":"reviewer-operations","process_id":"process-alpha","expected_state":"OBSERVED"}
            ]
        },
        "declaration":{"quote_id":"quote-alpha","account_id":"account-alpha","declared_line_count":2,"line_ids":["line-alpha","line-beta"]},
        "catalog_items":[
            {"item_id":"item-alpha","catalog_id":"catalog-alpha","catalog_version":"catalog-version-alpha","pricebook_id":"pricebook-alpha","pricebook_version":"pricebook-version-alpha","pricebook_entry_id":"entry-alpha","item_type":"license","unit":"seat","quantity_scale":"0","currency":"USD","price_basis":"net-unit-price","billing_period":"one-time","effective_at":"2026-07-01T00:00:00Z","expires_at":None,"list_unit_price":"100","active":True,"source_id":"source-catalog","schema_version":"schema-catalog","observed_at":"2026-07-10T00:00:00Z"},
            {"item_id":"item-beta","catalog_id":"catalog-alpha","catalog_version":"catalog-version-alpha","pricebook_id":"pricebook-alpha","pricebook_version":"pricebook-version-alpha","pricebook_entry_id":"entry-beta","item_type":"service","unit":"seat","quantity_scale":"0","currency":"USD","price_basis":"net-unit-price","billing_period":"one-time","effective_at":"2026-07-01T00:00:00Z","expires_at":None,"list_unit_price":"50","active":True,"source_id":"source-catalog","schema_version":"schema-catalog","observed_at":"2026-07-10T00:00:00Z"}
        ],
        "quote_lines":[
            {"line_id":"line-alpha","quote_id":"quote-alpha","account_id":"account-alpha","item_id":"item-alpha","catalog_id":"catalog-alpha","catalog_version":"catalog-version-alpha","pricebook_id":"pricebook-alpha","pricebook_version":"pricebook-version-alpha","pricebook_entry_id":"entry-alpha","quantity":"2","quoted_unit_price":"90","provided_discount_percent":"10","unit":"seat","currency":"USD","price_basis":"net-unit-price","billing_period":"one-time","tax_present":False,"fee_present":False,"shipping_present":False,"ramp_present":False,"usage_present":False,"indefinite_term":False,"source_id":"source-quote","schema_version":"schema-quote","observed_at":"2026-07-10T01:00:00Z"},
            {"line_id":"line-beta","quote_id":"quote-alpha","account_id":"account-alpha","item_id":"item-beta","catalog_id":"catalog-alpha","catalog_version":"catalog-version-alpha","pricebook_id":"pricebook-alpha","pricebook_version":"pricebook-version-alpha","pricebook_entry_id":"entry-beta","quantity":"1","quoted_unit_price":"50","provided_discount_percent":"0","unit":"seat","currency":"USD","price_basis":"net-unit-price","billing_period":"one-time","tax_present":False,"fee_present":False,"shipping_present":False,"ramp_present":False,"usage_present":False,"indefinite_term":False,"source_id":"source-quote","schema_version":"schema-quote","observed_at":"2026-07-10T01:00:00Z"}
        ],
        "approval_processes":[{"process_id":"process-alpha","process_version":"process-version-alpha","mode":"ALL","active":True,"applicable_rule_ids":["rule-discount"],"reviewer_role_ids":["reviewer-finance"],"permission_receipt_id":"permission-alpha","permission_state":"OBSERVED","side_effects_receipt_id":"effects-alpha","side_effects_state":"OBSERVED","state":"OBSERVED","source_id":"source-approval","schema_version":"schema-approval","observed_at":"2026-07-10T02:00:00Z"}]
    }


def facts(result): return {x["fact_id"]:x for x in result["numeric_fact_receipts"]}
def rules(result): return {x["rule_id"]:x for x in result["rule_results"]}


class Tests(unittest.TestCase):
    def test_valid(self):
        r=review_quote_configuration(fixture()); self.assertEqual(r["review_type"],"QUOTE_CONFIGURATION_EVIDENCE_REVIEW"); self.assertEqual(rules(r)["rule-discount"]["state"],"RULE_MATCHED")
    def test_boundary(self): self.assertEqual(review_quote_configuration(fixture())["boundary"],BOUNDARY)
    def test_exact_renderer(self):
        r=review_quote_configuration(fixture()); self.assertEqual(render_review_output(r),json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    def test_decimal_math(self):
        f=facts(review_quote_configuration(fixture())); self.assertEqual(f["fact:line-alpha:list-amount"]["value"],"200"); self.assertEqual(f["fact:line-alpha:quoted-amount"]["value"],"180"); self.assertEqual(f["fact:line-alpha:discount-amount"]["value"],"20"); self.assertEqual(f["fact:line-alpha:discount-percent"]["value"],"10")
    def test_numbers_only_in_fact_or_rule_receipts(self):
        r=review_quote_configuration(fixture()); line=r["quote_line_receipts"][0]; self.assertNotIn("quantity",line); self.assertNotIn("quoted_unit_price",line); self.assertIn("quantity_fact_id",line)
    def test_no_action_keys(self):
        out=render_review_output(review_quote_configuration(fixture())).lower()
        for key in ('"recommendation":','"approver_email":','"approve":','"send":','"crm_write":','"margin":'): self.assertNotIn(key,out)
    def test_r1_absent(self):
        out=render_review_output(review_quote_configuration(fixture())).lower()
        for word in ("small","large","enough","limited","insufficient","good","poor"," high "," low "): self.assertNotIn(word,out)
    def test_unknown_root(self):
        d=fixture(); d["extra"]=1
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_unknown_line(self):
        d=fixture(); d["quote_lines"][0]["extra"]=1
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_direct_email(self):
        d=fixture(); d["policy"]["owner_id"]="person@example.com"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_composite_name_key(self):
        d=fixture(); d["declaration"]["customer_name"]="person"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_free_text_key(self):
        d=fixture(); d["quote_lines"][0]["customer_message"]="text"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_wrong_purpose(self):
        d=fixture(); d["policy"]["approved_purpose"]="quote-send"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_missing_prohibition(self):
        d=fixture(); d["policy"]["prohibited_uses"].remove("customer-send")
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_policy_not_effective(self):
        d=fixture(); d["policy"]["effective_at"]="2026-07-12T00:00:00Z"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_policy_expired(self):
        d=fixture(); d["policy"]["expires_at"]="2026-07-11T00:00:00Z"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_naive_time(self):
        d=fixture(); d["quote_lines"][0]["observed_at"]="2026-07-10T00:00:00"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_future_evidence(self):
        d=fixture(); d["quote_lines"][0]["observed_at"]="2026-07-12T00:00:00Z"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_bad_count(self):
        d=fixture(); d["declaration"]["declared_line_count"]=3
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_duplicate_declared_line(self):
        d=fixture(); d["declaration"]={"quote_id":"quote-alpha","account_id":"account-alpha","declared_line_count":2,"line_ids":["line-alpha","line-alpha"]}
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_missing_line(self):
        d=fixture(); d["quote_lines"]=d["quote_lines"][:1]
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_extra_line(self):
        d=fixture(); x=copy.deepcopy(d["quote_lines"][0]); x["line_id"]="line-extra"; d["quote_lines"].append(x)
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_missing_item(self):
        d=fixture(); d["catalog_items"]=d["catalog_items"][:1]
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_duplicate_item(self):
        d=fixture(); d["catalog_items"].append(copy.deepcopy(d["catalog_items"][0]))
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_inactive_item(self):
        d=fixture(); d["catalog_items"][0]["active"]=False
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_expired_item(self):
        d=fixture(); d["catalog_items"][0]["expires_at"]="2026-07-11T00:00:00Z"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_catalog_version_mismatch(self):
        d=fixture(); d["catalog_items"][0]["catalog_version"]="other"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_pricebook_entry_mismatch(self):
        d=fixture(); d["quote_lines"][0]["pricebook_entry_id"]="entry-other"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_schema_mismatch(self):
        d=fixture(); d["quote_lines"][0]["schema_version"]="other"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_decimal_exponent_rejected(self):
        d=fixture(); d["quote_lines"][0]["quantity"]="1e2"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_float_rejected(self):
        d=fixture(); d["quote_lines"][0]["quoted_unit_price"]=90.0
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_zero_list_rejected(self):
        d=fixture(); d["catalog_items"][0]["list_unit_price"]="0"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_negative_quote_rejected(self):
        d=fixture(); d["quote_lines"][0]["quoted_unit_price"]="-1"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_quantity_precision(self):
        d=fixture(); d["quote_lines"][0]["quantity"]="1.5"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_currency_mismatch(self):
        d=fixture(); d["quote_lines"][0]["currency"]="EUR"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_basis_mismatch(self):
        d=fixture(); d["quote_lines"][0]["price_basis"]="gross-unit-price"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_period_mismatch(self):
        d=fixture(); d["quote_lines"][0]["billing_period"]="monthly"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_adjustment_not_combined(self):
        d=fixture(); d["quote_lines"][0]["tax_present"]=True; r=review_quote_configuration(d); line=next(x for x in r["quote_line_receipts"] if x["line_id"]=="line-alpha"); self.assertEqual(line["state"],"NOT_COMPARABLE"); self.assertEqual(line["derived_fact_ids"],[])
    def test_each_adjustment_blocks(self):
        for field in ("fee_present","shipping_present","ramp_present","usage_present","indefinite_term"):
            d=fixture(); d["quote_lines"][0][field]=True; r=review_quote_configuration(d); self.assertEqual(next(x for x in r["quote_line_receipts"] if x["line_id"]=="line-alpha")["state"],"NOT_COMPARABLE")
    def test_provided_discount_conflict(self):
        d=fixture(); d["quote_lines"][0]["provided_discount_percent"]="11"; r=review_quote_configuration(d); self.assertEqual(next(x for x in r["quote_line_receipts"] if x["line_id"]=="line-alpha")["state"],"PRICE_CONFLICT")
    def test_quote_above_list_is_not_margin(self):
        d=fixture(); d["quote_lines"][0]["quoted_unit_price"]="110"; d["quote_lines"][0]["provided_discount_percent"]="-10"; f=facts(review_quote_configuration(d)); self.assertEqual(f["fact:line-alpha:discount-percent"]["value"],"-10")
    def test_requires_rule_nonmatch(self):
        d=fixture(); d["quote_lines"]=d["quote_lines"][:1]; d["declaration"]={"quote_id":"quote-alpha","account_id":"account-alpha","declared_line_count":1,"line_ids":["line-alpha"]}; r=review_quote_configuration(d); self.assertEqual(rules(r)["rule-requires"]["state"],"RULE_NOT_MATCHED")
    def test_excludes_rule(self):
        d=fixture(); d["policy"]["rules"].append({"rule_id":"rule-excludes","rule_type":"excludes_item","precedence":10,"observation_label":"record-observation-exclusion","human_review_role_id":"reviewer-product","left_item_id":"item-alpha","right_item_id":"item-beta"}); self.assertEqual(rules(review_quote_configuration(d))["rule-excludes"]["state"],"RULE_NOT_MATCHED")
    def test_quantity_nonmatch(self):
        d=fixture(); d["policy"]["rules"][2]["threshold"]="3"; self.assertEqual(rules(review_quote_configuration(d))["rule-quantity"]["state"],"RULE_NOT_MATCHED")
    def test_quantity_unit_mismatch(self):
        d=fixture(); d["policy"]["rules"][2]["unit"]="license"; self.assertEqual(rules(review_quote_configuration(d))["rule-quantity"]["state"],"NOT_COMPARABLE")
    def test_numeric_not_comparable(self):
        d=fixture(); d["policy"]["rules"][0]["currency"]="EUR"; self.assertEqual(rules(review_quote_configuration(d))["rule-discount"]["state"],"NOT_COMPARABLE")
    def test_missing_fact_source_required(self):
        d=fixture(); d["policy"]["rules"][0]["fact_id"]="fact:missing:value"; self.assertEqual(rules(review_quote_configuration(d))["rule-discount"]["state"],"SOURCE_REQUIRED")
    def test_rule_conflict(self):
        d=fixture(); x=copy.deepcopy(d["policy"]["rules"][0]); x["rule_id"]="rule-discount-other"; x["observation_label"]="review-observation-other"; d["policy"]["rules"].append(x); r=review_quote_configuration(d); self.assertEqual(rules(r)["rule-discount"]["state"],"RULE_CONFLICT")
    def test_price_conflict_blocks_numeric_rule(self):
        d=fixture(); d["quote_lines"][0]["provided_discount_percent"]="11"; self.assertEqual(rules(review_quote_configuration(d))["rule-discount"]["state"],"PRICE_CONFLICT")
    def test_unknown_configuration_item_rejected(self):
        d=fixture(); d["policy"]["rules"][1]["right_item_id"]="item-missing"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_action_label_rejected(self):
        d=fixture(); d["policy"]["rules"][0]["observation_label"]="approve-quote"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_prefixed_action_label_rejected(self):
        d=fixture(); d["policy"]["rules"][0]["observation_label"]="review-observation-send"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_approval_modes_preserved(self):
        for mode in ("ALL","ANY","SEQUENTIAL","PARALLEL"):
            d=fixture(); d["approval_processes"][0]["mode"]=mode; self.assertEqual(review_quote_configuration(d)["approval_process_receipts"][0]["mode"],mode)
    def test_bad_approval_mode(self):
        d=fixture(); d["approval_processes"][0]["mode"]="AUTO"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_missing_permission_receipt(self):
        d=fixture(); d["approval_processes"][0]["permission_receipt_id"]=""
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_permission_conflict_requires_source(self):
        d=fixture(); d["approval_processes"][0]["permission_state"]="CONFLICT"; self.assertEqual(rules(review_quote_configuration(d))["rule-process"]["state"],"SOURCE_REQUIRED")
    def test_side_effects_conflict_requires_source(self):
        d=fixture(); d["approval_processes"][0]["side_effects_state"]="CONFLICT"; self.assertEqual(rules(review_quote_configuration(d))["rule-process"]["state"],"SOURCE_REQUIRED")
    def test_process_missing_reviewer_role_rejected(self):
        d=fixture(); d["approval_processes"][0]["reviewer_role_ids"]=["reviewer-other"]
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_missing_process_rule_source_required(self):
        d=fixture(); d["policy"]["rules"][3]["process_id"]="process-missing"; self.assertEqual(rules(review_quote_configuration(d))["rule-process"]["state"],"SOURCE_REQUIRED")
    def test_inactive_process_requires_source(self):
        d=fixture(); d["approval_processes"][0]["active"]=False; self.assertEqual(rules(review_quote_configuration(d))["rule-process"]["state"],"SOURCE_REQUIRED")
    def test_unknown_process_rule_id_rejected(self):
        d=fixture(); d["approval_processes"][0]["applicable_rule_ids"]=["rule-missing"]
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_group_receipt_has_line_ids(self):
        r=review_quote_configuration(fixture()); self.assertEqual(r["amount_group_receipts"][0]["line_ids"],["line-alpha","line-beta"])
    def test_customer_rounding_policy(self):
        d=fixture(); d["catalog_items"][0]["list_unit_price"]="3"; d["quote_lines"][0]["quoted_unit_price"]="2"; d["quote_lines"][0]["provided_discount_percent"]="33.3333"; f=facts(review_quote_configuration(d)); self.assertEqual(f["fact:line-alpha:discount-percent"]["value"],"33.3333")
    def test_bad_rounding_policy(self):
        d=fixture(); d["policy"]["calculation_policy"]["discount_rounding"]="ROUND_RANDOM"
        with self.assertRaises(ValueError): review_quote_configuration(d)
    def test_empty_complete_quote(self):
        d=fixture(); d["declaration"]={"quote_id":"quote-alpha","account_id":"account-alpha","declared_line_count":0,"line_ids":[]}; d["quote_lines"]=[]; d["policy"]["rules"]=[d["policy"]["rules"][3]]; d["approval_processes"][0]["applicable_rule_ids"]=["rule-process"]; d["approval_processes"][0]["reviewer_role_ids"]=["reviewer-operations"]; r=review_quote_configuration(d); self.assertEqual(r["quote_line_receipts"],[])
    def test_group_separation(self):
        d=fixture(); d["catalog_items"][1]["currency"]="EUR"; d["quote_lines"][1]["currency"]="EUR"; r=review_quote_configuration(d); self.assertEqual(len(r["amount_group_receipts"]),2)
    def test_order_independence(self):
        a=render_review_output(review_quote_configuration(fixture())); d=fixture(); d["policy"]["source_bindings"].reverse(); d["policy"]["rules"].reverse(); d["catalog_items"].reverse(); d["quote_lines"].reverse(); self.assertEqual(a,render_review_output(review_quote_configuration(d)))
    def test_no_eval_or_writes_in_helper(self):
        source=Path(__file__).with_name("quote_configuration.py").read_text(); self.assertNotIn("eval(",source); self.assertNotIn("requests",source); self.assertNotIn("write_text",source); self.assertNotIn("o"+"pen(",source)


if __name__=="__main__": unittest.main()
