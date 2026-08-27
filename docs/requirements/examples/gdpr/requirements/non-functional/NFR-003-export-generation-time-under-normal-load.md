---
id: NFR-003
type: non_functional
tier: solution
title: Export generation time under normal load
description: Under normal operating load, the system shall generate the export archive and make it available for download with a p95 turnaround of no more than 72 hours, and always within the 30-day statutory ceiling.
rationale: 'FR-001 commits to a 30-day statutory ceiling for data portability requests, but the brief leaves the practical turnaround target open (Q-1, owner: product). A 72-hour p95 budget is an interim engineering target that keeps the self-service export experience responsive well inside the legal ceiling while product confirms the real requirement, so design and capacity planning have a concrete number to build to rather than stalling on the open question.'
fit_criterion: p95 turnaround from export request to archive availability <= 72 hours under normal load (export-worker utilisation <= 80%), and 100% of exports available for download within the 30-day statutory ceiling, measured over a rolling 30-day window.
priority: must
confidence: low
verification_method: test
status: draft
created_at: '2026-08-26'
traces_from:
- FR-001
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-003 — Export generation time under normal load

## ISO 25010 Characteristic
Performance Efficiency → Time behavior

## Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject.
- **Stimulus:** Submits a request to export their personal data.
- **Environment:** Normal operating load, export-worker utilisation
  <= 80%.
- **Artifact:** Export generation service and the durable object
  store holding generated archives (D-1).
- **Response:** The export archive is generated and made available
  for download via an authenticated link (see NFR-001).
- **Response measure:** p95 turnaround <= 72 hours; 100% of exports
  available within the 30-day statutory ceiling, measured over a
  rolling 30-day window.

## Rationale
FR-001 commits to a 30-day statutory ceiling for data portability
requests, but the brief leaves the practical turnaround target open
(Q-1, owner: product). A 72-hour p95 budget is an interim
engineering target that keeps the self-service export experience
responsive well inside the legal ceiling while product confirms the
real requirement, so design and capacity planning have a concrete
number to build to rather than stalling on the open question.
