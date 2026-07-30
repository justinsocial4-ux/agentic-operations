# Contract observations

The helper does not parse or interpret documents. Accept only structured observations produced under a customer-approved method and tied to document ID, exact version, SHA-256, page/section/span locator, observation key, timestamp, source/schema, and deal ID.

Require receipts that the reviewed document is complete and that amendments and precedence relationships are complete. `OBSERVED` means the supplied reviewer/extractor recorded the policy key at the locator. `NOT_OBSERVED` means only that the approved observation process did not record it. Neither state establishes legal effect.

Missing pages, versions, hashes, locators, amendments, precedence, or conflicting observations produce `DOCUMENT_REVIEW_REQUIRED` or `EVIDENCE_CONFLICT`. Do not draft replacement language or advise negotiation.
