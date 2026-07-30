# Outbound Performance Data Contract

Read this before querying a platform or accepting an export.

## Touch ledger

Require or explicitly mark missing:

- source platform, workspace, touch ID, sequence ID, step ID, variant ID;
- rep ID, recipient/contact ID, account ID;
- original subject and body/CTA variant identifiers;
- send timestamp UTC, recipient timezone, recipient-local timestamp;
- delivery state: sent, delivered, hard bounce, soft bounce;
- reply state and timestamp;
- reply class: positive, referral, objection, not-now, unsubscribe, out-of-office, negative, unknown;
- experiment ID and assigned variant;
- campaign, persona, territory, list source, and segment;
- explicit meeting/opportunity link IDs and timestamps.

## Denominator contract

- Delivery rate uses sent attempts.
- Reply and positive-reply rates use delivered attempts.
- Bounce rate uses sent attempts.
- Meeting rates must name whether the numerator is explicitly linked or heuristically associated.

Do not merge platform definitions without a mapping receipt. Preserve source values.

## Deduplication

Use source touch ID as the primary key. If unavailable, document a composite key such as platform + sequence + recipient + step + send timestamp. Report collisions and keep reruns from double counting.

## Coverage receipt

For each required field, show valid, missing, invalid, and excluded counts. Use `AVAILABLE`, `DEGRADED`, `UNKNOWN`, or `NOT_APPLICABLE`. Never encode unknown as zero.
