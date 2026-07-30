# Input And Lineage

Accept complete customer-supplied structured exports only. Each contract names one source/version, schema/version, authorization receipt/window, query receipt, complete-page receipt, reporting level, local period/timezone, freshness time, and measurement basis.

Each population receipt must declare exactly the row IDs supplied for that contract. Each row belongs to one contract and one population. Duplicate, undeclared, extra, stale, future, partially paged, or unauthorized evidence fails closed.
