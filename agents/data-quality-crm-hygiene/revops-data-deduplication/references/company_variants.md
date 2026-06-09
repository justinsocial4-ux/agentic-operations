# Company Name Variants & Dedup Matching

Company names are a strong secondary signal in deduplication. Two "John Smith"s at the **same company** are likely the same person; at **different companies**, they're different people.

This file documents common company variants and how the Deduplication Engine handles them.

---

## Common Company Name Patterns

### Legal Entity Suffixes

| Base Name | Variants | Notes |
|-----------|----------|-------|
| Acme | Acme Corp | Acme Corporation | Acme Inc. | Acme Ltd. | Legal entity suffix varies by jurisdiction; all refer to same company |
| Microsoft | Microsoft Corporation | Microsoft Corp | MS | Ticker symbol sometimes used |
| Apple | Apple Inc. | Apple Computer | Apple Inc. | Official name changed over time |

**Dedup behavior:** Jaro-Winkler matching catches "Acme" vs. "Acme Corp" (JW ≈ 0.92) → **flagged as company match**.

### Abbreviations & Acronyms

| Full Name | Abbreviations | Domain |
|-----------|---------------|----|
| International Business Machines | IBM | ibm.com |
| Amazon Web Services | AWS | aws.amazon.com |
| Salesforce | SFDC | salesforce.com |
| ServiceNow | NOW | servicenow.com |

**Dedup behavior:** Fuzzy-match fails on "International Business Machines" vs. "IBM" (JW ≈ 0.15). **Fallback strategy:** Extract email domain (IBM employees → @ibm.com) → exact domain match → confidence boost ✓

### Ticker Symbols vs. Legal Name

| Legal Name | Ticker | Notes |
|-----------|--------|-------|
| Microsoft Corporation | MSFT | Ticker sometimes appears in email domains or data |
| Alphabet Inc. | GOOGL | Google / Alphabet confusion common in CRM |
| Amazon.com Inc. | AMZN | Amazon employees use AMZN sometimes |

**Dedup behavior:** Engine does not match on ticker alone; requires email domain confirmation (for example, a known company domain that maps to the parent organization).

### Parent / Subsidiary / Brand Confusion

| Parent | Subsidiaries / Brands | Notes |
|--------|---------------------|-------|
| Alphabet Inc. | Google, YouTube, DoubleClick, Waze | Same company, different brands; CRM may record as separate companies |
| Meta Platforms | Facebook, Instagram, Oculus | Rebranding; older records say Facebook, newer say Meta |
| Broadcom Inc. | Avago, Emulex (post-acquisition) | Acquisitions; old company name persists in legacy records |

**Dedup behavior:** "John Smith at Google" vs. "John Smith at Alphabet" = different company strings, but same org. Engine flags this as **questionable match** (80–85% confidence depending on other signals). **Recommendation:** Manual review or enrichment to confirm.

### Hyphenation / Punctuation Variants

| Variant Set | Notes |
|-------------|-------|
| Doe-Smith Inc. vs. Doe Smith Inc. | Hyphenation inconsistent |
| O'Brien Corp vs. Obrien Corp | Apostrophe dropped |
| AT&T vs. AT & T | Ampersand formatting |
| US Bank vs. U.S. Bank | Abbreviation variants |

**Dedup behavior:** Jaro-Winkler catches most (JW 0.88–0.96), **flagged as company match** ✓

### Capitalization & Spacing

| Variant Set | Notes |
|-------------|-------|
| APPLE INC vs. Apple Inc | Case inconsistency |
| Salesforce.com vs. Salesforce | Spacing/punctuation |
| TechCorp Inc. vs. Tech Corp Inc. | Spacing in company name |

**Dedup behavior:** Normalized to lowercase before matching; **all caught as exact/fuzzy match** ✓

---

## Dedup Engine's Company-Matching Strategy

### Strategy 1: Exact Company Match (After Normalization)

```
NORMALIZE(company_a) == NORMALIZE(company_b)
where NORMALIZE = lowercase + trim + remove leading/trailing punctuation
```

**Confidence:** Adds **+15%** to name-match confidence.  
**Example:** "Acme Corp" + "ACME CORP" → normalized to same string → **+15% bonus**

### Strategy 2: Fuzzy Company Match (Jaro-Winkler ≥ 0.85)

```
jaro_winkler(company_a, company_b) ≥ 0.85
```

**Confidence:** Adds **+10%** to name-match confidence.  
**Example:** "Acme Corp" vs. "Acme Corporation" → JW 0.92 → **+10% bonus + +15% exact** (no additive stacking)

### Strategy 3: Email Domain Match

```
extract_domain(email_a) == extract_domain(email_b)
where extract_domain removes subdomains (sales.example.com -> example.com)
```

**Confidence:** Adds **+5%** if name matches but company string differs.  
**Example:**
- Record A: "person@sales.example.com" (company field = "Example Co" or blank)
- Record B: "person@example.com" (company field = "Example Corporation")
- Domain match + name fuzzy match → **company mismatch penalty waived; +5% boost**

### Strategy 4: Company Mismatch Penalty

```
If company_a != company_b and email domains differ → confidence -= 20%
```

**Example:**
- Record A: "John Smith" @ Company A (email: john@example.com)
- Record B: "John Smith" @ Company B (email: john@example.org)
- Name match 90%, but company + domain differ → **90% - 20% = 70%** → **rejected** (below 85% threshold)

---

## False Positive Risks by Company Pattern

### High False-Positive Risk

**Pattern:** Same first + last name, same company, but different job titles / departments / hiring dates

**Example:**
```
John Smith, Account Executive, Acme Corp (hired 2022)
John Smith, Sales Development Rep, Acme Corp (hired 2024)

Likely: Two different people sharing a name at same company
Signal: Created 2 years apart, different job levels → low confidence
Dedup behavior: Flagged for manual review (70–80% confidence)
```

**What to do:** Ask sales ops to confirm with department/manager before merging.

### Medium False-Positive Risk

**Pattern:** Duplicate due to name reuse after person leaves

**Example:**
```
Jane Doe, Acme Corp (hired 2020, no activity since 2023)
Jane Doe, Acme Corp (hired 2024)

Likely: Different people; first Jane left, second Jane hired
Dedup behavior: Age difference > 1 year → flagged (75–85% confidence)
```

**What to do:** Check activity dates; if stale (>12 months), consider archiving instead of merging.

### Low False-Positive Risk

**Pattern:** Same name, same company, different record sources (CRM native vs. integration import)

**Example:**
```
John Smith, Acme Corp (manually created in CRM 2023)
John Smith, Acme Corp (imported from Outreach 2024)

Likely: Same person, duplicate from integration overlap
Dedup behavior: Same phone + email → 95%+ confidence ✓
```

**What to do:** Safe to auto-merge; dedup engine catches this as high-confidence.

---

## Company Handling Checklist

When dedup flags a pair with company variance, confirm:

- [ ] **Email domain match?** Does email domain extract to same company?
  - Yes → company mismatch is false alarm; safe to merge
  - No → different companies; question if same person

- [ ] **Exact or fuzzy company match?** Are company strings very similar?
  - Yes → likely same company (legal suffix variation); safe to merge
  - No → could be parent/subsidiary; needs enrichment

- [ ] **Phone match?** If emails differ but phones match + same company → safe merge
  - Email variants (john vs. jon) + phone exact → **high confidence ✓**

- [ ] **Activity pattern?** Do activities suggest one person or two?
  - Intermingled activities with same email thread → one person ✓
  - Separate activity streams, different email addresses → two people ✗

---

## Examples: Real-World Dedup Scenarios

### Scenario 1: Acme Inc / Acme Corp / Acme Ltd (Acquisition)

**Records:**
```
Record A: john@acme-inc.example.com (Acme Inc, created 2020)
Record B: john@acme-corp.example.com (Acme Corp, created 2024)
```

**Analysis:**
- Email domain fuzzy match (acme-inc vs. acme-corp) → **-20% penalty**
- Name exact match ✓
- Phone exact match ✓
- Company JW match (Acme Inc vs. Acme Corp) ≈ 0.88 → **+10%**
- Email + phone + company boost → **Final: 92% confidence**

**Recommendation:** **Review (medium confidence)** — Likely same person post-acquisition; domain rebranding common. Ask HR to confirm before merge.

### Scenario 2: Google / Alphabet (Rebranding)

**Records:**
```
Record A: jane@example.com (company: "Former Brand Inc.", created 2018)
Record B: jane@example.com (company: "New Parent Inc.", created 2022)
```

**Analysis:**
- Email **exact match** → **95% baseline**
- Phone exact match ✓
- Company fuzzy match (Former Brand vs. New Parent) ≈ 0.62 → **below 0.85, no boost** (but email exact overrides)
- Final: **95% confidence**

**Recommendation:** **Safe to auto-merge** ✓ — Same email and phone; company field is metadata mismatch from internal rebranding.

### Scenario 3: Same Name, Different Company (False Positive)

**Records:**
```
Record A: john@example.com (company: "Company A", created 2023)
Record B: john@example.org (company: "Company B", created 2023)
```

**Analysis:**
- Email domain mismatch (example.com vs. example.org) → **company mismatch penalty -20%**
- Name exact match → **90%**
- Phone fuzzy match → **0.88**
- Final: **(0.90 × 0.20) + (0.88 × 0.35) = 0.488 ≈ 49%**

**Recommendation:** **Rejected** ✗ — Different companies, different email domains; clearly different people.
