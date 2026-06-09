# Repository Structure

The repo is organized by operating domain.

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
    operating-boundaries.md
    repo-structure.md
```

## Why Categories Matter

Revenue operations work breaks down into repeatable control areas: data
foundation, GTM motion, revenue execution, customer lifecycle, and systems
control. The folder structure follows those areas so agents are easy to locate,
combine, and extend.

## Folder Naming

Folder names use stable operating language:

- `data-quality-crm-hygiene`
- `marketing-operations`
- `customer-success-operations`
- `tech-stack-operations`
- `icp-market-strategy`
- `enablement-operations`

Inside each category, each agent keeps a stable slug so downstream references,
documentation, and orchestration can point to the same unit of work over time.
