# CRM Health Score Benchmarks

Use this file when applying or citing the DQH-04 pilot thresholds. The scoring bands below are frozen pilot decisions and must not be silently replaced with newer vendor thresholds.

## Evidence Caveat

The supporting pages are vendor-authored guidance, not independent standards. They currently resolve and support the broad measurement categories and many of the underlying cutoff ranges, but they do not independently validate every composite score, weight, or ROI claim in DQH-04. Treat the six-dimension formula and weights as pilot defaults to validate against the customer's outcomes.

Verified on 2026-07-10:

- [Cleanlist CRM Data Quality Benchmarks](https://www.cleanlist.ai/blog/2026-02-24-crm-data-quality-benchmarks) publishes bands for field completion, duplicates, freshness, contact-to-account matching, email validity, and related hygiene measures.
- [Prospeo CRM Data Audit Guide](https://prospeo.io/s/crm-data-audit) publishes audit dimensions, red-flag/target ranges, sequencing guidance, and a 1-2 hour baseline estimate for CRMs under 100K records.
- [Landbase CRM Data Audit Guide](https://www.landbase.com/blog/crm-data-audit-2026-step-by-step-revops) is supporting vendor guidance for audit dimensions and decay risk.
- [Databar CRM Data Quality Guide](https://databar.ai/blog/article/the-complete-guide-to-crm-data-quality-metrics-standards-best-practices) is supporting vendor guidance for CRM data-quality measurement.

## Frozen Pilot Bands

| Dimension | Raw metric | Score bands |
|---|---|---|
| Completeness | Core Contact fields populated | 90%+ = 90; 80-89% = 80; 65-79% = 65; 50-64% = 50; below 50% = 25 |
| Accuracy | Valid email, phone, and company-name checks | 95%+ = 95; 90-94% = 90; 80-89% = 80; 70-79% = 70; below 70% = 50 |
| Duplicates | Duplicate Contact rate | below 3% = 95; 3-5% = 90; above 5-10% = 75; above 10-20% = 50; above 20% = 25 |
| Freshness | Contacts updated within 90 days | 80%+ = 80; 65-79% = 65; 50-64% = 50; 35-49% = 35; below 35% = 20 |
| Consistency | Contacts linked to a valid Account | above 95% = 95; 88-95% = 85; 75-87% = 70; 60-74% = 50; below 60% = 30 |
| Connectivity | Verified/reachable Contacts plus Opportunity linkage | above 95% = 90; 88-95% = 80; 75-87% = 70; 60-74% = 50; below 60% = 30 |

## Composite Tiers

- 85-100: EXCELLENT
- 75-84: GOOD
- 65-74: AVERAGE
- 50-64: POOR
- Below 50: CRITICAL

These bands are implemented exactly in `scripts/crm_health_score.py` and covered by boundary tests.
