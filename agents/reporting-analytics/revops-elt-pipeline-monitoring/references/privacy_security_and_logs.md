# Privacy, security, and logs

- Pipeline metadata can contain owner emails, user identities, query text, table/field names, URLs, error text, record counts, and infrastructure identifiers.
- Credentials, tokens, service-account keys, connection strings, webhook URLs, and raw logs are never accepted.
- BigQuery job views can expose `user_email` and query text; pseudonymize and minimize upstream before this skill receives evidence.
- Do not claim vault, encryption, retention, regional storage, GDPR, SOX, HIPAA, PCI, or audit compliance from a skill packet.
- Require exact collection, minimization, pseudonymization, recipient, retention, and review receipts.
- This skill does not persist operational logs or create an audit trail; it returns one frozen evidence receipt.
