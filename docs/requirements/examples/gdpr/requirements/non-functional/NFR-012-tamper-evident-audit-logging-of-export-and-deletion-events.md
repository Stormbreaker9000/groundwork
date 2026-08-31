---
id: NFR-012
type: non_functional
tier: solution
title: Tamper-evident audit logging of export and deletion events
description: Every export and deletion lifecycle event (request, confirmation, cancellation, completion) shall be recorded in a tamper-evident audit log capturing the actor, timestamp, and outcome of each event, retained indefinitely with no automated deletion until a future retention policy is defined (open question Q-3).
rationale: 'Explicit non-functional concern in the brief: "Audit logging of export and deletion events is an expected operational concern." An irreversible, legally-consequential action needs a non-repudiable record independent of the account it acted on (the account itself may no longer exist to consult). The elicited context specifies no retention period for this log (Q-3, owner: legal); retaining entries indefinitely by default, with no automated purge, is the safer interim posture until a retention policy is set, since under-retaining a compliance record is far costlier than a temporarily larger retention footprint.'
fit_criterion: 100% of export/deletion lifecycle events are captured in the audit log with actor, timestamp, and outcome; log entries are immutable/tamper-evident; no automated deletion occurs absent a defined retention policy (open question Q-3); verified via inspection of log integrity controls and a sample compliance audit.
priority: must
confidence: low
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
  timestamp, and outcome; entries are immutable/tamper-evident; no
  automated deletion occurs absent a defined retention policy (open
  question Q-3); verified via log-integrity inspection and a sample
  compliance audit.

## Rationale
After erasure, the account's own records are gone by design; the audit
log is the only remaining evidence that the process was followed
correctly (re-authentication occurred, retention rules were applied),
which is exactly what a regulator or internal auditor would ask to see.
No retention duration for this log is specified anywhere in the
elicited context, so no duration is asserted here; entries are kept
indefinitely by default until legal defines the actual required
retention period (Q-3).
