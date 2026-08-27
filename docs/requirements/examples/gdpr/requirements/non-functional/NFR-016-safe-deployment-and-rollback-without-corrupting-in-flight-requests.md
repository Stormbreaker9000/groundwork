---
id: NFR-016
type: non_functional
tier: solution
title: Safe deployment and rollback without corrupting in-flight requests
description: Releases to the export and deletion pipelines shall deploy and, if needed, roll back without leaving an in-flight export or deletion job in an inconsistent or corrupted state.
rationale: Export/deletion jobs run over hours to days against a legal deadline; an ordinary release cadence must not be able to corrupt or silently abandon a job partway through. Not stated explicitly — inferred gap-fill given the long-running, compliance-critical nature of the jobs.
fit_criterion: A deployment or rollback performed while export/deletion jobs are in-flight leaves 0 jobs in an inconsistent state (e.g., partially erased account, orphaned archive), verified via a deployment/rollback demonstration under simulated in-flight load.
priority: could
confidence: low
verification_method: demonstration
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

# NFR-016 — Safe deployment and rollback without corrupting in-flight requests

## ISO 25010 Characteristic
Extension: Deployability

## Quality Attribute Scenario
- **Source of stimulus:** Engineering team performing a release.
- **Stimulus:** A deployment or rollback occurs while export/deletion
  jobs are in-flight.
- **Environment:** Normal release activity.
- **Artifact:** Export generation and erasure processing pipelines and
  their deployment mechanism.
- **Response:** In-flight jobs either complete safely or resume
  cleanly after the release; none are left partially applied.
- **Response measure:** 0 jobs left in an inconsistent state, verified
  via a deployment/rollback demonstration under simulated in-flight
  load.

## Rationale
Given that deletion is irreversible and has no recovery path, a
release-induced partial deletion would be indistinguishable from a
severe data-integrity incident; deployability safeguards are the
operational counterpart to the functional atomicity implied by
NFR-002.
