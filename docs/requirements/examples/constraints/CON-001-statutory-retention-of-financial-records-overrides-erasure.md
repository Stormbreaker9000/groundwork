---
id: CON-001
type: constraint
tier: business
title: Statutory retention of financial records overrides erasure
description: The system shall retain financial and tax records for the statutory retention period mandated by applicable law even when the associated user account is erased, storing them in pseudonymised form isolated from active personal-data stores.
rationale: Tax and financial-reporting law imposes a minimum retention period that supersedes the GDPR right to erasure for those specific records; deleting them to satisfy an erasure request would itself be unlawful.
fit_criterion: For every deleted account that had financial records within the statutory window, those records remain retrievable in pseudonymised form for the full retention period, and a compliance inspection finds 0 unlawful early deletions.
priority: must
confidence: high
verification_method: inspection
status: draft
created_at: 2026-06-26
traces_from: []
traces_to:
  design: [FR-002]
  tests: []
  code: []
scope: project
parent_scope: null
---

# CON-001 — Statutory retention of financial records overrides erasure

## Statement
The system shall retain financial and tax records for the statutory retention
period mandated by applicable law (e.g. 6–10 years), even when the associated user
account is erased, storing them in pseudonymised form isolated from active
personal-data stores.

## Category
regulatory

## Bounds / Implemented by
Bounds the erasure behavior of FR-002 by carving the legally retained financial
records out of the data subject to permanent deletion.

## Rationale
Tax and financial-reporting law imposes a minimum retention period that supersedes
the GDPR right to erasure for those specific records; deleting them to satisfy an
erasure request would itself be unlawful.

## Fit Criterion
For every deleted account that had financial records within the statutory window,
those records remain retrievable in pseudonymised form for the full retention
period, and a compliance inspection finds 0 unlawful early deletions.
