# Descriptive Metrics And Limits

## Permitted calculations

With valid timestamped segments, calculate:

- union transcript coverage = unique covered milliseconds / call duration;
- uncovered, overlapping, uncertain, and redacted milliseconds;
- milliseconds per approved speaker;
- speaker share of total segment time;
- exact annotation counts by approved category and review state.

Use `scripts/call_evidence.py`. Report raw numerators, denominators, units, and overlap behavior.

## Interpretation boundaries

Speaker share is not listening quality. Question count is not discovery quality. Mention count is not urgency. Category frequency is not causal impact. Transcript coverage is not transcription accuracy. A model-generated “confidence” number is not validation.

Do not supply universal good/bad thresholds. A customer benchmark requires a versioned metric definition, comparable call cohort, language/coverage policy, observation period, exclusions, peer count, and approved interpretation. Otherwise return `COMPARABILITY_REQUIRED`.

## Multi-call comparisons

Before comparing calls, align source/platform, transcript generation, language/translation, call type, duration scope, speaker mapping, taxonomy/rubric, coverage, redaction, cutoff, and metric definitions. Show missingness and sample count. Do not call a cohort small/large, significant, representative, or causal without an approved design and test.

Do not rank reps, infer improvement, or attribute outcomes to call behavior from descriptive differences.
