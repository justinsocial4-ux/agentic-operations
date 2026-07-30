# Aggregation and overlap

Sum segment values only with a verified-disjoint aggregation receipt. Require the same count unit, coverage, geography/taxonomy semantics, currency, period, price basis, cutoff, and complete source state.

Overlapping geography, industry, size bands, parent/child entities, multi-establishment firms, duplicate vendor records, and taxonomy crosswalks can double count a universe. If disjointness is not verified, keep per-segment values and return `AGGREGATION_UNAVAILABLE`.

For a single segment, do not reprint its values as an aggregate. Return `SINGLE_SEGMENT_NOT_REPRINTED`.

Prior-period comparisons require matched definitions and a supplied decomposition receipt. Do not infer market growth, contraction, or cause from changed totals alone.
