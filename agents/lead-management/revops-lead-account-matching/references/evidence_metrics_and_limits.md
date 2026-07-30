# Evidence, Metrics, and Limits

Use this file before citing business impact or declaring success.

## Evidence Discipline

The original research contains vendor/consultancy statistics, derived calculations, and several unsupported baselines. Do not present these as guaranteed customer outcomes:

- 5-8 hours/week manual matching
- $1.6M-$2.4M pipeline leakage/recovery
- $100K-$300K ABM platform costs
- 21x conversion from five-minute response
- 85% match success, under-5% false positives, over-90% recall, or 98% hierarchy-routing accuracy

Use them only as historical research hypotheses with a direct source and caveat. Establish customer-specific baselines before ROI claims.

## Measurement Contract

- **coverage:** leads with a proposed candidate / eligible leads
- **precision:** approved/correct proposals / reviewed proposals
- **recall:** known correct matches found / all known correct matches in a labeled sample
- **false-positive rate:** incorrect proposals / reviewed proposals
- **review acceptance:** accepted MEDIUM proposals / reviewed MEDIUM proposals
- **latency:** time from lead eligibility to proposal and, separately, to approved association
- **write success:** successful associations / approved attempted associations
- **hierarchy-routing accuracy:** correct parent/subsidiary motion / reviewed hierarchy-aware matches

Validate on a labeled holdout sample. Report sample size, selection method, confidence intervals where appropriate, and errors by segment.

## Current Limits

- CRM data only; no external enrichment calls in v1.
- Company/account evidence only; no personal phone or contact-name matching.
- Core matching works without DQH-06, but parent routing does not.
- Static algorithm; no learning from reviewer corrections.
- Complex multi-parent structures remain a DQH-06/manual-review problem.

## Live Source Check

Record current URL checks in the project QA citation receipt before publication. A resolving page is not enough: verify that it directly supports the exact claim and identify vendor bias or secondary aggregation.
