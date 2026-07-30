# Circular Reference Examples

Use this file when validating proposed parent links or resolving a cycle.

## Frozen Pilot Rule

Walk the proposed parent chain depth-first. Reject the proposal when:

- an Account points to itself
- an Account ID repeats in the ancestry path
- the chain exceeds 10 levels

Do not write any link until the chain passes.

## Examples

### Two-Node Loop

```text
A → B → A
```

Reject. Inspect both existing ParentAccountId values and ask the user which Account is the true root.

### Three-Node Loop

```text
A → B → C → A
```

Reject. Preserve the path in the transaction log and require manual resolution.

### Self-Reference

```text
A → A
```

Reject immediately. Clear or correct the self-reference only after approval.

### Valid Chain

```text
Acme EMEA → Acme Corp → null
```

Pass when neither existing pointer changes the chain and depth stays within 10.

### Depth Violation

A chain with more than 10 parent steps is rejected as likely data corruption even when no Account repeats.

## Resolution Receipt

Record the original path, proposed change, approver, timestamp, and post-change cycle result. Re-run the same check after persistence.
