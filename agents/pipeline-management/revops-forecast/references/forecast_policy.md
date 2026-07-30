# Forecast Policy

Read before inclusion, category mapping, amount selection, or currency conversion.

The approved policy must define forecast type, period, cutoff, included pipelines/scopes, forecast unit, amount field, splits, products, category IDs/order, closed-won treatment, close-date rule, null/zero/negative handling, reporting currency, dated FX source, and manual-adjustment treatment.

Category names are not enough. HubSpot categories are configurable and can be manually changed. Salesforce supports multiple forecast types, custom dates/measures, product families, groups, splits, and territories. Preserve the configured semantics.

Never auto-map categories or assume exclusive categories are cumulative. If the org wants cumulative rollups, define the exact included categories mechanically.
