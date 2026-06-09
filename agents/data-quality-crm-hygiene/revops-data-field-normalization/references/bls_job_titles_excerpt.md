# BLS Standard Occupational Classification (SOC) — Job Title Taxonomy Excerpt

**Source:** U.S. Bureau of Labor Statistics, Standard Occupational Classification System  
**Version:** 2018 (used as canonical reference for normalization)  
**Total titles in full taxonomy:** 900+ standard occupational categories

---

## Sales & Account Management (Relevant Sample)

| SOC Code | Standard Title | Common Variants Mapped |
|----------|---|---|
| 41-2011 | Cashiers | Cashier, POS operator, checkout clerk |
| 41-2021 | Counter and Rental Clerks | Counter clerk, rental agent, car rental agent |
| 41-2022 | Parts Salespersons | Parts sales, parts manager, parts specialist |
| 41-3011 | Advertising Sales Agents | Ad sales, advertising rep, media seller |
| 41-3021 | Insurance Sales Agents | Insurance agent, insurance seller, policy agent |
| 41-3031 | Securities, Commodities, and Financial Services Sales Agents | Broker, investment advisor, financial advisor |
| 41-3099 | Sales and Related Workers, All Other | Sales specialist, sales professional |
| 41-4011 | Sales Managers | Sales director, VP of Sales, Director of Sales, Sales head |
| 41-4012 | Sales Representatives, Wholesale and Manufacturing, Technical and Scientific Products | Sales engineer, technical sales, solutions engineer |
| 41-4013 | Sales Representatives, Wholesale and Manufacturing, Except Technical and Scientific Products | Account executive, enterprise sales, sales rep |
| **43-4051** | **Customer Service Representatives** | **Support specialist, customer support, help desk, customer care** |
| 41-9041 | Telemarketers | Telemarketer, phone sales, outbound caller |

---

## Account/Customer Success (Relevant Sample)

| SOC Code | Standard Title | Common Variants Mapped |
|----------|---|---|
| 11-1011 | Chief Executives | CEO, President, Chief executive officer |
| 11-1021 | General and Operations Managers | COO, operations director, general manager, GM |
| 11-2011 | Accountants and Auditors | Accountant, auditor, CPA |
| 13-1011 | Agents and Business Managers of Artists, Performers, and Athletes | Talent agent, artist manager, agent |
| **11-3021** | **Computer and Information Systems Managers** | **IT director, director of IT, CTO (if engineering-focused), technology director** |
| **11-3031** | **Financial Managers** | **CFO, controller, treasurer, finance director** |
| **13-1161** | **Customer Service Managers** | **CS manager, customer success manager, CSM, support manager, customer care manager** |

---

## Executive & Management Hierarchy

| SOC Code | Standard Title | Seniority Level | Common Variants |
|----------|---|---|---|
| 11-1000s | Chief executives and managers | C-level | C-suite, executive, chief, officer |
| 11-2000s | Operations & HR managers | Director | Director of [function], Head of [function], VP of [function] |
| 13-1000s | Business & financial specialists | Senior Manager | Manager of [function], lead, senior [role] |
| 41-1000s | Supervisors in sales | Manager | Sales manager, team lead, supervisor, team manager |
| 41-2000s | Retail & wholesale | Frontline | Associate, representative, agent, specialist |

---

## Title Normalization Mapping Examples

**How the engine maps variants to canonical BLS titles:**

```
"VP of Sales" → 41-4011 (Sales Managers)
  Reasoning: VP = Vice President = management level; 
             "of Sales" indicates sales function
  Confidence: 0.95 (high — exact phrase match to common executive title pattern)

"Account Exec" → 41-4013 (Sales Representatives, Wholesale/Manufacturing, Non-Tech)
  Reasoning: Account = customer/account relationship; Exec = executive position
             (high-touch sales role, not support)
  Confidence: 0.89 (medium-high — abbreviation + role type)

"AE" → 41-4013 (Sales Representatives, Wholesale/Manufacturing, Non-Tech)
  Reasoning: AE commonly stands for Account Executive in SaaS/tech contexts
  Confidence: 0.75 (medium-low — very short, context-dependent)

"Sales" → [AMBIGUOUS: could be 41-4013 or 41-2022 or 41-4011]
  Reasoning: Single word insufficient for mapping to specific title
  Confidence: <0.70 (too low — requires context, manual review)

"Sales Engineer" → 41-4012 (Sales Reps, Tech & Scientific Products)
  Reasoning: "Engineer" in title + sales context = technical sales specialist
  Confidence: 0.98 (very high — exact standard title)

"CSM" → 13-1161 (Customer Service Managers) [if manager-level] 
         or 43-4051 (Customer Service Reps) [if IC-level]
  Reasoning: CSM = Customer Success Manager; context determines seniority
  Confidence: 0.80 (medium — depends on account size & org structure)
```

---

## Notes on International & Emerging Roles

**Limitation:** BLS taxonomy was published in 2018. Emerging job titles popular in SaaS/tech (e.g., "Growth Manager," "DevOps Engineer," "Prompt Engineer," "Product Operations Manager") may not have exact matches.

**Normalization strategy for emerging roles:**
1. Map to closest parent category (e.g., "Growth Manager" → Sales Manager or Marketing Manager)
2. Allow customer custom mappings (e.g., "In our org, 'Growth Manager' = Account Executive")
3. Flag low-confidence matches for manual review

**International considerations:**
- This excerpt uses U.S. BLS taxonomy (standard in North America)
- For international companies, consider ISCO (International Standard Classification of Occupations) from ILO
- Agent supports both; customer can choose canonical source at runtime
