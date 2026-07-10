# Calendars and due times

Use direct UTC addition only for an approved continuous clock expressed in exact integer seconds.

For business hours, service hours, holidays, shifts, pauses, regional calendars, or daylight-saving policies, require a supplied due-time receipt containing record ID, due time, calendar ID/version, calculator ID, computation time, and evidence ID. Do not approximate calendar logic in prose or replace it with elapsed wall time.

The helper validates supplied calendar receipts but does not invent holidays, working days, locale rules, pause intervals, or grace periods.
