---
name: revops-data-account-hierarchy
description: "Maps subsidiary companies, divisions, and regional offices to their parent accounts, creating a unified tree structure of corporate family relationships. Detects parent-child links using D-U-N-S matching, email domain analysis, fuzzy company name matching, and manual overrides. Constructs clean hierarchies, detects circular references, flags orphaned accounts, and enables consolidated revenue reporting for account families. Trigger on: build account hierarchy, map parent child accounts, organize account structure, fix account relationships, identify subsidiaries, account hierarchy, parent company mapping, create account family structure."
metadata:
  category: "Data Quality & Hygiene"
  phase: "Phase 1"
  data_readiness: "day_1"
  version: "1.0"
  author: "RevOps Agent Factory"
  last_updated: "2026-04-12"
  dependencies:
    agents:
      - "revops-data-deduplication (hard dependency: run first)"
      - "revops-data-field-normalization (soft dependency: improves accuracy of name matching; not required)"
    mcps:
      - "Salesforce MCP (for Salesforce orgs)"
      - "HubSpot MCP (for HubSpot orgs)"
    minimum_data:
      - "Account object with Id, Name, Website fields"
      - "ParentAccountId field (Salesforce) or Parent Company field (HubSpot)"
      - "Contact records with email addresses (recommended, for email domain matching)"
---

# DQH-06 Account Hierarchy Engine

## Why This Agent Exists

**Source: Research Brief DQH-06_account_hierarchy_research_v2.5.md, Section 2b**

**Who it's for (ICP):** Revenue Operations Manager at B2B SaaS, 100–500 employees, North America

**The painkiller pain points we're solving:**

### Pain Point 1: Fragmented Account Revenue View
- **Problem:** Revenue is split across 50+ subsidiary records without a common grouping field, making it impossible to report total revenue for a single customer family.
- **Quantified cost to the role:** $15,600–$23,400 per year in labor cost (4–6 hours/week at $75/hr) spent on manual consolidation of parent account revenue.
- **What teams do today:** Native Salesforce reports and manual spreadsheet consolidation. 80% of RevOps teams have inaccurately linked parent-child data, requiring ongoing manual fixes.
- **Why it's urgent:** 20% of companies undergo M&A, rebranding, or restructuring annually. Without automation, hierarchies decay. Over 12 months, a single lost upsell opportunity per quarter ($50k–$200k) compounds the cost of inaction.

### Pain Point 2: Territory & Segmentation Misalignment
- **Problem:** A subsidiary is assigned to a junior rep when its parent company is a Fortune 500 giant, leading to rep under-resourcing and lost expansion opportunities.
- **Quantified cost to the role:** $100k–$200k per mis-segmented account in lost revenue (1–2 lost upsells per year). At 50–100 such accounts, this is $5M–$20M in annual revenue leakage.
- **What teams do today:** Manual quarterly audit of segmentation rules (20–40 hours/quarter) and custom Salesforce formula fields to try to override automatic segmentation.
- **Why it's urgent:** Territory misalignment is compounding: rep turnover and quota misses perpetuate misconfiguration. At 12–24 months, enterprises churn or downgrade due to contact gaps and inconsistent service.

### Pain Point 3: Cross-Sell and Upsell Whitespace Blindness
- **Problem:** RevOps cannot identify which customer families have product gaps or expansion potential because they cannot see the full family tree. A $50M global customer is treated as a $100k prospect.
- **Quantified cost to the role:** $2.5M–$5M in lost new ARR per year (5–10% of cross-sell volume missed). Companies implementing ABM see 200% increase in marketing-generated revenue when account structure is accurate.
- **What teams do today:** Third-party data enrichment tools ($10k–$50k/year) and manual account research.
- **Why it's urgent:** As customer bases grow, whitespace blindness compounds. After 24 months, competitors win expansion deals in accounts where the customer didn't know they needed the solution.

---

## What This Agent Does

The Account Hierarchy Engine is your account structure detective. It scans your account database to find parent-child relationships using six signals: D-U-N-S matching (highest confidence), email domain analysis (subsidiary employees use parent's email), fuzzy company name matching (Jaro-Winkler for "GE" vs "General Electric"), website domain matching, subsidiary pattern recognition, and manual overrides. For each candidate pair, it calculates a confidence score (0–100), detects and flags circular references and orphaned accounts, constructs clean multi-level hierarchies, and generates a detailed report showing which accounts will be linked, why, and what risks exist. You get a unified account family tree that enables consolidated revenue reporting, accurate territory assignment, and cross-sell visibility—all without expensive third-party data enrichment.

---

## Getting Started (Preflight Check)

When you trigger this agent, the first thing I'll do is verify your CRM connection, confirm required data exists, assess data quality, and ask you to scope the run.

**Step 1: MCP Connection Verification**
- I'll check if Salesforce MCP or HubSpot MCP is connected and authenticated.
- **If connection fails:** I'll offer workarounds: export accounts to CSV for analysis, or help you reconnect the MCP.
- **If successful:** Proceed to Step 2.

**Step 2: Required Data Validation**
I'll verify that your Account object has these minimum fields:
- Id, Name, Website, ParentAccountId (or Parent Company field)
- BillingCountry, Industry, NumberOfEmployees (recommended)

**Go/No-Go decision:**
- ✓ All required fields present → Proceed
- ⚠️ Website or ParentAccountId missing → Partial results possible; I'll flag limitations and proceed with available data
- ✗ Account object missing entirely → No-go; cannot proceed without accounts

**Step 3: Data Quality Assessment**
I'll calculate:
- % of accounts with valid website (should be >50% for domain matching)
- % of accounts with D-U-N-S number (optional but helpful; improves accuracy)
- Whether ParentAccountId field is populated (if existing, I'll preserve relationships)
- Current estimated parent-child coverage (sample ~500 accounts; extrapolate to full set)

**Step 4: Contact Data (Optional but Recommended)**
I'll check if Contact records are available with email addresses, as email domain matching significantly improves parent identification accuracy.

**Step 5: Define Your Hierarchy Scope**
Before running the analysis, I'll ask:
- "Do you want to map ALL accounts, or start with a pilot (e.g., top 500 by revenue, specific industries, specific regions)?"
- "Do you want analysis-only (I show you recommendations, you approve), or should I execute linkages immediately for high-confidence pairs (≥95%)?"
- "Any accounts or business units to exclude (e.g., do not touch specific divisions, avoid certain parent assumptions)?"

**Preflight Report**
I'll summarize:
```
✓ Salesforce MCP connected (Org: EXAMPLE_ORG_ID)
✓ Account object ready with required fields
✓ Website data quality: 78% of accounts have valid domain
✓ D-U-N-S coverage: 42% of accounts (optional, recommend ZoomInfo integration)
✓ Contact records available (68% of accounts have ≥1 contact with email)
✓ ParentAccountId field: Partially populated (15% of accounts already linked)
✓ Estimated parent accounts (roots): ~180 out of 5,000 accounts
✓ Ready to proceed

Scope: Analyze all 5,000 accounts | Analysis + Approval mode | No exclusions

Next step: Fetching account records and building candidate parent-child pairs...
```

---

## Step-by-Step Workflow

### Phase 1: Fetch & Prepare Data

I'll query your Account and Contact objects in batches, normalize company names, extract email domains, and build lookup tables for fast matching.

**What I fetch:**
- Account: Id, Name, Website, Industry, BillingCountry, NumberOfEmployees, D-U-N-S__c (if exists), ParentAccountId, CreatedDate, LastModifiedDate, AnnualRevenue (if available)
- Contact: Email, AccountId (to extract email domains)

**Data normalization:**
- Company names: trim whitespace, lowercase, remove legal suffixes ("Inc.", "Corp.", "Ltd.", "GmbH")
- Domains: extract from website URL (e.g., "ge.com" from "https://www.ge.com")
- Phone normalization: convert to standardized format for matching

**Build lookup tables:**
- By normalized name (for prefix/fuzzy matching)
- By domain (for domain-based matching)
- By D-U-N-S (for authoritative matching)

### Phase 2: Generate Candidate Parent-Child Pairs (Six Signals)

I'll use six matching signals to find parent-child relationships:

**Signal 1: D-U-N-S Number Matching (40% weight, 98% confidence)**
- If Child's D-U-N-S matches Parent D-U-N-S in hierarchy data → Highest confidence match
- Availability: Only ~40–50% of accounts track D-U-N-S; strong signal where available

**Signal 2: Email Domain Matching (30% weight, 90% confidence)**
- If ≥20% of Child account's contacts use Parent's email domain → Strong match
- Example: "GE Aviation" employees using @ge.com emails → GE is parent

**Signal 3: Company Name Matching (20% weight, 75–95% confidence)**
- Prefix match: Parent name is substring of Child name (e.g., "GE" in "GE Power") → 95% confidence
- Fuzzy match: Jaro-Winkler similarity ≥0.85 (e.g., "GE Corp" vs "GE Corporation") → 85% confidence

**Signal 4: Website Domain Match (15% weight, 85–88% confidence)**
- Exact domain match: Parent and Child share same domain → 88% confidence
- Subdomain match: Child on parent's domain structure → 85% confidence

**Signal 5: Subsidiary Pattern Recognition (10% weight, 78–80% confidence)**
- If Child name contains patterns like "[Parent] Inc.", "[Parent] Division", "[Parent] EMEA" → match detected

**Signal 6: Manual Mapping Override (100% weight, 100% confidence)**
- If you provide explicit parent-child pairs → highest precedence, override all algorithmic signals

### Phase 3: Score & Filter Candidates

For each candidate pair, I calculate confidence using weighted formula:

```
Confidence = (
  email_signal × 0.30 +
  duns_signal × 0.40 +
  name_signal × 0.20 +
  domain_signal × 0.15 -
  false_positive_adjustments
) × 100
```

**Confidence tiers:**
- ≥95% → Auto-link (pending your approval)
- 85–94% → Review recommended
- 70–84% → Manual review required
- <70% → Discard; too risky

### Phase 4: Detect Circular References

I'll trace ancestry chains for each proposed linkage. If Child → Parent → Grandparent → ... → loops back to Child, I'll flag as CIRCULAR and stop before linking.

**Detection method:** Depth-first search on parent chain; reject any cycle or chain >10 levels deep.

### Phase 5: Build Hierarchy Tree

For each root account (account with no parent), I'll construct a multi-level tree showing all descendants. Example:

```
General Electric (Root)
├─ GE Power (Level 1)
│  ├─ GE Power Systems (Level 2)
│  └─ GE Power Renewables (Level 2)
├─ GE Aviation (Level 1)
└─ GE Digital (Level 1)
```

### Phase 6: Flag Orphaned Accounts

I'll identify accounts that should have a parent but don't:
- Account name contains subsidiary indicators ("Inc.", "Division") but ParentAccountId is NULL
- ParentAccountId points to non-existent account
- Contact email domain suggests belonging to another parent
- Account is very small (likely subsidiary) with no parent

### Phase 7: Generate Report & Output

I'll create:
- **Markdown report** with summary, hierarchy examples, flags, recommended actions
- **JSON hierarchy tree** with all parent-child relationships and confidence scores
- **JSON transaction log** with proposed changes and approval requirements
- **Orphan remediation checklist** for manual follow-up

---

## Configuration Options

Before I start, you can customize:

**Matching Thresholds:**
- "What confidence level triggers auto-approval?" (Default: 85%)
  - Conservative: 90% (fewer false positives, more manual review)
  - Balanced: 85% (recommended)
  - Aggressive: 75% (catches more, needs more manual review)

**Signal Weights:**
- "Should I prioritize email domain, D-U-N-S, or name equally?" (Default: 30% email, 40% D-U-N-S, 20% name, 15% domain)

**Hierarchy Rules:**
- "Maximum hierarchy depth?" (Default: 10 levels)
- "Which accounts to exclude?" (e.g., do not touch specific divisions)
- Manual parent mappings (override algorithmic scores)

**Orphan Handling:**
- "How should I classify orphaned accounts?" (Review, Research, or Accept as root)

---

## Error Handling

**If MCP connection fails:**
- Offer to work with CSV export instead
- Provide MCP reconnection troubleshooting steps

**If required data is missing:**
- Continue with available data; flag limitations in report
- Example: No email data → domain matching skipped (confidence drops to ~70%)

**If data quality is too low:**
- >50% missing website/email → Proceed with caution; flag high false-positive risk
- <30% coverage of any signal → Degrade that signal's weight in scoring

**If circular references detected:**
- Stop; do not link. Flag all involved accounts for manual review.
- Suggest: "Manually verify parent linkages in these 3 accounts and resolve cycle."

---

## What to Run Next

After hierarchy mapping is complete:

1. **Downstream: Lead-to-Account Matching Agent** — Links leads to parent accounts, not just subsidiaries; increases assignment accuracy.

2. **Downstream: Multi-Threading Agent** — Uses hierarchy to identify all divisions and regional offices; enables multi-stakeholder contact strategies.

3. **Downstream: Account Expansion Intelligence Agent** — Uses hierarchy to calculate family-level revenue, penetration, and whitespace opportunities.

4. **Monitor & Refresh:** Schedule quarterly hierarchy refresh to catch M&A, rebranding, and restructuring changes.

---

## Example: End-to-End Hierarchy Session

**You:** "Map parent-child relationships for our 5,000 accounts. I want to see high-confidence matches but review medium-confidence ones before we apply them."

**Me (Preflight):**
```
✓ Salesforce MCP connected
✓ 5,000 accounts loaded (78% have website, 42% have D-U-N-S)
✓ 8,500 contacts with email domains
✓ Ready to analyze
```

**You:** "Go ahead. Start with all accounts, analysis mode."

**Me (Analysis):**
```
Scanning 5,000 accounts for parent-child relationships...
✓ D-U-N-S matches found: 234 pairs (98% confidence)
✓ Email domain matches: 189 pairs (90% confidence)
✓ Name prefix matches: 312 pairs (86% confidence)
✓ Fuzzy name matches: 98 pairs (81% confidence)
✓ Total candidate pairs: 847

Scoring and filtering...
✓ 621 pairs at ≥85% confidence (safe to link)
✓ 201 pairs at 70–84% confidence (review recommended)
✓ 25 pairs at <70% confidence (likely false positives)

Building hierarchies...
✓ 156 root accounts identified (top-level parents)
✓ Multi-level hierarchies created (avg depth: 2.3 levels, max: 4)
✓ Circular references detected: 3 (flagged for review)
✓ Orphaned accounts: 34 (flagged for remediation)
```

**Report (Markdown):**
```markdown
# Account Hierarchy Analysis Report
**Date:** 2026-04-12 | **Scope:** 5,000 accounts | **CRM:** Salesforce

## Summary
847 parent-child relationships identified across 156 family trees.
- ✓ 621 high-confidence pairs (≥85%) — safe to link
- ⚠️ 201 medium-confidence pairs (70–84%) — review recommended
- ✗ 25 low-confidence pairs (<70%) — likely false positives, discarded
- 🔄 3 circular references detected — flagged for manual resolution
- 🔍 34 orphaned accounts — no parent candidate found

## Top Hierarchies by Consolidated ARR
| Parent Account | Subsidiaries | Depth | Consolidated ARR |
|---------------|-------------|-------|-----------------|
| General Electric | 11 | 4 | $450,000 |
| Acme Corp | 7 | 3 | $320,000 |
| Globex Industries | 5 | 2 | $210,000 |

## Data Quality & Limitations
- Website coverage: 78% (22% of accounts lacked domain data for Signal 4)
- D-U-N-S coverage: 42% (Signal 1 only applied to 2,100 accounts)
- ParentAccountId pre-populated: 15% (750 existing linkages preserved)

## Recommended Actions
1. Resolve 3 circular references (see Circular Ref tab)
2. Research 16 high-value orphans (>$50K ARR with no parent)
3. Verify 5 ambiguous pairs (multiple candidate parents)
4. Deploy rollup fields for parent-level ARR, contact count, opportunity reporting
```

**Report (JSON hierarchy tree — excerpt):**
```json
{
  "parent": "General Electric (001ABC)",
  "confidence": 0.97,
  "children": [
    {
      "account": "GE Healthcare (001DEF)",
      "confidence": 0.98,
      "signals": ["duns_match", "email_domain", "name_prefix"],
      "children": [
        {"account": "GE Healthcare IT (001GHI)", "confidence": 0.91, "signals": ["email_domain", "name_prefix"]}
      ]
    },
    {"account": "GE Aviation (001JKL)", "confidence": 0.96, "signals": ["duns_match", "email_domain"]}
  ]
}
```

**You:** "This looks good. Approve the 621 high-confidence pairs. I want to manually review the 201 medium-confidence ones before we persist."

**Me:** "Showing 201 medium-confidence pairs for your review..."

[You review and approve subset; I execute approved linkages]

**Result:** "✓ 580 hierarchies successfully created. 5,000 accounts now linked to 156 family trees. Rollup fields enabled. Next: Run quarterly refresh to catch M&A changes."

---

## References & Further Reading

**Detailed Files** (in `references/` folder):
- `company_name_variants.md` — Common company name variations and how agent handles them
- `international_subsidiaries.md` — Guidance on mapping cross-border hierarchies
- `circular_reference_examples.md` — Real-world examples of loops and how to resolve them
- `orphan_remediation_guide.md` — Checklist for fixing accounts with missing parents

---

**Status:** Architecture Complete — Ready for Implementation  
**Last Reviewed:** April 12, 2026  
**Questions?** Flag ambiguities in project Slack #revops-agents
