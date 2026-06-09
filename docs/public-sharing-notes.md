# Public Sharing Notes

This repo is intended to be safe to share publicly as a portfolio and interview
artifact.

## What This Repo Is

- A library of RevOps agent specifications.
- A demonstration of workflow design, business logic, and agentic operating
  patterns.
- A discussion artifact for interviews and technical/product conversations.

## What This Repo Is Not

- It is not a live automation system.
- It does not include customer exports.
- It does not include private credentials.
- It does not run against Salesforce, HubSpot, Slack, Gong, or any other live
  business system by itself.
- It should not make business changes without explicit human approval.

## Data Boundary

The agent files may describe fields that would exist in real systems, such as
CRM records, emails, renewal dates, user roles, or usage data. Those are schema
and workflow examples, not real customer data.

Before publishing or sharing updates, run a safety check for:

- private keys
- API tokens
- real customer names
- real emails
- real exports
- internal-only links

## Human Approval Boundary

For real-world use, any action that changes a live business system should require
human review. Examples:

- merging CRM records
- changing user permissions
- updating account health scores
- writing back to CRM fields
- sending customer-facing messages
- escalating renewal or churn alerts

The safest interpretation is: agents can analyze and recommend; humans approve
business-impacting changes.
