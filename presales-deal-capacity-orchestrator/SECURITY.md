# Security

## Supported state

This is a credential-free, local-first evaluation prototype, not a live vendor connection or production deployment. Production readiness is `NOT_ASSESSED`. Report suspected issues privately to the repository owner before public disclosure; no hosted security contact or SLA is claimed.

## Enforced foundations

- HTTPX clients are constructed with `trust_env=False`, normal TLS verification, and redirects disabled.
- Endpoint policy is exact method/operation/host/path; vendor endpoints require HTTPS. Write operations are absent.
- Caller-supplied authorization, cookie, proxy-authorization, forwarding, and host headers are denied. Cookie state is cleared around requests.
- Local-model URLs are restricted to loopback and redirects are rejected; there is no remote LLM route.
- Credentials, ambient environment credentials/proxies, `.netrc`, browser state, and keychains are not configuration sources.
- Authorized-data storage is outside the repository with owner-only permissions.
- SQLite has no credential, token, full-transcript, segment-text, or uncited-text column.

## Gong official artifact review (2026-07-24)

A credential-free GET fetched the official documentation artifact from:

`https://gong.app.gong.io/ajax/settings/api/documentation/specs?version=`

The exact empty `version` parameter is the URL emitted by the public documentation page; the artifact reports OpenAPI `3.0.1` and info version `V2`. Its SHA-256, reviewed operation IDs, and manually approved connector host set are bound in `config/connector_security_v1.json` and `data/replay/gong/openapi-review-v1.json`.

The artifact's generated `servers` entry is `https://127.0.0.1:8443`; it was explicitly rejected as a non-vendor generated server and is not allowlisted. The manually approved public Gong API host is exactly `api.gong.io`, corroborated by the official public artifact's API examples and the official public API endpoint. No wildcard or tenant override is accepted. This package performs no live Gong transport and no real account call; the Gong adapter is exercised only against checked-in replay fixtures with fake credentials.

## Known limitations

Python memory cannot be securely zeroed. Local hashes are reproducibility and accidental-integrity evidence, not signatures or a tamper-proof ledger. DNS pinning/rebinding controls and connector-specific auth injection are later transport implementation work and must pass their named gates before connector execution is enabled.
