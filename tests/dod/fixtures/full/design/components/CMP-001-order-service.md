---
id: CMP-001
type: component
title: Order Service
description: Owns order state transitions and the cancellation rule.
traces_from: [FR-001, BR-001]
traces_to:
  adr: [ADR-001]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-09-07'
responsibility: Owns order state transitions.
boundary: internal
depends_on: [IF-001]
---

# CMP-001 — Order Service

## Responsibility
Owns order state transitions.
