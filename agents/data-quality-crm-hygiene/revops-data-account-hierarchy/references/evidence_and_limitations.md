# Evidence and Limitations

Use this file when citing market claims or explaining the pilot model's limits.

## Live-Checked Sources

Checked on 2026-07-10:

- [Delpha Ultimate Parent Guide](https://delpha.io/blog/salesforce-ultimate-parent-guide/) supports the fragmented-reporting problem, one-level Parent link discussion, manual-maintenance limits, M&A decay framing, and name-only matching risk.
- [Traction Complete Account Hierarchies](https://tractioncomplete.com/use-case/account-hierarchies/) supports its vendor claim that 80% of RevOps teams have inaccurate parent-child data, manual-linking pain, rollup gaps, and its claimed 80% reduction in manual work.
- [GTM8020 ABM Statistics](https://www.gtm8020.com/blog/account-based-marketing-statistics) republishes ABM market and revenue statistics with links to the cited underlying pages.
- [PoweredBySearch ABM Statistics](https://www.poweredbysearch.com/learn/b2b-abm-statistics/) provides supporting commercial guidance on ABM adoption and outcomes.
- [HubSpot associations documentation](https://developers.hubspot.com/docs/api-reference/latest/crm/associations/associate-records/guide) documents company-to-company association labels, including child-to-parent company.

## Evidence Caveats

- Delpha and Traction Complete sell hierarchy/data products. Treat their performance and prevalence numbers as vendor claims, not independent standards.
- GTM8020 and PoweredBySearch aggregate or interpret statistics from other sources. Follow their source links before using a number in an investment decision.
- The pilot research's labor, lost-revenue, third-party pricing, and success-baseline figures include derived or unsupported assumptions. Do not present them as universal outcomes.

## Frozen Formula Limitation

The published skill formula uses weights of 0.30 + 0.40 + 0.20 + 0.15 = 1.05. It does not include the subsidiary-pattern signal in that equation and does not specify renormalization when a signal is missing. Preserve the literal formula for pilot equivalence, cap displayed confidence at 100, and disclose the limitation.

For the fictional Acme example with no D-U-N-S/email signal, a 0.95 name signal and 0.88 domain signal produce 32.2%, not a renormalized score. A manual mapping remains the explicit 100% override.

Adding only an email signal of 0.90 produces 59.2% (`32.2 + 0.90 × 0.30 × 100`), still below the 70% floor. Recompute the whole formula before claiming a new signal crosses a tier.
