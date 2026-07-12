# Routes and coverage

Use only supplied, approved route evidence. Each assigned account/rep pair needs a route ID, approved work-anchor ID, account ID, mode, departure policy, routing preference/policy, source and version, element status, fallback state, duration, distance/unit, visit frequency, and evidence ID.

Do not convert Haversine or straight-line distance to drive time. Do not substitute ZIP centroids for a person's location, invent average speeds, infer visit frequency, or sum separate trips and label them an optimized weekly route.

Multiply supplied per-visit duration/distance only by an approved supplied frequency. Keep source element errors, missing routes, fallback routes, different modes, different departure policies, and different routing policies visible. Incomplete coverage is `SOURCE_REQUIRED`; incompatible policies are `INCOMPARABLE`.

Route summaries include every declared in-scope rep. Under one compatible route policy, a rep with no assigned pairs receives exact zero totals; when the policy is unresolved or incompatible, keep the rep row and emit `null` totals instead of dropping the population. Route totals describe supplied evidence only. They do not prove commute burden, productivity, satisfaction, cost savings, or a preferred territory.
