# Identity And Privacy

The helper accepts stable event IDs and pseudonymous organization IDs only. Names, emails, phones, job titles, social URLs, raw domains, free text, and attendee-level records are prohibited.

Organization identity must be resolved by the customer's approved source-system rule and carry a receipt. Salesforce and HubSpot matching or association features are configurable mechanisms; they do not prove that an external roster and CRM record represent the same organization.

Ambiguous, conflicting, unknown, or unapproved matches remain `IDENTITY_REVIEW`. Do not lower a threshold, choose among duplicate domains, or use a language model to force a match.
