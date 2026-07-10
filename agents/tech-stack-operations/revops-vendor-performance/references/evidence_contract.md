# Evidence Contract

## Minimum review identity

Require `vendor_id`, legal entity, `service_id`, product/service name, contract ID/version, service tier, owner, evaluation start/end, cutoff, timezone, extraction time, and intended use.

## Evidence record

Each evidence item needs:

- stable `evidence_id` and source record ID;
- lane: `CONTRACT`, `SERVICE`, `SUPPORT`, `COMMITMENTS`, `ADOPTION`, `COST`, or `SECURITY`;
- evidence kind: `CONTRACTUAL`, `CUSTOMER_OBSERVED`, `VENDOR_ATTESTED`, `INDEPENDENT`, or `UNATTRIBUTED`;
- source system/file, source owner, version/revision, extraction time, and immutable locator/hash where available;
- observation period, timezone, service/region/severity scope, unit, and coverage;
- raw value or faithful excerpt pointer, transformation, exclusions, and known limits;
- access/privacy classification and retention rule.

`UNATTRIBUTED` evidence may appear in the gap register but cannot support a requirement state.

## Provenance precedence

Do not invent a universal hierarchy. Apply only the customer's approved precedence policy. Signed terms define contractual obligations; they do not automatically prove observed performance. Customer telemetry can support an observation; it does not rewrite the contract. Vendor attestations can support what the vendor stated; they do not prove independence.

## Frozen inputs

Hash or version every input snapshot. Assign a review ID and output version. A correction creates a superseding receipt that names the earlier receipt and change reason.

## Privacy

Prefer aggregate counts and pseudonymous case/user IDs. Exclude case bodies, names, email, phone, free text, credentials, and secrets unless specifically authorized and necessary. Record access and retention constraints.
