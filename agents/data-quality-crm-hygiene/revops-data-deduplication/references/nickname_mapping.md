# Common First-Name Variants (Nickname Mapping)

When the Deduplication Engine encounters similar first names, it uses Jaro-Winkler fuzzy matching (threshold 0.85) to catch most variants automatically. This file documents common variants that fuzzy-matching typically catches, so you understand why "John" and "Jon" will be flagged as likely duplicates.

## Name Variants by Category

### Shortening / Abbreviation

| Full Form | Common Variants |
|-----------|-----------------|
| Robert | Bob, Rob, Robby |
| Richard | Dick, Rich, Rick, Ricky |
| William | Bill, Will, Liam |
| James | Jim, Jimmy, Jamie |
| Charles | Charlie, Chuck, Chas |
| Edward | Ed, Eddie, Ted |
| Benjamin | Ben, Benji, Benny |
| Jonathan | Jon, Jonny, Jono |
| Christopher | Chris, Topher |
| Michael | Mike, Mick, Mikey |
| Nicholas | Nick, Nicky, Colin |
| Margaret | Meg, Maggie, Marge |
| Elizabeth | Liz, Beth, Liza |
| Katherine | Kate, Katie, Kathy, Katherine |
| Jennifer | Jen, Jenny, Jenn |
| Christina | Chris, Chrissy, Tina |
| Victoria | Vicky, Vita |

**Fuzzy-match behavior:** Jaro-Winkler ≥ 0.85 typically catches these (0.88–0.94 range).

### Spelling Variants (Same Pronunciation)

| Variant Set | Examples |
|------------|----------|
| Stephen / Steven / Stephan / Stefan | Different spellings, same sound |
| Jeffrey / Geoffrey / Jeffery | -frey / -ery variants |
| Phillip / Philip | Double L vs. single |
| Sara / Sarah | Silent H |
| Claire / Clare | Accent variance |
| Cecilia / Cecelia | -ilia / -elia |
| Kathryn / Katherine / Catherine | -yn / -ne variants |

**Fuzzy-match behavior:** Jaro-Winkler 0.88–0.92 range (caught by fuzzy match).

### Phonetic Variants (Different Spelling, Same Sound)

| Set | Examples | Metaphone Encoding |
|-----|----------|-------------------|
| Steven / Stephen | STFN | STFN (matches via Metaphone) |
| Smith / Smythe | X | X (matches via Metaphone) |
| Phillip / Filip / Phillipe | F | FLP (close) |
| Cynthia / Synthia | 0N0 | SNT0 (close) |

**Fuzzy-match behavior:** Jaro-Winkler < 0.85 on spelling, but Metaphone encoding catches these (Strategy 4 in workflow).

### Gendered Variants

| Masculine | Feminine | Notes |
|-----------|----------|-------|
| James | Jamie | Cross-gender usage common |
| Alex | Alexandra | Both masculine and feminine |
| Jordan | Jordan | Neutral |
| Casey | Casey | Neutral |

**Fuzzy-match behavior:** Flagged as separate names (JW < 0.85), but company + phone match will boost confidence.

---

## What the Dedup Engine Does with Variants

The engine handles variants through two mechanisms:

1. **Fuzzy-matching (Jaro-Winkler):**
   - "John" vs. "Jon" = 0.92 JW → **caught as candidate pair**
   - "Stephen" vs. "Steven" = 0.89 JW → **caught as candidate pair**
   - "Robert" vs. "Bob" = 0.71 JW → **rejected** (below 0.85 threshold)

2. **Phonetic matching (Metaphone):**
   - "Stephen" → STFN
   - "Steven" → STFN
   - **Metaphone match + name fuzzy match → confidence boost**

3. **Company + Phone context:**
   - "Bob Smith" (Acme) + "+1-415-555-0100"
   - "Robert Smith" (Acme) + "+1-415-555-0100"
   - Email different, but phone exact match (92%) + company match → **confidence 92–95%**

---

## Edge Cases & False Positives

### Common False Positives (Be Alert)

**Scenario 1: Common Name + Variants**
- "John Smith" (Acme) vs. "Jon Smith" (Acme) = 94% confidence ✓ (safe merge)
- "John Smith" (Acme) vs. "Jon Smith" (Microsoft) = 78% confidence ✗ (reject; different company)

**Scenario 2: Short Names / Nicknames**
- "Bob" as nickname for Robert isn't caught by fuzzy-match (JW 0.71)
- If same phone/email → caught by exact match (high confidence) ✓
- If different phone + "Bob at Acme" vs. "Robert at Acme" → likely false negative (recommend enrichment)

**Scenario 3: Name Reuse in Family/Teams**
- "John Smith" hired in 2024 at Acme (one person)
- "John Smith" hired in 2022 at Acme (different person, different team)
- Both have same company but different creation dates → flag as "likely career change, not duplicate"

---

## Manual Review Checklist

When reviewing flagged pairs with variant names, confirm:

- [ ] **Email match?** If emails identical or very close (john vs. jon in email), → safe merge
- [ ] **Phone match?** If phones identical, → safe merge
- [ ] **Company match?** If different companies, → likely different people (reject)
- [ ] **Time difference?** If >1 year between creation dates at same company, → likely career change (consider archiving instead of merging)
- [ ] **Activity pattern?** Check if activities logged separately (suggests two people) or intermingled (suggests same person using two profiles)

