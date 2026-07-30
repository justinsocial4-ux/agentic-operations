# Decay Thresholds by Segment

Use this reference only when the user wants to customize the frozen defaults. It is a tuning worksheet, not a table of proven industry benchmarks.

## Frozen defaults

- Email no-open threshold: 180 days.
- Phone no-call threshold: 240 days.
- Title stale threshold: 24 months.
- Composite tiers: 0–30 Active, 31–60 Decaying, 61–85 Stale, 86–100 Archived Candidate.

## What may justify tuning

Review thresholds against:

- normal sales-cycle length;
- renewal or buying cadence;
- contact role and lifecycle stage;
- active opportunity or customer status;
- channel coverage and tracking completeness;
- historical response and false-positive rates.

Long-cycle enterprise accounts may require longer inactivity windows than high-velocity segments. That is a hypothesis to test, not permission to invent a segment-specific number.

## Safe tuning process

1. Keep the default model as the baseline.
2. Select a representative pilot cohort and protected exclusions.
3. Propose one threshold change at a time.
4. Show how many contacts would change tier.
5. Spot-check false positives, especially active deals, customers, VIPs, and contacts engaged through another channel.
6. Obtain approval before applying the configuration.
7. Record the version, effective date, owner, and measured outcome.

Never lower the archival boundary or shorten inactivity windows solely to reduce CRM storage. Archived Candidate remains a review state, and archival remains approval-gated.
