# Measurement Contracts

Treat spend, impressions, clicks, and conversion credit as separate declared constructs. Require exact definition IDs and an amount basis. Conversion evidence additionally requires an action ID, action category, counting mode, attribution model, attribution window, and date basis.

Use Decimal strings. Sum raw values first, then calculate CTR as clicks divided by impressions, CPC as spend divided by clicks, and cost per conversion as spend divided by conversions. A zero denominator produces `null`. Do not substitute, round inputs, or relabel conversion credit as leads, customers, pipeline, or revenue.
