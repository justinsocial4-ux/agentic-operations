# Action Handoff

Keep three decisions separate:

1. event evidence qualifies for a customer-defined human-review lane;
2. the person/channel passes current contactability and ownership gates;
3. a named human approves one exact downstream action.

This skill performs decision 1 and reports evidence for 2 and 3. It does not create CRM records, tasks, activities, audiences, tags, alerts, or messages.

Send sequence-selection work to `revops-sequence-enrollment` with the current contactability, suppression, owner, enrollment, frequency, mapping, library, and approval receipt. Recheck every mutable gate immediately before execution.
