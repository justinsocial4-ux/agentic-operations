---
name: revops-permission-audit
description: Automates discovery of user access anomalies (over-privileged users,
  inactive accounts, orphaned credentials, permission creep, role mismatches) in Salesforce
  or HubSpot. Generates SOC 2 Type II-compliant audit reports, cost recovery analysis,
  and remediation task lists on a monthly cadence. Replaces 15–20 hours of manual
  spreadsheet reconciliation per month.
metadata:
  trigger_phrases:
  - audit user permissions
  - find over-permissioned users
  - detect orphaned accounts
  - check permission compliance
  - review access anomalies
  - generate soc 2 evidence
  - flag inactive users
  - permission creep detection
  category: Tech Stack & Operations
  phase: 30_days
  data_readiness: day_1
  version: '1.0'
  author: RevOps Agent Factory
  last_updated: '2026-04-13'
  dependencies:
    agents: []
    mcps:
    - Salesforce MCP (for Salesforce orgs)
    - HubSpot MCP (for HubSpot orgs)
    minimum_data:
    - User object with Email, FirstName, LastName, IsActive fields
    - Profile or Role object with permission assignments
    - LoginHistory (Salesforce) or last_active_timestamp (HubSpot) data
    - Role-permission matrix (admin-supplied configuration)
  output_format: Markdown report + CSV + JSON + PDF evidence
---

# TSO-04 Permission Audit Agent

## Why This Agent Exists

**Who it's for (ICP):** IT Security Manager or RevOps Manager at B2B SaaS companies, 100–500 employees, North America, with Salesforce or HubSpot.

**The painkiller: 80% of breaches involve privileged credentials, and 85% of granted permissions go unused. Manual permission audits take 15–20 hours per month and fail SOC 2 Type II compliance reviews.**

### Scorecard

| Dimension | Score | Evidence | Data Quality |
|-----------|-------|----------|--------------|
| **Problem Severity** | 9/10 | 80% of breaches involve privileged credentials; $4.45M median breach cost (IBM) | TIER 1 |
| **Population Fit** | 8/10 | Target: RevOps / IT Security at mid-market SaaS; SOC 2 annual/bi-annual audits | TIER 1 |
| **Market Urgency** | 8/10 | Permission creep (Capital One, Morgan Stanley cases); SOC 2 Type II requires documented annual access reviews | TIER 1 |
| **Solution Maturity** | 7/10 | Competitors (Varonis, BetterCloud) expensive; native Salesforce tools have 180-day limit; day 1 feasible | TIER 1 |
| **Technical Feasibility** | 8/10 | Salesforce Tooling API, HubSpot User API available; no enrichment required | TIER 1 |

---

## What This Agent Does

The Permission Audit Agent is your access control detective. It scans your Salesforce or HubSpot user base monthly to discover six types of permission anomalies: over-privileged users (who have more access than their role requires), inactive accounts (who haven't logged in >60 days but still consume seats), orphaned credentials (former employees still marked active), role mismatches (assigned profile doesn't match actual job function), under-provisioned users (missing required permissions), and excessive admin access (non-admins with System Admin privilege). It ranks findings by severity (critical, high, medium, low), calculates cost recovery potential, and produces SOC 2 Type II-compliant audit evidence with remediation task lists. Unlike Salesforce's native 180-day audit tool, this agent creates multi-month trend analysis, automates orphaned account detection via HRIS matching, and generates compliance artifacts that satisfy annual access review requirements.

---

## Getting Started (Preflight Check)

When you trigger this agent, I verify your setup in three steps.

**Step 1: CRM Connection Verification**
- Checking if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If connection fails:** I'll offer a workaround (manual CSV import) or explain how to reconnect.
- **If successful:** Proceed to Step 2.

**Step 2: Required Data Validation**
I'll verify that your CRM has:
- User object with Email, FirstName, LastName, IsActive/inactive_at fields
- Profile (Salesforce) or Role (HubSpot) objects
- PermissionSet + PermissionSetAssignment data (Salesforce only)
- LoginHistory or last_active_timestamp (for inactivity detection)

**Go/No-Go decision:**
- ✓ All required fields present → Proceed
- ⚠️ 1–2 fields missing → Partial results possible; I'll flag limitations
- ✗ Core fields missing (Email, Profile/Role) → No-go; request data enrichment first

**Step 3: Role-Permission Matrix Confirmation**
Before analyzing, I need your documented role-permission matrix (a spreadsheet or JSON mapping job roles to expected permission sets). This defines what "normal" looks like for each role.

**Preflight Report**
I'll summarize:
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ User + Profile objects present with required fields
✓ LoginHistory available (90-day window)
✓ PermissionSet data found (243 sets, 1,840 assignments)
? Role-permission matrix: Not yet uploaded. (Upload or paste your role definitions.)

Ready to proceed. Awaiting role matrix...
```

---

## Step-by-Step Workflow

### Phase 1: Permission Data Extraction (Day 1)

**What I'll do:**
- Query all User records from your CRM (with Email, FirstName, LastName, IsActive)
- Fetch all Profile (Salesforce) or Role (HubSpot) objects
- Extract all PermissionSet + PermissionSetAssignment records
- Retrieve LoginHistory or last_active_timestamp for inactivity detection
- Cache results for 24 hours to avoid rate limiting

**Batch Strategy:** Fetch in 1,000-record increments.

**What you'll see:** Progress indicator ("Fetched 1,000 / 5,000 users...").

**Output:** User snapshot with all permission assignments cached.

---

### Phase 2: Effective Permissions Calculation

**What I'll do:**
- For each user, compute their **effective permissions** (union of profile + all assigned permission sets)
- Flatten "View All" and "Modify All" shortcuts into specific object/field permissions
- Build expected permissions lookup from your role-permission matrix
- Compare actual vs. expected for each user

**Calculation Logic:**
```
effective_permissions[user] = 
  profile_permissions[user.profile] 
  ∪ permission_set_1 ∪ permission_set_2 ∪ ... ∪ permission_set_N
```

**Example:**
- User "Alice" assigned to "Sales Rep" profile → {Read Account, Create Opportunity}
- Alice also assigned "Marketing Manager" permission set → adds {Read Campaign, Create Campaign}
- Alice's effective permissions → {Read Account, Create Opportunity, Read Campaign, Create Campaign}
- Expected for "Sales Rep" → {Read Account, Create Opportunity}
- **Discrepancy:** Alice has 2 excess permissions

---

### Phase 3: Anomaly Detection — Six Discrepancy Types

I analyze each user against their expected role and flag six types of anomalies:

**1. Over-Permissioned Users (Severity: HIGH)**
- Definition: User has permissions beyond their current role
- Example: Sales Rep with "System Administrator" profile; Finance user with Opportunity.Create
- Detection: effective_permissions[user] ⊃ expected_permissions[role]

**2. Inactive Users (Severity: MEDIUM–HIGH)**
- Definition: User has not logged in >60 days (configurable)
- Example: User last login 120 days ago; dormant account consuming seat
- Detection: last_login < (today - threshold_days)
- Cost impact: Seat cost × (days_inactive / 365)

**3. Orphaned Accounts (Severity: CRITICAL)**
- Definition: User marked active in CRM but inactive/terminated in HRIS
- Example: Former employee still has Salesforce login; contractor contract expired
- Detection: HRIS integration (if available) or manual employee list CSV match
- Impact: Security risk + immediate cost recovery

**4. Excessive Admin Access (Severity: CRITICAL)**
- Definition: Non-admin user has System Admin, API, or sensitive permissions
- Example: Junior sales rep has "System Administrator" profile
- Detection: user.role != "Admin" AND user.permissions includes "System Administrator"

**5. Role Mismatch (Severity: MEDIUM)**
- Definition: User's assigned role differs from role-permission matrix
- Example: User assigned "Sales User" profile but performs Customer Success function
- Detection: assigned_role != expected_role OR permission set inconsistency

**6. Under-Permissioned Users (Severity: LOW–MEDIUM)**
- Definition: User missing required permissions for their stated role
- Example: Sales Manager without "Modify All Opportunities"
- Detection: expected_permissions[role] ⊃ effective_permissions[user]

---

### SOC 2 Type II Control Mapping

Each discrepancy type detected by the Permission Audit Agent aligns to specific SOC 2 Trust Service Criteria under the Security category. The mapping below ensures that audit findings directly satisfy compliance requirements.

| Discrepancy Type | SOC 2 Control | Trust Service Criteria | Evidence Artifact |
|---|---|---|---|
| Over-Permissioned Users | CC6.1 — Logical Access Security | Security | Permission delta report showing excess permissions vs. role baseline |
| Inactive Accounts | CC6.2 — User Account Management | Security | Inactive user list with last_login_date exceeding threshold |
| Orphaned Accounts | CC6.3 — Account Deprovisioning | Security | Terminated employee list cross-referenced with active accounts |
| Excessive Admin Access | CC6.1 — Segregation of Duties | Security | Admin-role holders vs. business justification registry |
| Role Mismatch | CC6.1 — Role-Based Access Control | Security | Current role vs. HRIS/CRM role assignment comparison |
| Under-Permissioned Users | CC6.1 — Minimum Necessary Access | Security | Users with insufficient permissions for their documented role |

Each audit run generates a PDF evidence packet mapping findings to these control IDs. The packet includes: (1) timestamp and scope of audit, (2) discrepancy counts by control, (3) remediation status, and (4) attestation signature block for the compliance officer. This evidence is formatted for direct submission to external SOC 2 auditors.

---

### Phase 4: Confidence Scoring

For each discrepancy, I assign a confidence score (0–100) indicating how certain I am it's real, not a false positive.

| Scenario | Score | Rationale |
|----------|-------|-----------|
| User email matches HRIS as terminated + inactive in CRM | 95+ | High confidence orphaned account |
| Last login >90 days + HRIS shows active | 80–90 | Likely inactive; could be legitimate LOA |
| Role "Sales Rep" but has "Marketing Manager" permission set + 30-day overlap | 70–75 | Likely in transition |
| User has 5 permission sets, only 1 expected, but org-wide grant occurred | 60–70 | Could be bulk provision |
| Effective permissions slightly exceed median (top 10% of role) | 50–65 | Potential over-provision |

**Filtering:** Only report discrepancies with confidence > 60% (configurable).

---

### Phase 5: Report Generation

**Outputs (four formats):**

1. **Markdown Report** (`audit_report_YYYY_MM_DD.md`)
   - Executive summary with key metrics (% inactive, % over-privileged, cost recovery)
   - Compliance status (SOC 2 Type II: PASS / VIOLATIONS / MANUAL REVIEW)
   - Top 5 critical findings
   - Detailed discrepancy table (user, role, anomaly type, severity, excess permissions, remediation)
   - Trend analysis (month-over-month change)
   - Assumptions and limitations

2. **CSV Export** (`audit_discrepancies_YYYY_MM_DD.csv`)
   - One row per discrepancy
   - Columns: user_email, current_role, discrepancy_type, severity, excess_permissions, last_login_date, days_inactive, confidence_score, remediation_action, owner

3. **JSON Export** (`audit_results_YYYY_MM_DD.json`)
   - Structured data for integration with Jira, Asana, or custom workflows
   - Includes: audit_run_id, timestamp, discrepancy details, summary counts

4. **Compliance Evidence PDF** (`compliance_evidence_YYYY_MM_DD.pdf`)
   - 1-page executive summary
   - Discrepancy table (2–5 pages)
   - Audit attestation section (admin sign-off checkbox)
   - Audit metadata (who ran it, when, org ID, role matrix version)

---

### Phase 6: Remediation Task Generation

For each critical or high-severity discrepancy, I create actionable remediation tasks:

**Task example:**
```json
{
  "task_id": "AUDIT-001",
  "title": "Remove System Administrator permission from person@example.com",
  "description": "User person@example.com (Sales Rep) has System Administrator permission, exceeding their role. Remove this permission set immediately.",
  "severity": "critical",
  "owner": "IT Security Manager",
  "due_date": "2026-05-15",
  "remediation_steps": [
    "1. Log in to Salesforce as admin",
    "2. Navigate to Setup > Users > [person@example.com]",
    "3. Click 'Remove' next to 'System Administrator' permission set",
    "4. Confirm removal",
    "5. Verify in audit report next month"
  ]
}
```

Tasks can be imported to Jira, Asana, or managed manually.

---

## Configuration Options

Before I start analyzing, you can customize:

**Inactivity Threshold (Default: 60 days)**
- "How many days without login should trigger 'inactive' flag?"
  - Conservative: 90 days (only flag truly dormant accounts)
  - Balanced: 60 days (recommended for cost recovery + security)
  - Aggressive: 30 days (catch light users)

**Confidence Threshold (Default: 60%)**
- "What's your minimum confidence score?"
  - Strict: 80% (fewer false positives, miss some real issues)
  - Balanced: 60% (recommended)
  - Permissive: 40% (catch more, manual review needed)

**HRIS Integration (Default: None)**
- "Do you have Workday, SuccessFactors, or Bamboo HR connected?"
  - Yes → I'll use it to detect orphaned accounts (ex-employees)
  - No → I'll accept a manual CSV of active employees

**Output Scope (Default: All Users)**
- "Audit all users, or filter to specific accounts/departments?"

**Compliance Mode (Default: On)**
- "Generate SOC 2 evidence PDF?" (yes/no)

---

## Error Handling

**If CRM connection fails:**
- Offer CSV export / import workaround
- Provide MCP reconnection instructions
- Don't block on authentication—work with available data

**If role-permission matrix is incomplete:**
- Proceed with available role definitions
- Flag users whose roles aren't in the matrix as "unknown role" (lower confidence)
- Recommend completing the matrix for next run

**If data quality is too low (>80% missing email/login data):**
- Warn that inactivity detection will be unreliable
- Suggest data enrichment before running
- Offer to proceed with degraded confidence (60–70%)

**If API rate limits are hit:**
- Implement exponential backoff (2s, 4s, 8s)
- Batch smaller (500 records instead of 1,000)
- Split audit into multiple runs (by department/date range)

**Never crash silently.** Always explain what went wrong and what to do next.

---

## What to Run Next

After permission audit is complete:

1. **Remediation Execution** — Act on high/critical findings within 30 days. Track completion in Jira/Asana.

2. **Trend Monitoring** — Schedule monthly audits (same day each month) to track permission creep and remediation progress.

3. **TSO-02 Tool Adoption Agent** — Correlate low tool adoption with permission restrictions (users may avoid tools if they can't access required objects).

4. **SOC 2 Evidence Archive** — Store compliance PDF in secure archive for auditor review during SOC 2 Type II assessment.

---

## Example: End-to-End Session

**You:** "Audit my Salesforce user permissions and flag anything that looks risky."

**Me (Preflight):**
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ User + Profile objects ready
✓ PermissionSet data found (156 sets, 892 assignments)
✓ LoginHistory available (90-day window)
? Role-permission matrix: Not uploaded. (Paste your role definitions as JSON or CSV.)

Please provide your role-permission matrix. Example format:
[
  {
    "role_name": "Sales Representative",
    "expected_permission_sets": ["Read Account", "Create Opportunity", "Read Contact"],
    "forbidden_permissions": ["System Administrator", "Create Customize Reports"]
  }
]
```

**You:** "Here's our matrix..." (paste/upload)

**Me (Analysis):**
```
Extracting user data...
✓ Found 387 active users
✓ Fetched 156 permission sets
Calculating effective permissions...
✓ Completed for 387 users
Detecting anomalies...
✓ Found 34 discrepancies (18 over-permissioned, 8 inactive, 5 role mismatch, 3 orphaned)
Generating report...
✓ Complete
```

**Report Summary:**
```
## Permission Audit Report — April 15, 2026

**Total Users Audited:** 387  
**Critical Findings:** 3  
**High Priority:** 12  
**Estimated Cost Recovery:** $18,500/year  

### Key Metrics
| Metric | Count | % of User Base |
|--------|-------|----------------|
| Inactive Users (>60 days) | 22 | 5.7% |
| Over-Permissioned Users | 18 | 4.7% |
| Orphaned Accounts | 3 | 0.8% |
| Excessive Admin Access | 1 | 0.3% |

### Compliance Status
**SOC 2 Type II:** VIOLATIONS FOUND  
→ 3 users with excessive admin access must be remediated before audit

### Critical Findings
1. **Sarah Chen (person@example.com)** — Sales Rep with System Administrator permission. Remove immediately. [Confidence: 95%]
2. **person@example.com** — Inactive 145 days; still assigned "Sales User" profile. Deactivate account. [Confidence: 92%]
3. **Former contractor (person@example.com)** — Marked active in Salesforce, terminated in HRIS 3 months ago. Deactivate. [Confidence: 98%]
```

**You:** "Got it. Remove the critical ones and create Jira tickets for the rest."

**Me:** (Creates 12 Jira tickets, sends summary to Slack)
```
✓ Removed System Administrator from Sarah Chen
✓ Deactivated person@example.com account
✓ Deactivated person@example.com account
✓ Created 12 Jira tickets for medium/low findings
✓ Posted summary to #security Slack channel

Next audit scheduled: May 15, 2026
```

---

## References & Further Reading

**Spec & Research:**
- `TSO-04_permission_audit_spec.md` — Full technical specification
- `TSO-04_permission_audit_research.md` — Pain points, competitive landscape, population analysis

**External Standards:**
- SOC 2 Type II Trust Service Criteria (AICPA) — Access Control requirements
- NIST Cybersecurity Framework — Identity & Access Management controls
- Salesforce Tooling API Docs — User, Profile, PermissionSet objects
- HubSpot API Docs — User role and permission endpoints

**Related Agents:**
- DQH-01 Deduplication Engine — Clean duplicate contacts before analyzing permissions
- TSO-02 Tool Adoption Agent — Correlate low adoption with permission restrictions
- Future: Compliance & Governance agents will consume Permission Audit evidence

**Configuration Templates:**
- Role-permission matrix template (JSON + CSV formats available)
- HRIS field mapping guide (Workday, SuccessFactors, Bamboo HR)
- Slack integration setup (post summaries to #security channel)
