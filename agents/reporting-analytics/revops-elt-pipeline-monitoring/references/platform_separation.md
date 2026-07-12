# Platform separation

Fivetran connections, dbt freshness snapshots, dbt job/test artifacts, Snowflake metadata, BigQuery job metadata, Workato jobs, and customer SQL jobs have different states, timestamps, permissions, delays, scopes, and definitions.

- Keep every platform/source/definition/rule combination in its own lane.
- Never convert a platform code into a universal state.
- Never average lane conditions or create a stack score.
- Never substitute warehouse metadata for a connector result, a connector result for a dbt result, or one account/region/role scope for another.
- Never relax a customer rule because another lane is missing or reports a different condition.
- Permission-scoped absence is not object absence; delayed metadata is not current evidence.
