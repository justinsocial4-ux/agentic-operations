#!/usr/bin/env python3
"""Deterministic read-only observed-entitlement comparison."""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

BOUNDARY="NO COMPLIANCE VERDICT / NO RISK OR SAVINGS SCORE / NO ACCESS, TICKET, MESSAGE, SCHEDULE, OR WORKFORCE ACTION"
SENSITIVE=("email","phone","first_name","last_name","full_name","person_name","job_performance","message_content")

def strict(row, fields, label):
    if not isinstance(row,dict): raise ValueError(f"{label} must be an object")
    unknown=set(row)-set(fields); missing=set(fields)-set(row)
    if unknown or missing: raise ValueError(f"{label} fields mismatch: unknown={sorted(unknown)} missing={sorted(missing)}")
    return dict(row)

def text(value,label):
    if not isinstance(value,str) or not value.strip(): raise ValueError(f"{label} must be non-empty text")
    return value.strip()

def when(value,label):
    value=text(value,label)
    try: parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc: raise ValueError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None: raise ValueError(f"{label} must include an offset")
    return parsed.astimezone(timezone.utc)

def reject_sensitive(value,path="root"):
    if isinstance(value,dict):
        for key,item in value.items():
            if any(part in str(key).casefold() for part in SENSITIVE): raise ValueError(f"sensitive field prohibited: {path}.{key}")
            reject_sensitive(item,f"{path}.{key}")
    elif isinstance(value,list):
        for index,item in enumerate(value): reject_sensitive(item,f"{path}[{index}]")
    elif isinstance(value,str) and "@" in value:
        raise ValueError(f"direct identifier prohibited: {path}")

def validate_policy(raw):
    fields={"policy_id","version","purpose","cutoff","max_age_days","source_policy_id","population_policy_id","system_id","source_schema_id","source_schema_version","entitlement_namespace_id","entitlement_namespace_version","observed_access_semantics","account_type_policy_id","access_rule_policy_id","authorization_policy_id","exception_policy_id","activity_policy_id","activity_threshold_days","activity_eligible_account_types","control_context_id","privacy_policy_id","workforce_policy_id","owner_role","reviewer_role","approver_role","correction_path","prohibited_uses"}
    row=strict(raw,fields,"policy")
    for key in fields-{"max_age_days","activity_threshold_days","activity_eligible_account_types","prohibited_uses"}: row[key]=text(row[key],f"policy.{key}")
    for key in ("max_age_days","activity_threshold_days"):
        if not isinstance(row[key],int) or isinstance(row[key],bool) or row[key]<0: raise ValueError(f"policy.{key} must be a non-negative integer")
    if row["observed_access_semantics"]!="OBSERVED_ASSIGNMENTS_ONLY": raise ValueError("unsupported observed_access_semantics")
    for key in ("activity_eligible_account_types","prohibited_uses"):
        if not isinstance(row[key],list): raise ValueError(f"policy.{key} must be a list")
        row[key]=sorted({text(item,key) for item in row[key]})
    when(row["cutoff"],"policy.cutoff")
    return row

def evidence_registry(rows,policy):
    fields={"evidence_id","system_id","source_id","source_version","schema_id","schema_version","as_of","extracted_at","access_scope","policy_id"}; registry={}; states={}; cutoff=when(policy["cutoff"],"cutoff")
    for raw in rows:
        row=strict(raw,fields,"evidence")
        for key in fields: row[key]=text(row[key],f"evidence.{key}")
        if row["evidence_id"] in registry: raise ValueError("duplicate evidence_id")
        as_of=when(row["as_of"],"evidence.as_of"); extracted=when(row["extracted_at"],"evidence.extracted_at")
        if extracted<as_of: raise ValueError("evidence extraction precedes as_of")
        state="AVAILABLE"
        if as_of>cutoff or extracted>cutoff: state="CONFLICTING"
        elif (cutoff-as_of).total_seconds()>policy["max_age_days"]*86400: state="STALE"
        elif row["system_id"]!=policy["system_id"] or row["policy_id"]!=policy["source_policy_id"] or row["schema_id"]!=policy["source_schema_id"] or row["schema_version"]!=policy["source_schema_version"]: state="POLICY_REQUIRED"
        registry[row["evidence_id"]]=row; states[row["evidence_id"]]=state
    return registry,states

def review_access(*,review_id,policy,evidence_rows,population_receipt,rule_rows,account_rows,exception_rows=None,approval_state="APPROVAL_REQUIRED"):
    reject_sensitive({"policy":policy,"evidence":evidence_rows,"population":population_receipt,"rules":rule_rows,"accounts":account_rows,"exceptions":exception_rows or []})
    review_id=text(review_id,"review_id"); policy=validate_policy(policy)
    if approval_state not in {"APPROVAL_REQUIRED","REVIEWED_NOT_APPROVED","APPROVED_FOR_REVIEW_ONLY"}: raise ValueError("invalid approval_state")
    evidence,states=evidence_registry(evidence_rows,policy); cutoff=when(policy["cutoff"],"cutoff")
    pfields={"receipt_id","policy_id","system_id","declared_account_count","declared_assignment_count","declared_entitlement_occurrence_count","evidence_id"}; population=strict(population_receipt,pfields,"population_receipt")
    for key in ("receipt_id","policy_id","system_id","evidence_id"): population[key]=text(population[key],f"population.{key}")
    for key in ("declared_account_count","declared_assignment_count","declared_entitlement_occurrence_count"):
        if not isinstance(population[key],int) or isinstance(population[key],bool) or population[key]<0: raise ValueError(f"population.{key} must be a non-negative integer")
    if population["policy_id"]!=policy["population_policy_id"] or population["system_id"]!=policy["system_id"]: raise ValueError("population policy or system mismatch")
    if states.get(population["evidence_id"])!="AVAILABLE": raise ValueError("population evidence unavailable")
    rfields={"rule_id","policy_id","entitlement_namespace_id","entitlement_namespace_version","account_type","required_entitlement_ids","allowed_entitlement_ids","prohibited_entitlement_ids","evidence_id"}; rules={}
    for raw in rule_rows:
        row=strict(raw,rfields,"rule"); rid=text(row["rule_id"],"rule_id")
        if rid in rules: raise ValueError("duplicate rule_id")
        for key in ("policy_id","entitlement_namespace_id","entitlement_namespace_version","account_type","evidence_id"): row[key]=text(row[key],key)
        if row["policy_id"]!=policy["access_rule_policy_id"] or row["entitlement_namespace_id"]!=policy["entitlement_namespace_id"] or row["entitlement_namespace_version"]!=policy["entitlement_namespace_version"]: raise ValueError("access rule policy or namespace mismatch")
        if states.get(row["evidence_id"])!="AVAILABLE": raise ValueError("rule evidence unavailable")
        for key in ("required_entitlement_ids","allowed_entitlement_ids","prohibited_entitlement_ids"):
            if not isinstance(row[key],list): raise ValueError(f"rule.{key} must be a list")
            cleaned=[text(item,key) for item in row[key]]
            if len(cleaned)!=len(set(cleaned)): raise ValueError(f"duplicate entitlement in rule.{key}")
            row[key]=sorted(cleaned)
        if not set(row["required_entitlement_ids"])<=set(row["allowed_entitlement_ids"]): raise ValueError("required entitlements must be allowed")
        if set(row["allowed_entitlement_ids"])&set(row["prohibited_entitlement_ids"]): raise ValueError("allowed and prohibited entitlements overlap")
        row["rule_id"]=rid; rules[rid]=row
    efields={"account_id","entitlement_id","state","policy_id","entitlement_namespace_id","entitlement_namespace_version","begin_at","expires_at","approval_receipt_id","evidence_id"}; exceptions=[]; exception_keys=set()
    for raw in exception_rows or []:
        row=strict(raw,efields,"exception")
        for key in ("account_id","entitlement_id","state","policy_id","entitlement_namespace_id","entitlement_namespace_version","approval_receipt_id","evidence_id"): row[key]=text(row[key],f"exception.{key}")
        if row["policy_id"]!=policy["exception_policy_id"] or row["entitlement_namespace_id"]!=policy["entitlement_namespace_id"] or row["entitlement_namespace_version"]!=policy["entitlement_namespace_version"]: raise ValueError("exception policy or namespace mismatch")
        exception_key=(row["account_id"],row["entitlement_id"])
        if exception_key in exception_keys: raise ValueError("duplicate account entitlement exception")
        exception_keys.add(exception_key)
        if row["state"] not in {"APPROVED","REVOKED"}: raise ValueError("invalid exception state")
        begin=when(row["begin_at"],"exception.begin_at"); expires=when(row["expires_at"],"exception.expires_at")
        if expires<=begin: raise ValueError("exception expiry must follow begin")
        evidence_state=states.get(row["evidence_id"],"SOURCE_REQUIRED")
        if evidence_state!="AVAILABLE": row["exception_result_state"]=evidence_state
        elif row["state"]=="REVOKED": row["exception_result_state"]="REVOKED"
        elif begin<=cutoff<expires: row["exception_result_state"]="ACTIVE"
        elif cutoff>=expires: row["exception_result_state"]="EXPIRED"
        else: row["exception_result_state"]="NOT_YET_ACTIVE"
        exceptions.append(row)
    afields={"account_id","subject_id","identity_state","account_type","account_type_policy_id","rule_id","entitlement_namespace_id","entitlement_namespace_version","platform_state","authorization_state","authorization_policy_id","observed_entitlement_ids","assignment_count","activity_state","activity_policy_id","last_activity_at","evidence_id","identity_evidence_id","authorization_evidence_id","activity_evidence_id"}; accounts=[]; seen=set(); queue=[]
    for raw in account_rows:
        row=strict(raw,afields,"account")
        for key in ("account_id","subject_id","identity_state","account_type","account_type_policy_id","rule_id","entitlement_namespace_id","entitlement_namespace_version","platform_state","authorization_state","authorization_policy_id","activity_state","activity_policy_id","evidence_id","identity_evidence_id","authorization_evidence_id","activity_evidence_id"): row[key]=text(row[key],f"account.{key}")
        if row["account_id"] in seen: raise ValueError("duplicate account_id")
        seen.add(row["account_id"])
        if row["identity_state"] not in {"VERIFIED","UNAVAILABLE","CONFLICTING"} or row["platform_state"] not in {"ACTIVE","DISABLED","UNKNOWN"} or row["authorization_state"] not in {"AUTHORIZED","REVOKED","PENDING","UNKNOWN"} or row["activity_state"] not in {"AVAILABLE","UNAVAILABLE","CONFLICTING"}: raise ValueError("invalid account state")
        if row["account_type_policy_id"]!=policy["account_type_policy_id"] or row["authorization_policy_id"]!=policy["authorization_policy_id"] or row["activity_policy_id"]!=policy["activity_policy_id"]: raise ValueError("account lane policy mismatch")
        if row["entitlement_namespace_id"]!=policy["entitlement_namespace_id"] or row["entitlement_namespace_version"]!=policy["entitlement_namespace_version"]: raise ValueError("entitlement namespace mismatch")
        if not isinstance(row["observed_entitlement_ids"],list): raise ValueError("observed_entitlement_ids must be a list")
        cleaned=[text(item,"entitlement_id") for item in row["observed_entitlement_ids"]]
        if len(cleaned)!=len(set(cleaned)): raise ValueError("duplicate observed entitlement_id")
        row["observed_entitlement_ids"]=sorted(cleaned)
        if not isinstance(row["assignment_count"],int) or isinstance(row["assignment_count"],bool) or row["assignment_count"]<0: raise ValueError("assignment_count must be non-negative")
        rule=rules.get(row["rule_id"]); source_state=states.get(row["evidence_id"],"SOURCE_REQUIRED"); identity_evidence_state=states.get(row["identity_evidence_id"],"SOURCE_REQUIRED"); auth_state=states.get(row["authorization_evidence_id"],"SOURCE_REQUIRED"); activity_evidence_state=states.get(row["activity_evidence_id"],"SOURCE_REQUIRED")
        active_exception_ids={item["entitlement_id"] for item in exceptions if item["account_id"]==row["account_id"] and item["exception_result_state"]=="ACTIVE"}
        if not rule or rule["account_type"]!=row["account_type"]: entitlement={"state":"POLICY_REQUIRED","required_missing":[],"prohibited_observed":[],"outside_allowed":[],"active_exception_entitlements":sorted(active_exception_ids)}
        elif source_state!="AVAILABLE": entitlement={"state":source_state,"required_missing":[],"prohibited_observed":[],"outside_allowed":[],"active_exception_entitlements":sorted(active_exception_ids)}
        else:
            observed=set(row["observed_entitlement_ids"]); required=set(rule["required_entitlement_ids"]); allowed=set(rule["allowed_entitlement_ids"]); prohibited=set(rule["prohibited_entitlement_ids"])
            missing=required-observed; prohibited_seen=(observed&prohibited)-active_exception_ids; outside=(observed-allowed)-active_exception_ids
            entitlement={"state":("MATCHED_WITH_ACTIVE_EXCEPTION" if active_exception_ids else "MATCHED") if not (missing or prohibited_seen or outside) else "DIFFERENCE_FOUND","required_missing":sorted(missing),"prohibited_observed":sorted(prohibited_seen),"outside_allowed":sorted(outside),"active_exception_entitlements":sorted(active_exception_ids)}
        identity_result=identity_evidence_state if identity_evidence_state!="AVAILABLE" else row["identity_state"]
        authorization_result=auth_state if auth_state!="AVAILABLE" else ("AUTHORIZATION_UNRESOLVED" if row["authorization_state"] in {"PENDING","UNKNOWN"} or row["platform_state"]=="UNKNOWN" else ("STATE_CONFLICT" if (row["authorization_state"]=="REVOKED" and row["platform_state"]=="ACTIVE") or (row["authorization_state"]=="AUTHORIZED" and row["platform_state"]=="DISABLED") else "NO_CONFLICT_OBSERVED"))
        activity_result="NOT_APPLICABLE"; elapsed_days=None
        if row["account_type"] in policy["activity_eligible_account_types"]:
            if activity_evidence_state!="AVAILABLE": activity_result=activity_evidence_state
            elif row["activity_state"]!="AVAILABLE" or row["last_activity_at"] is None: activity_result="SOURCE_REQUIRED" if row["activity_state"]=="UNAVAILABLE" else "CONFLICTING"
            else:
                activity_at=when(row["last_activity_at"],"last_activity_at")
                if activity_at>cutoff: activity_result="CONFLICTING"
                else: elapsed_days=(cutoff-activity_at).days; activity_result="THRESHOLD_EXCEEDED" if elapsed_days>policy["activity_threshold_days"] else "WITHIN_THRESHOLD"
        if row["activity_state"]!="AVAILABLE" and row["last_activity_at"] is not None: raise ValueError("non-available activity cannot contain last_activity_at")
        accounts.append({"account_id":row["account_id"],"subject_id":row["subject_id"],"identity_result_state":identity_result,"account_type":row["account_type"],"rule_id":row["rule_id"],"platform_state":row["platform_state"],"authorization_state":row["authorization_state"],"observed_entitlement_ids":row["observed_entitlement_ids"],"observed_entitlement_count":len(row["observed_entitlement_ids"]),"assignment_count":row["assignment_count"],"evidence_ids":{"account":row["evidence_id"],"identity":row["identity_evidence_id"],"authorization":row["authorization_evidence_id"],"activity":row["activity_evidence_id"]},"entitlement_result":entitlement,"authorization_result_state":authorization_result,"activity_result_state":activity_result,"activity_elapsed_days":elapsed_days})
    actual=(len(account_rows),sum(row["assignment_count"] for row in account_rows),sum(len(set(row["observed_entitlement_ids"])) for row in account_rows)); declared=(population["declared_account_count"],population["declared_assignment_count"],population["declared_entitlement_occurrence_count"])
    population_state="RECONCILED" if actual==declared else "POPULATION_INCOMPLETE"
    account_ids={row["account_id"] for row in account_rows}
    observed_by_account={row["account_id"]:set(row["observed_entitlement_ids"]) for row in account_rows}
    for item in exceptions:
        if item["account_id"] not in account_ids: raise ValueError("exception references unknown account")
        if item["entitlement_id"] not in observed_by_account[item["account_id"]]: raise ValueError("exception entitlement is not observed on account")
    if population_state!="RECONCILED":
        for account in accounts:
            account["entitlement_result"]={"state":"POPULATION_INCOMPLETE","required_missing":[],"prohibited_observed":[],"outside_allowed":[],"active_exception_entitlements":[]}
    for account in accounts:
        for lane,state,accepted in (
            ("IDENTITY",account["identity_result_state"],{"VERIFIED"}),
            ("ENTITLEMENT",account["entitlement_result"]["state"],{"MATCHED","MATCHED_WITH_ACTIVE_EXCEPTION"}),
            ("AUTHORIZATION",account["authorization_result_state"],{"NO_CONFLICT_OBSERVED"}),
            ("ACTIVITY",account["activity_result_state"],{"WITHIN_THRESHOLD","NOT_APPLICABLE"}),
        ):
            if state not in accepted: queue.append({"account_id":account["account_id"],"lane":lane,"state":state})
    for item in exceptions:
        if item["exception_result_state"]!="ACTIVE": queue.append({"account_id":item["account_id"],"lane":"EXCEPTION","state":item["exception_result_state"],"entitlement_id":item["entitlement_id"]})
    source_coverage_state="AVAILABLE" if all(states.get(row["evidence_id"])=="AVAILABLE" for row in account_rows) else "SOURCE_REQUIRED"
    return {"review_id":review_id,"policy":policy,"evidence":[evidence[key] for key in sorted(evidence)],"population_reconciliation":{"receipt_id":population["receipt_id"],"policy_id":population["policy_id"],"system_id":population["system_id"],"evidence_id":population["evidence_id"],"state":population_state,"account_source_coverage_state":source_coverage_state,"declared":{"account_count":declared[0],"assignment_count":declared[1],"entitlement_occurrence_count":declared[2]},"observed":{"account_count":actual[0],"assignment_count":actual[1],"entitlement_occurrence_count":actual[2]}},"access_rules":[rules[key] for key in sorted(rules)],"comparison_interpretation":"OBSERVED_ENTITLEMENT_COMPARISON","account_results":sorted(accounts,key=lambda item:item["account_id"]),"exception_receipts":sorted(exceptions,key=lambda item:(item["account_id"],item["entitlement_id"])),"exception_queue":sorted(queue,key=lambda item:(item["account_id"],item["lane"],item["state"],item.get("entitlement_id",""))),"control_context_interpretation":"REVIEW_EVIDENCE_NOT_CERTIFICATION_OR_COMPLIANCE_VERDICT","approval_state":approval_state,"ranked":False,"compliance_verdict_authorized":False,"risk_score_authorized":False,"savings_score_authorized":False,"access_action_authorized":False,"workforce_action_authorized":False,"boundary":BOUNDARY}

def render_review_output(review):
    if not isinstance(review,dict): raise ValueError("review must be an object")
    return "```json\n"+json.dumps(review,indent=2,sort_keys=True)+"\n```\n\n"+BOUNDARY

def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv; document=json.loads(Path(argv[0]).read_text() if argv else sys.stdin.read()); print(render_review_output(review_access(**document)))

if __name__=="__main__": main()
