# Sample mapping profiles

Ready-to-adapt, credential-free mapping profiles for the import path. Each
profile maps a checked-in fictional import sample to canonical fields. They
contain only field names, conversions, and explicit ID crosswalks — no values,
secrets, or private data — and each is hash-bound (`canonical_profile_sha256`).

- `example_deal_priority_csv_v1.json` maps
  `data/examples/import/deal_priority_v1.csv` to the canonical deal-work-request
  fields for the Deal-prioritization lane. The deliberately unknown headers
  (`SE Need`, `Bench`, `Hero`) are intentionally **not** mapped: unknown fields
  are never invented or silently mapped.

Regenerate after editing the generator:

```bash
uv run --frozen python scripts/generate_sample_profiles.py
```

To adapt one to your own export: copy it, change `source_instance_id`, the
`source_field_id` values (your headers), and the crosswalk entries, then let the
UI re-hash it on acceptance. The tool re-computes and verifies the hash; a
tampered profile fails closed.
