---
id: NFR-002
type: non_functional
tier: solution
title: Audit log integrity
description: Order lifecycle events shall be recorded in a tamper-evident log.
rationale: Disputes are resolved from the audit trail.
fit_criterion: 100% of lifecycle events captured with actor, timestamp and outcome.
priority: must
confidence: high
verification_method: inspection
status: draft
created_at: '2026-09-07'
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
---

# NFR-002 — Audit log integrity

## ISO 25010 Characteristic
Security → Accountability

## Quality Attribute Scenario
- **Source of stimulus:** An order lifecycle event
- **Stimulus:** An order is placed, cancelled or fulfilled
- **Environment:** Normal operation
- **Artifact:** Audit logging subsystem
- **Response:** The event is appended immutably
- **Response measure:** 100% of events captured; 0 entries mutable after write
