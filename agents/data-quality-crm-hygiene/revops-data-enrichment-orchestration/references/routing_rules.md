# Routing Rules

Read this before calculating missing-field scores, choosing a provider path, resolving conflicts, or explaining confidence tiers. These are the frozen pilot rules mirrored by `scripts/enrichment_router.py`.

## Missing-Field Score

| Missing field | Points |
|---|---:|
| Email | 40 |
| Phone | 30 |
| Job title | 15 |
| Company data | 15 |

Interpret the total as: 90–100 critical, 70–89 high, 50–69 medium, below 50 low.

## Provider Path

1. Score above 70 plus strict accuracy → Cleanlist.
2. Score above 70 plus cost sensitivity → Apollo.
3. Score 50–70 → Clearbit or Cognism, selected from the customer's measured cost/accuracy results.
4. Score below 50 → cheapest available provider for confirmation enrichment.

The default waterfall order is Cleanlist → Apollo → ZoomInfo → Clearbit → Cognism. “Not found” cascades to the next available provider. Never call an unavailable, unlicensed, blacklisted, or over-budget provider.

## Conflict Priority

Apply in this exact order:

1. Verified beats unverified.
2. Newer beats older.
3. Majority agreement beats a minority value.
4. Higher measured provider accuracy breaks the remaining tie.

## Confidence Tiers

| Score | Meaning |
|---|---|
| 95–100 | Verified or confirmed by at least two providers |
| 85–94 | One high-accuracy provider or two-provider agreement |
| 75–84 | One mid-accuracy provider |
| Below 75 | Conflict or low-confidence single source |

The default write-back threshold remains above 80%. Critical fields below 60% require manual handling. Never overwrite verified manual data.

## Budget And Failure Rules

- Track spend per provider and in aggregate.
- Pause before exceeding the approved total or provider cap.
- On “not found,” try the next provider and report unresolved records.
- On rate limits, back off 2, 4, then 8 seconds; do not silently skip records.
- If the provider set cannot meet the requested quality threshold, stop and explain the gap.
