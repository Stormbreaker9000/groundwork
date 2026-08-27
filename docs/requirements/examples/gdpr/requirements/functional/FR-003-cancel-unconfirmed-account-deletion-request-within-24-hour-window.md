---
id: FR-003
type: functional
tier: solution
title: Cancel unconfirmed account deletion request within 24-hour window
description: If an account deletion request is not confirmed via re-authentication within 24 hours of submission, then the system shall cancel the deletion request and leave the account and its personal data unchanged.
rationale: Erasure is irreversible, so the deletion request must be confirmed by the data subject themselves before it proceeds; bounding confirmation to a 24-hour window using the existing identity provider's step-up re-authentication flow prevents an unconfirmed, unauthorized, or abandoned request from leaving the account in an indefinitely pending or accidentally-deleted state.
fit_criterion: 100% of deletion requests left unconfirmed for 24 hours are automatically cancelled with 0 mutations to account state or personal data; 0 accounts are deleted without a corresponding recorded re-authentication event within the 24-hour window.
priority: must
confidence: high
verification_method: test
ears_pattern: unwanted
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

# FR-003 — Cancel unconfirmed account deletion request within 24-hour window

## Description
If an account deletion request is not confirmed via re-authentication
within 24 hours of submission, then the system shall cancel the deletion
request and leave the account and its personal data unchanged.

## Rationale
Erasure is irreversible, so the deletion request must be confirmed by the
data subject themselves before it proceeds; bounding confirmation to a
24-hour window using the existing identity provider's step-up
re-authentication flow prevents an unconfirmed, unauthorized, or abandoned
request from leaving the account in an indefinitely pending or
accidentally-deleted state.

## Acceptance Criteria
### AC-1 — Confirmation within the window proceeds
```gherkin
Given a data subject has submitted an account deletion request
When the data subject completes re-authentication via the identity
  provider within 24 hours of submission
Then the deletion request is confirmed and proceeds to erasure processing
```

### AC-2 — Timeout cancels the request with no changes
```gherkin
Given a data subject has submitted an account deletion request
When 24 hours elapse from submission without the data subject completing
  re-authentication
Then the system cancels the deletion request
And the account and its personal data remain unchanged
```

## Fit Criterion
100% of deletion requests left unconfirmed for 24 hours are automatically
cancelled with 0 mutations to account state or personal data; 0 accounts
are deleted without a corresponding recorded re-authentication event
within the 24-hour window.
