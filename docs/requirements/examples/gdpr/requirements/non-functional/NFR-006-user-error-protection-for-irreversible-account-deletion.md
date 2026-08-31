---
id: NFR-006
type: non_functional
tier: solution
title: User error protection for irreversible account deletion
description: The deletion flow shall require an explicit, distinct user acknowledgment of irreversibility in addition to re-authentication before a deletion request is queued.
rationale: Deletion is stated as irreversible with no recovery or undo path; user error protection is the primary control available at the interaction layer against an unrecoverable mistake.
fit_criterion: 100% of deletion initiations require a distinct irreversibility acknowledgment step separate from the re-authentication step, verified via UI test; 0 deletion requests are queued without both steps recorded.
priority: must
confidence: medium
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

# NFR-006 — User error protection for irreversible account deletion

## ISO 25010 Characteristic
Interaction Capability → User error protection

## Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject.
- **Stimulus:** Initiates account deletion.
- **Environment:** Normal operation, self-service deletion flow.
- **Artifact:** Deletion request UI/flow.
- **Response:** The system presents an explicit irreversibility warning
  and requires a distinct confirmation, separate from the
  re-authentication step, before the request is queued.
- **Response measure:** 100% of deletion initiations require the
  distinct acknowledgment step; 0 deletion requests are queued without
  both the acknowledgment and the re-authentication event recorded.

## Rationale
Because "no administrative or automated path restores erased data,"
the interaction design carries real weight in preventing accidental,
unrecoverable harm — this is the interaction-layer counterpart to the
security-layer re-authentication control (NFR-011).
