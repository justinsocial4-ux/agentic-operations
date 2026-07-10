# Contact Decay Scoring Guide

Use this reference for exact arithmetic, tier-boundary review, or scoring QA. The rules below are the frozen DQH-03 pilot rules; they are operating defaults, not independently validated industry standards.

## Composite

Each input must be a finite number from 0 through 100.

| Signal | Weight |
|---|---:|
| Email engagement | 0.35 |
| Phone engagement | 0.25 |
| Title staleness | 0.15 |
| Company departure | 0.15 |
| Overall engagement | 0.10 |

The tier-consistent calculation is the weighted sum:

`email×0.35 + phone×0.25 + title×0.15 + company×0.15 + overall×0.10`

The main skill's legacy formula block shows a trailing `×100`. Do not apply that extra multiplier: the inputs are already 0–100, the weights total 1, and the skill's approved worked example does not apply it. Applying it would produce values outside the declared 0–100 scale.

Keep both values in audit output:
- `raw_score`: the weighted sum, rounded only for display precision.
- `display_score`: the raw score rounded to the nearest whole number using conventional half-up rounding.

## Frozen worked example

Inputs: email 60, phone 35, title 20, company 0, overall 60.

`21 + 8.75 + 3 + 0 + 6 = 38.75`, displayed as `39`.

That is `DECAYING`, routed to `RE_ENGAGE`.

## Tier boundaries

| Display score | Tier | Route |
|---:|---|---|
| 0–30 | ACTIVE | MONITOR |
| 31–60 | DECAYING | RE_ENGAGE |
| 61–85 | STALE | ENRICH_AND_DECIDE |
| 86–100 | ARCHIVED_CANDIDATE | ARCHIVE_RECOMMEND |

An archive recommendation is not an archive command. Archival always requires explicit user approval.

## QA checks

- Reject missing, nonnumeric, non-finite, or out-of-range signals.
- Do not silently impute a missing signal during exact scoring.
- State any degraded-data limitation separately from the deterministic score.
- Test every boundary: 0, 30, 31, 60, 61, 85, 86, and 100.
