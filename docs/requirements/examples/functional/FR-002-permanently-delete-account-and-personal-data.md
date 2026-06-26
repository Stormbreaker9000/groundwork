---
id: FR-002
type: functional
tier: solution
title: Permanently delete account and personal data
description: When an authenticated user confirms an account-deletion request, the system shall permanently erase all personal data associated with that account, excluding records under a statutory retention obligation, within 30 days of confirmation.
rationale: GDPR Article 17 (right to erasure) requires that a data subject can have their personal data deleted without undue delay; permanent erasure subject to legal retention carve-outs discharges this obligation and limits the organisation's personal-data liability.
fit_criterion: After deletion completes, a data audit finds 0 personal-data records for the account outside the documented statutory-retention set, and authentication attempts for the account fail 100% of the time.
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: 2026-06-26
traces_from: [BR-001, BR-002, CON-001]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-002 — Permanently delete account and personal data

## Description
When an authenticated user confirms an account-deletion request, the system shall
permanently erase all personal data associated with that account, excluding
records under a statutory retention obligation, within 30 days of confirmation.

## Rationale
GDPR Article 17 (right to erasure) requires that a data subject can have their
personal data deleted without undue delay. Permanent erasure (subject to legal
retention carve-outs) discharges this obligation and limits the organisation's
personal-data liability.

## Acceptance Criteria
### AC-1 — Personal data is erased after confirmed deletion
```gherkin
Given an authenticated user who has confirmed an account-deletion request
When 30 days have elapsed since confirmation
Then all personal data for that account is permanently erased from primary and replica stores
And the account can no longer be authenticated
```

### AC-2 — Statutorily retained records are preserved
```gherkin
Given a deleted account that had financial transaction records under a statutory retention period
When the account's personal data is erased
Then the legally retained financial records are preserved in pseudonymised form
And no other personal data for the account remains
```

## Fit Criterion
After deletion completes, a data audit finds 0 personal-data records for the
account outside the documented statutory-retention set, and authentication
attempts for the account fail 100% of the time.
