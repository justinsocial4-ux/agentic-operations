# Freshness, jobs, and schema

- dbt freshness is defined by a customer-configured loaded-at field/query or supported warehouse metadata plus `warn_after` and/or `error_after` criteria.
- If neither dbt criterion is configured, dbt does not calculate freshness snapshots for that source.
- A Fivetran 2xx response can mean a request was accepted; confirm asynchronous outcomes from the documented state field and frozen observation.
- Fivetran setup, sync, and update states are different fields; do not merge them.
- Snowflake Information Schema visibility depends on current-role privileges and can be inconsistent during concurrent DDL. Account Usage views have view-specific latency.
- BigQuery Information Schema is region- and permission-scoped and may include recently deleted-resource metadata.
- A timestamp measures the frozen definition only. It does not prove correctness, completeness, downstream impact, or root cause.
- A schema snapshot difference does not prove corruption or justify pausing transformations.
