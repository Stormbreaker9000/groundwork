---
id: FR-003
type: functional
tier: solution
title: Require re-authentication before account deletion
description: If a pending account-deletion request is not confirmed by re-authentication within the 24-hour confirmation window, then the system shall cancel the request and leave the account and its data unchanged.
rationale: Irreversible erasure must be protected against accidental or malicious triggering; requiring fresh re-authentication within a bounded window prevents unauthorised or unintended deletions while still honouring genuine erasure requests.
fit_criterion: 100% of deletion requests lacking successful re-authentication within 24 hours are cancelled with no data mutation, and 0 accounts are deleted without a recorded re-authentication event.
priority: must
confidence: high
verification_method: test
ears_pattern: unwanted
status: draft
created_at: 2026-06-26
traces_from: [FR-002]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-003 — Require re-authentication before account deletion

## Description
If a pending account-deletion request is not confirmed by re-authentication within
the 24-hour confirmation window, then the system shall cancel the request and leave
the account and its data unchanged.

## Rationale
Irreversible erasure must be protected against accidental or malicious triggering;
requiring fresh re-authentication within a bounded window prevents unauthorised or
unintended deletions while still honouring genuine erasure requests.

## Acceptance Criteria
### AC-1 — Unconfirmed deletion request expires safely
```gherkin
Given a pending account-deletion request created more than 24 hours ago
When the confirmation window elapses without successful re-authentication
Then the system cancels the deletion request
And the account and all its data remain unchanged
```

### AC-2 — Re-authenticated request proceeds
```gherkin
Given a pending account-deletion request within the 24-hour confirmation window
When the user successfully re-authenticates and confirms the request
Then the deletion request is accepted for processing
```

## Fit Criterion
100% of deletion requests lacking successful re-authentication within 24 hours are
cancelled with no data mutation, and 0 accounts are deleted without a recorded
re-authentication event.
