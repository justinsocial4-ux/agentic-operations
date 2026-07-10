# Output Template

Read this file before the final report.

## 1. Preflight receipt

Show decision, source, extraction time, lifecycle mapping, episode rule, window, cutoff, history start, filters, completeness, target/baseline, and enabled/disabled analyses.

## 2. Maturity funnel

| State | Count | Denominator note |
|---|---:|---|
| Total MQL episodes | | All in scope |
| Pending, not mature | | Excluded from outcome rates |
| Mature episodes | | Outcome-rate denominator |
| Converted within window | | Mature episodes |
| Rejected within window | | Mature episodes |
| Recycled/other | | Mature episodes |
| Unresolved at deadline | | Mature episodes |

## 3. Conversion and velocity

Show rate, count, denominator, Wilson interval, converted velocity count, median days, and p75 days. Put `unknown` where evidence is absent.

## 4. Rejections

Show capture rate first. Then show raw reason, normalized reason if approved, count, share of all rejections, and share of captured reasons. Include `UNKNOWN_REASON`.

## 5. Comparisons and scoring

Show counts, rates, intervals, absolute difference, relative difference, test result, evidence label, and confounders. Do not use red/green status without a customer-approved target.

## 6. Action preview and validation

Separate observed evidence, interpretation, unknowns, and proposed human actions. Confirm count reconciliation, identical comparison definitions, and that no CRM or scoring change occurred.
