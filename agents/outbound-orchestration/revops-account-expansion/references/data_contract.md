# Data Contract

## Account identity

Choose the approved account unit before joining data: legal customer, CRM account, billing customer, workspace, parent, subsidiary, or another unit. Record the durable key and a crosswalk for each system. Report matched, unmatched, duplicate, and conflicting rows separately.

Do not roll child usage into a parent contract, or parent entitlement into a child account, unless the approved hierarchy policy permits it.

## Evidence domains

Keep these columns separate:

- contract: product, edition, licensed quantity, effective dates, renewal/cancel dates
- product catalog: product/SKU identity and entitlement meaning
- usage: actor, event, account/group, event time, ingestion time, environment
- adoption: approved eligible denominator and observed adopted numerator
- health: named source, definition, timestamp, and policy eligibility—not a generic score
- support/payment: source status and cutoff, with access restricted to the decision need
- commercial history: opportunity/order/quote, state, amount basis, currency, and timestamps
- pricing: price-book/quote/contract version, quantity, unit price, discount, currency, effective date
- contacts: verified relationship/role evidence, consent constraints, and freshness

## Product instrumentation receipt

Record the tracking-plan version, event/property definitions, group/account mapping, mapping start date, instrumentation start date, analysis window, timezone, known bot/test exclusions, eligible actor population, and identity coverage.

Amplitude documents that account analysis uses groups and group properties, and that group/property updates are forward-looking rather than retroactive. A current group value cannot rewrite historical evidence.

## Snapshot rules

Use records available by the cutoff. Preserve event time and ingestion time. Do not use current contract, group, owner, stage, or health values to reconstruct an earlier state.

Quarantine ambiguous joins and contradictory evidence; never choose the convenient record silently.
