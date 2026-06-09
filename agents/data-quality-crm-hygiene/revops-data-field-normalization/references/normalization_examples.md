# Real-World Field Normalization Examples

**Purpose:** Help users understand mapping decisions and edge cases the Field Normalization Engine encounters.

---

## Job Title Normalization: Tricky Cases

### Case 1: Abbreviation Ambiguity

**Variant:** "VP"  
**Possible canonical matches:**
1. Vice President of Sales (41-4011) → confidence 0.72
2. Vice President of Marketing (11-2021) → confidence 0.68
3. Vice President of Engineering (11-3021) → confidence 0.65

**Engine decision:** Too ambiguous (no clear winner). Confidence <0.70.  
**Action:** Flag for manual review. User selects context-appropriate title.

**User resolution:** "In our org, VP almost always means VP of Sales. Let me add a custom mapping."

---

### Case 2: Career Changer

**Variant:** "Analyst"  
**Records:** 120 contacts with title "Analyst"  
**Context:** 40 from financial services companies, 60 from tech companies, 20 from marketing teams

**Possible canonical matches:**
- 13-2011: Accountants and Auditors (for finance context) → 0.65 confidence
- 15-1121: Computer Programmers (for tech context) → 0.62 confidence
- 41-4011: Sales Managers (if analytics/insights team) → 0.58 confidence

**Engine decision:** No single mapping applies to all 120. Split by industry context.

**Resolution:**
```
- Finance context (40 records) → 13-2011 (Accountants)
- Tech context (60 records) → 15-1121 (Computer Programmers)
- Marketing context (20 records) → Flag for manual review (unclear role)

Recommendation: Ask user "What does 'Analyst' mean in each department?"
```

---

### Case 3: Emerging Role Not in BLS

**Variant:** "Growth Manager"  
**BLS match:** None exact. Closest fuzzy matches:
- Sales Manager (41-4011) → 0.78 confidence
- Marketing Manager (11-2021) → 0.72 confidence
- Business Analyst (15-1121) → 0.65 confidence

**Engine decision:** Medium confidence (0.78) to Sales Manager.

**User override:** "In our company, Growth Manager is actually a post-sales account expansion role, closer to Customer Success. Map to CSM (13-1161)."

**Result:** Custom mapping created. All 15 "Growth Manager" records standardized to "Customer Success Manager."

---

### Case 4: Title with Seniority Modifiers

**Variants:**
- "Senior Sales Representative"
- "Senior Sales Rep"
- "Jr. Sales Rep"
- "Sales Rep (junior)"

**Engine approach:**
1. Normalize for comparison: "senior", "sales", "representative" → keywords
2. Match core role: Sales Representative (41-4013)
3. Store seniority modifier: "senior" or "junior"
4. Option A: Map all to 41-4013 (ignore seniority)
5. Option B: Use seniority to fine-tune confidence or create sub-categories

**Recommendation:** Map core title; preserve seniority as separate metadata (for future use in comp analysis, career pathing, etc.)

**Result:**
```
| Original | Canonical | Seniority | Confidence |
|----------|-----------|-----------|------------|
| Senior Sales Rep | Sales Representative (41-4013) | Senior | 0.95 |
| Jr. Sales Rep | Sales Representative (41-4013) | Junior | 0.92 |
| Sales Rep (junior) | Sales Representative (41-4013) | Junior | 0.88 |
```

---

## Industry Normalization: Tricky Cases

### Case 5: Ambiguous Industry Abbreviations

**Variant:** "SaaS"  
**Appears in:** 340 records

**NAICS lookup:**
- "SaaS" is not a NAICS code (NAICS uses detailed industry names, not abbreviations)
- Fuzzy match to "Software Publishers" (NAICS 511210) → 0.75 confidence
- Company enrichment API (Clearbit) may return different industry codes per account

**Engine decision:** Map to "Software Publishers" with 0.75 confidence (medium).

**Context boost:**
- If company's domain is .com and employee count >50 → tech company context → +0.05
- Final confidence: 0.80 (medium-high)

**Alternative:** If customer has enrichment data, use that to validate/override.

---

### Case 6: Sector vs. Industry Confusion

**Variant:** "Financial Services"  
**Appears in:** 890 records

**Interpretation issue:**
- "Financial Services" is a sector (very broad)
- NAICS requires more specific classification:
  - 522110: Commercial Banking
  - 523130: Commodity Contracts Brokerage
  - 524210: Insurance Agencies and Brokerages
  - etc.

**Engine decision:**
1. Recognize "Financial Services" as sector-level (too broad)
2. Confidence: 0.60 (too low for auto-map)
3. Request user to clarify: "What type of financial services? Banking, insurance, investment, etc.?"

**User resolution:** Customer adds custom mappings per account type.

---

### Case 7: Company Name as Industry

**Variant:** Contact.Industry field contains company names instead of industries

Examples:
- "Acme Corp" (should be company name, not industry)
- "TechStartup Inc" (should be company name)
- "Finance Department" (should be department, not industry)

**Engine detection:** Fuzzy match against known company names + company name patterns (Inc, Corp, LLC, etc.)

**Action:** Flag as data quality issue (incorrect field usage). Recommend:
1. Review and correct in CRM
2. Map company names to actual industries (using enrichment API)
3. Exclude these records from normalization until corrected

---

## Country Code Normalization: Tricky Cases

### Case 8: Non-Standard Country Formats

**Variants found in Account.BillingCountry field:**
- "US" (ISO 2-letter code)
- "USA" (common abbreviation, not standard)
- "United States" (full name)
- "United States of America" (formal)
- "U.S.A." (with periods)
- "United States - Federal" (with region)
- "America" (informal, ambiguous)

**Normalization:**
- All map to ISO 3166-1 alpha-2 code: "US"
- Or ISO 3166-1 alpha-3 code: "USA" (though USA is not standard)
- Canonical recommendation: Use 2-letter codes (US, CA, GB, DE, JP, etc.)

**Confidence scores:**
```
| Input | Canonical | Confidence | Reason |
|-------|-----------|------------|--------|
| US | US | 1.0 | Exact match |
| USA | US | 0.95 | Common variant |
| United States | US | 0.98 | Full name → code |
| America | US | 0.65 | Ambiguous (could be US, Canada, Mexico) |
| UK | GB | 0.92 | Common variant for Great Britain |
| England | GB | 0.88 | Region → country |
```

---

### Case 9: Region-Level Input (Non-Country)

**Variant:** "California", "Texas", "Ontario", "Quebec"

**Issue:** State/province names, not country codes. Agent must detect and decide.

**Options:**
1. **Ignore:** Skip normalization (too risky; missing country context)
2. **Infer:** If company is US-based, state codes indicate "US" country
3. **Reject:** Flag for manual review; ask user to provide country

**Engine approach:** Detect state/province patterns; if detected + company context suggests country, map accordingly. Otherwise, flag as low confidence.

**Example:**
```
Input: "California"
Context: Company domain is .com (likely US)
Inference: State in US → country code "US"
Confidence: 0.80 (medium; based on domain inference)
```

---

## Company Name Normalization: Tricky Cases

### Case 10: Legal Suffix Variations

**Variants:**
- "Acme Corporation"
- "Acme Corp"
- "Acme Corp."
- "Acme Incorporated"
- "Acme Inc"
- "Acme Inc."
- "Acme Limited"
- "Acme Ltd"
- "Acme Ltd."
- "Acme LLC"
- "Acme, LLC"

**Normalization:**
1. Remove legal suffix
2. Trim whitespace
3. Standardize case (Title Case)
4. Result: "Acme"

**Confidence:** 0.95+ (very high; suffix removal is deterministic)

---

### Case 11: International Company Names

**Variants:**
- "Société Générale" (French: "General Company")
- "Société Générale SA" (with corporate form)
- "Société Générale S.A." (with periods)
- "Societe Generale" (without accents; common anglicization)

**Challenge:** Accents, non-Latin characters, corporate forms (SA, GmbH, Pty Ltd) vary by country.

**Normalization strategy:**
1. Remove accents: "Société" → "Societe"
2. Remove corporate form: "SA" → nothing
3. Trim whitespace and standardize case
4. Result: "Societe Generale"

**Confidence:** 0.90+ if enrichment API (ZoomInfo, Clearbit) confirms master company name. Otherwise 0.75–0.85.

---

### Case 12: Acquisition/Name Change Detection

**Scenario:** Company "Acme Corp" was acquired by "BigTech Inc" and rebranded as "BigTech Acme Division."

**Records in CRM:**
- 100 old contacts: "Acme Corp"
- 50 new contacts: "BigTech Acme"
- 30 contacts: "BigTech Inc"

**Challenge:** Which is the current/canonical name?

**Engine approach:**
1. Detect acquisition pattern (compare to enrichment API)
2. ZoomInfo/Clearbit confirms: "Acme Corp" is now subsidiary of "BigTech Inc"
3. Offer three normalization options:
   - **Option A:** Map all to "BigTech Inc" (parent company)
   - **Option B:** Map all to "BigTech Acme" (current division name)
   - **Option C:** Keep division separation (add "division" field for segmentation)

**Recommendation:** Ask user for business context. Different strategies depending on whether you want to see Acme separately or as part of BigTech.

---

## Cross-Field Normalization: Title + Industry Context

### Case 13: Title Meaning Changes by Industry

**Variant:** "Operations Manager"  
**Appears in:** 240 records across multiple industries

**Context matters:**
- In Tech (SaaS/software): Often means technical operations/DevOps-adjacent
  → Could map to 11-3021 (Computer Systems Managers)
- In Sales: Often means sales operations / pipeline management
  → Map to 41-4011 (Sales Managers)
- In Finance: Often means finance operations / FP&A
  → Map to 11-3031 (Finance Managers)
- In Manufacturing: Often means operations/production management
  → Map to 11-3051 (Industrial Production Managers)

**Normalization strategy:**
1. Group records by industry
2. Apply context-specific mapping for each group
3. Confidence scores vary by context strength

**Example:**
```
| Original | Industry | Canonical | Confidence |
|----------|----------|-----------|------------|
| Operations Manager | Software | Computer Systems Manager (11-3021) | 0.85 |
| Operations Manager | Financial Services | Finance Manager (11-3031) | 0.80 |
| Operations Manager | Manufacturing | Industrial Prod. Manager (11-3051) | 0.88 |
| Operations Manager | [missing] | [ambiguous; flag for review] | 0.45 |
```

---

## Handling Low-Confidence Mapping Decisions

### Case 14: When to Exclude (Confidence <0.70)

**Examples of low-confidence variants:**
- "Admin" (Could be Administrative Assistant, Executive Assistant, etc.)
- "Manager" (Could be any type of manager)
- "Specialist" (Could be technical, business, domain expert)
- "Coordinator" (Could be project, event, program, etc.)
- Single letters or numbers ("X", "1", "Manager #2")

**Engine action:** Flag all <0.70 confidence for manual review.

**User options:**
1. Skip normalization for this variant (leave as-is)
2. Add context (e.g., "Admin at Tech companies → IT Administrator")
3. Manually assign to canonical title
4. Request data enrichment to clarify intent

---

## Summary: When to Trust Confidence Scores

| Confidence Range | Recommendation | Example |
|---|---|---|
| **0.95–1.0** | Auto-map; safe to apply without review | "Sales Manager" → 41-4011 |
| **0.85–0.94** | Show user 1–2 alternatives; request confirmation | "VP Sales" → "Vice President of Sales" |
| **0.75–0.84** | Flag for manual review; require user input | "Analyst" (context-dependent) |
| **<0.75** | Exclude from auto-mapping; requires manual resolution | "Manager" (too ambiguous) |

**Best practice:** Run at 0.85+ confidence threshold for initial bulk normalization. Increase to 0.90+ if you want maximum safety (fewer changes, but some variants skipped).
