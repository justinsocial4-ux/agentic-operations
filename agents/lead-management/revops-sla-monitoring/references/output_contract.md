# Output contract

Run the deterministic helper and pass its complete result to `render_report_json`.

Return exactly:

1. one JSON code block containing the verbatim renderer output; and
2. `NO ALERT / NO ESCALATION / NO CRM OR WORKFORCE ACTION`.

Do not add a numeric headline, summary, table, list, note, calculation, or correction outside the JSON. Do not rename, reorder, abbreviate, omit, or hand-add fields.

R1: do not use `small`, `large`, `enough`, `limited`, or `insufficient` unless an approved bundled rule numerically defines the label. R2: every output number comes from the helper and is printed in the JSON once; a wrong value requires fixing inputs/code and rerunning, never inline self-correction.
