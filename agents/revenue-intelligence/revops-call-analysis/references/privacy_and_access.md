# Privacy And Access Gate

## Required receipt

Before retrieval, record:

- recording-policy ID/version, owner, effective date, and evidence location;
- approved analysis purpose and intended audience;
- requester access grant and source-system permission;
- included call IDs and cutoff;
- redaction/minimization policy;
- retention/deletion policy for source, working data, and output;
- approved downstream uses and prohibited uses;
- handling rule for data-subject or employee requests.

`POLICY_EVIDENCE_PRESENT` means the required receipt fields exist. It does **not** mean the activity is legally compliant. Send jurisdiction, consent, labor, employment, sector, or contractual questions to the customer's privacy/legal owner.

## Minimize before analysis

Use pseudonymous IDs. Remove unrelated conversation, credentials, payment data, health information, protected-trait data, personal contact details, private family matters, and any other content outside the approved purpose. Preserve a redaction marker and time span so missing content is not mistaken for silence.

Do not copy a full transcript into a report when a short exact evidence window is sufficient. Do not expose a recording URL unless the audience already has source-system access.

## Access is not transferable

The ability to view a call does not automatically authorize downloading, processing in another model, quoting to another audience, posting to chat, adding to CRM, retaining a derivative, or using it in an employment/deal decision. Check each proposed use separately.

Stop with:

- `ACCESS_DENIED` when requester or audience access is absent;
- `SENSITIVE_SCOPE_REVIEW` when minimization cannot safely separate in-scope evidence;
- `POLICY_EVIDENCE_REQUIRED` when a required policy receipt is missing.
