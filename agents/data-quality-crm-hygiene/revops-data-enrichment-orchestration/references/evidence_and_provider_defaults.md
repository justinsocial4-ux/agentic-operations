# Evidence And Provider Defaults

Read this file before quoting performance, cost, labor, deliverability, or ROI figures, and before using a provider default in a live plan.

## Evidence Warning

The pilot research used 20 receipts from one commercial source: Cleanlist. The pages are live and support the quoted Cleanlist test results, but Cleanlist benefits from the comparison. Treat the figures as vendor-reported pilot defaults—not independent benchmarks.

Before a live run:

1. Pull the customer's contracted provider prices and remaining credits.
2. Run the same 50–500 representative records through every available provider.
3. Measure fill rate, verified-email rate, phone connection rate, latency, and effective cost per accepted field.
4. Override the defaults with those customer-specific results.

## Frozen Pilot Defaults

These values reproduce the pilot's existing behavior. They do not promise current market pricing or performance.

| Provider | Email | Phone | Title | Company | Pilot cost per lookup | Pilot accuracy context |
|---|---|---|---|---|---:|---|
| ZoomInfo | yes | yes | yes | yes | $0.50 | 82–85% email range in the pilot materials |
| Apollo | yes | yes | yes | yes | $0.12 | 78–80% email range in the pilot materials |
| Clearbit | yes | partial | yes | yes | $0.25 | 76–85% email range in the pilot materials |
| Cleanlist | verified | yes | yes | yes | $0.50 | 98% vendor-reported verified email accuracy |
| Cognism | yes | yes | yes | yes | $0.30 | Use as a balanced-cost option; validate locally |

The skill's default waterfall remains Cleanlist → Apollo → ZoomInfo → Clearbit → Cognism. Provider access, customer contracts, measured results, and geography may justify reordering it at run time.

## Verified Sources

- [Cleanlist comparison, updated April 2026](https://www.cleanlist.ai/blog/zoominfo-apollo-clearbit-data-provider-comparison-2026) reports its own 500-contact test: ZoomInfo 85%, Apollo 80%, Clearbit 85%, Cleanlist 98%; it also publishes its effective-cost table. This is the source behind the pilot's performance and cost assumptions.
- [Cleanlist 1,000-lead provider ranking](https://www.cleanlist.ai/blog/15-best-b2b-data-enrichment-providers-in-2025-ranked) states that roughly 30% of B2B data goes stale annually and describes Cleanlist's 15-source waterfall. This remains vendor-authored evidence.
- [Apollo's official pricing page](https://www.apollo.io/pricing?solution=enrichment) uses plan credits and says enrichment consumes 1–8 credits for data fields (up to 9 per record in its FAQ). It does **not** confirm a universal fixed $0.12 live price.
- [Apollo's official API credit guide](https://docs.apollo.io/docs/api-pricing) says enrichment credit use varies by plan, endpoint, returned data, and waterfall usage.

## Claim Discipline

- Say “Cleanlist reports” or “the pilot assumes,” not “independent testing proves.”
- Do not quote $0.12, $0.25, $0.30, or $0.50 as the customer's real unit cost until their contract or credit ledger confirms it.
- Do not promise 98% deliverability. Report the measured rate from the customer's blind sample.
- The ROI and labor figures in the pilot are scenarios. Recalculate them from the customer's volume, loaded labor rate, provider spend, and observed outcomes.
