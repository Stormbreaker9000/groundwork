---
id: NFR-015
type: non_functional
tier: solution
title: Monitoring and alerting on requests approaching the statutory deadline
description: Operations shall be alerted when an export or deletion request approaches the 30-day statutory ceiling without completion, so it can be remediated before breach.
rationale: The brief's audit-logging concern establishes that export/deletion events must be observable; alerting on at-risk requests is the natural operational extension needed to actually prevent, not just record, a missed 30-day deadline. Not stated explicitly — inferred gap-fill.
fit_criterion: 100% of export/deletion requests within an assumed 5-day margin of the 30-day ceiling without completion trigger an operational alert, verified via test of the monitoring pipeline; 0 silent breaches.
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

# NFR-015 — Monitoring and alerting on requests approaching the statutory deadline

## ISO 25010 Characteristic
Extension: Observability

## Quality Attribute Scenario
- **Source of stimulus:** Clock / scheduled monitoring job.
- **Stimulus:** An export or deletion request is still open as it nears
  the 30-day statutory ceiling.
- **Environment:** Normal operation.
- **Artifact:** Monitoring/alerting pipeline over export and deletion
  request state.
- **Response:** Operations receives an alert identifying the at-risk
  request before the ceiling is breached.
- **Response measure:** 100% of requests within an assumed 5-day margin
  of the ceiling trigger an alert, verified via test; 0 silent
  breaches.

## Rationale
The 100%-within-30-days success criterion is a compliance-critical
target with no tolerance; achieving it in practice requires visibility
into at-risk requests early enough for a human to intervene, not only
an after-the-fact audit.
