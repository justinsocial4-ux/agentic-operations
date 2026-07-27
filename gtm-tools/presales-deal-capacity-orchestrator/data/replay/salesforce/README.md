# Salesforce replay

Minimized synthetic Salesforce REST response shapes for Phase 4 contract tests. `fixture-manifest.json` binds each fixture to its SHA-256. Tests use a fake bearer token and `httpx.MockTransport`; these files require and authorize no live vendor traffic.
