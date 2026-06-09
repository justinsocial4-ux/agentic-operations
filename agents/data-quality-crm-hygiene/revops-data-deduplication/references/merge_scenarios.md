# Real-World Merge Scenarios & Edge Cases

This document walks through tricky dedup scenarios you may encounter. Each scenario shows: the situation, what the Deduplication Engine will do, what the right decision is, and when to override the engine's recommendation.

---

## Scenario 1: Career Changer (Same Person, Different Company Over Time)

**Real-world situation:**
A prospect, Jane Doe, worked at Microsoft (2020–2024) and just joined Google (Jan 2025). Your CRM has both records because she re-signed up for a webinar at her new company.

**CRM Records:**
```
Contact A (ID: 0013000000ABC):
  Email: jane@example.com
  Phone: +1-415-555-0100
  Company: Microsoft
  Created: 2020-08-15
  LastActivity: 2024-11-20

Lead B (ID: 00Q3000000XYZ):
  Email: jane@example.org
  Phone: +1-415-555-0100
  Company: Google
  LeadSource: Webinar (Jan 2025)
  Created: 2025-01-10
  LastActivity: 2025-01-10
```

**Engine Analysis:**
- Email: Different domains (example.com vs. example.org) → **fuzzy match 0.70** (not caught)
- Phone: **Exact match** → **92% base confidence**
- Name: **Exact match** → **covered**
- Company: Different (Microsoft vs. Google) → **-20% penalty**
- Final: **(1.0 × 0.35) + (0.92 × 0.35) - 20% = ~68%** → **Rejected** (below 85%)

**What engine does:** Flags as **low confidence; manual review required**.

**Right decision:** **Do NOT merge**. Jane Doe at Microsoft and Jane Doe at Google are separate selling motions and prospects should not be conflated. Consider:
- Archive the old Microsoft contact (if engagement is stale)
- Keep the new Google lead as a fresh prospect
- Link them in a CRM note if relationship mapping is needed (e.g., "contact transferred to new company")

**Lesson:** Same person ≠ same prospect. Career changers should be tracked as separate contacts unless explicitly linked by your sales team.

---

## Scenario 2: Job Title Evolution (Same Contact, Same Company, Different Roles)

**Real-world situation:**
John Smith was a Sales Manager at Acme (2020–2024). He was promoted to Director of Sales in 2024. Your CRM has two records because the import script created a new record instead of updating.

**CRM Records:**
```
Contact A:
  Email: john@example.com
  Phone: +1-415-555-0100
  JobTitle: Sales Manager
  Created: 2020-08-15

Contact B:
  Email: john@example.com
  Phone: +1-415-555-0100
  JobTitle: Director of Sales
  Created: 2024-06-01
```

**Engine Analysis:**
- Email: **Exact match** → **95% base**
- Phone: **Exact match** → **92% base**
- Company: **Exact match** (Acme) → **+15% boost**
- Final: **~97% confidence** → **Safe to auto-merge ✓**

**What engine does:** **High-confidence pair; ready for auto-merge**.

**Right decision:** **Merge Contact A into Contact B**. Master should be Contact B (newer, more recent job title). All activities from A (calls, emails) get reassigned to B. Preserve JobTitle = "Director of Sales" (most current).

**Lesson:** Same email + phone + company = almost certainly same person. Engine gets this right.

---

## Scenario 3: Name Typo or Data Quality Issue

**Real-world situation:**
A contact was entered twice—once correctly (John Smith) and once with a typo (Jon Smith). Both have identical emails and phones, but the typo record has incomplete data.

**CRM Records:**
```
Contact A:
  Email: john@example.com
  Phone: +1-415-555-0100
  FirstName: John
  LastName: Smith
  Company: Acme
  MailingCity: San Francisco
  Industry: Technology
  Created: 2024-08-15

Contact B:
  Email: john@example.com
  Phone: +1-415-555-0100
  FirstName: Jon
  LastName: Smith
  Company: Acme
  MailingCity: [empty]
  Industry: [empty]
  Created: 2025-03-01
```

**Engine Analysis:**
- Email: **Exact match** → **95%**
- Phone: **Exact match** → **92%**
- Name: Jaro-Winkler(John Smith, Jon Smith) ≈ **0.93**
- Company: **Exact match** → **+15%**
- Final: **~97% confidence** → **Safe to auto-merge ✓**

**Master selection:**
- Contact A is older (created Aug 2024 vs. Mar 2025)
- Contact A is more complete (100% vs. 60% fields filled)
- **Master: Contact A**

**What engine does:** **Recommend auto-merge; Contact B deleted; data from A retained**.

**Right decision:** **Merge B → A** ✓. Contact A becomes master. Contact B's empty fields remain empty (no data loss). All activities from B reassigned to A.

**Lesson:** Exact email + phone matches are your highest-confidence duplicates; these are safe to auto-merge without manual review.

---

## Scenario 4: Shared Email (False Positive)

**Real-world situation:**
A company has a shared inbox for a department: "sales@example.com". Two different reps (Mike Johnson and Sarah Chen) both log into this email for receiving leads. Your CRM imported both as separate contacts with the shared email.

**CRM Records:**
```
Contact A:
  Email: sales@example.com
  Phone: +1-415-555-0200
  FirstName: Mike
  LastName: Johnson
  Title: Account Executive
  Created: 2024-01-15

Contact B:
  Email: sales@example.com
  Phone: +1-415-555-0300
  FirstName: Sarah
  LastName: Chen
  Title: Sales Development Rep
  Created: 2024-02-01
```

**Engine Analysis:**
- Email: **Exact match** (sales@example.com) → **95% base** ⚠️
- Phone: **Different** (+1-415-555-0200 vs. +1-415-555-0300) → **0 signal**
- Name: **Completely different** (Mike vs. Sarah, Johnson vs. Chen) → **0 signal**
- Company: Acme (inferred) → **match**
- Final: **(1.0 × 0.35) + (0.10) = 0.45 ≈ 45%** → **Rejected** (below 85%)

**Wait—what if the engine only caught the email match?**  
- Pure email match would give 95% confidence → **Would recommend auto-merge ✗** (false positive!)

**Engine safeguards:**
The engine implements a **false-positive detector**: if email matches but name + phone are completely different, confidence is **reduced by 50–60%**. This brings 95% down to 35–45% and flags for manual review.

**What engine does:** **Flags as low-confidence; recommendation: MANUAL REVIEW**.

**Right decision:** **Do NOT merge**. The shared email is a red flag. Sales ops should:
1. Ask Acme to provide individual email addresses (mike@example.com, sarah@example.com)
2. Split the shared inbox contact into two real contacts
3. Re-sync after clarification

**Lesson:** Shared business emails are a common pitfall. Engine has a safeguard (false-positive detector), but shared emails should ideally be resolved at the source (CRM enrichment/integration config).

---

## Scenario 5: Parent-Child Account (Do Not Merge)

**Real-world situation:**
A large company (Acme Corp) has a parent account and a subsidiary (Acme Analytics). Your sales team tracks them separately for billing and contract reasons. An import accidentally created "John Smith" records for both accounts.

**CRM Records:**
```
Contact A (Parent Account: Acme Corp):
  Email: john@parent.example.com
  Phone: +1-415-555-0100
  Company: Acme Corp
  Created: 2024-01-15

Contact B (Child Account: Acme Analytics):
  Email: john@analytics.example.com
  Phone: +1-415-555-0100
  Company: Acme Analytics
  Created: 2024-02-01
```

**Engine Analysis:**
- Email: Fuzzy match (parent.example.com vs. analytics.example.com) → **0.75** (not caught)
- Phone: **Exact match** → **92%**
- Name: **Exact match**
- Company: Fuzzy match (Acme Corp vs. Acme Analytics) → **0.78** (not caught; too dissimilar)
- Final: **(1.0 × 0.35) + (1.0 × 0.10) = 0.45 ≈ 45%** → **Rejected** (below 85%)

**What engine does:** **Flags as low-confidence; manual review required**.

**Right decision:** **Do NOT merge**. These are legitimately different business entities with different contracts and billing. Keep them separate.

**How to prevent:** Use the **scope filter** when running dedup:
```
"exclude_accounts": ["Acme Analytics"]  // Don't analyze subsidiaries
// OR
"cross_object_matching": false  // Don't match across account boundaries
```

**Lesson:** Parent-child hierarchies should be respected. Use scope filters to avoid accidental merges of intentionally separate accounts.

---

## Scenario 6: Duplicate with Conflicting Data (Data Loss)

**Real-world situation:**
Jane Doe has two records. Both are high-quality, but they have conflicting information (different job titles, different industries). After merging, which one wins?

**CRM Records:**
```
Contact A (Master selected: created first):
  Email: jane@example.net
  Phone: +1-415-555-0100
  FirstName: Jane
  LastName: Doe
  JobTitle: Senior Product Manager
  Industry: SaaS
  MailingCity: San Francisco
  Company: BigCorp
  Created: 2023-06-15

Contact B (Duplicate):
  Email: jane@example.net
  Phone: +1-415-555-0100
  FirstName: Jane
  LastName: Doe
  JobTitle: VP Product
  Industry: Enterprise Software
  MailingCity: Boston
  Company: BigCorp
  Created: 2025-03-01
```

**Conflict Resolution (Field-Level Merge Rules):**

| Field | Master (A) | Duplicate (B) | Decision | Reason |
|-------|-----------|--------------|----------|--------|
| JobTitle | Senior Product Manager | VP Product | Keep A | A is verified; B's newer title suggests promotion, but A was first/verified |
| Industry | SaaS | Enterprise Software | Keep A | Soft field; A is original |
| MailingCity | San Francisco | Boston | Keep A | Same company, so A's city is likely correct (assume not relocated) |

**Data Loss:** Job title and city from B are discarded. This is logged in the merge report.

**What engine does:** **Warns in report**: "Merge will discard Jane's VP Product title from Contact B. Review and confirm before approving."

**Right decision:** **Review before merge**. Options:
1. Merge as planned (accept data loss)
2. Manually update Contact A's JobTitle to "VP Product" before merge
3. Keep both records if they represent different time periods / positions

**Lesson:** When conflicts exist, the engine favors the master record but flags the loss. Sales ops should review and decide whether to accept, modify, or skip the merge.

---

## Scenario 7: International Name / Character Encoding

**Real-world situation:**
A contact from Spain (José) was entered twice—once with accent marks (José López) and once without (Jose Lopez). CRM encoding is inconsistent.

**CRM Records:**
```
Contact A:
  Email: person@example.com
  Phone: +34-91-555-0100
  FirstName: José
  LastName: López
  Company: Iberia Airlines
  Created: 2024-06-15

Contact B:
  Email: person@example.com
  Phone: +34-91-555-0100
  FirstName: Jose
  LastName: Lopez
  Company: Iberia Airlines
  Created: 2025-02-01
```

**Engine Analysis:**
- Email: **Exact match** → **95%**
- Phone: **Exact match** → **92%**
- Name: Jaro-Winkler(José López, Jose Lopez) ≈ **0.96** (accent marks normalized)
- Company: **Exact match** → **+15%**
- Final: **~97% confidence** → **Safe to auto-merge ✓**

**What engine does:** **Normalizes accents** before fuzzy-matching (removes José → Jose). Exact email + phone confirms. **Recommends auto-merge.**

**Right decision:** **Merge B → A** ✓. Master is A (older, original encoding). All activities from B reassigned to A.

**Lesson:** The engine normalizes international characters (accents, diacritics) before matching, so José and Jose are treated as equivalent. Email + phone confirmation makes this safe.

---

## Decision Checklist: When to Override the Engine

Use this checklist when deciding whether to accept, modify, or reject the engine's recommendation:

**Auto-approve the merge if:**
- [ ] Email match is exact (jane@example.net = jane@example.net)
- [ ] AND phone match is exact OR both belong to same company
- [ ] AND no obvious data conflicts (or conflicts are low-value fields)

**Require manual review if:**
- [ ] Email differs but phones match (jon.smith@acme vs. john.smith@acme + same phone)
- [ ] Name differs significantly (but email/phone same) (Robert vs. Bob)
- [ ] Company names differ (Acme Inc. vs. Acme Corp.) — even if email domains match
- [ ] Created dates differ by >1 year (likely career change; consider archiving instead)
- [ ] One record is stale (>6 months no activity) — consider archiving old record instead of merging

**Do NOT merge if:**
- [ ] Email/phone differ AND names differ → Different people
- [ ] Different companies + no email domain match → Different people
- [ ] Parent-child account structure → Keep separate for billing
- [ ] Shared email address + different names + different phones → Likely false positive (fix at source)
