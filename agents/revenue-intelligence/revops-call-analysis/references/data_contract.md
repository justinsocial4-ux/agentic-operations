# Call Evidence Data Contract

## Call record

Require:

- `call_id`: stable, non-empty ID;
- `source_platform` and source workspace/tenant ID;
- recording start, timezone, and positive `call_duration_ms`;
- transcript ID/version, language, generation/update time, and extraction cutoff;
- recording/transcript access classification;
- policy receipt IDs from `privacy_and_access.md`;
- redaction and translation status.

## Speaker record

Require a pseudonymous `speaker_id`, mapping status, mapping evidence source, mapping reviewer, and effective time. Keep invitee, participant, speaker track, employee/customer side, CRM contact, and buying role as separate fields.

Do not infer speaker identity or role from voice, title, email domain, company name, speaking time, or transcript content. Shared rooms, brief speakers, silent invitees, dial-ins, mono audio, and name corrections can break naive mappings.

## Segment record

Require:

```json
{
  "segment_id": "s-17",
  "speaker_id": "speaker-2",
  "start_ms": 100000,
  "end_ms": 130000,
  "text": "Exact transcript text",
  "status": "verified"
}
```

Allowed status values are `verified`, `uncertain`, and `redacted`. Timestamps must satisfy `0 <= start_ms < end_ms <= call_duration_ms`. Preserve overlap; do not force simultaneous speech into one speaker.

## Annotation record

Require annotation ID, segment ID, exact quote, speaker ID, approved category ID, taxonomy/rubric ID/version, review status, and reviewer when human verified or rejected. Allowed review states are `MODEL_CANDIDATE`, `HUMAN_VERIFIED`, and `REJECTED`. Redacted segments cannot support annotations; an uncertain segment cannot support `HUMAN_VERIFIED` evidence.

The quote must be an exact substring of the source segment. A paraphrase belongs in interpretation, never in the quote field.

## CRM context

CRM account, opportunity, owner, stage, amount, forecast, outcome, and next-step fields are separate contextual records with their own source, version, and cutoff. Do not overwrite them or claim the transcript independently verifies them.
