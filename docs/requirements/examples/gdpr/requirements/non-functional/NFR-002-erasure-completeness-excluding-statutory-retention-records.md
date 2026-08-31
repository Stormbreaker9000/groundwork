---
id: NFR-002
type: non_functional
tier: solution
title: Erasure completeness excluding statutory-retention records
description: After account deletion completes, no personal-data records shall remain in any active data store outside the documented statutory-retention set, and authentication against the deleted account shall no longer succeed.
rationale: Directly protects the success criteria that a post-deletion audit finds 0 personal-data records outside the retention set and that 100% of authentication attempts against the deleted account fail.
fit_criterion: A post-deletion data audit finds 0 personal-data records outside the documented statutory-retention set, and 100% of authentication attempts against the deleted account fail.
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

# NFR-002 — Erasure completeness excluding statutory-retention records

## ISO 25010 Characteristic
Functional Suitability → Functional correctness

## Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject.
- **Stimulus:** Confirms a deletion request via re-authentication.
- **Environment:** Normal operation, after the erasure process completes.
- **Artifact:** Erasure processing subsystem across all catalogued
  personal-data stores.
- **Response:** All personal data is removed except pseudonymised
  statutory-retention records isolated from active stores; the account's
  credentials no longer authenticate.
- **Response measure:** A data audit finds 0 personal-data records
  outside the documented statutory-retention set; 100% of authentication
  attempts against the deleted account fail.

## Rationale
Directly protects the stated success criteria for post-deletion audit
results and authentication failure — the measurable definition of "the
account is actually gone."
