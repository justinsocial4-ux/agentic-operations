# Capacity And Segment Allocation

## Global Capacity

Use one non-negative integer `capacity` for the declared cohort. Rank exact available policy scores descending. A zero capacity is a valid policy result, not an error.

## Optional Segment Slots

Use `segment_field` plus `segment_slots` only when the policy owner has approved exact integer slots. Slot values must be non-negative and sum exactly to global capacity. Require each rankable candidate to have a verified segment named in the slot map.

Rank independently within each segment. Do not invent minimum representation, maximum concentration, redistribution, or a catch-all bucket. Unused slots remain unused. A planning target or pipeline gap does not create account eligibility or score points.

## Capacity Receipts

Report requested slots, rankable candidates, filled slots, unfilled slots, provisional-above-boundary candidates, and any tied review set. Never silently shrink or expand the policy capacity.
