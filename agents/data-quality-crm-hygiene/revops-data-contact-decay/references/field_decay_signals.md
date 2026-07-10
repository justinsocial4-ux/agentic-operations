# Field Decay Signals

Use this reference when raw CRM and engagement evidence must be converted into the five frozen pilot signal scores. These breakpoints are configurable pilot defaults and should be validated against the customer's sales cycle.

## 1. Email engagement

Consider days since last open plus bounce history.

| Evidence | Default score |
|---|---:|
| Active, under 30 days | 0 |
| 31–90 days | 25 |
| 91–180 days | 60 |
| Over 180 days | 90 |

A hard bounce is a strong risk signal; a soft bounce is weaker. A bounce alone must not erase recent engagement through another channel.

## 2. Phone engagement

| Evidence | Default score |
|---|---:|
| Activity within 120 days | 0 |
| 121–240 days | 35 |
| Over 240 days | 70 |

Use a verified disconnected status only when its source and timestamp are available.

## 3. Title staleness

| Evidence | Default score |
|---|---:|
| Current and accurate | 0 |
| Aging | 30 |
| Very stale | 60 |

The main workflow treats under 12 months as current, 12–24 months as aging, and over 24 months as stale. A promotion is not automatically decay; review context.

## 4. Company departure risk

| Evidence | Default score |
|---|---:|
| Linked to active company | 0 |
| Orphaned or ownership changed | 50 |
| Company acquired or deleted | 85 |

Account unlinking is an inference, not proof that a person left. Record the evidence source.

## 5. Overall engagement

Use the most recent timestamp across email, phone, meeting, and website activity.

| Evidence | Default score |
|---|---:|
| Under 30 days | 0 |
| 31–90 days | 25 |
| 91–180 days | 60 |
| Over 180 days | 90 |

## Missing-channel guard

Do not treat missing data as inactivity. If a channel is unavailable, flag reduced confidence and follow the main skill's degraded-data path. Exact composite scoring requires all five explicit inputs.
