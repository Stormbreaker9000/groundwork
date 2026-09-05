<!--
  GENERATED FILE — do not edit.
  Source: docs/requirements/examples/gdpr/requirements/business-rules/
  Regenerate: python3 site/scripts/export_examples.py
-->

# Business rules

The 2 business rules from the `gdpr` worked example, exactly as the pipeline wrote them.

## BR-001 — Completed account deletion is irreversible [#br-001]

| Field | Value |
| --- | --- |
| Type | business_rule |
| Tier | business |
| Priority | must |
| Status | draft |
| Confidence | high |
| Verification | test |

### Statement
Once an account deletion has completed, it may not be undone or restored
by any means. No administrative override, support process, or automated
recovery path may bring back an erased account or its erased personal data.

### Implemented by
FR-002 (Erase account and personal data on confirmed deletion request)
enforces this rule by performing erasure as a one-way operation with no
restore path exposed anywhere in the system.

### Rationale
Irreversibility is what makes an erasure operation actually discharge the
GDPR Article 17 obligation rather than merely hiding data that could later
resurface; offering any restore path would reintroduce the liability the
deletion was meant to remove and would misrepresent to the data subject
that their data is truly gone.

### Fit Criterion
For 100% of accounts whose deletion has completed, no operation exposed to
any actor — including support staff, operators, or automated jobs —
restores the account or its erased personal data; any attempted restore
request is rejected.

## BR-002 — Data under an active legal retention obligation is exempt from erasure until it expires [#br-002]

| Field | Value |
| --- | --- |
| Type | business_rule |
| Tier | business |
| Priority | must |
| Status | draft |
| Confidence | high |
| Verification | test |

### Statement
Personal data subject to a legal retention obligation is exempt from
deletion in response to an erasure request for as long as its mandated
retention period remains active. Once that retention period expires, the
data is no longer exempt and must be deleted.

### Implemented by
FR-002 (Erase account and personal data on confirmed deletion request)
applies this rule by excluding statutory-retention records from the
erasure it performs, and by deleting them once their retention window
expires.

### Rationale
GDPR Article 17(3) permits an organisation to withhold erasure only to
the extent necessary for compliance with a legal obligation that requires
processing; the exemption is bounded in time by that obligation and does
not authorise indefinite retention once the obligation lapses.

### Fit Criterion
100% of erasure operations preserve data that falls within an active
legal-retention window at the time of the request, and 100% of that data
is deleted within 30 days of its retention window expiring.
