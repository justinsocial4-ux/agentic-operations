# Output Template

Read this file before the final report.

## Exact rendering rule

Pass the complete `build_funnel_report` object to `render_funnel_json`. Return that JSON code block once and nothing else. Every numeric output must come from that object and appear only in the one rendered artifact. Never add a prose summary, table, correction, adequacy label, or recomputed value.

The JSON object owns the field structure: funnel reach, transition evidence, minimum-point observation, unavailable analyses, human-review questions, validation checks, action authorization, and boundary. Reach counts appear only in `funnel_reach`; transition rows point to their source stages instead of repeating those counts. The minimum-point receipt points to its transition row instead of repeating its rate, mature count, or interval.
