# Recruiter / hiring-manager playbook

A 5–10 minute walkthrough for a hiring manager (e.g. Kevin) or recruiter (e.g.
Callie) to evaluate this project — and to try it on their own data without
handing it any credentials.

> Scope reminder: this is a local-first, recommendation-only prototype. The
> vendor adapters are contract-tested against checked-in replay fixtures with
> fake credentials; they are not a live vendor connection. Every source
> instance's live-validation proof is `NOT_LIVE_VALIDATED`, and production
> readiness is `NOT_ASSESSED`. Nothing is ever written back to any system.

---

## 0. One-time setup (about a minute)

```bash
uv sync --frozen        # pinned toolchain + dependencies
uv run --frozen pytest  # optional: prove the whole suite passes offline
```

No account, API key, model, or network is needed.

## 1. The fictional demo (no data of your own)

```bash
./run_demo.command      # or ./run_demo.sh
```

Open the printed `http://127.0.0.1:8501` and click **Run fictional demo**. Walk
through these, in order — this is the story to tell:

1. **Landing** — three start paths: fictional demo, authorized file import,
   optional read-only connect. Status shows `FICTIONAL_REPLAY` /
   `RECORDED_ANALYST_REPLAY`.
2. **Run setup** — one screen. Pick a lane (Deal prioritization, Assignment, or
   Capacity heatmap), confirm source slots and policy in at most two actions.
   The four-week horizon is fixed and confirm-only. There is no second screen and
   no per-field grilling.
3. **Deal prioritization queue** — deals ranked by a transparent score. No
   individual win-rate input is used.
4. **Assignment recommendation** — the best eligible consultant plus
   alternatives, with the objective and each contribution shown. Status is
   `OPTIMAL` or `RECOMMENDATION_ONLY`.
5. **Capacity heatmap + EMEA +25%** — where capacity is tight over four weeks,
   and a labeled `USER_SELECTED_ASSUMPTION_NOT_A_FORECAST` scenario (an
   assumption, not a forecast).
6. **Readiness evidence** — conversation evidence is additive only: it can
   satisfy a cited readiness dimension via an exact deal crosswalk, and it never
   picks or scores a consultant.
7. **Leadership digest** — fact-bound summary.
8. **Per-source proof + conservative run summary** — one three-field row per
   source (execution / implementation proof / live-validation proof) and a run
   summary derived from the **weakest decision-bearing source**. Runtime success
   never promotes proof.
9. **Manager dispositions** — accept / override / reject / defer, recorded
   locally only.
10. **Export + reset** — the export is inert (recommendation only, no write);
    reset purges local run state.

## 2. Use your own data — file import (no credentials)

```bash
./run_demo.sh --mode import
```

On the single Run-setup screen:

1. Attest that you are authorized and selected the minimum necessary fields and
   time range.
2. Choose your CSV/JSON export (start with the checked-in sample
   `data/examples/import/deal_priority_v1.csv`).
3. Select the exact fields, preview, and map each source field to a canonical
   field. Unknown fields are never mapped for you. A ready-to-adapt sample
   profile lives in `config/mapping_profiles/`.
4. Reconcile populations and accept the data-health report (missing, invalid,
   duplicate, stale, and conflicting rows are shown, never silently dropped).
5. Analyze and review, exactly as in the demo.

For an Assignment recommendation you additionally provide the consultant
roster / eligibility / workload / capacity / availability populations; for the
capacity heatmap you provide the demand fields plus the supply populations.
Deal prioritization needs only the mapped deal fields — there is no roster
requirement for it.

## 3. Optional: your own authorized read-only connect

```bash
./run_demo.sh --mode connect
```

If you have your own authorized read-only access (Salesforce / ClickUp / Fathom
/ Gong), attest authorization first — no preflight, schema read, file read,
preview, or connector call happens before that. Paste a session-only token
(memory only, never persisted). The adapters use a GET / read-by-POST allowlist
and perform no writes. You obtain your own token per each vendor's own
documentation; token permissions may exceed the app's enforced read-only
allowlist. File import is always available as the contract-tested fallback, and
using a valid account does not by itself change any proof label.

## 4. What to look for as a reviewer

- **Honest proof labels.** Nothing claims to be validated against a live vendor
  account; the run summary always reflects the most conservative source.
- **Read-only everywhere.** No CRM write, task, webhook, message, assignment, or
  production mutation exists in the code (`scripts/no_write_scan.py`).
- **Privacy discipline.** Full transcript text stays in memory; only hashes,
  metadata, and cited excerpts are persisted.
- **Deterministic decisions.** Rules and Google OR-Tools own every
  decision-bearing value; a brute-force oracle cross-checks the optimizer.
- **Reproducibility.** `scripts/verify_release.py` checks the file manifest,
  hashes, license inventory, and the secret/no-write scans.

## 5. Talking points

- Solves a real presales problem: prioritize deals, recommend an assignment,
  and see capacity — from the manager's own data, locally.
- Built credential-free and honestly labeled: contract-tested adapters, not a
  live vendor connection; production readiness `NOT_ASSESSED`.
- Safety by construction: recommendation-only, no writes, no individual
  win-rate input, transcripts can never pick a consultant.
