# Field and route contract

- Each field has a stable ID/version plus definition, approved-purpose, minimization, and field-policy receipts.
- Each declared record-field pair has exactly one supplied route row and unique receipt.
- `eligible` rows require one supplied provider ID. `suppressed`, `unauthorized`, `conflicting`, and `missing` rows must not carry a provider.
- A matched route proves only that the supplied provider contract covers that field at the cutoff. It does not prove that enrichment is necessary, the provider will find a match, or returned data will be accurate.
