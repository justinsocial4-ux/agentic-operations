# Evidence Lanes

Keep these lanes independent:

- **Usage:** approved account grouping, metric definition/version, numerator/denominator basis, population, windows, timezone, and supplied values.
- **Support:** exact structured ticket population, statuses, occurrence timestamps, counts, and durations. No ticket text or sentiment inference.
- **Survey:** invited and responding populations, exact question/scale/version, and response timestamp. Nonresponse is unknown.
- **Engagement:** only customer-defined activity occurrence and association semantics. Record creation, tasks, assignment, and email-pixel loading do not inherently mean engagement.
- **Contract:** exact contract ID/version, recorded date/basis, and structured auto-renew field. No legal interpretation or estimated date.
- **Billing:** exact currency, basis, period, structured status, and occurrence time. No hardship, willingness-to-pay, or revenue-recognition inference.
- **Outcome:** only an actually observed event under an approved outcome definition and window. Do not infer cause or future outcome.

Never combine lanes into a score, probability, tier, ranking, priority, forecast, causal story, or intervention plan.
