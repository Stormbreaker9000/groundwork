---
id: NFR-011
type: non_functional
tier: solution
title: Deletion requires fresh re-authentication and auto-cancels if unconfirmed
description: Account deletion shall execute only after a re-authentication event via the existing identity provider's step-up flow within a 24-hour confirmation window; unconfirmed requests shall auto-cancel with no data mutation.
rationale: Directly protects the success criteria "0 accounts are deleted without a recorded re-authentication event" and "100% of unconfirmed deletion requests are cancelled with no data mutation," and enforces the constraint that re-authentication reuses the existing identity provider's step-up flow rather than a new mechanism.
fit_criterion: 0 accounts are deleted without a recorded re-authentication event within the prior 24 hours; 100% of unconfirmed deletion requests are auto-cancelled at the 24-hour boundary with no data mutation, verified via test.
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

# NFR-011 — Deletion requires fresh re-authentication and auto-cancels if unconfirmed

## ISO 25010 Characteristic
Security → Authenticity / non-repudiation

## Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject, or an attacker
  operating a hijacked or unattended session.
- **Stimulus:** A deletion request is submitted, with or without a
  subsequent step-up re-authentication event.
- **Environment:** Normal operation, within or beyond the 24-hour
  confirmation window.
- **Artifact:** Deletion confirmation flow and its integration with the
  existing identity provider's step-up re-authentication capability.
- **Response:** Deletion executes only if a step-up re-authentication
  event is recorded within the window; otherwise the request is
  automatically cancelled and the account/data are left unchanged.
- **Response measure:** 0 accounts deleted without a recorded
  re-authentication event in the prior 24 hours; 100% of unconfirmed
  requests auto-cancelled with no data mutation.

## Rationale
Because deletion is irreversible with no recovery path, the
re-authentication gate is the last checkpoint against an attacker with
a stolen session, or a user's own accidental click, triggering
permanent account loss.
