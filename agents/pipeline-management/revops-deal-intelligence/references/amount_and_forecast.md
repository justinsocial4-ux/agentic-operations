# Amount And Forecast

Require one customer-approved CRM amount basis, reporting currency, and null/zero/negative policy. Preserve exact non-negative Decimal strings. Never replace null with zero or sum mixed currencies.

Deal amount is pipeline exposure under the named CRM basis. It is not recognized revenue, cash, expected value, loss, or recoverable value.

This helper does not calculate close probability, probability-weighted amount, forecast, confidence, calibration, revenue at risk, ROI, or future outcome. Those require separate frozen forecast/model and finance contracts.
