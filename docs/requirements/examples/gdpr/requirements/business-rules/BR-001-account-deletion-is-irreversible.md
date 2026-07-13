---
id: BR-001
type: business_rule
tier: business
title: Account deletion is irreversible
description: Once an account deletion has completed, it cannot be reversed; the erased personal data is permanently unrecoverable and the account cannot be reinstated.
rationale: The right to erasure is only meaningful if deletion is genuine; retaining a hidden recovery copy would defeat the legal purpose and re-expose the data subject, so irreversibility must be an explicit, communicated policy.
fit_criterion: After deletion completes, no system path — administrative or automated — restores the erased personal data; a recovery attempt in testing succeeds 0% of the time.
priority: must
confidence: high
verification_method: test
status: draft
created_at: 2026-06-26
traces_from: []
traces_to:
  design: []
  tests: []
  code: [FR-002]
scope: project
parent_scope: null
---

# BR-001 — Account deletion is irreversible

## Statement
Once an account deletion has completed, it cannot be reversed: the erased personal
data is permanently unrecoverable and the account cannot be reinstated.

## Implemented by
FR-002 (Permanently delete account and personal data) enforces this policy in the
system.

## Rationale
The right to erasure is only meaningful if deletion is genuine; retaining a hidden
recovery copy would defeat the legal purpose and re-expose the data subject.
Irreversibility must therefore be an explicit, communicated policy.

## Fit Criterion
After deletion completes, there exists no system path — administrative or
automated — that restores the erased personal data; a recovery attempt in testing
succeeds 0% of the time.
