---
id: FR-002
type: functional
tier: solution
title: Erase account and personal data on confirmed deletion request
description: When a data subject's deletion request has been confirmed, the system shall permanently erase all personal data associated with the account within 30 days of confirmation, excluding records subject to a statutory retention obligation.
rationale: Discharges the GDPR Article 17 right to erasure directly through self-service, without requiring administrative or support intervention; success is measured by a post-deletion audit finding zero personal-data records outside the documented statutory-retention set.
fit_criterion: For 100% of confirmed deletion requests sampled in acceptance testing, a data audit conducted on or before day 30 after confirmation finds 0 personal-data records for the account outside the documented statutory-retention set, and 100% of authentication attempts against the deleted account fail.
priority: must
confidence: low
verification_method: test
ears_pattern: event
status: draft
created_at: '2026-08-26'
traces_from:
- BR-001
- BR-002
- CON-001
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-002 — Erase account and personal data on confirmed deletion request

## Description
When a data subject's deletion request has been confirmed, the system shall
permanently erase all personal data associated with the account within 30 days
of confirmation, excluding records subject to a statutory retention obligation.

## Rationale
Discharges the GDPR Article 17 right to erasure directly through self-service,
without requiring administrative or support intervention. Success is measured
by a post-deletion audit finding zero personal-data records outside the
documented statutory-retention set, and by the account becoming fully
inaccessible.

## Acceptance Criteria
### AC-1 — Successful erasure excludes statutory-retention records
```gherkin
Given an authenticated data subject has confirmed a deletion request for their account
And the account has financial/tax records within their statutory retention period
When 30 days have elapsed since the deletion request was confirmed
Then all personal data associated with the account is erased from active personal-data stores
And the financial/tax records remain preserved in pseudonymised form, isolated from active personal-data stores
And a data audit of the account finds 0 personal-data records outside the documented statutory-retention set
```

### AC-2 — Authentication fails against a deleted account
```gherkin
Given an authenticated data subject's deletion request has completed erasure
When any party attempts to authenticate using the deleted account's credentials
Then the authentication attempt fails
And no administrative or automated path restores access to the erased account
```

## Fit Criterion
For 100% of confirmed deletion requests sampled in acceptance testing, a data
audit conducted on or before day 30 after confirmation finds 0 personal-data
records for the account outside the documented statutory-retention set, and
100% of authentication attempts against the deleted account fail.
