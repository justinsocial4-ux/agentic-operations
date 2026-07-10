# Exact output contract

Return `render_review_output(review_market(...))` byte for byte. The first response character is the opening backtick; the last response characters are the exact boundary.

The JSON contains policy, evidence register, one result per segment, exception queue, conditional aggregation, approval/action state, and boundary. Do not add a headline, table, summary, recommendation, rounded display value, correction, or duplicate receipt.

Every helper field renders once at its canonical path. Segment source and price inputs live inside their result; aggregate values are new calculations and appear only when verified-disjoint aggregation is allowed.
