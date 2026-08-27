---
id: NFR-012
type: non_functional
tier: solution
title: Tamper-evident audit logging of export and deletion events
description: Every export and deletion lifecycle event (request, confirmation, cancellation, completion) shall be recorded in a tamper-evident audit log capturing the actor, timestamp, and outcome of each event, retained for 7 years from the event date.
rationale: 'Explicit non-functional concern in the brief: "Audit logging of export and deletion events is an expected operational concern." An irreversible, legally-consequential action needs a non-repudiable record independent of the account it acted on (the account itself may no longer exist to consult).'
fit_criterion: 100% of export/deletion lifecycle events are captured in the audit log with actor, timestamp, and outcome; log entries are immutable/tamper-evident and retained for 7 years from the event date, verified via inspection of log integrity controls, retention configuration, and a sample compliance audit.
priority: must
confidence: medium
verification_method: inspection
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

# NFR-012 — Tamper-evident audit logging of export and deletion events

## ISO 25010 Characteristic
Security → Accountability / non-repudiation

## Quality Attribute Scenario
- **Source of stimulus:** Any actor (data subject, identity provider
  callback, or system scheduler) causing an export or deletion
  lifecycle event.
- **Stimulus:** A request is created, confirmed, cancelled, or
  completed.
- **Environment:** Normal operation.
- **Artifact:** Audit logging subsystem for export/deletion events.
- **Response:** The event is written to an immutable, tamper-evident
  log entry, independent of the account's own data.
- **Response measure:** 100% of lifecycle events captured with actor,
  timestamp, and outcome; entries are immutable/tamper-evident and
  retained for 7 years from the event date; verified via
  log-integrity inspection, retention-configuration inspection, and a
  sample compliance audit.

## Rationale
After erasure, the account's own records are gone by design; the audit
log is the only remaining evidence that the process was followed
correctly (re-authentication occurred, retention rules were applied),
which is exactly what a regulator or internal auditor would ask to see.
