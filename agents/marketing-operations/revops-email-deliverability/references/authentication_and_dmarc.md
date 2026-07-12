# Authentication and DMARC

- SPF, DKIM, and DMARC are distinct mechanisms.
- DMARC pass requires at least one authenticated identifier aligned with the Author Domain; relaxed and strict alignment are different states.
- A DNS record's presence does not prove that a particular message authenticated.
- An authentication ratio is source-, population-, and time-bound.
- `p=none` is monitoring mode; changing to enforcement requires domain-owner analysis of aggregate reports and authorized mail sources.
- Authentication evidence does not by itself prove inbox placement, reputation, wanted mail, legal compliance, root cause, or a safe DNS change.
- This skill never edits or recommends DNS records.
