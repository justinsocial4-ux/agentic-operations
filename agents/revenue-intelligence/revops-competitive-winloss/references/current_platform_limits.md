# Current Platform Limits

HubSpot documents `Closed lost reason`, `Closed won reason`, deal stage, and platform-calculated closed-state fields as deal properties. Its close date can be automatically changed when a deal moves between closed stages. Treat each as a platform observation with the customer's exact configuration and timestamp semantics, not as causal truth or original event time.

Salesforce opportunity reporting uses customer-configured stage types, including custom stage names. Bind the exact org, schema, and active stage mapping. Do not assume the literal text `Closed Lost` is universal.

External pages, reviews, postings, announcements, and social records are mutable source observations. Require approved access and exact capture provenance. Never infer competitor strategy, pricing, product availability, hiring intent, or impact.

Sources checked 2026-07-11:
- https://knowledge.hubspot.com/properties/hubspots-default-deal-properties
- https://help.salesforce.com/s/articleView?id=000385922&language=en_US&type=1
- https://airc.nist.gov/airmf-resources/airmf/5-sec-core/
- https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/purpose-limitation
- https://www.ftc.gov/policy/advocacy-research/tech-at-ftc/2024/01/ai-companies-uphold-your-privacy-confidentiality-commitments
