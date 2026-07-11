# Access Rules and Exceptions

Read before comparing entitlements or temporary access.

- Each rule declares exact required, allowed, and prohibited entitlement IDs in the frozen namespace/version.
- Required must be a subset of allowed. Allowed and prohibited sets must not overlap.
- Compare supplied observed IDs only. Do not expand names, infer dependencies, or invent permission equivalence.
- Preserve required-missing, prohibited-observed, outside-allowed, and unknown IDs separately.
- A temporary exception requires account/entitlement IDs, approved state, begin/expiry times, approval receipt, and registered evidence.
- An active exception documents approval context; it does not change the observed entitlement or certify safety. Expired/revoked exceptions remain visible.
