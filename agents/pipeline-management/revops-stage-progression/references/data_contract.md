# Data Contract

Require stable deal ID, pipeline ID, stable internal stage ID, stage label, entered-at timestamp, event/source ID, extraction time, and cutoff. Optional amount requires amount basis and currency.

Current stage and record modification time do not reconstruct history. Preserve repeated stage entries as distinct episodes. Quarantine duplicate timestamps, unknown stage IDs, impossible post-cutoff events, pipeline changes without policy, and conflicting histories.

Report deal coverage, event coverage, history horizon, unknown-stage rows, duplicates, exclusions, and current-entry coverage. Missing is not zero.
