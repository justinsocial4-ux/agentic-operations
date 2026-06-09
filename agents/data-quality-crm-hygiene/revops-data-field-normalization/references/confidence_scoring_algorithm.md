# Confidence Scoring Algorithm for Field Normalization

**Purpose:** Explain how the Field Normalization Engine calculates confidence scores (0–100) for mapping variants to canonical values.

---

## Core Scoring Formula

### Base Formula

```
Confidence = (
  base_match_signal × 0.70 +
  context_boost × 0.20 +
  frequency_signal × 0.10
) × 100
```

Where:
- **base_match_signal** (0.0–1.0): How well the variant matches the canonical value (Jaro-Winkler distance or exact match)
- **context_boost** (0.0–1.0): Industry, company, or seniority context that improves match likelihood
- **frequency_signal** (0.0–1.0): How often this variant appears (rare variants = lower confidence)

### Example Calculation

**Scenario:** Normalizing "VP Sales" to "Vice President of Sales"

**Step 1: Calculate base_match_signal**
- Jaro-Winkler distance("VP Sales", "Vice President of Sales") = 0.82
- base_match_signal = 0.82

**Step 2: Calculate context_boost**
- Is "Sales" in the title? YES → +0.15
- Is company in tech/SaaS industry? YES → +0.05
- Have we seen "VP Sales" → "Vice President of Sales" mapping before? YES → +0.05
- context_boost = 0.25 (capped at 1.0, but boosted past 1.0, so normalize)
- Actually: context_boost = min(0.82 + 0.25, 1.0) = 1.0

**Step 3: Calculate frequency_signal**
- "VP Sales" appears 243 times in dataset
- Total unique variants: 2,400
- Frequency ratio: 243 / 2,400 = 0.10
- Variants that appear frequently (>1% of dataset) = signal of intentionality
- frequency_signal = 0.95 (high; common variant, not a typo)

**Step 4: Combine**
```
Confidence = (0.82 × 0.70 + 1.0 × 0.20 + 0.95 × 0.10) × 100
           = (0.574 + 0.20 + 0.095) × 100
           = 0.869 × 100
           = 86.9% ≈ 87%
```

**Interpretation:** Medium-high confidence. Show user 1–2 alternatives for confirmation.

---

## Base Match Signals: Detailed Breakdown

### 1. Exact Match

**Definition:** Variant value exactly equals canonical value (after normalization)

```
Exact match("Sales Manager", "Sales Manager") = 1.0
```

**Confidence:** 100% (no normalization needed; field is already correct)

---

### 2. Jaro-Winkler Distance (Fuzzy Match)

**Definition:** Measure of similarity between two strings, accounting for character differences and transpositions.

**Formula:**
```
JW(s1, s2) = 
  IF s1 == s2 THEN 1.0
  ELSE
    j = (m/|s1| + m/|s2| + (m-t)/m) / 3
    THEN apply prefix weight factor
```

Where:
- `m` = # of matching characters (within distance threshold)
- `t` = # of transpositions (character swaps)
- Prefix weight factor boosts similarity if first chars match

**Examples:**

| Input | Canonical | JW Score | Interpretation |
|-------|-----------|----------|---|
| "VP Sales" | "Vice President of Sales" | 0.82 | Good match; likely same role |
| "V.P. Sales" | "Vice President of Sales" | 0.88 | Very good; just formatting difference |
| "Sales Manager" | "Sales Manager" | 1.0 | Exact match |
| "Sales Rep" | "Sales Representative" | 0.91 | Abbreviation; clear match |
| "Account Exec" | "Account Executive" | 0.89 | Abbreviation; clear match |
| "AE" | "Account Executive" | 0.42 | Poor; initials too ambiguous |
| "Sales" | "Sales Manager" | 0.71 | Low; missing context |
| "Consultant" | "Sales Representative" | 0.55 | Poor; different roles |

**Threshold:** Typically use JW ≥ 0.75 as "candidate for normalization"

---

### 3. Phonetic Matching (Metaphone)

**Definition:** Match based on phonetic similarity, ignoring spelling variations.

**Use case:** Catch spelling variants that Jaro-Winkler might miss.

**Examples:**

| Input | Canonical | Phonetic Match | JW | Combined Confidence |
|-------|-----------|---|---|---|
| "Stephen" | "Steven" | MATCH (STFN) | 0.90 | 0.95 |
| "Smythe" | "Smith" | MATCH (X) | 0.88 | 0.92 |
| "Jon" | "John" | MATCH (JN) | 0.75 | 0.86 |
| "Janice" | "Janis" | MATCH (JNS) | 0.85 | 0.91 |

**Boost logic:**
- If phonetic match but JW is low → boost JW by 0.05–0.10
- If phonetic AND JW match → add 0.05 confidence bonus

---

## Context Boosts: Detailed Breakdown

### 1. Industry Context (+0.05 to +0.15)

**Principle:** Same job title might mean different things in different industries. Apply industry-specific context.

**Example:**

| Variant | Industry | Canonical | Boost | Reasoning |
|---------|----------|-----------|-------|-----------|
| "Operations Manager" | Tech/SaaS | Computer Systems Manager | +0.10 | Tech ops often involve technical systems |
| "Operations Manager" | Finance | Finance Manager | +0.08 | Finance ops focus on FP&A/accounting |
| "Operations Manager" | Manufacturing | Industrial Prod. Manager | +0.12 | Clear operational context |
| "Operations Manager" | [No industry] | [Ambiguous] | 0.00 | No context; can't boost |

**Implementation:**
- Extract company industry from Account record
- Look up industry → job title mapping table
- If mapping exists, boost confidence by factor

---

### 2. Company Context (+0.03 to +0.08)

**Principle:** Companies of different sizes use titles differently.

**Example:**

| Variant | Company Size | Boost | Reasoning |
|---------|---|---|---|
| "VP Sales" | Enterprise (>10k emp) | +0.05 | Large orgs use formal VP titles |
| "VP Sales" | Mid-market (100–1k emp) | +0.03 | Smaller orgs more variable |
| "VP Sales" | SMB (<100 emp) | +0.01 | Very small orgs often non-standard |

**Implementation:**
- Extract employee count from Account enrichment data (if available)
- Apply size-specific boost factor
- More confident in larger orgs (standardized titles); less confident in small orgs (variable naming)

---

### 3. Seniority Level Context (+0.02 to +0.10)

**Principle:** Seniority modifiers help disambiguate role level.

**Example:**

| Variant | Seniority Modifier | Boost | Interpretation |
|---------|---|---|---|
| "Senior Sales Manager" | Senior | +0.08 | Clear seniority; easier to map |
| "Sales Manager" | None | 0.00 | Neutral; ambiguous level |
| "Junior Sales Rep" | Junior | +0.05 | Clearly entry-level |

---

### 4. Frequency/Prevalence Context (+0.01 to +0.10)

**Principle:** Common variants are likely intentional; rare variants might be typos.

**Example:**

| Variant | Frequency | Confidence Boost | Reasoning |
|---------|---|---|---|
| "VP Sales" | 243 / 2,400 (10.1%) | +0.10 | Very common; intentional variant |
| "V.P. Sales" | 45 / 2,400 (1.9%) | +0.05 | Moderate frequency |
| "Vp Sales" (typo) | 1 / 2,400 (0.04%) | +0.01 | Rare; likely typo but still exists |

**Formula:**
```
frequency_ratio = variant_count / total_unique_variants
boost = IF frequency_ratio > 0.05 THEN 0.10
        ELSE IF frequency_ratio > 0.01 THEN 0.05
        ELSE IF frequency_ratio > 0.001 THEN 0.02
        ELSE 0.01
```

---

### 5. Historical Pattern Context (+0.02 to +0.08)

**Principle:** If we've successfully mapped this variant before (in this org or others), boost confidence.

**Example:**

| Variant | Times Seen | Successful Maps | Boost | Reasoning |
|---------|---|---|---|---|
| "VP Sales" | 243 | 240 (98.8%) | +0.08 | Highly consistent mapping |
| "Sales Manager" | 892 | 890 (99.8%) | +0.09 | Excellent track record |
| "Manager" | 1200 | 300 (25%) | -0.10 | Very inconsistent; negative boost |

---

## Frequency Signal: Detailed Breakdown

### Rare Variant Penalty

**Principle:** Variants that appear only once or twice might be typos or data entry errors.

**Example:**

| Variant | Count | Rarity Ratio | Frequency Signal | Interpretation |
|---------|---|---|---|---|
| "VP Sales" | 243 | 0.10 (10%) | 0.95 | Common; high confidence |
| "V.P. Sales" | 45 | 0.02 (2%) | 0.80 | Moderate frequency |
| "Vp Slaes" | 1 | 0.0004 (0.04%) | 0.30 | Likely typo; very low signal |

**Formula:**
```
frequency_signal = LOG10(variant_count) / LOG10(max_count)
                 (normalized to 0–1 range)
```

---

## Special Cases: Non-Linear Scoring

### 1. Exact Dictionary Match (Very High Confidence)

If variant exactly matches a known canonical value in the reference dictionary:

```
Confidence = 0.98–1.0 (near-certain)
```

Example: "Sales Manager" (already standard) → "Sales Manager" (canonical)

---

### 2. Multi-Match Scenario (Lower Confidence)

If variant could plausibly map to 2+ canonical values:

```
Confidence = (1.0 / num_matches) × base_score
           + (tie_breaking_factor)
```

Example: "Manager" could be Sales Manager, Finance Manager, Ops Manager, etc.
- If 4 plausible matches and base JW = 0.70
- Confidence = (1.0 / 4) × 0.70 = 0.175 (17.5%, too low)
- Tie-breaker: use company industry or frequency to pick winner
- Final: 0.65–0.75 (low to medium-low; flag for review)

---

### 3. Acronym/Abbreviation (Medium Confidence)

Abbreviations are ambiguous by nature:

```
Base JW for "AE" vs. "Account Executive" = 0.42 (poor)
Boost for known abbreviation context (+0.30) = 0.72 (medium)
Industry context: Tech/SaaS (+0.05) = 0.77 (medium)
Frequency: "AE" appears 73 times (+0.05) = 0.82 (medium-high)
Final Confidence = 0.82 (medium-high; recommend user review)
```

---

### 4. International/Non-English (Lower Confidence)

Non-English titles are harder to map to English-language taxonomies:

```
Base JW("Directeur Commercial" vs. "Sales Manager") = 0.55 (poor)
Translation boost (French "Commercial" = "Sales") = +0.25
Final = 0.80 (medium; recommend confirming)
```

---

## Confidence Thresholds & Actions

### Default Thresholds

| Confidence | Recommendation | User Action |
|---|---|---|
| **≥0.95** | Auto-map; very safe | None required (or log and proceed) |
| **0.90–0.94** | Safe to auto-map; show user sample | Review sample; approve or adjust |
| **0.85–0.89** | Medium-high; recommend review | Show 1–2 alternatives; user picks |
| **0.80–0.84** | Medium; manual review | Flag for human decision |
| **0.75–0.79** | Low-medium; likely needs context | Requires user confirmation |
| **0.70–0.74** | Low; risky | Exclude from auto-mapping; manual only |
| **<0.70** | Too low; skip | Exclude; ask user to clarify |

### Customizable Thresholds

Users can adjust thresholds based on risk tolerance:

**Conservative (safety-first):**
```
Auto-apply: ≥0.95
Review recommended: 0.90–0.94
Manual review: 0.80–0.89
Skip: <0.80
```

**Balanced (recommended):**
```
Auto-apply: ≥0.90
Review recommended: 0.85–0.89
Manual review: 0.75–0.84
Skip: <0.75
```

**Aggressive (catch more variants):**
```
Auto-apply: ≥0.85
Review recommended: 0.80–0.84
Manual review: 0.70–0.79
Skip: <0.70
```

---

## Quality Assurance: Post-Normalization Accuracy

### Sampling Strategy

After bulk normalization, verify by sampling:

1. **Sample 20 records** randomly from normalized set
2. **Manual review** by user or domain expert
3. **Calculate false positive rate:** # of incorrect mappings / 20

**Interpretation:**
- 0–1 errors (0–5%) → Excellent; can proceed with confidence
- 2–3 errors (10–15%) → Good; acceptable, monitor
- 4+ errors (20%+) → Poor; adjust confidence thresholds and re-run

### Continuous Learning (Optional)

If customer agrees, collect feedback on mappings:

- User marks mapping as "Correct" or "Incorrect"
- Feed back into confidence scoring for future runs
- Improve base mappings with customer-specific patterns

**Example:**
```
Iteration 1: "Growth Manager" → "Sales Manager" (confidence 0.78)
User feedback: "That's wrong; in our org it's Account Management (CSM)"
Iteration 2: Store custom mapping; boost confidence for future "Growth Manager" records in this org
```

---

## Reference: Confidence Score Interpretation Table

| Score | Meaning | Example | User Action |
|---|---|---|---|
| 0.99–1.00 | Certain | "Sales Manager" = "Sales Manager" | Auto-apply; no review |
| 0.95–0.98 | Very High | "VP Sales" = "Vice President of Sales" | Auto-apply; show user sample |
| 0.90–0.94 | High | "V.P. Sales" = "Vice President of Sales" | Show alternatives; user confirms |
| 0.85–0.89 | Medium-High | "Account Exec" = "Account Executive" | Flag for review; 1–2 options |
| 0.80–0.84 | Medium | "Operations Manager" (context needed) | Requires user decision |
| 0.75–0.79 | Low-Medium | "Analyst" (industry dependent) | Exclude unless user specifies |
| 0.70–0.74 | Low | "Manager" (too ambiguous) | Exclude; manual review only |
| <0.70 | Too Low | "X" (nonsense) | Skip; ask for clarification |
