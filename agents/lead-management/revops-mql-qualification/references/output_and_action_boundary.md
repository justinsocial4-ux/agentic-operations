# Output and action boundary

Return one deterministic JSON document ending at `}` with no trailing whitespace. It contains the frozen policy, declared/source populations, population-bound pseudonymization receipt, condition observations, per-record evidence state, and fixed false action flags. A valid review remains human-review evidence; it never authorizes an MQL label, ranking, route, nurture, archive, outreach, enrichment, CRM write, workflow, alert, publication, or downstream decision.

Render exactly once, including the helper's explicit empty terminal line after the closing brace. Do not repeat numeric values in prose, summaries, recommendations, or corrections.
