# Dimension Calculations

Use this file for the detailed field definitions and fallbacks behind the six scores. The main workflow remains the authority if this support file ever conflicts with it.

## Completeness

For each Contact, count populated core fields and divide by the number of required fields. Aggregate the record-level percentages. The pilot lists Email, Phone, FirstName, LastName, Title, Company, and Industry as the core set; confirm the customer's actual required-field policy during preflight.

## Accuracy

Use a 100-200 Contact spot sample.

- Email: validate that the address has a usable format and domain structure.
- Phone: strip formatting and validate length for the expected country.
- Company: compare the Contact company value with `Account.Name` using Jaro-Winkler similarity of at least 0.85.
- If an external truth source is unavailable, use these internal format and consistency checks only, label the result as a proxy, and reduce confidence.

## Duplicates

Use the DQH-01 output when available. Otherwise, match exact email or phone plus the pilot fuzzy-match rule (Jaro-Winkler at least 0.88), then calculate duplicate Contacts divided by total Contacts.

## Freshness

Calculate Contacts with `LastModifiedDate` in the past 90 days divided by total Contacts. If Activity data is unavailable, disclose the limitation instead of inventing engagement recency.

## Consistency

Calculate Contacts linked to a valid Account divided by total Contacts, then flag invalid field types and formats. This is not a substitute for DQH-02 normalization; missing prerequisite work remains visible in the score.

## Connectivity

- Preferred: use customer-provided `email_verified` and `phone_verified` fields when they exist.
- Fallback: count email or phone as reachable only when populated and format-valid.
- Also measure Opportunities linked to a Contact.
- Disclose which path was used and reduce confidence when verification flags are unavailable.

## Deterministic Helper

Map one raw value to the frozen band:

```bash
python3 scripts/crm_health_score.py dimension --dimension completeness --raw 90
```

Calculate the composite only after all six scores exist:

```bash
python3 scripts/crm_health_score.py composite --scores-json '{"completeness":90,"accuracy":80,"duplicates":95,"freshness":65,"consistency":85,"connectivity":80}'
```

Custom weights must include all six dimensions, each weight must be nonnegative, and the sum must equal 1.
