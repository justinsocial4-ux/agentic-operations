# TSO-03 Evidence Handoff

Export only:

- tool/service ID;
- window boundaries, cutoff, timezone;
- population/event/identity/source policy IDs and versions;
- evidence IDs and extraction times;
- paid, assigned, eligible assigned, active eligible, unclassified assigned, excluded, unmatched, unknown, withheld, and conflicting counts;
- exact observed active-assigned rate and state;
- source coverage, lag, missingness, conflicts, and comparison status;
- approved cost basis/currency/period if supplied.

Use `build_tso03_handoff` as the exact bounded schema. Supply all eight policy IDs, the validated evidence rows, raw population counts, source coverage/lag/missingness, and raw matched-window inputs. The helper recomputes the population and comparison, sorts provenance deterministically, and fixes the lane to `ADOPTION`; do not add fields by hand.

Render every returned key, including the full sorted `evidence` array with source version, extraction time, policy, taxonomy, and aggregate flag. An evidence-ID list alone is not provenance. If lag was not supplied, set lag to `SOURCE_REQUIRED`; do not translate complete coverage into zero or “none-stated” lag.

Do not export adoption score, engagement score, vendor-health score, renewal risk, consolidation flag, savings, confidence, recommended action, or person-level data.

TSO-03 must keep this evidence in its separate `ADOPTION` customer-utilization lane. It cannot improve or worsen contract/service/support findings.
