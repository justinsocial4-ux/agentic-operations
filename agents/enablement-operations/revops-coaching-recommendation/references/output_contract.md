# Output contract

Return the exact helper-rendered JSON and no surrounding prose. The output includes policy and source receipts, the complete population receipt, one result per declared record, one state summary, limitations, and permanent no-authority flags.

Every calculated count appears once in `state_summary`. Sorting and rendering are deterministic. The final response ends with the helper's explicit empty terminal line.
