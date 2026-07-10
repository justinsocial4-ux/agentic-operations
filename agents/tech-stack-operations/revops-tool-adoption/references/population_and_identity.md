# Population And Identity

Keep these populations distinct:

- paid/committed entitlements;
- provisioned or assigned entitlements;
- eligible assigned human identities;
- active eligible humans under the event policy;
- unassigned entitlements;
- approved exclusions by reason;
- unclassified assigned identities;
- unmatched, unknown, withheld, duplicate, and conflicting identities.

For compatible named-seat models, require `assigned <= paid` and `active_eligible <= eligible_assigned`. The eligible, excluded, unmatched, unknown, withheld, and conflicting assigned partitions must not exceed assigned identities. Any remainder is `unclassified_assigned` and forces `IDENTITY_REVIEW`; do not silently drop it.

For concurrent, pooled, consumption, enterprise-wide, bundled, or capacity pricing, do not force a named-seat hierarchy. State the license model and use its approved denominator or return `POLICY_REQUIRED`.

Identity coverage is a metric, not permission to reveal identity. Opted-out/withheld records remain withheld; do not count them as inactive. Unmatched records remain in coverage counts and never silently disappear.

Group/department comparisons require an approved group taxonomy, identity coverage, minimum-group/suppression policy, and a non-workforce-decision purpose.
