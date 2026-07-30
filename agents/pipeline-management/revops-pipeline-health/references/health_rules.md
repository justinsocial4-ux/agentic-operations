# PM-01 Health Rules

Read before changing score weights, status boundaries, stall rules, or required fields.

## Score

| Component | Maximum | Default evidence |
|---|---:|---|
| Core fields | 40 | stage, amount, close date, next step; 10 each |
| Buyer activity | 30 | qualifying activity source available |
| Stage age | 30 | stage entry plus approved expected duration |

`health_score = raw_points / evidence_coverage * 100`.

Do not classify when evidence coverage is below 80. Otherwise: Green `>=60`, Yellow `>=40 and <60`, Red `<40`.

## Activity Points

| Full days since qualifying activity | Points |
|---:|---:|
| 0–6 | 30 |
| 7–13 | 22 |
| 14–20 | 14 |
| 21–29 | 7 |
| 30+ | 0 |

No history with an available source earns 0. Unavailable activity data removes the 30 points from evidence coverage.

## Stage-Age Points

| `days_in_stage / expected_days` | Points |
|---:|---:|
| `<=0.50` | 30 |
| `<=1.00` | 20 |
| `<=1.50` | 10 |
| `>1.50` | 0 |

Missing inputs remove 30 points from coverage. Creation age is not stage age.

## Legacy Stall Defaults

Prospecting 30, Qualification 30, Proposal 21, Negotiation 21, Pending Signature 14 days. Apply only after a seven-day new-deal grace period and customer approval.

At threshold means stalled. Pending Signature at threshold and any 30-day inactivity are Critical; other threshold crossings are Alert.
