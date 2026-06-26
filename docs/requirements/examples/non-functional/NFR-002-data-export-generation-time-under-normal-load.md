---
id: NFR-002
type: non_functional
tier: solution
title: Data export generation time under normal load
description: Under normal operating load, the system shall generate and make available a typical user's data-export archive well within the statutory deadline.
rationale: The 30-day statutory ceiling is a legal backstop, not a user-experience target; generating typical exports within an hour keeps the feature usable and prevents a backlog that would risk breaching the legal deadline under load.
fit_criterion: 95% of export requests for accounts holding <= 1 GB of personal data complete and become available within 1 hour, and 100% complete within the 30-day legal ceiling, measured at <= 80% export-worker utilisation.
priority: should
confidence: high
verification_method: test
status: draft
created_at: 2026-06-26
traces_from: [FR-001]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-002 — Data export generation time under normal load

## ISO 25010 Characteristic
Performance Efficiency → Time behavior

## Quality Attribute Scenario
- **Source of stimulus:** An authenticated user.
- **Stimulus:** Submits a data-export request for a typical account.
- **Environment:** Normal operating load, with export workers at or below 80% utilisation.
- **Artifact:** The asynchronous data-export generation service.
- **Response:** The archive is assembled across all personal-data stores and made available for download.
- **Response measure:** 95% of export requests for accounts holding <= 1 GB of personal data complete and become available within 1 hour; 100% complete within the 30-day legal ceiling.

## Rationale
The 30-day statutory ceiling is a legal backstop, not a user-experience target;
generating typical exports within an hour keeps the feature usable and prevents a
backlog that would risk breaching the legal deadline under load.
