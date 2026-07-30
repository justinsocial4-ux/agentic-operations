# Provider separation

Gmail, Yahoo, Microsoft, an email platform, a seed test, DNS, a blocklist, and a feedback loop can use different populations, denominators, delays, filtering stages, and definitions.

- Keep every provider/source/definition combination in its own lane.
- Do not average or compare lanes unless a separate customer-owned comparison contract exists; this skill accepts no such contract.
- Gmail Postmaster data applies to personal Gmail traffic, is delayed, can omit low-volume data for privacy, and can use bounded or categorical values.
- Yahoo calculates its own complaint measure using its own delivered-to-inbox basis.
- A seed placement test is a test population, not proof of recipient inbox placement.
- Absence from one blocklist is not universal clearance.
