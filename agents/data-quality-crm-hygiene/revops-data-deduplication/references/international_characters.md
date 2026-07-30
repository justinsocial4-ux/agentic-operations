# International Characters

Read this file when names contain accents, non-Latin scripts, or transliterated variants.

## Guardrails

- Preserve the original value for display and audit evidence.
- Normalize Unicode consistently before comparison.
- Compare accent-folded or transliterated forms only as additional signals, never as proof of identity.
- Require a second strong signal such as exact phone, verified email, or verified company context before proposing a merge.
- Route cross-script matches and ambiguous transliterations to manual review.

Examples such as `José`/`Jose` or `Müller`/`Mueller` can be legitimate variants, but they can also identify different people. The pilot's confidence formula and approval tiers still govern the decision.
