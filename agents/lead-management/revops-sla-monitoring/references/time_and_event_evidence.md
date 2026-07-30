# Time and event evidence

Require stable event ID, record ID, approved event type, occurrence timestamp, record-creation timestamp, association evidence, source/version, and evidence ID.

Use occurrence time for SLA evaluation only when the source contract defines it. A CRM activity object's creation time can differ from when the call, email, or meeting occurred. Never treat object existence, login, background sync, task creation, or note creation as human response unless policy explicitly qualifies that event.

Reject naive timestamps. Normalize offset-aware timestamps to UTC. Preserve events before the SLA start, events tied to unknown records, and events with unregistered provenance in conflict queues; never silently drop them.
