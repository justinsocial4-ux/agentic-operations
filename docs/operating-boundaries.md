# Operating Boundaries

Agentic Operations is designed around one rule: agents can move fast, but they
do not get unlimited authority.

The system separates work into three levels.

## Level 1: Analyze

Agents can inspect connected data, detect problems, score risk, and produce
structured findings.

Examples:

- detect duplicate CRM records
- score customer renewal risk
- identify stale data pipelines
- surface underused software licenses
- rank events by expected ROI

## Level 2: Recommend

Agents can propose actions with confidence levels, evidence, and tradeoffs.

Examples:

- recommend which duplicate records should be merged
- recommend which accounts need save plays
- recommend which campaigns should be cut or reallocated
- recommend which permissions should be removed
- recommend which vendors should be renegotiated

## Level 3: Execute With Approval

Agents can prepare live-system changes, but business-impacting writes require
human approval.

Approval-gated actions include:

- merging CRM records
- changing user permissions
- updating account health scores
- writing back to Salesforce or HubSpot fields
- sending customer-facing messages
- escalating churn, renewal, or security alerts
- archiving contacts or accounts

## Data Boundary

This repository contains the controlled inspection surface. It excludes:

- real customer exports
- live credentials
- private API keys
- OAuth tokens
- customer-specific reports
- internal deployment configuration

Any implementation that connects these agents to live systems should keep
credentials and customer data outside the repo.

## Design Bias

Agentic Operations favors:

- clear ownership per agent
- evidence-backed recommendations
- confidence thresholds
- escalation paths
- auditability
- human approval before irreversible changes

The point is not to automate blindly. The point is to make operational judgment
faster, more consistent, and easier to inspect.
