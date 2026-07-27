# Phase 0 Threat Model

## Assets and trust boundaries

Assets are session credentials, authorized operational records, private transcript buffers, minimized SQLite receipts, mapping/policy approvals, lineage, and inert exports. Trust boundaries are local file selection, vendor HTTPS, loopback local-model HTTP, SQLite persistence, browser UI, and package/replay inputs. Phase 0 crosses only public-documentation network access to pin Gong's artifact; tests use synthetic data.

## Threats and controls

| Threat | Phase 0 control | Residual / later gate |
|---|---|---|
| Ambient credential or proxy leakage | HTTPX `trust_env=False`; deny auth/cookie/proxy headers; no env/keychain/browser credential path | Connector auth injection must remain post-fingerprint and memory-only |
| SSRF, lookalike host, redirect credential forwarding | Exact host/path/method policy, HTTPS vendors, loopback validator, no redirects, deny userinfo/fragments/non-default ports | DNS rebinding checks complete in connector transport phase |
| Source mutation | Capability schema requires `external_writes_supported=false`, empty writes, and only GET or explicitly declared read-by-POST | Static/dynamic vendor no-write suites before connectors |
| Secret persistence | SQLite/static schema denial; no credential fields; fake-only tests | Scan logs/exports/DB/WAL with each connector |
| Transcript persistence | No transcript/segment/uncited-text SQL columns; conversation segment marked ephemeral | Sentinel scans on import/Gong success/failure/crash routes |
| Remote private-data transmission | No remote model route; only future loopback URLs accepted | Local model behavior belongs to user; app still validates citations |
| Consultant harm from transcript or win rate | Contract has no consultant fields in observations; no win-rate field; instrumentation separates source fields from decision roots | Taint/call-graph tests in deterministic phases |
| Invented mappings or silent defaults | Strict/forbid-extra contracts and explicit lineage shape | Mapping implementation and reconciliation in Phase 1 |
| Proof inflation / omitted weak source | Serializer derives contributor closure and `decision_bearing`; rejects omitted sources; weakest source summary | Full graph enforcement expands with Phase 1 artifacts |
| Setup confirmation fatigue or hidden authority | Authority is folded into core setup confirmation; max two total lane actions | UI proof in Phase 7 |
| Mixed-currency distortion | Typed source-supplied corporate normalization approval and lineage contract; no FX dependency | Fail-closed scoring in Phase 2 |
| Multi-role source authority loss | Manifest accepts multiple slot-authority bindings | Identity mismatch and reconciliation gates in Phase 1 |
| Dependency compromise/license surprise | Resolved `uv.lock`, hash-exported fallback lock, full installed transitive license inventory | Vulnerability/legal/trademark review remains a release gate |
| Local data exposure | Owner-only directory/file helper, outside-repo/import checks, fail closed | Windows owner-only ACL equivalent remains unverified in this macOS run |

## Abuse cases explicitly denied

No production account access, remote LLM fallback, arbitrary URL, webhooks, task/message/assignment creation, CRM mutation, automatic staffing, sentiment/performance inference, transcript-derived consultant fit, individual win-rate scoring, or caller-edited proof classification.

## Rollback

The package is self-contained and untracked. Rollback is deletion of this new directory by the owner. Future adapter rollback disables its static registry entry while fictional/import paths remain. There is no source-system state to undo.
