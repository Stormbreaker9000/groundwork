---
id: FR-002
type: functional
tier: solution
title: Erase account and personal data on confirmed deletion, excluding statutory retention records
description: When a data subject's account deletion request has been confirmed via re-authentication, the system shall permanently erase the account and all personal data held for that account within 30 days of confirmation, excluding records subject to statutory retention.
rationale: GDPR Article 17 grants a data subject the right to erasure; permanent self-service deletion discharges this obligation directly. Statutory retention requirements (e.g. for financial and tax records) are separate legal mandates that must be preserved even after erasure, so the erasure behavior must exclude those records rather than delete them outright.
fit_criterion: Following a confirmed deletion, a data audit conducted within 30 days of confirmation finds 0 personal-data records for the account outside the documented statutory-retention set; 100% of authentication attempts against the deleted account fail.
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: '2026-08-26'
traces_from:
- CON-001
- BR-001
- BR-002
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-002 — Erase account and personal data on confirmed deletion, excluding statutory retention records

## Description
When a data subject's account deletion request has been confirmed via
re-authentication, the system shall permanently erase the account and all
personal data held for that account within 30 days of confirmation,
excluding records subject to statutory retention.

## Rationale
GDPR Article 17 grants a data subject the right to erasure; permanent
self-service deletion discharges this obligation directly. Statutory
retention requirements (e.g. for financial and tax records) are separate
legal mandates that must be preserved even after erasure, so the erasure
behavior must exclude those records rather than delete them outright.

## Acceptance Criteria
### AC-1 — Confirmed deletion erases data except retained records
```gherkin
Given a data subject's account deletion request has been confirmed via
  re-authentication
When the system processes the confirmed deletion
Then the account and all of its personal data are permanently erased
  within 30 days of confirmation
And any records within an active statutory retention period, such as
  financial and tax records, are retained in pseudonymised form isolated
  from active personal-data stores
```

### AC-2 — Deleted account can no longer authenticate
```gherkin
Given an account whose deletion has completed
When any authentication attempt is made against that account's identity
Then the authentication attempt fails
```

## Fit Criterion
Following a confirmed deletion, a data audit conducted within 30 days of
confirmation finds 0 personal-data records for the account outside the
documented statutory-retention set; 100% of authentication attempts
against the deleted account fail.
