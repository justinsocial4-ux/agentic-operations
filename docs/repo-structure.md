# Repository Structure

The repo is organized by business problem, not by build order.

```text
agentic-operations/
  README.md
  agents/
    customer-success-operations/
    data-quality-crm-hygiene/
    enablement-operations/
    event-marketing/
    icp-market-strategy/
    lead-management/
    marketing-operations/
    outbound-orchestration/
    reporting-analytics/
    revenue-intelligence/
    tech-stack-operations/
  docs/
    agent-map.md
    public-sharing-notes.md
    repo-structure.md
```

## Why Categories Matter

The original source separated agents by maturity:

- first proof-of-concept agents
- agents ready for testing

That is useful internally, but less useful for an interview audience.

This public repo groups agents by the business problem they solve. That makes it
easier for a reader to scan the library and understand the operating system.

## Folder Naming

Folder names use simple, stable business language:

- `data-quality-crm-hygiene`
- `marketing-operations`
- `customer-success-operations`
- `tech-stack-operations`
- `icp-market-strategy`
- `enablement-operations`

Inside each category, each agent keeps its original slug so the design history
is still traceable.
