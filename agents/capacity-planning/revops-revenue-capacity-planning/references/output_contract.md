# Output Contract

Return the exact JSON bytes produced by `render_review_output`. Do not add headings, Markdown, commentary, duplicated numbers, summaries, or corrections.

The document contains one policy receipt and a sorted list of scenario receipts. Each scenario has:

- `scenario_id`
- `review_state`
- `action_authorized`
- one `input_receipt` containing each supplied numeric fact once
- one `calculation_receipt` containing each derived numeric fact once
- source and population lineage
- `limitations`

The helper sorts keys and scenarios deterministically. It emits decimal values as plain strings, never JSON numbers. It emits no counts, percentages, confidence, adequacy labels, timestamps created by the model, advice, or natural-language numeric restatement.

`HUMAN_REVIEW_REQUIRED` does not mean approved, adequate, correct for a business decision, or likely to occur. It means only that arithmetic completed and no action is authorized.
