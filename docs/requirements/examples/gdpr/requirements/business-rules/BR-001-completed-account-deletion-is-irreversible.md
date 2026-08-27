---
id: BR-001
type: business_rule
tier: business
title: Completed account deletion is irreversible
description: Once an account deletion has completed, it may not be undone or restored by any means. No administrative override, support process, or automated recovery path may bring back an erased account or its erased personal data.
rationale: Irreversibility is what makes an erasure operation actually discharge the GDPR Article 17 obligation rather than merely hiding data that could later resurface; offering any restore path would reintroduce the liability the deletion was meant to remove and would misrepresent to the data subject that their data is truly gone.
fit_criterion: For 100% of accounts whose deletion has completed, no operation exposed to any actor — including support staff, operators, or automated jobs — restores the account or its erased personal data; any attempted restore request is rejected.
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

# BR-001 — Completed account deletion is irreversible

## Statement
Once an account deletion has completed, it may not be undone or restored
by any means. No administrative override, support process, or automated
recovery path may bring back an erased account or its erased personal data.

## Implemented by
FR-002 (Erase account and personal data on confirmed deletion) enforces
this rule by performing erasure as a one-way operation with no restore
path exposed anywhere in the system.

## Rationale
Irreversibility is what makes an erasure operation actually discharge the
GDPR Article 17 obligation rather than merely hiding data that could later
resurface; offering any restore path would reintroduce the liability the
deletion was meant to remove and would misrepresent to the data subject
that their data is truly gone.

## Fit Criterion
For 100% of accounts whose deletion has completed, no operation exposed to
any actor — including support staff, operators, or automated jobs —
restores the account or its erased personal data; any attempted restore
request is rejected.
