# Company Name Variants

Use this file during detailed name matching. The main skill remains authoritative if any support note conflicts with it.

## Normalization

Before comparing names:

1. trim whitespace
2. lowercase
3. remove punctuation
4. remove common legal suffixes such as Inc, Incorporated, Corp, Corporation, Ltd, Limited, LLC, GmbH, PLC, BV, and SA
5. collapse repeated spaces

Do not remove regional or business-unit terms such as EMEA, APAC, Aviation, Digital, or Division; they help distinguish a subsidiary from its parent.

## Frozen Pilot Name Signal

- Parent normalized name is contained in the Child normalized name: name signal = 0.95.
- Otherwise calculate Jaro-Winkler similarity.
- Similarity at least 0.85: use the measured similarity as the name signal.
- Similarity below 0.85: name signal = 0.

## False-Positive Checks

- Identical or similar names in different countries may be different legal entities.
- A shared word or acronym is not enough when industries conflict.
- A shared website domain can indicate siblings rather than parent/child direction.
- A Child larger than the proposed Parent needs manual review.
- Never infer direction only from a name. Confirm ParentAccountId, D-U-N-S, contact domains, size, or an explicit manual mapping.

## Examples

| Parent | Child | Interpretation |
|---|---|---|
| Acme Corp | Acme EMEA | Strong prefix/pattern evidence; regional direction still needs confirmation |
| GE | GE Aviation | Strong prefix evidence; corroborate with domain or D-U-N-S |
| Delta | Delta | Ambiguous homonym; do not link on name alone |
| Example GmbH | Example Limited | Legal suffix removal improves comparison but does not prove hierarchy |
