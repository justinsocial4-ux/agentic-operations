# Review Playbook and Examples

Use this file when presenting ambiguous candidates or a review queue.

## Introduction

Explain that the skill matches unassociated leads to existing accounts, shows exact component scores, and separates HIGH proposals from MEDIUM review and LOW manual lookup. Ask for the CRM/data source, hierarchy availability, scope, thresholds, exclusions, and read-only versus approved write mode.

## Ambiguous Match Template

```text
82% confidence: Acme → Acme Inc.

- name similarity: 88%
- domain match: no
- employee count: within configured range
- location: matched
- missing/conflicting evidence: personal email domain
- bucket: MEDIUM
- recommendation: human review before association
```

Let the reviewer accept, decline, or request manual lookup. Record the decision and reviewer; do not treat UI shortcuts as approval unless the actual interface supplies an authenticated action.

## Formula-Checked Examples

### HIGH

```text
name 0.92, domain 1, employee 1, location 1, phonetic 0.5
score = 0.40(0.92) + 0.30(1) + 0.15(1) + 0.10(1) + 0.05(0.5)
      = 94.3 → HIGH at the default 90 threshold
```

### MEDIUM

```text
name 0.88, domain 0, employee 1, location 1, phonetic 0.5
score = 62.7 → LOW, not MEDIUM
```

This corrects an old prose example that labeled a similar scenario 78% without showing arithmetic. To reach MEDIUM, the exact component values must produce at least 75.

### LOW

Generic names, missing domain, no employee count, and many candidate accounts should remain LOW/manual lookup even when a weak phonetic code matches.

## Final Confirmation

Before writes, show exact HIGH count plus individually approved MEDIUM count, error policy, and rollback/reconciliation plan. Require an explicit final confirmation.
