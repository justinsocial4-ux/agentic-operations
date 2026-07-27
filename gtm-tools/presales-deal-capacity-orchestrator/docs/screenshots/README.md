# Screenshots

Representative captures of the credential-free fictional demo path, taken from
the loopback-only Streamlit dashboard (`./run_demo.sh` → **Run fictional demo**).
All content is synthetic; no account, credential, network, or model is involved.

| File | Shows |
|---|---|
| `01-landing.png` | Landing page: the three start paths (fictional demo, authorized CSV/JSON import, optional read-only connect). |
| `02-results-overview.png` | Top of the results page: deal prioritization queue, assignment recommendation (`OPTIMAL \| RECOMMENDATION_ONLY`), capacity heatmap, EMEA +25% assumption, and the fact-bound leadership digest. |
| `03-results-full.png` | Full results page including per-source proof rows (`FICTIONAL_REPLAY` / `FULLY_IMPLEMENTED_CONTRACT_TESTED` / `NOT_LIVE_VALIDATED`, each `Decision-bearing: True`), the conservative run summary (`WEAKEST_DECISION_BEARING_SOURCE`, `Production readiness: NOT_ASSESSED`), manager dispositions (accept / override / reject / defer), the inert export, and reset. |

To reproduce:

```bash
./run_demo.sh --headless --port 8501
# open http://127.0.0.1:8501 and click "Run fictional demo"
```
