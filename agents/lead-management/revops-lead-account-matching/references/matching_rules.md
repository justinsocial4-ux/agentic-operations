# Lead-to-Account Matching Rules

Use this file for detailed normalization, candidate generation, and tie-breaking.

## Normalize Inputs

- lowercase and trim company names
- remove punctuation and legal suffixes such as Inc, Incorporated, Corp, Corporation, LLC, Ltd, Limited, GmbH, PLC, BV, SA, and SAS
- collapse repeated spaces
- lowercase email and website domains and remove `www.`
- preserve regional, product, and division terms because they distinguish subsidiaries
- generate Soundex as the deterministic phonetic fallback

## Candidate Signals

1. Domain exact match: `domain_match = 1`, weight 0.30.
2. Company-name similarity: Jaro-Winkler value from 0 to 1, weight 0.40. Keep candidates at or above the configurable 0.85 default.
3. Employee count: `1` when counts are within ±25%, otherwise `0`; weight 0.15.
4. Location: `1` when the configured city/country comparison matches, otherwise `0`; weight 0.10.
5. Phonetic fallback: `0.5` when phonetic codes match, otherwise `0`; weight 0.05.

```text
confidence = 0.40 × name_similarity
           + 0.30 × domain_match
           + 0.15 × employee_count_match
           + 0.10 × location_match
           + 0.05 × phonetic_match

score = confidence × 100
```

## Buckets

- HIGH: score at or above the configurable auto-associate threshold (default 90).
- MEDIUM: score below auto-associate and at or above the review threshold (default 75).
- LOW: score below the review threshold.

Never write a HIGH match without the final approval step in the main workflow.

## Multiple-Candidate Tie Break

1. prefer exact normalized name match
2. then prefer domain match
3. then prefer closer employee-count alignment
4. if still tied, route to manual review

## Hierarchy Context

Core matching must still work when DQH-06 is missing or stale. Only subsidiary-to-parent routing is disabled. When hierarchy data is current, preserve the matched subsidiary and parent in the output and choose the new-business, expansion, or multi-thread motion described in the main workflow.
