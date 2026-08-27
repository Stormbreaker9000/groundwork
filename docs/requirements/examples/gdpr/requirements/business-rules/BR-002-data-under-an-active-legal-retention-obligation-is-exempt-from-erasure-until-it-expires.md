---
id: BR-002
type: business_rule
tier: business
title: Data under an active legal retention obligation is exempt from erasure until it expires
description: Personal data subject to a legal retention obligation is exempt from deletion in response to an erasure request for as long as its mandated retention period remains active. Once that retention period expires, the data is no longer exempt and must be deleted.
rationale: GDPR Article 17(3) permits an organisation to withhold erasure only to the extent necessary for compliance with a legal obligation that requires processing; the exemption is bounded in time by that obligation and does not authorise indefinite retention once the obligation lapses.
fit_criterion: 100% of erasure operations preserve data that falls within an active legal-retention window at the time of the request, and 100% of that data is deleted within 30 days of its retention window expiring.
priority: must
confidence: high
verification_method: test
status: draft
created_at: '2026-08-26'
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# BR-002 — Data under an active legal retention obligation is exempt from erasure until it expires

## Statement
Personal data subject to a legal retention obligation is exempt from
deletion in response to an erasure request for as long as its mandated
retention period remains active. Once that retention period expires, the
data is no longer exempt and must be deleted.

## Implemented by
FR-002 (Erase account and personal data on confirmed deletion request)
applies this rule by excluding statutory-retention records from the
erasure it performs, and by deleting them once their retention window
expires.

## Rationale
GDPR Article 17(3) permits an organisation to withhold erasure only to
the extent necessary for compliance with a legal obligation that requires
processing; the exemption is bounded in time by that obligation and does
not authorise indefinite retention once the obligation lapses.

## Fit Criterion
100% of erasure operations preserve data that falls within an active
legal-retention window at the time of the request, and 100% of that data
is deleted within 30 days of its retention window expiring.
