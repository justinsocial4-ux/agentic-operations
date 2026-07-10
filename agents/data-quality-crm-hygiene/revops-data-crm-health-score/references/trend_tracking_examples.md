# Trend Tracking Examples

Use this file when two or more health-score runs exist.

## Snapshot Contract

Store each run as a timestamped JSON snapshot in `health_score_history/`. Include:

- assessment timestamp
- composite score and tier
- all six dimension scores
- Contact, Account, and Opportunity counts
- confidence and known limitations
- configuration used, including custom weights or thresholds

Do not claim a trend from one snapshot. At least two comparable snapshots are required.

## Pilot Example

```text
Current Health Score: 76 (GOOD)
Previous Assessment (2 weeks ago): 72 (AVERAGE)
Delta: +4 points ↑ improving
Trend rate: +2 points/week

Dimension-by-dimension trends:
  Completeness: 75 → 81 (+6 points) ↑
  Freshness: 50 → 54 (+4 points) ↑
  Duplicates: 85 → 84 (-1 point) ↓
  Accuracy: 87 → 89 (+2 points) ↑

Biggest movers: Completeness (+6), Freshness (+4)
```

## Deterministic Helper

```bash
python3 scripts/crm_health_score.py trend \
  --current-json '{"completeness":81,"accuracy":89,"duplicates":84,"freshness":54,"consistency":72,"connectivity":90}' \
  --previous-json '{"completeness":75,"accuracy":87,"duplicates":85,"freshness":50,"consistency":72,"connectivity":90}' \
  --periods 2
```

`periods` is the number of weeks or other equal intervals between snapshots. State the interval unit in the user-facing report.
