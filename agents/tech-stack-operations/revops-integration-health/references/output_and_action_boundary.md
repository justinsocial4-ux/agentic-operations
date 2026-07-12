# Output and action boundary

The only lane and integration states are:

- `CONTRACT_OBSERVATION_MATCHED`
- `CONTRACT_OBSERVATION_NOT_MATCHED`
- `EVIDENCE_MISSING`
- `EVIDENCE_CONFLICT`
- `SUPPRESSED`
- `UNAUTHORIZED`

Never add health, availability, outage, recovery, risk, severity, priority, confidence, cause, impact, recommendation, forecast, or compliance prose. Alert, escalation, remediation, system action, downstream decision, and publication flags are always false. Do not send, export, write, schedule, or publish anything.
