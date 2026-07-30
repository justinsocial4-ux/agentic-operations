# Orphan Remediation Guide

Use this file after candidate scoring and tree construction.

## Orphan Signals

Flag an Account when any of these apply:

- the name contains a subsidiary indicator but ParentAccountId is empty
- ParentAccountId points to an Account that does not exist
- Contact email domains suggest another Account family
- the Account is unusually small and has no parent

These are review signals, not automatic proof of a parent.

## Classification

- **Review:** a plausible parent exists but confidence is below the configured approval threshold.
- **Research:** no defensible parent exists in current data.
- **Accept as root:** the customer confirms the Account is independent.

## Checklist

1. Preserve the Account ID, current parent, ARR, owner, and evidence signals.
2. Search only approved CRM/export data unless the user authorizes external research.
3. If the parent is missing, recommend creating a verified parent record or accepting the Account as a root.
4. If multiple parents are plausible, keep all candidates in manual review; v1 supports one parent.
5. If a proposed repair creates a cycle or exceeds 10 levels, reject it.
6. Require explicit approval before writing ParentAccountId or a HubSpot parent association.
7. Re-run cycle detection and orphan counts after persistence.

## Output Fields

Include Account ID/name, current parent state, candidate parent(s), confidence, supporting signals, missing evidence, severity by revenue, recommended action, owner, and approval status.
