---
id: NFR-009
type: non_functional
tier: solution
title: Fault tolerance and recovery of export generation
description: Transient failures during export generation shall be automatically retried and recovered without data loss, duplicate archives, or breach of the 30-day ceiling.
rationale: Export generation touches every store in the data map; a single failing dependency should degrade to a retry, not a missed statutory deadline or a corrupted archive.
fit_criterion: Automatic retry resolves >= 99% of transient export-generation failures within 3 attempts; 100% of affected requests still complete within the 30-day statutory ceiling, verified via fault-injection testing.
priority: should
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

# NFR-009 — Fault tolerance and recovery of export generation

## ISO 25010 Characteristic
Reliability → Fault tolerance / recoverability

## Quality Attribute Scenario
- **Source of stimulus:** A transient failure (e.g., data-store
  timeout) during export generation.
- **Stimulus:** One or more source stores fail to respond during
  archive assembly.
- **Environment:** Normal operation, no sustained outage.
- **Artifact:** Export generation pipeline.
- **Response:** The pipeline retries and recovers, producing one
  correct archive with no data loss or duplication.
- **Response measure:** >= 99% of transient failures resolved within 3
  retry attempts; 100% of affected requests still complete within the
  30-day ceiling, verified via fault-injection testing.

## Rationale
Because export completeness is audited at the field level (NFR-001), a
failure that silently drops a store's contribution rather than
retrying would produce an incomplete archive that still "succeeds" —
fault tolerance closes that gap.
